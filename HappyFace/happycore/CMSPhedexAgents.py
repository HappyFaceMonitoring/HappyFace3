from ModuleBase import *
from XMLParsing import *

#
# Friederike Nowak
# University of Hamburg
# 2009/06/20
#

#################################################
#                                               #
# Uses the informations about the phedex agents #
# provided by the phedex API. The agents are    #
# considered "down", if they have not reported  #
# back for x hours, where x can be specified    #
# in the config file.                           #
#                                               #
#################################################

class CMSPhedexAgents(ModuleBase):

    def __init__(self,category,timestamp,storage_dir):
        
        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,category,timestamp,storage_dir)

        config = self.readConfigFile('./happycore/CMSPhedexAgents')
	self.addCssFile(config,'./happycore/CMSPhedexAgents')

        ## the url of the Phedex Agents Api
        self.base_url = self.mod_config.get('setup','base_url')
        self.phpArgs = {}

        ## needed arguments: node = ARG
        self.getPhpArgs(self.mod_config)

        ## define how long an agent is allowed not to answer
        self.critical = self.mod_config.get('setup','critical')
        self.warning = self.mod_config.get('setup','warning')

        ## get the instance
        self.instance = self.mod_config.get('setup','instance')

        ## abort test if no instance is given
        ## self.status will be pre-defined -1
        if not self.instance:
            print "Error: no instance specified. Abort"
            return

        # definition of the database table keys and pre-defined values
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.dsTag = 'cmsPhedexAgents_xml_source'
        self.fileType = 'xml'

        self.makeUrl()

    def getPhpArgs(self, config):
        for i in config.items('phpArgs'):
            self.phpArgs[i[0]] = i[1]

    def makeUrl(self):
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

        self.downloadRequest[self.dsTag] = 'wget:'+self.fileType+':'+self.base_url+'/'+self.instance+'/agents'+"?"+"&".join(argList)


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
	details_database = self.__module__ + "_table_details"
	
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

        details_db_keys["name"] = StringCol()
        details_db_keys["label"] = StringCol()
        details_db_keys["version"] = StringCol()
        details_db_keys["host"] = StringCol()
        details_db_keys["dir"] = StringCol()
        details_db_keys["time"] = FloatCol()
        details_db_keys['agent_status'] = FloatCol()

        ## write global after which the query will work
	details_db_keys["timestamp"] = IntCol()
	details_db_values["timestamp"] = self.timestamp

	## create index for timestamp
	details_db_keys["index"] = DatabaseIndex('timestamp')

	## lock object enables exclusive access to the database
	self.lock.acquire()

        Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

        Details_DB_Class.sqlmeta.cacheValues = False
	Details_DB_Class.sqlmeta.fromDatabase = True
	#Details_DB_Class.sqlmeta.lazyUpdate = True

        ## if table is not existing, create it
        Details_DB_Class.createTable(ifNotExists=True)


        ## now start parsing the xml tree
	root = source_tree.getroot()
        
        agentStatusList = []
        if root.get("request_timestamp"):
            request_time = float(root.get("request_timestamp"))
        else:
            print "Error: could not get request time at instance "+self.instance+". Aborting."
            return

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
                    ## time in hours
                    time = (request_time - time_update)/3600

                    details_db_values['time'] = time

                    agent_status = self.determineAgentStatus(time, label)
                    agentStatusList.append(agent_status)

                    details_db_values['agent_status'] = agent_status
                    
                    # store the values to the database
                    Details_DB_Class(**details_db_values)

        # unlock the database access
	self.lock.release()

        # happy, if all groups don't use more space than allowedfor now always happy
        self.status = self.determineStatus(agentStatusList)

    def output(self):

        module_content = """
        <?php

        $details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

        printf('<table class="AgentsTable">');
        printf('<tr><td>agent</td><td>label</td><td>time [hours]</td></tr>');


        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            if ($info["agent_status"] == 1){
                  $service_status_color_flag = "up";
        }
             else if ($info["agent_status"] == 0.5){
                  $service_status_color_flag = "warning";
        }
             else if ($info["agent_status"] == 0){
                  $service_status_color_flag = "critical";
        }
             else $service_status_color_flag = "undef";

        printf('<tr class="' .$service_status_color_flag . '"><td>' . $info["name"] . '</td><td>'.$info["label"].'</td><td>' .round($info["time"],1) . '</td></tr>');
        
        }

        printf('</table><br/>');

        printf('
        <input type="button" value="details" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """);" />
        <div class="AgentsDetailedInfo" id=""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """ style="display:none;">
        <table class="AgentsTableDetails">

        <tr><td>agent</td><td>label</td><td>host</td><td>directory</td><td>version</td></tr>
        
        ');

         foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            if ($info["agent_status"] == 1){
                  $service_status_color_flag = "up";
        }
             else if ($info["agent_status"] == 0.5){
                  $service_status_color_flag = "warning";
        }
             else if ($info["agent_status"] == 0){
                  $service_status_color_flag = "critical";
        }
             else $service_status_color_flag = "undef";

        printf('<tr class="' .$service_status_color_flag . '"><td>' . $info["name"] . '</td><td>'.$info["label"].'</td><td>' .$info["host"] . '</td><td>'.$info["dir"].'</td><td>'.$info["version"].'</td></tr>');
        
        }       

        printf('</table></div>');
                
        ?>

        """

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
                self.critical = 2

            if not self.warning:
                print "Warning: warning status not defined in config file."
                print "setting it to 1 hour."
                self.warning = 1

            if time > self.critical:
                status = 0

            elif time > self.warning:
                status = 0.5

            else:
                status = 1

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
