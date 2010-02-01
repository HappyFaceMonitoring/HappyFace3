##############################################
# PhEDEx Block Consistency module 
# Created: N.Ratnikova 09-10-09.
##############################################

from ModuleBase import *
from XMLParsing import *

class CMSPhedexBlockConsistency(ModuleBase):
    """
    Module to show results of the PhEDEx block consistency check.
    """
    def __init__(self,category,timestamp,storage_dir):
        """
         Defines keys for the module database table.
        """
        ModuleBase.__init__(self,category,timestamp,storage_dir)
        self.warning_limit = float(self.configService.get("setup",
                                                          "warning_limit"))
        self.old_result_warning_limit = float(self.configService.get("setup",
                                                          "old_result_warning_limit"))
        self.dsTag = 'consistency_xml_source'
        # Module table description:
        self.db_keys["buffer"] = StringCol(default=None)
        self.db_keys["application"] = StringCol(default=None)
        self.db_keys["test"] = StringCol(default=None)

        self.db_keys["starttime"] = StringCol(default=None)
        self.db_keys["endtime"] = StringCol(default=None)
        self.db_keys["duration"] = StringCol(default=0)
        self.db_keys["warning_limit"] = FloatCol(default=self.warning_limit)

        self.db_keys["technology"] = StringCol(default=None)
        self.db_keys["protocol"] = StringCol(default=None)
        self.db_keys["dumpfile"] = StringCol(default=None)

        self.db_keys["total_datasets"] = IntCol(default=0)
        self.db_keys["total_blocks"] = IntCol(default=0)
        self.db_keys["total_files"] = IntCol(default=0)

        self.db_keys["failed_datasets"] = IntCol(default=0)
        self.db_keys["failed_blocks"] = IntCol(default=0)
        self.db_keys["failed_files"] = IntCol(default=0)

        self.db_keys["total_size"] = StringCol(default=None)

	############################################################
	# Dump detailed information about files into details table
	self.details_database = self.__module__ + "_table_details"

    def __old_result__(self):
        # Get starttime in unix format from the name of the dumpfile:
        tmp=os.path.basename(self.db_values["dumpfile"])
        # Convert result age into hours:
        result_age = (float(self.timestamp) - float(tmp.split('.')[0]))/3600.0
        if (result_age > self.old_result_warning_limit):
            return self.old_result_warning_limit

    def run(self):
        """
        Downloads input source xml file.
        Parses xml document and saves data in the database.
        Defines algorithm for module status.
        """
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


        #######################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

	root = source_tree.getroot()

        ###############################################################
        for data in root:
            if data.tag == "test_summary":
                for element in data.iter():
                    if element.tag == "application":
                        element_attrib = element.attrib
                        self.db_values["buffer"] =  element_attrib["buffer"]
                        self.db_values["application"] =  element_attrib["name"]
                        self.db_values["test"] =  element_attrib["test"]

                        self.db_values["starttime"] = element_attrib["starttime"]
                        self.db_values["endtime"] = element_attrib["endtime"]
                        self.db_values["duration"] = element_attrib["duration"]

                        self.db_values["technology"] =  element_attrib["technology"]
                        self.db_values["protocol"] =  element_attrib["protocol"]
                        self.db_values["dumpfile"] =  element_attrib["dump"]

                    if element.tag == "total":
                        element_attrib = element.attrib
                        self.db_values["total_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["total_blocks"] =  int(element_attrib["blocks"])
                        self.db_values["total_files"] =  int(element_attrib["lfns"])
                        self.db_values["total_size"] =  element_attrib["size"]

                    if element.tag == "number_of_affected":
                        element_attrib = element.attrib
                        self.db_values["failed_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["failed_blocks"] =  int(element_attrib["blocks"])
                        self.db_values["failed_files"] =  int(element_attrib["files"])


        # Details table description:
	details_db_keys = {}

        details_db_keys["lfn"] = StringCol()
        details_db_keys["status"] = StringCol()
        details_db_keys["dataset"] = StringCol()
        details_db_keys["block"] = StringCol()

	my_subtable_class = self.table_init( self.details_database, details_db_keys )

        # Fill in the values:
	details_db_values = {}

        for data in root:
            if data.tag == "details":
                for element in data.iter():
                    if element.tag == "file":
                        element_attrib = element.attrib
                        details_db_values["lfn"] =  element_attrib["name"]
                        details_db_values["status"] =  element_attrib["status"]
                        details_db_values["dataset"] =  element_attrib["dataset"]
                        details_db_values["block"] =  element_attrib["block"]
                        # write details to databse

                        self.table_fill( my_subtable_class, details_db_values )

        

        ################################
        # Rating algorithm
        # Status legend:
        #  1.0  = success
        #  0.5  = warning # duration and/or result age exceed warning limit
        #  0.0  = error   # at least one dataset failed
        self.status = 1.0
        #------------------------------
        # Warning conditions definition:
        duration=float(self.db_values["duration"])
        if duration > self.warning_limit:
            self.status = 0.5
        if (self. __old_result__()):
            self.status = 0.5
        #------------------------------
        # Error condition definition:
        failed_datasets=int(self.db_values["failed_datasets"])
        if failed_datasets > 0:
            self.status = 0.0

    def output(self):
	""" Creates module contents for the web page, filling in
        the data from the database.
        """
        # Predefine warnings to be inserted in output:
        warning_color=""
        if (self.__old_result__()):
            warning_message="<p class=CMSPhedexBlockConsistencyWarningMessage> WARNING: Result is older than " + str(self.__old_result__()) + " hours</p>"
            warning_color=" class=warning"
	module_content = """
	<?php
        if ($data["status"] == "1.0"){
        $status_color="ok";
        }elseif ($data["status"] == "0.0"){
        $status_color="critical";
        }
        if ($data["duration"] >= $data["warning_limit"]){
        $duration_color="warning";
        }

	printf('"""+warning_message+"""
        
	<table class="TableDataSmall">
		<tr class=\"TableHeader\">
                  <td>Buffer:</td>
                  <td>'.$data["buffer"].'</td>
                </tr>
		<tr>
                  <td>Application:</td>
                  <td>'.$data["application"].'</td>
                </tr>
		<tr>
                  <td>Test:</td>
                  <td>'.$data["test"].'</td>
                </tr>
		<tr"""+warning_color+""">
                  <td>Started:</td>
                  <td>'.$data["starttime"].'</td>
                </tr>
               	<tr>
                  <td>Ended:</td>
                  <td>'.$data["endtime"].'</td>
                </tr>
               	<tr class=\"'.$duration_color.'\">
                  <td>Duration:</td>
                  <td>'.$data["duration"].' hours <br />warning limit: '.$data["warning_limit"].'</td>
                </tr>
                <tr>
                  <td>Total size:</td>
                  <td>'.$data["total_size"].'</td>
                </tr>
		<tr>
                  <td>Technology:</td>
                  <td>'.$data["technology"].'</td>
                </tr>
		<tr>
                  <td>Protocol:</td>
                  <td>'.$data["protocol"].'</td>
                </tr>
<!--
               	<tr>
                  <td>Input file:</td>
                  <td>'.$data["dumpfile"].'</td>
                </tr>
-->
	</table>
    <br />
	<table class="TableDataSmall">
                <tr class=\"TableHeader\">
                  <td> Tested:</td>
                  <td> Datasets:</td>
                  <td> Blocks:</td>
                  <td> Files:</td>
                </tr>
                <tr>
                  <td> Total:</td>
                  <td>'.$data["total_datasets"].'</td>
                  <td>'.$data["total_blocks"].'</td>
                  <td>'.$data["total_files"].'</td>
                </tr>
                <tr class=\"'.$status_color.'\">
                  <td> Failed:</td>
                  <td>'.$data["failed_datasets"].'</td>
                  <td>'.$data["failed_blocks"].'</td>
                  <td>'.$data["failed_files"].'</td>
                </tr>
	</table>
	<br/>

	<input type="button" value="show/hide Failed Datasets" onfocus="this.blur()" onclick="show_hide(\\\'datasets_details\\\');" />
	<div class="DetailedInfo" id=\\\'datasets_details\\\' style="display:none;">

	<table class="TableDetails">
            <tr class=\"TableHeader\">
		<td>Dataset</td>
		<td>Failed Blocks</td>
		<td>Failed Files</td>
		</tr>
    
	');

	$details_db_sqlquery = "SELECT dataset, count(distinct block) as blocks, count(distinct lfn) as files FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"] . " group by dataset";
        
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		printf('<tr>
                        <td>'.$info["dataset"].'</td>
			<td>'.$info["blocks"].'</td>
			<td>'.$info["files"].'</td>
                        </tr>'
		);
	}

	printf('</table></div><br/>

	<input type="button" value="show/hide Inconsistent Files" onfocus="this.blur()" onclick="show_hide(\\\'files_details\\\');" />
	<div class="DetailedInfo" id=\\\'files_details\\\' style="display:none;">

	<table class="TableDetails">
            <tr class=\"TableHeader\">
		<td>Logical File Name</td>
		<td>Status</td>
		</tr>
	');

	$details_db_sqlquery = "SELECT * FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		printf('<tr>
                        <td>'.$info["lfn"].'</td>
			<td>'.$info["status"].'</td>
                        </tr>'
		);
	}
	printf('</table></div><br/>')

	?>
	"""
	return self.PHPOutput(module_content)
