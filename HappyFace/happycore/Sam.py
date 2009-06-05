from ModuleBase import *
from DownloadTag import *
from XMLParsing import *

#############################################
# class to donwload plots (via WGET command)
# self.url has to be defined by the inhereting module
#############################################

class Sam(ModuleBase):

    def __init__(self, category, timestamp, archive_dir):
        ModuleBase.__init__(self, category, timestamp, archive_dir)

        # read class config file
	config = self.readConfigFile('./happycore/Sam') # empty

	self.addCssFile(config,'./happycore/Sam')

        # definition of the database table keys and pre-defined values

	self.db_keys["details_database"] = StringCol()
	self.db_keys["site"] =	StringCol()
	
	self.db_values["details_database"] = ""
	self.db_values["site"] = ""
	
	
	self.base_url = self.mod_config.get('setup','base_url')
	self.report_url	= self.mod_config.get('setup','report_url')
        self.phpArgs = {}
        self.fileType = ""
	
        if self.mod_config.has_option('setup','fileextension'):
            self.fileType = self.mod_config.get('setup','fileextension')


        # read module specific phpArgs from modul config file
        self.getPhpArgs(self.mod_config)	
	
        self.dsTag = 'sam_xml_source'

        self.makeUrl()

    def getPhpArgs(self, config):
        for i in config.items('phpArgs'):
            self.phpArgs[i[0]] = i[1]
	
    def makeUrl(self):
        if len(self.phpArgs) == 0:
            print "PhpPlot Error: makeUrl called without phpArgs"
            sys.exit()
        if self.base_url == "":
            print "PhpPlot Error: makeUrl called without base_url"
            sys.exit()


        argList = []
        for i in self.phpArgs:
	    for j in self.phpArgs[i].split(","):
		argList.append(i+'='+j)

        #argList.sort()
        self.downloadRequest[self.dsTag] = 'wgetXmlRequest:'+self.fileType+':'+self.base_url+"?"+"&".join(argList)

	
    def run(self):

        # run the test

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

	# parse the details and store it in a special database table
	details_database = self.__module__ + "_details_" + str(self.timestamp) + "_table"
	
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

	details_db_keys["service_type"] = StringCol()
	details_db_keys["service_name"] = StringCol()
	details_db_keys["service_status"] = StringCol()
	details_db_keys["status"] = StringCol()
	details_db_keys["url"] = StringCol()
	details_db_keys["age"] = StringCol()
	details_db_keys["type"] = StringCol()
	details_db_keys["time"] = StringCol()

	# lock object enables exclusive access to the database
	self.lock.acquire()

	Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

	Details_DB_Class.sqlmeta.cacheValues = False
	Details_DB_Class.sqlmeta.fromDatabase = True
	#Details_DB_Class.sqlmeta.lazyUpdate = True

	# if table is not existing, create it
        Details_DB_Class.createTable(ifNotExists=True)

	root = source_tree.getroot()
	
	for element in root:
	    if element.tag == "data": data_branch = element

	for element in data_branch:
	    for item in element:
	        if item.tag == "Services": services = item
		if item.tag == "VOName": self.db_values["site"] = item.text

	sn = {}
	tests = {}
	
	ServiceName = ""
	ServiceStatus = ""
	Status = ""
	Url = ""
	Age = ""
	Type = ""
	Time = ""

	for services_item in services:

	    for services_prop in services_item:
		if services_prop.tag == "ServiceType":
		    ServiceType = services_prop.text

	    for services_prop in services_item:
		if services_prop.tag == "ServiceNames":
		    sn = services_prop

		    for sn_item in sn:
			
		        for sn_prop in sn_item:
			    if sn_prop.tag == "ServiceName":
			        ServiceName = sn_prop.text

			for sn_prop in sn_item:
			    if sn_prop.tag == "ServiceStatus":
			        ServiceStatus = sn_prop.text

			for sn_prop in sn_item:
			    if sn_prop.tag == "Tests":
			        tests = sn_prop

			        for tests_item in tests:

			            for tests_prop in tests_item:

				        if tests_prop.tag == "Status": Status = tests_prop.text
				        elif tests_prop.tag == "Url": Url = tests_prop.text
				        elif tests_prop.tag == "Age": Age = tests_prop.text
				        elif tests_prop.tag == "Type": Type = tests_prop.text
				        elif tests_prop.tag == "Time": Time = tests_prop.text
			
				    details_db_values["service_type"] = ServiceType
				    details_db_values["service_name"] = ServiceName
				    details_db_values["service_status"] = ServiceStatus
				    details_db_values["status"] = Status
				    details_db_values["url"] = (self.report_url + Url.__str__()).replace('&','&amp;').replace('%','%%')
				    details_db_values["age"] = Age
				    details_db_values["type"] = Type
				    details_db_values["time"] = Time

				    # store the values to the database
				    Details_DB_Class(**details_db_values)

	# unlock the database access
	self.lock.release()

        # at the moment always happy
        self.status = 1.0


    def output(self):

        # this module_content string will be executed by a printf('') PHP command
        # all information in the database are available via a $data["key"] call
        module_content = """
        <?php
	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"];
	$temp_element = "";
		
	printf('<table class="SamTable">');
	
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
	    if ($temp_element != $info["service_name"]) {

		if ($info["service_status"] == "1") {
		    $service_status_color_flag = "success";
		} else {
		    $service_status_color_flag = "fail";
		}
		
		printf('<tr class="' .$service_status_color_flag . '"><td><strong>' . $info["service_type"] . '</strong></td><td><strong>' . $info["service_name"] . '</strong></td></tr>');
	    }
	    $temp_element = $info["service_name"];
	}
	
	printf('</table><br/>');
	
	printf('
		<input type="button" value="error/warning results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """);" />
		<input type="button" value="successful results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_success_result\\\'" + """);" />
		<div class="SamDetailedInfo" id=""" + "\\\'" + self.__module__+ "_success_result\\\'" + """ style="display:none;">
		<table class="SamTableDetails">
			<tr><td><strong>Element Type</strong></td><td><strong>Element Name</strong></td><td><strong>Status</strong></td><td><strong>Test Name</strong></td><td><strong>Test Time</strong></td></tr>
	    ');
	
	foreach ($dbh->query($details_db_sqlquery) as $results)
	{
	    if ($results["status"] == "ok")
		printf('<tr>
			<td>'.$results["service_type"].'</td>
			<td>'.$results["service_name"].'</td>
			<td><a href="'.$results["url"].'"><strong>'.$results["status"].'</strong></a></td>
			<td>'.$results["type"].'</td>
			<td>'.$results["time"].'</td>
		</tr>');
	}
	printf('</table></div>');

	printf('
		<div class="SamDetailedInfo" id=""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """ style="display:none;">
		<table class="SamTableDetails">
		<tr><td><strong>Element Type</strong></td><td><strong>Element Name</strong></td><td><strong>Status</strong></td><td><strong>Test Name</strong></td><td><strong>Test Time</strong></td></tr>
	    ');
	
	foreach ($dbh->query($details_db_sqlquery) as $results)
	{
	    if ($results["status"] != "ok" && $results["status"] != "")
		printf('<tr>
			<td>'.$results["service_type"].'</td>
			<td>'.$results["service_name"].'</td>
			<td><a href="'.$results["url"].'"><strong>'.$results["status"].'</strong></a></td>
			<td>'.$results["type"].'</td>
			<td>'.$results["time"].'</td>
		</tr>');
	}
	printf('</table></div><br/>');
	?>
	"""

        return self.PHPOutput(module_content)
