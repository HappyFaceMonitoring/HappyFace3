from ModuleBase import *
from XMLParsing import *

class PhedexStats(ModuleBase):

    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)

	self.db_keys["startlocaltime"] = StringCol()
	self.db_keys["endlocaltime"] = StringCol()
	self.db_keys["total_transfers"] = IntCol()
	self.db_keys["failed_transfers"] = IntCol()
	self.db_keys["details_database"] = StringCol()

	self.db_values["startlocaltime"] = ""
	self.db_values["endlocaltime"] = ""
	self.db_values["total_transfers"] = None
	self.db_values["failed_transfers"] = None
	self.db_values["details_database"] = ""

        self.dsTag = 'phedex_xml_source'

    def run(self):

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

        dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
        if dl_error != "":
            self.error_message+= dl_error
            return

	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)
        self.error_message += xml_error

        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

	root = source_tree.getroot()
	
	root_attrib = root.attrib
	self.db_values["startlocaltime"] = root_attrib["startlocaltime"]
	self.db_values["endlocaltime"] = root_attrib["endlocaltime"]

	# pre-defined direction of transfers
	transfer_direction = "incoming"

	total_transfers = 0

	for element in root:
	    if element.tag == "SiteStat":
		for fromsite in element:
		    fromsite_attrib = fromsite.attrib

		    # check for the direction of transfers
		    # for outgoing tranfers there is no information about total/successful transfers
		    if fromsite_attrib["name"] == "noinfo":
			transfer_direction = "outgoing"
			total_transfers = None
			break
		    if "OK" in fromsite_attrib:		total_transfers = total_transfers + int(fromsite_attrib["OK"])
		    if "FAILED" in fromsite_attrib:	total_transfers = total_transfers + int(fromsite_attrib["FAILED"])
	
	self.db_values["total_transfers"] = total_transfers


	#############################################################################
	# parse the details and store it in a special database table
	details_database = self.__module__ + "_table_details"
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

	details_db_keys["site_name"] = StringCol()
	details_db_keys["number"] = IntCol()
	details_db_keys["origin"] = StringCol()
	details_db_keys["error_message"] = StringCol()
	


	my_subtable_class = self.table_init( details_database, details_db_keys )

	failed_transfers = 0

	for element in root:

	    if element.tag == "fromsite":
		if transfer_direction == "incoming": details_db_values["site_name"] = element.attrib["name"]

		for tosite in element:

		    for reason in tosite:

			if transfer_direction == "outgoing": details_db_values["site_name"] = tosite.attrib["name"]
			details_db_values["number"] = int(reason.attrib["n"])
			details_db_values["origin"] = reason.attrib["origin"]
			details_db_values["error_message"] = reason.text
			
			failed_transfers = failed_transfers + int(reason.attrib["n"])
			
			# store the values to the database
			self.table_fill( my_subtable_class, details_db_values )
	

	self.db_values["failed_transfers"] = failed_transfers

	# at the moment always happy
	self.status = 1.0

    def output(self):

	begin = []
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="PhedexStatsTableFirstCol">Start Time</td>')
	begin.append("""  <td>'.$data["startlocaltime"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="PhedexStatsTableFirstCol">End Time</td>')
	begin.append("""  <td>'.$data["endlocaltime"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br />')
	begin.append(  '')
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="PhedexStatsTableFirstCol">Total Transfers</td>')
	begin.append("""  <td>'.$data["total_transfers"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="PhedexStatsTableFirstCol">Failed Transfers</td>')
	begin.append("""  <td>'.$data["failed_transfers"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br />')
	begin.append(  '')
	begin.append("""<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_result\\\');" />""")
	begin.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_result" style="display:none;">')
	begin.append(  ' <table class="TableDetails">')
	begin.append(  '  <tr class="TableHeader">')
	begin.append(  '   <td>Site Name</td>')
	begin.append(  '   <td>Failed Transfers</td>')
	begin.append(  '   <td>Origin</td>')
	begin.append(  '   <td>Error Message</td>')
	begin.append(  '  </tr>')

	detailed_row = []
	detailed_row.append(  '  <tr class="report">')
	detailed_row.append("""   <td>' . $info["site_name"] . '</td>""")
	detailed_row.append("""   <td>' . $info["number"] . '</td>""")
	detailed_row.append("""   <td>' . $info["origin"] . '</td>""")
	detailed_row.append("""   <td>' . trim($info["error_message"]) . '</td>""")
	detailed_row.append(  '  </tr>');

	end = []
	end.append(  ' </table>')
	end.append(  '</div>')
	end.append(  '<br />')

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call
        module_content = """<?php
	
	if ($data["total_transfers"] == "") {
		$data["total_transfers"] = "no information";
	}
	
	printf('""" + self.PHPArrayToString(begin) + """');
	
	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		printf('""" + self.PHPArrayToString(detailed_row) + """');
	}

	printf('""" + self.PHPArrayToString(end) + """');
	?>"""

        return self.PHPOutput(module_content)
