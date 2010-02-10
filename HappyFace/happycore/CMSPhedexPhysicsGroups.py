from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

#
# Friederike Nowak
# University of Hamburg
# 2009/06/21
#
# 2009/09/18, Volker Buege:
#             Module ported to new config service
#             Module now inhertis from PhpDownload to avoid code doubling
#
# ToDo:


###################################################
#                                                 #
# Uses the informations about the space usage of  #
# the physics groups on a T2 provided by the      #
# phedex API. It is possible to make individual   #
# restrictions for each group, or to use a global #
# one.                                            #
#                                                 #
###################################################

class CMSPhedexPhysicsGroups(ModuleBase,PhpDownload):

    def __init__(self,module_options):

        """
        The CMSPhedexPhysicsGroups class uses the
        informations about the space usage of the physics
        groups on a T2 provided by the phedex API.
        It is possible to make individual restrictions for
        each group, or to use a global one.
        """

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)
	PhpDownload.__init__(self)
 
        ## get the instance
        self.instance = self.configService.get('setup','instance')

        ## read in how much space is entitled to the groups (in TB)
        self.maxSpace = self.configService.get('setup', 'maxSpace')

        ## now read in individual space permissions
        self.allowedSpace = self.getAllowedSpace()
            
        # definition of the database table keys and pre-defined values
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.dsTag = 'cmsPhedexGroupUsage_xml_source'

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


    def getAllowedSpace(self):

        restrictions = {}

        #try:
        if not self.configService.getDefault('setup', 'allowedSpace',0) == 0:
            #for entry in self.configService.get('setup', 'allowedSpace').split(','):
            for entry in self.configService.get('setup', 'allowedSpace').split(','):
                physGroup,rest = entry.split(':')
                restrictions[physGroup] = rest

        #except:
        #    restrictions = {}

        return restrictions


    def run(self):

        # run the test

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

        success,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
	source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile)
        if not error_message == '':
            self.error_message += error_message
            return -1

        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

        # parse the details and store it in a special database table
	details_database = self.__module__ + "_table_details"
	
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

        details_db_keys["phys_group"] = StringCol()
        details_db_keys["dest_bytes"] = IntCol()
        details_db_keys["node_bytes"] = IntCol()
        details_db_keys["node_files"] = IntCol()
        details_db_keys["dest_files"] = IntCol()
        details_db_keys["group_status"] = FloatCol()

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

        ## each group gets its status
        groupStatus = {}

        for element in root:
            if element.tag == 'node':
                data_branch = element

                ## stay in loop for if there are more than one node
                for group in data_branch:
                    d_bytes = int(group.get("dest_bytes"))
                    n_bytes = int(group.get("node_bytes"))
                    d_files = int(group.get("dest_files"))
                    n_files = int(group.get("node_files"))
                    name = str(group.get("name"))

                    groupStatus[name] = self.determineGroupStatus(n_bytes,name)
                    
                    details_db_values["dest_bytes"] = d_bytes
                    details_db_values["node_bytes"] = n_bytes
                    details_db_values["dest_files"] = d_files
                    details_db_values["node_files"] = n_files
                    details_db_values["phys_group"] = name

                    ## save the group status as well
                    details_db_values["group_status"] = groupStatus[name]

                    ## store the values to the database
                    Details_DB_Class(**details_db_values)


        # unlock the database access
	self.lock.release()

        # happy, if all groups don't use more space than allowed
        self.status = self.determineStatus(groupStatus)


    def output(self):

	mc_begin = []
	mc_begin.append('<table class="TableData">')
        mc_begin.append(' <tr class="TableHeader">')
	mc_begin.append('  <td>Group</td>')
	mc_begin.append('  <td>resident data [TB]</td>')
	mc_begin.append('  <td>percent of subscribed data</td>')
	mc_begin.append(' </tr>');

	mc_row = []
        mc_row.append(""" <tr class="' .$service_status_color_flag . '">""")
	mc_row.append("""  <td>' . $info["phys_group"] . '</td>""")
	mc_row.append("""  <td>' . $resident_data_TB . '</td>""")
	mc_row.append("""  <td>' . $resident_data_percent. ' </td>""")
	mc_row.append(  ' </tr>');

	mc_mid = []
	mc_mid.append('</table>')
	mc_mid.append('<br />');

        mc_mid.append("""<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_details\\\');" />""")
	mc_mid.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_details" style="display:none;">')
	mc_mid.append(  ' <table class="TableDetails">')
	mc_mid.append(  '  <tr class="TableHeader">')
	mc_mid.append(  '   <td>Group</td>')
	mc_mid.append(  '   <td>resident data [TB]</td>')
	mc_mid.append(  '   <td>subscribed data [TB]</td>')
	mc_mid.append(  '   <td>resident files</td>')
	mc_mid.append(  '   <td>subscribed files</td>')
	mc_mid.append(  '  </tr>')

	detailed_row = []
	detailed_row.append("""  <tr class="' .$service_status_color_flag . '">""")
	detailed_row.append("""   <td>' . $info2["phys_group"] . '</td>""")
	detailed_row.append("""   <td>' . $resident_data_TB . '</td>""")
	detailed_row.append("""   <td>' . $subscribed_data_TB . '</td>""")
	detailed_row.append("""   <td>' . $resident_files_Nb . '</td>""")
	detailed_row.append("""   <td>' . $subscribed_files_Nb . '</td>""")
	detailed_row.append(  '  </tr>')

	mc_end = []
	mc_end.append(' </table>')
	mc_end.append('</div>')
	mc_end.append('<br />');

        # this module_content string will be executed by a print('') PHP command
        # all information in the database are available via a $data["key"] call
        module_content = """<?php

	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

	print('""" + self.PHPArrayToString(mc_begin) + """');

        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
            if ($info["group_status"] == 0.)
                $service_status_color_flag = "critical";
            elseif ($info["node_files"] != $info["dest_files"])
                $service_status_color_flag = "warning";
            else
                $service_status_color_flag = "ok";
        
            $resident_data_TB = round($info["node_bytes"]/(1024*1024*1024*1024),2);
            $resident_data_percent = round(($info["node_bytes"]/$info["dest_bytes"])*100,1);

            print('""" + self.PHPArrayToString(mc_row) + """');
        }

        print('""" + self.PHPArrayToString(mc_mid) + """');

        foreach ($dbh->query($details_db_sqlquery) as $info2)
       	{
            if ($info2["group_status"] == 0.)
                $service_status_color_flag = "critical";
            elseif ($info2["node_files"] != $info2["dest_files"])
                $service_status_color_flag = "warning";
            else
                $service_status_color_flag = "ok";
        
            $resident_data_TB = round($info2["node_bytes"]/(1024*1024*1024*1024),2);
            $subscribed_data_TB = round($info2["dest_bytes"]/(1024*1024*1024*1024),2);
            $resident_files_Nb = $info2["node_files"];
            $subscribed_files_Nb = $info2["dest_files"];

            print('""" + self.PHPArrayToString(detailed_row) + """');
        }

        print('""" + self.PHPArrayToString(mc_end) + """');

        ?>"""

        return self.PHPOutput(module_content)


    ## check if groups use more space than global (or local, if existent)
    ## restriction allows
    def determineGroupStatus(self, n_bytes, name):

        status = -1.
        if not n_bytes:
            print "Error: Number of Bytes for group "+name+" is Not A Number."
            print "\tCould not determine status"
            return status
        
        else:
            ## some groups shouldn't fall under the global restrictions
            ## but can always restricted locally
            if name == 'local' or name == 'undefined' or name == 'DataOps':
                try:
                    if float(n_bytes)/(1024*1024*1024*1024) > self.allowedSpace[name]:
                        status = 0.
                    else:
                        status = 1.
                except:
                        status = 1.
            else:
                Tbyte = float(n_bytes)/(1024*1024*1024*1024)

                ## use the individual restrictions if existent
                try: 
                    rest = self.allowedSpace[name]
                except:
                    rest = self.maxSpace

                ## check against restrictions
                if Tbyte > float(rest):
                    status = 0.
                else:
                    status = 1.
                    
        return status


    ## status algorithm is 'worst'
    def determineStatus(self,groupStatus):
        status = -1.
        if groupStatus:
            status = 1.
            for group in groupStatus:
                if groupStatus[group] < status:
                    status = groupStatus[group]

        return status
