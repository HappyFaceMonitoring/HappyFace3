##############################################
# Quick Consistency Check module 
# Created: N.Ratnikova 29-11-2009.
##############################################

from ModuleBase import *
from XMLParsing import *
################################################################
# Module to store and display results of Quick Consistency Check
# produced by quickConsistencyCheck script.
#################################################################
class CMSFileConsistencyCheck(ModuleBase):
    # Defines keys for the module database tables.
    def __init__(self,module_options):
        ModuleBase.__init__(self,module_options)
        self.duration_warning_limit = float(self.configService.get("setup",
                                                                   "duration_warning_limit"))
        self.duration_critical_limit = float(self.configService.get("setup",
                                                                    "duration_critical_limit"))
        self.old_result_warning_limit = float(self.configService.get("setup",
                                                                     "old_result_warning_limit"))
        self.old_result_critical_limit = float(self.configService.get("setup",
                                                                      "old_result_critical_limit"))

        self.dsTag = 'consistency_xml_source'
        # Module table description:
        self.db_keys["reference"] = StringCol(default=None)
        self.db_keys["buffer"] = StringCol(default=None)
        self.db_keys["application"] = StringCol(default=None)
        self.db_keys["query"] = StringCol(default=None)

        self.db_keys["starttime"] = StringCol(default=None)
        self.db_keys["endtime"] = StringCol(default=None)
        self.db_keys["duration"] = StringCol(default='0')
        self.db_keys["duration_warning_limit"] = FloatCol(default=self.duration_warning_limit)
        self.db_keys["duration_critical_limit"] = FloatCol(default=self.duration_critical_limit)
        self.db_keys["old_result_warning_limit"] = FloatCol(default=self.old_result_warning_limit)
        self.db_keys["old_result_critical_limit"] = FloatCol(default=self.old_result_critical_limit)

        self.db_keys["protocol"] = StringCol(default=None)
        self.db_keys["logs"] = StringCol(default=None)

        self.db_keys["total_datasets"] = IntCol(default=0)
        self.db_keys["total_files"] = IntCol(default=0)

        self.db_keys["failed_datasets"] = IntCol(default=0)
        self.db_keys["failed_blocks"] = IntCol(default=0)
        self.db_keys["failed_files"] = IntCol(default=0)

        self.db_keys["total_size"] = StringCol(default=None)

	############################################################
	# Dump detailed information about files into details table  
	self.details_database = self.__module__ + "_table_details"

    def __old_result__(self):
        # Get starttime in unix format from the name of the logfile:
        tmp=os.path.basename(self.db_values["logs"])
        result_age = (float(self.timestamp) - float(tmp))/3600.0
        if (result_age > self.old_result_critical_limit):
            return 0.0
        if (result_age > self.old_result_warning_limit):
            return 0.5
	return 1.0

    def __duration_limit__(self):
        # Convert duration in hours, check limits
        durationHours=float(self.db_values['duration'])/3600
        if (durationHours > self.duration_critical_limit):
            return 0.0
        if (durationHours > self.duration_warning_limit):
            return 0.5
	return 1.0

    def process(self):
        """
        Downloads input source xml file.
        Parses xml document and saves data in the database.
        Defines algorithm for module status.
        """

	self.configService.addToParameter('setup', 'definition', '<br/><br/>Duration warning limit: ' + str(self.duration_warning_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br/>Duration critical limit: ' + str(self.duration_critical_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br/>Old result warning limit: ' + str(self.old_result_warning_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br/>Old result critical limit: ' + str(self.old_result_critical_limit) + ' hours')

        dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)

        self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))

	root = source_tree.getroot()

        ###############################################################
        for data in root:
            if data.tag == "test_summary":
                for element in data.iter():
                    if element.tag == "application":
                        element_attrib = element.attrib
                        self.db_values["reference"]   = element_attrib["reference"]
                        self.db_values["buffer"]      = element_attrib["buffer"]
                        self.db_values["application"] = element_attrib["name"]
                        self.db_values["query"]       = element_attrib["query"]
                        self.db_values["starttime"]   = element_attrib["starttime"]
                        self.db_values["endtime"]     = element_attrib["endtime"]
                        self.db_values["duration"]    = element_attrib["duration"]
                        self.db_values["protocol"]    = element_attrib["protocol"]
                        self.db_values["logs"]        = element_attrib["logs"]

                    if element.tag == "total":
                        element_attrib = element.attrib
                        self.db_values["total_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["total_files"]    =  int(element_attrib["lfns"])
                        self.db_values["total_size"]     =  element_attrib["size"]

                    if element.tag == "number_of_affected":
                        element_attrib = element.attrib
                        self.db_values["failed_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["failed_files"]    =  int(element_attrib["files"])

        # Details table description:
	details_db_keys = {}

        details_db_keys["lfn"]     = StringCol()
        details_db_keys["status"]  = StringCol()
        details_db_keys["dataset"] = StringCol()

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
        duration = float(self.db_values["duration"])/3600
        self.status = min(self.status, self.__duration_limit__())
        self.status = min(self.status, self.__old_result__())
        #------------------------------
        # Error condition definition:
        failed_datasets=int(self.db_values["failed_datasets"])
        if failed_datasets > 0:
            self.status = 0.0

    # Creates module contents for the web page, filling in
    # the data from the database.
    def output(self):
        # Predefine warnings to be inserted in output:
	duration_warning_message = []
	duration_critical_message = []
        old_result_warning_message = []
        old_result_critical_message = []

        old_result_warning_message.append("""<p class="quick_consistency_checkWarningMessage">WARNING: Result is older than ' . $data['old_result_warning_limit'] . ' hours</p>""")
        old_result_critical_message.append("""<p class="quick_consistency_checkWarningMessage">WARNING: Result is older than ' . $data['old_result_critical_limit'] . ' hours</p>""")

	duration_warning_message.append("""<p class="quick_consistency_checkWarningMessage">WARNING: Duration is more than ' . $data['duration_warning_limit'] . ' hours</p>""")
	duration_critical_message.append("""<p class="quick_consistency_checkWarningMessage">WARNING: Duration is more than ' . $data['duration_critical_limit'] . ' hours</p>""")

        mc_begin = []
	mc_begin.append(  '<table class="TableDataSmall">')
	mc_begin.append(  ' <tr class=\"TableHeader\">')
        mc_begin.append(  '  <td>Reference:</td>')
        mc_begin.append("""  <td>'.$data["reference"].'</td>""")
        mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr class=\"TableHeader\">')
        mc_begin.append(  '  <td>Buffer:</td>')
        mc_begin.append("""  <td>'.$data["buffer"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Application:</td>')
        mc_begin.append("""  <td>'.$data["application"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Query:</td>')
        mc_begin.append("""  <td>'.$data["query"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Test:</td>')
        mc_begin.append(  '  <td>file size</td>')
        mc_begin.append(  ' </tr>')
	mc_begin.append(""" <tr'.$old_result_color.'>""")
        mc_begin.append(  '  <td>Started:</td>')
        mc_begin.append("""  <td>'.$data["starttime"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(""" <tr'.$old_result_color.'>""")
        mc_begin.append(  '  <td>Ended:</td>')
        mc_begin.append("""  <td>'.$data["endtime"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(""" <tr'.$duration_color.'>""")
        mc_begin.append(  '  <td>Duration:</td>')
        mc_begin.append("""  <td>'.secondsToWords_""" + self.__module__ + """($data["duration"]).'<br />warning limit: '.$data["warning_limit"].' hours</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Total size:</td>')
        mc_begin.append("""  <td>'.$data["total_size"].'</td>""")
        mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Protocol:</td>')
        mc_begin.append("""  <td>'.$data["protocol"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td>Log files directory:</td>')
        mc_begin.append("""  <td>'.$data["logs"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  '</table>')
        mc_begin.append(  '<br />')
        mc_begin.append(  '')
	mc_begin.append(  '<table class="TableDataSmall">')
        mc_begin.append(  ' <tr class="TableHeader">')
        mc_begin.append(  '  <td> Tested:</td>')
        mc_begin.append(  '  <td> Datasets:</td>')
        mc_begin.append(  '  <td> Files:</td>')
        mc_begin.append(  ' </tr>')
        mc_begin.append(  ' <tr>')
        mc_begin.append(  '  <td> Total:</td>')
        mc_begin.append("""  <td>'.$data["total_datasets"].'</td>""")
        mc_begin.append("""  <td>'.$data["total_files"].'</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(""" <tr class="'.$status_color.'">""")
        mc_begin.append(  '  <td> Failed:</td>')
        mc_begin.append("""  <td>'.$data["failed_datasets"].'</td>""")
        mc_begin.append("""  <td>'.$data["failed_files"].'</td>""")
        mc_begin.append(  ' </tr>')
	mc_begin.append(  '</table>')
	mc_begin.append(  '<br />')
        mc_begin.append(  '')
	mc_begin.append("""<input type="button" value="show/hide Failed Datasets" onfocus="this.blur()" onclick="show_hide(\\\'datasets_details_""" + self.__module__ + """\\\');" />""")
	mc_begin.append(  '<div class="DetailedInfo" id="datasets_details_' + self.__module__ + '" style="display:none;">')
        mc_begin.append(  '')
	mc_begin.append(  ' <table class="TableDetails">')
        mc_begin.append(  '  <tr class="TableHeader">')
	mc_begin.append(  '   <td>Dataset</td>')
	mc_begin.append(  '   <td>Failed Files</td>')
	mc_begin.append(  '  </tr>')

        mc_detailed_datasets = []
        mc_detailed_datasets.append(  '  <tr>')
        mc_detailed_datasets.append("""   <td>'.$info["dataset"].'</td>""")
        mc_detailed_datasets.append("""   <td>'.$info["files"].'</td>""")
        mc_detailed_datasets.append(  '  </tr>')

        mc_mid = []
	mc_mid.append(  ' </table>')
        mc_mid.append(  '</div>')
        mc_mid.append(  '<br />')
        mc_mid.append(  '')
	mc_mid.append("""<input type="button" value="show/hide Inconsistent Files" onfocus="this.blur()" onclick="show_hide(\\\'files_details_""" + self.__module__ + """\\\');" />""")
	mc_mid.append(  '<div class="DetailedInfo" id="files_details_' + self.__module__ + '" style="display:none;">')
        mc_mid.append(  '')
        mc_mid.append(  ' <table class="TableDetails">')
        mc_mid.append(  '  <tr class="TableHeader">')
	mc_mid.append(  '   <td>Logical File Name</td>')
	mc_mid.append(  '   <td>Status</td>')
	mc_mid.append(  '  </tr>')

        mc_detailed_files = []
        mc_detailed_files.append(  '  <tr>')
        mc_detailed_files.append("""   <td>'.$info["lfn"].'</td>""")
        mc_detailed_files.append("""   <td>'.$info["status"].'</td>""")
        mc_detailed_files.append(  '  </tr>')

        mc_end = []
        mc_end.append(' </table>')
        mc_end.append('</div>')
        mc_end.append('<br />')

	module_content = """<?php
        /**
        *
        * @convert seconds to hours minutes and seconds
        *
        * @param int $seconds The number of seconds
        *
        * @return string
        *
        */
        function secondsToWords_""" + self.__module__ + """($seconds)
        {
            /*** return value ***/
            $ret = "";         
            /*** get the hours ***/
            $hours = intval(intval($seconds) / 3600);
            if($hours > 0)
            {
                $ret .= "$hours hours ";
            }
            /*** get the minutes ***/
            $minutes = bcmod((intval($seconds) / 60),60);
            if($hours > 0 || $minutes > 0)
            {
                $ret .= "$minutes minutes ";
            }
            /*** get the seconds ***/
            $seconds = bcmod(intval($seconds),60);
            $ret .= "$seconds seconds";
            return $ret;
        }
        ?>"""

	module_content += """<?php
        $status_color="ok";
        if (intval($data["failed_datasets"]) > 0)
            $status_color="critical";

	$duration_color = '';
	if(isset($data['duration_critical_limit']) && isset($data['duration_warning_limit']))
	{
            $durationHours = intval(intval($data["duration"]) / 3600);
            if ($durationHours >= $data["duration_critical_limit"])
	    {
                $duration_color=' class="critical"';
	        print('""" + self.PHPArrayToString(duration_critical_message) + """');
	    }
            elseif ($durationHours >= $data["duration_warning_limit"])
	    {
                $duration_color=' class="warning"';
	        print('""" + self.PHPArrayToString(duration_warning_message) + """');
	    }
	}

	$old_result_color='';
	$index = strrpos($data["logs"], '/');
	if($index !== false && isset($data['old_result_critical_limit']) && isset($data['old_result_warning_limit']))
	{
	    $resultAge = intval(($data["timestamp"] - intval(substr($data["logs"], $index+1))) / 3600);
	    if($resultAge >= $data["old_result_critical_limit"])
	    {
	        $old_result_color=' class="critical"';
	        print('""" + self.PHPArrayToString(old_result_critical_message) + """');
	    }
	    elseif($resultAge >= $data["old_result_warning_limit"])
	    {
	        $old_result_color=' class="warning"';
	        print('""" + self.PHPArrayToString(old_result_warning_message) + """');
	    }
	}

        print('""" + self.PHPArrayToString(mc_begin) + """');
        
        $details_db_sqlquery = "SELECT dataset, count(distinct lfn) as files FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"] . " group by dataset";
        
        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            print('""" + self.PHPArrayToString(mc_detailed_datasets) + """');
        }

        print('""" + self.PHPArrayToString(mc_mid) + """');

        $details_db_sqlquery = "SELECT * FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"];
        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            print('""" + self.PHPArrayToString(mc_detailed_files) + """');
        }

        print('""" + self.PHPArrayToString(mc_end) + """');

	?>"""

	return self.PHPOutput(module_content)
