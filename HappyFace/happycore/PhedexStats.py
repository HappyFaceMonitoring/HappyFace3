from ModuleBase import *
from XMLParsing import *

class PhedexStats(ModuleBase):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,category,timestamp,storage_dir)

	config = self.readConfigFile('./happycore/PhedexStats')
	self.addCssFile(config,'./happycore/PhedexStats')

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

        success,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
	source_tree = XMLParsing().parse_xmlfile_lxml(sourceFile)

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

	# write global after which the query will work
	details_db_keys["timestamp"] = IntCol()
	details_db_values["timestamp"] = self.timestamp

	# create index for timestamp
	details_db_keys["index"] = DatabaseIndex('timestamp')

	details_db_keys["site_name"] = StringCol()
	details_db_keys["number"] = IntCol()
	details_db_keys["origin"] = StringCol()
	details_db_keys["error_message"] = StringCol()
	
	# lock object enables exclusive access to the database
	self.lock.acquire()

	Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

	Details_DB_Class.sqlmeta.cacheValues = False
	Details_DB_Class.sqlmeta.fromDatabase = True
	#Details_DB_Class.sqlmeta.lazyUpdate = True
		
	# if table is not existing, create it
        Details_DB_Class.createTable(ifNotExists=True)

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
			Details_DB_Class(**details_db_values)
	
	# unlock the database access
	self.lock.release()

	self.db_values["failed_transfers"] = failed_transfers

	# at the moment always happy
	self.status = 1.0

    def output(self):

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call
        module_content = """
	<?php
	
	if ($data["total_transfers"] == "") {
		$data["total_transfers"] = "no information";
	}
	
	printf('
	<table class="PhedexStatsTable">
		<tr>
			<td>Start Time</td><td>'.$data["startlocaltime"].'</td>
		</tr>
               	<tr>
			<td>End Time</td><td>'.$data["endlocaltime"].'</td>
		</tr>
	</table>
	<br/>

	<table class="PhedexStatsTable">
		<tr>
			<td>Total Transfers</td><td>'.$data["total_transfers"].'</td>
		</tr>
               	<tr>
			<td>Failed Tranfers</td><td>'.$data["failed_transfers"].'</td>
		</tr>
	</table>
	<br />

	<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />
	<div class="PhedexStatsDetailedInfo" id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">
	<table class="PhedexStatsTableDetails">
		<tr><td><strong>Site Name</strong></td><td><strong>Failed Transfers</strong></td><td><strong>Origin</strong></td><td><strong>Error Message</strong></td></tr>
	');
	
	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		printf('<tr><td>'.$info["site_name"].'</td><td>'.$info["number"].'</td><td>'.$info["origin"].'</td><td>'.$info["error_message"].'</td></tr>');
	}
	printf('</table></div><br/>')
	?>
	"""

        return self.PHPOutput(module_content)
