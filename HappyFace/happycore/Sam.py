from ModuleBase import *
from DownloadTag import *
from XMLParsing import *
from PhpDownload import *


class Sam(ModuleBase,PhpDownload):

    def __init__(self, category, timestamp, archive_dir):
        ModuleBase.__init__(self, category, timestamp, archive_dir)
        PhpDownload.__init__(self)

        # definition of the database table keys and pre-defined values

	self.db_keys["details_database"] = StringCol()
	self.db_keys["site"] =	StringCol()
	
	self.db_values["details_database"] = ""
	self.db_values["site"] = ""


        self.db_keys["details_database_summary"] = StringCol()
	self.db_values["details_database_summary"] = ""


	
	self.report_url	= self.configService.get('setup','report_url')
	
        self.dsTag = 'sam_xml_source'

        self.downloadRequest[self.dsTag] = 'wgetXmlRequest|'+self.makeUrl()
        self.blacklist = self.configService.getDefault('setup','blacklist',"").split(",")

        self.configService.addToParameter('setup','definition','Blacklist: '+', '.join(self.blacklist)+'<br />')


	
    def run(self):

        # run the test

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1


	dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
        if dl_error != "":
            self.error_message+= dl_error
            return

        self.configService.addToParameter('setup','source',self.downloadService.getUrlAsLink(self.downloadRequest[self.dsTag]))


	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)
        self.error_message += xml_error

        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

	# parse the details and store it in a special database table
	details_database = self.__module__ + "_table_details"
	self.db_values["details_database"] = details_database

	details_database_summary = self.__module__ + "_table_details_summary"
	self.db_values["details_database_summary"] = details_database_summary

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

	details_summary_db_keys = {}
	details_summary_db_values = {}

        details_summary_db_keys["name"] = StringCol()
        details_summary_db_keys["nodes"] = StringCol()
        details_summary_db_keys["status"] = FloatCol()

        subtable_details = self.table_init( self.db_values["details_database"], details_db_keys )
        subtable_summary = self.table_init( self.db_values["details_database_summary"], details_summary_db_keys )

	sn = {}
	tests = {}
	
	ServiceName = ""
	ServiceStatus = ""
	Status = ""
	Url = ""
	Age = ""
	Type = ""
	Time = ""



	root = source_tree.getroot()

        self.SamResults = {}
	
	try:
	    for element in root:
		if element.tag == "data": data_branch = element

	    for element in data_branch:
		for item in element:
		    if item.tag == "Services": services = item
		    if item.tag == "VOName": self.db_values["site"] = item.text


	    for services_item in services:

		for services_prop in services_item:
		    if services_prop.tag == "ServiceType":
			ServiceType = services_prop.text

		    if services_prop.tag == "ServiceNames":
			sn = services_prop

			for sn_item in sn:
				
			    for sn_prop in sn_item:
				if sn_prop.tag == "ServiceName":
				    ServiceName = sn_prop.text


                            if ServiceName in self.blacklist: continue


			    for sn_prop in sn_item:
				if sn_prop.tag == "ServiceStatus":
				    ServiceStatus = sn_prop.text



			    if ServiceStatus == str(1): service_status = 1.
			    elif ServiceStatus == str(-1) : service_status = 0.
			    else : service_status = 0.5

                            self.SamResults[ServiceName] = {}
                            self.SamResults[ServiceName]["name"] = ServiceName
                            self.SamResults[ServiceName]["type"] = ServiceType
                            self.SamResults[ServiceName]["status"] = service_status
                            self.SamResults[ServiceName]["tests"] = []
                            

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

                                        details = {}
                                        details["status"] = Status
                                        details["url"] = (self.report_url + Url.__str__()).replace('&','&amp;').replace('%','%%')
                                        details["age"] = Age
                                        details["type"] = Type
                                        details["time"] = Time
                                        self.SamResults[ServiceName]["tests"].append(details)

	except:
	    # module status will be -1
	    self.error_message = "Couldn't extract any usefull data from the XML source code for the status calculation."



        samGroups = {}
   
        self.configService.addToParameter('setup','definition','Definition of Service Groups:'+'<br />')
        groupConfig = self.configService.getSection('SamGroups')
        for group in groupConfig.keys():

            self.configService.addToParameter('setup','definition','*  '+group+': '+self.EscapeHTMLEntities(groupConfig[group])+'<br />')

            samGroups[group] = {}
            samGroups[group]['ident'] = groupConfig[group]
            samGroups[group]['nodes'] =[]
            samGroups[group]['NumWarning'] = 0
            samGroups[group]['NumError'] = 0
            samGroups[group]['NumOk'] = 0
            samGroups[group]['NumTotal'] = 0
            samGroups[group]['status'] = -1
            
            
            if samGroups[group]['ident'].find('Type:') == 0:
                nodeclass =  samGroups[group]['ident'].replace('Type:','')
                for service in  self.SamResults.keys():
                    if  self.SamResults[service]['type'] == nodeclass:
                        samGroups[group]['nodes'].append(service)
            else:
                samGroups[group]['nodes'] = samGroups[group]['ident'].split(',')
            samGroups[group]['nodes'].sort()

        self.configService.addToParameter('setup','definition','Thresholds:'+'<br />')
        groupThresholds = self.configService.getSection('SamGroupsThresholds')
        for val in groupThresholds.keys():
            self.configService.addToParameter('setup','definition','* '+val+': '+self.EscapeHTMLEntities(groupThresholds[val])+'<br />')
            tmp = val.split('_')
            if len(tmp) != 3: self.error_message += "Config parameter "+val+" does not match group_Error/Warning."
            testCat = tmp[1]
            testValue = tmp[2]
            testRef = groupThresholds[val]

            if not samGroups.has_key(tmp[0]): next
            if not samGroups[ tmp[0] ].has_key(testCat): samGroups[ tmp[0] ][testCat] = []

            tmpThreshold = {}
            tmpThreshold['value'] = testValue
            tmpThreshold['condition'] =  str( testRef )[:1]
            tmpThreshold['threshold'] = float(str(testRef)[1:])
            samGroups[ tmp[0] ][testCat].append(tmpThreshold)





                     
        for group in samGroups:
            theGroup = samGroups[group]
            for service in theGroup['nodes']:
                if self.SamResults[service]['status'] == 1.0:  theGroup['NumOk'] = theGroup['NumOk']+1
                elif self.SamResults[service]['status'] == 0.5:  theGroup['NumWarning'] =theGroup['NumWarning']+1
                elif self.SamResults[service]['status'] == 0.0: theGroup['NumError'] =theGroup['NumError']+1
            theGroup['NumTotal'] = len( theGroup['nodes'] )
                

            if self.getGroupStatus(theGroup,'Error') == True: theGroup['status'] = 0.0
            elif self.getGroupStatus(theGroup,'Warning') == True: theGroup['status'] = 0.5
            else: theGroup['status'] = 1.0

            

        theNodes = self.SamResults.keys()
        theNodes.sort()
        for service in theNodes:
            serviceInfo =  self.SamResults[service]

            details_db_values["service_type"] = serviceInfo['type'] 
            details_db_values["service_name"] = serviceInfo['name']
            details_db_values["service_status"] = serviceInfo['status']
            for test in  serviceInfo['tests']:
                for i in test.keys():
                    details_db_values[i] = test[i]
                self.table_fill( subtable_details , details_db_values )


        worstGroupStatus = 99.0
        if len(samGroups) > 0:
            for group in samGroups:
                theGroup = samGroups[group]
                details_summary_db_values["name"] = group
                details_summary_db_values["nodes"] = ', '.join(theGroup['nodes'])
                details_summary_db_values["status"] = theGroup['status']
                self.table_fill( subtable_summary , details_summary_db_values )
                
                if theGroup['status'] >= 0:
                    if theGroup['status'] < worstGroupStatus: worstGroupStatus = theGroup['status']
            
                

        else:
            for service in theNodes:
                 serviceInfo =  self.SamResults[service]
                 if serviceInfo['status'] >= 0:
                     if serviceInfo['status'] < worstGroupStatus: worstGroupStatus = serviceInfo['status']

        if worstGroupStatus != 99.0: self.status = worstGroupStatus
        else: self.status = -1
             

    def getGroupStatus(self,theGroup,type):
          if not theGroup.has_key(type): return False
          for check in theGroup[type]:
              if not theGroup.has_key(check['value']): next
              if check['condition'] == ">":
                  if theGroup[check['value']] > check['threshold']: return True
              if check['condition'] == "<":
                  if theGroup[check['value']] < check['threshold']: return True
          return False


    def printInfo(self):
        for service in self.SamResults.keys():

            serviceInfo =  self.SamResults[service]
            print serviceInfo['type']+" "+ serviceInfo['name'] +" "+str(serviceInfo['status'])
            for i in  serviceInfo['tests']:
                print i
            print '  '

    def output(self):

        # this module_content string will be executed by a printf('') PHP command
        # all information in the database are available via a $data["key"] call
	mc_group_begin = []
        mc_group_begin.append('<strong>Group status:</strong>')
	mc_group_begin.append('<br />')
        mc_group_begin.append('<table class="TableData">');

	mc_group_row = []
	mc_group_row.append(""" <tr class="' .$service_status_color_flag . '">""")
	mc_group_row.append("""  <td>' . $info["name"] . '</td>""")
	mc_group_row.append("""  <td>' . $info["nodes"] . '</td>""")
	mc_group_row.append(  ' </tr>')

	mc_group_end = []
	mc_group_end.append(  '</table>')
	mc_group_end.append(  '<br />')

	mc_service_begin = []
	mc_service_begin.append('<strong>Individual service status:</strong>')
	mc_service_begin.append('<br />')
	mc_service_begin.append('<table class="TableData">');

	mc_service_row = []
	mc_service_row.append(""" <tr class="' .$service_status_color_flag . '">""")
	mc_service_row.append("""  <td>' . $info["service_type"] . '</td>""")
	mc_service_row.append("""  <td>' . $info["service_name"] . '</td>""")
	mc_service_row.append(  ' </tr>')

	mc_service_end = []
	mc_service_end.append('</table>')
	mc_service_end.append('<br />')

	mc_details_begin = []
	mc_details_begin.append( """<input type="button" value="error/warning results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_failed_result\\\');" />""")
	mc_details_begin.append(   '<div class="DetailedInfo" id="' + self.__module__+ '_failed_result" style="display:none;">')
	mc_details_begin.append(   ' <table class="TableDetails">')
	mc_details_begin.append(   '  <tr class="TableHeader">')
	mc_details_begin.append(   '   <td>Element Type</td>')
	mc_details_begin.append(   '   <td>Element Name</td>')
	mc_details_begin.append(   '   <td>Status</td>')
	mc_details_begin.append(   '   <td>Test Name</td>')
	mc_details_begin.append(   '   <td>Test Time</td>')
	mc_details_begin.append(   '  </tr>')

	mc_details_row_fail = []
	mc_details_row_fail.append("""<tr class="' . $color . '">""")
	mc_details_row_fail.append(""" <td>' . $results["service_type"] . '</td>""")
	mc_details_row_fail.append(""" <td>' . $results["service_name"] . '</td>""")
	mc_details_row_fail.append(""" <td><a href="' . $results["url"] . '"><strong>' . $results["status"] . '</strong>' . $results["$service_status"] . '</a></td>""")
	mc_details_row_fail.append(""" <td>' . $results["type"] . '</td>""")
	mc_details_row_fail.append("""   <td>' . $results["time"] . '</td>""")
	mc_details_row_fail.append('  </tr>');

	mc_details_mid = []
	mc_details_mid.append(     ' </table>')
	mc_details_mid.append(     '</div>')
	mc_details_mid.append(     '<br />')

	mc_details_mid.append(   """<input type="button" value="successful results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__ + """_success_result\\\');" />""")
	mc_details_mid.append(     '<div class="DetailedInfo" id="' + self.__module__+ '_success_result" style="display:none;">')
	mc_details_mid.append(     ' <table class="TableDetails">')
	mc_details_mid.append(     '  <tr class="TableHeader">')
	mc_details_mid.append(     '   <td>Element Type</td>')
	mc_details_mid.append(     '   <td>Element Name</td>')
	mc_details_mid.append(     '   <td>Status</td>')
	mc_details_mid.append(     '   <td>Test Name</td>')
	mc_details_mid.append(     '   <td>Test Time</td>')
	mc_details_mid.append(     '  </tr>')

	mc_details_row_ok = []
	mc_details_row_ok.append(  '  <tr class="ok">')
	mc_details_row_ok.append("""   <td>' . $results["service_type"] . '</td>""")
	mc_details_row_ok.append("""   <td>' . $results["service_name"] . '</td>""")
	mc_details_row_ok.append("""   <td><a href="' . $results["url"] . '"><strong>' . $results["status"] . '</strong></a></td>""")
	mc_details_row_ok.append("""   <td>' . $results["type"] . '</td>""")
	mc_details_row_ok.append("""   <td>' . $results["time"] . '</td>""")
	mc_details_row_ok.append(  '  </tr>')

	mc_details_end = []
	mc_details_end.append(' </table>')
	mc_details_end.append('</div>')
	mc_details_end.append('<br />');

        module_content = """<?php

	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];
	$details_summary_db_sqlquery = "SELECT * FROM " . $data["details_database_summary"] . " WHERE timestamp = " . $data["timestamp"];
	$temp_element = "";

        $GroupCount=0;
        foreach($dbh->query($details_summary_db_sqlquery) as $info)   
        {
            $GroupCount=$GroupCount+1;
        }

        if ($GroupCount != 0)
	{
	    printf('""" + self.PHPArrayToString(mc_group_begin) + """');
	
	    foreach ($dbh->query($details_summary_db_sqlquery) as $info)
       	    {
	        if ($info["status"] == "1.")
	            $service_status_color_flag = "ok";
                elseif ($info["status"] == "0.5")
	            $service_status_color_flag = "warning";
	        else
		    $service_status_color_flag = "critical";

#	        printf('<tr class="' .$service_status_color_flag . '"><td><strong>' . $info["name"] . '</strong></td><td><strong>' . $info["nodes"] . '</strong></td></tr>');
	        printf('""" + self.PHPArrayToString(mc_group_row) + """');
	    }

	    printf('""" + self.PHPArrayToString(mc_group_end) + """');
	}

        printf('""" + self.PHPArrayToString(mc_service_begin) + """');
	
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
	    if ($temp_element != $info["service_name"])
	    {
		if ($info["service_status"] == "1.")
		    $service_status_color_flag = "ok";
                elseif ($info["service_status"] == "0.5")
		    $service_status_color_flag = "warning";
		else
		    $service_status_color_flag = "critical";

#		printf('<tr class="' .$service_status_color_flag . '"><td><strong>' . $info["service_type"] . '</strong></td><td><strong>' . $info["service_name"] . '</strong></td></tr>');

		printf('""" + self.PHPArrayToString(mc_service_row) + """');
	    }
	    $temp_element = $info["service_name"];
	}

	printf('""" + self.PHPArrayToString(mc_service_end) + """');

	printf('""" + self.PHPArrayToString(mc_details_begin) + """');
	
	foreach ($dbh->query($details_db_sqlquery) as $results)
	{
	    if ($results["status"] != "ok" && $results["status"] != "")
            {
			$color = "critical";
			if($results["$service_status"] == "0.5") $color="warning";

			printf('""" + self.PHPArrayToString(mc_details_row_fail) + """');
	    }
	}

	printf('""" + self.PHPArrayToString(mc_details_mid) + """');

	foreach ($dbh->query($details_db_sqlquery) as $results)
	{
	    if ($results["status"] == "ok")
	    {
		printf('""" + self.PHPArrayToString(mc_details_row_ok) + """');
	    }
	}

	printf('""" + self.PHPArrayToString(mc_details_end) + """');

	?>"""

        return self.PHPOutput(module_content)



    def determineStatus(self, serviceStatusList):
        status = 1.

        for serviceStatus in serviceStatusList:
            if serviceStatus < status:
                status = serviceStatus

        if len(serviceStatusList) == 0:
            status = -1.

        return status
    

    def determineTestStatus(self,StatusString):
        testStatus = 1.

        if StatusString == 'ok':
            testStatus = 1.
        elif StatusString == 'warn':
            testStatus = 0.5
        elif StatusString == 'error':
            testStatus = 0.

        return testStatus

    def determineServiceStatus(self,StatusList):
        status = 1.

        for testStatus in StatusList:
            if testStatus < status:
                status = testStatus

        if len(StatusList) == 0:
            status = -1.

        return status
