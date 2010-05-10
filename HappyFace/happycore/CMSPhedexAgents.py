from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

from time import strftime

#
# Friederike Nowak
# University of Hamburg
# 2009/06/20
#
# 2009/09/18, Volker Buege:
#             Module ported to new config service
#	      Module now inhertis from PhpDownload to avoid code doubling
#
# 2010/04/16, Armin Scheurer:
#	      Introduced blacklisting feature for agents specified in
#             the config file
#
# ToDo:


#################################################
#                                               #
# Uses the informations about the phedex agents #
# provided by the phedex API. The agents are    #
# considered "down", if they have not reported  #
# back for x hours, where x can be specified    #
# in the config file.                           #
#                                               #
#################################################

class CMSPhedexAgents(ModuleBase,PhpDownload):

    def __init__(self,module_options):
        
        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)
        PhpDownload.__init__(self)

        ## define how long an agent is allowed not to answer
        self.critical = self.configService.get('setup','critical')
        self.warning = self.configService.get('setup','warning')

        ## get the instance
        self.instance = self.configService.get('setup','instance')

        ## abort test if no instance is given
        ## self.status will be pre-defined -1
        if not self.instance:
            print "Error: no instance specified. Abort"
            return

	# get black-list of agents which are ignored for status calculation
	self.blacklist = self.configService.get('setup','blacklist')

        # definition of the database table keys and pre-defined values
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.dsTag = 'cmsPhedexAgents_xml_source'

        self.base_url += '/'+self.instance+'/agents'
        self.downloadRequest[self.dsTag] = 'wget|'+self.makeUrl()

    def getPhpArgs_old(self, config):
        for i in config.items('phpArgs'):
            self.phpArgs[i[0]] = i[1]

    def makeUrl_old(self):
        if len(self.phpArgs) == 0:
            print "Php Error: makeUrl called without phpArgs"
            sys.exit()
        if self.base_url == "":
            print "Php Error: makeUrl called without base_url"
            sys.exit()

        ## if last char of url is "/", remove it
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]
            

        argList = []
        for i in self.phpArgs:
	    for j in self.phpArgs[i].split(","):
		argList.append(i+'='+j)

        self.downloadRequest[self.dsTag] = 'wget|'+self.fileType+'||'+self.base_url+'/'+self.instance+'/agents'+"?"+"&".join(argList)


    def process(self):

        # run the test
        success,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile)

        # parse the details and store it in a special database table
	details_database = self.__module__ + "_table_details"
	
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

        details_db_keys['name'] = StringCol()
        details_db_keys['label'] = StringCol()
        details_db_keys['version'] = StringCol()
        details_db_keys['host'] = StringCol()
        details_db_keys['dir'] = StringCol()
        details_db_keys['time'] = StringCol()
        details_db_keys['agent_status'] = FloatCol()
	details_db_keys['critical'] = StringCol()

	my_subtable_class = self.table_init( details_database, details_db_keys )

        ## now start parsing the xml tree
	root = source_tree.getroot()
        
        agentStatusList = []
        if root.get("request_timestamp"):
            request_time = float(root.get("request_timestamp"))
        else:
	    raise Exception("Could not get request time at instance " + self.instance)

        for element in root:
            if element.tag == "node":
                data_branch = element

                for agent in data_branch:
                    
                    time_update = float(agent.get("time_update"))

                    label = str(agent.get("label"))
                    details_db_values['version'] = str(agent.get("version"))
                    details_db_values['host'] = str(agent.get("host"))
                    details_db_values['dir'] = str(agent.get("state_dir"))
                    details_db_values['name'] = str(agent.get("name"))
                    details_db_values['label'] = label

                    ## store the time the agent has answered the last time
                    ## time in seconds
                    time = (request_time - time_update)

                    agent_status = self.determineAgentStatus(time/3600, label)

		    # check if agent is in black-list, then ignore its status
		    skipagent = False
		    for blagent in self.blacklist.rsplit(","):
			if blagent.strip() == label:		    
			    skipagent = True

		    if not skipagent:
			agentStatusList.append(agent_status)
			details_db_values['critical'] = "yes"
		    else:
			details_db_values['critical'] = "no"

                    details_db_values['agent_status'] = agent_status

                    time_format = self.formatTime(time, agent_status)
                    details_db_values['time'] = time_format
                    
                    # store the values to the database
		    self.table_fill( my_subtable_class, details_db_values )
        self.subtable_clear(my_subtable_class, [], self.holdback_time)

        # happy, if all groups don't use more space than allowedfor now always happy
        self.status = self.determineStatus(agentStatusList)

    def output(self):

	begin = []
	begin.append('<table class="TableData">')
	begin.append(' <tr class="TableHeader">')
	begin.append('  <td>agent</td>')
	begin.append('  <td>label</td>')
	begin.append('  <td>last report</td>')
	begin.append('  <td>critical</td>')
	begin.append(' </tr>')

	info_row = []
	info_row.append(""" <tr class="' .$service_status_color_flag . '">""")
	info_row.append("""  <td>' . $info["name"] . '</td>""")
	info_row.append("""  <td>' . $info["label"]. '</td>""")
	info_row.append("""  <td>' . $info["time"] . '</td>""")
	info_row.append("""  <td>' . $info["critical"] . '</td>""")
	info_row.append(  ' </tr>')

	mid = []
	mid.append(  '</table>')
	mid.append(  '<br />');
	mid.append("""<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ "_failed_result" + """\\\');" />""")
	mid.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_failed_result" style="display:none;">')
	mid.append(  ' <table class="TableDetails">')
	mid.append(  '  <tr class="TableHeader">')
	mid.append(  '   <td>agent</td>')
	mid.append(  '   <td>label</td>')
	mid.append(  '   <td>host</td>')
	mid.append(  '   <td>directory</td>')
	mid.append(  '   <td>version</td>')
	mid.append(  '  </tr>')
 
	detailed_row = []
	detailed_row.append("""  <tr class="' .$service_status_color_flag . '">""")
	detailed_row.append("""   <td>' . $info["name"]   . '</td>""")
	detailed_row.append("""   <td>' . $info["label"]  . '</td>""")
	detailed_row.append("""   <td>' . $info["host"]   . '</td>""")
	detailed_row.append("""   <td>' . $info["dir"]    . '</td>""")
	detailed_row.append("""   <td>' . $info["version"]. '</td>""")
	detailed_row.append(  '  </tr>');

	end = []
	end.append(' </table>')
	end.append('</div>')

        module_content = self.PHPArrayToString(begin) + """<?php

        $details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
             if ($info["agent_status"] == 1.)
                 $service_status_color_flag = "ok";
             else if ($info["agent_status"] == 0.5)
                 $service_status_color_flag = "warning";
             else if ($info["agent_status"] == 0.)
                 $service_status_color_flag = "critical";
             else
	         $service_status_color_flag = "undefined";

	     print('""" + self.PHPArrayToString(info_row) + """');
        }

	print('""" + self.PHPArrayToString(mid) + """');

        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            if ($info["agent_status"] == 1.)
                $service_status_color_flag = "ok";
            else if ($info["agent_status"] == 0.5)
                $service_status_color_flag = "warning";
            else if ($info["agent_status"] == 0.)
                $service_status_color_flag = "critical";
            else
	        $service_status_color_flag = "undefined";

            print('""" + self.PHPArrayToString(detailed_row) + """');
        }

        print('""" + self.PHPArrayToString(end) + """');
                
        ?>"""

        return self.PHPOutput(module_content)

    def determineAgentStatus(self,time,label):

        status = -1

        if not time:
            print "Error: parameter 'time' for agent " + label + " is not defined."
            print "leaving agent status undefined."
            return status

        else:

            if not self.critical:
                print "Warning: critical status not defined in config file."
                print "setting it to 2 hours."
                self.critical = 2.

            if not self.warning:
                print "Warning: warning status not defined in config file."
                print "setting it to 1 hour."
                self.warning = 1.

            if time > float(self.critical):
                status = 0.

            elif time > float(self.warning):
                status = 0.5

            else:
                status = 1.

        return status

    def determineStatus(self,agentStatusList):

        status = 1
        statusCounter = 0

        ## status algorithm is 'worst'
        for agentStatus in agentStatusList:
            if agentStatus == -1:
                statusCounter += 1
            else:
                if agentStatus < status:
                    status = agentStatus

        ## if all agent statii are -1, global status
        ## should be -1
        if statusCounter == len(agentStatusList):
            status = -1

        return status

    def formatTime(self,time_diff, agent_status):

        time_string = ""

        #if not agent_status == 1.:
        d,s = divmod(time_diff,(3600*24))
        h,s = divmod(s,3600)
        m,s = divmod(s,60)
        
        time_string = "%02.fd:%02.fh:%02.fm" % (d, h, m)

        #else:
            #time_string = "up"


        return time_string
        
