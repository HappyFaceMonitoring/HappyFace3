from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

#
# Friederike Nowak
# University of Hamburg
# 2009/06/30
#
# 2009/09/18, Volker Buege:
#             Module ported to new config service
#             Php functionality now inherited from PhpDownload to avoid code doubling
#
# ToDo:




#####################################################
#                                                   #
# Uses the informations about the failed transfers  #
# from the PhEDEx Api (not from the sites own       #
# log files). Status will be determined over        #
# the number of the sites own errors.               #
#                                                   #
#####################################################


class CMSPhedexErrorLog(ModuleBase,PhpDownload):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,category,timestamp,storage_dir)
	PhpDownload.__init__(self)



        ## to,from
        self.getInverseDirection()

        ## get the instance
        self.instance = self.configService.get('setup','instance')

        ## get the definitions for the warning/critical status
        self.getThresholds()

        ## get the age threshold for the oldest errorlogs
        self.timeThreshold = self.configService.get('setup', 'time_threshold')

        ## if number of errors falls under threshold, status stays happy.
        #try:
        #    self.errorThreshold = self.configService.get('setup','error_threshold')
        #except:
        #    self.errorThreshold = 10

        self.errorThreshold = self.configService.getDefault('setup','error_threshold',10)

        self.initiateVariables()

        # definition of the database table keys and pre-defined values
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.dsTag = 'cmsPhedexErrorLog_xml_source'
	
        self.base_url += '/'+self.instance+'/errorlog'
        self.downloadRequest[self.dsTag] = 'wget:'+self.makeUrl()



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

        self.downloadRequest[self.dsTag] = 'wget:'+self.fileType+':'+self.base_url+'/'+self.instance+'/errorlog'+"?"+"&".join(argList)


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

        details_db_keys['link_remote_node'] = StringCol()
        details_db_keys['file_detail_log'] = StringCol()
        details_db_keys['file_detail_log_nb'] = IntCol()

        details_db_keys['total_errors'] = IntCol()
        details_db_keys['dest_errors'] = IntCol()
        details_db_keys['transfer_errors'] = IntCol()
        details_db_keys['source_errors'] = IntCol()
        details_db_keys['unknown_errors'] = IntCol()

        details_db_keys["dest_errors_status"] = StringCol()
        details_db_keys["source_errors_status"] = StringCol()

        ## now start parsing the xml tree
	root = source_tree.getroot()

        self.linkList = []
        if not root.get("request_timestamp") == None:
            self.requestTime = float(root.get("request_timestamp"))

        else:
            err = "Error! Couldn't get the request time in module " + self.__module__+ "\n"
            sys.stdout.write(err)
            self.error_message +=err
            return -1
        
        for link in root:
            if link.tag == "link":

                current_link = self.ErrorLog()
                current_link.remoteNode = str(link.get(self.inverseDirection))

                for block in link:
                    ## there are sometimes empty blocks
                    if block.tag == "block" and block.get("name"):
                        current_block = current_link.Block()
                        current_block.dataset_name,current_block.block_name  = str(block.get("name")).split("#")

                        for file in block:
                            if file.tag == "file":
                                current_file = current_block.File()
                                current_file.file_name = str(file.get("name"))

                                ## there is always only one transfer_error per file
                                for transErr in file.iterdescendants(tag="transfer_error"):
                                    current_file.timeDone = float(transErr.get("time_done"))
                                    
                                current_file.getTimeDiff(self.requestTime)

                                ## there is always only one detail_log per file
                                for desc in file.iterdescendants(tag="detail_log"):
                                    current_file.detail_log = str(desc.text)

                                current_block.files.append(current_file)
                                del current_file

                        current_link.blocks.append(current_block)
                        del current_block

                current_link.countErrors(self.timeThreshold)
                #current_link.checkSelf()
                self.linkList.append(current_link)
                del current_link

        self.buildDict()
        self.getErrorFractions()
        self.getStatus()

        self.fillDatabase(details_database, details_db_keys, details_db_values)


    def output(self):

        module_content = """
        <?php


        $details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];


        $onlyOnce = 0;
        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
        if ($onlyOnce == 0) {

        if($info["total_errors"] == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<table class="ErrorLogTable">\n');
        printf('<tr class="'.$service_status_color_flag.'"><td>failed transfers</td><td>'.$info["total_errors"].'</td></tr>\n');
        printf('<tr><td colspan="2" class="center">failed transfers details</td></tr>\n');
        if($info["dest_errors"] == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<tr class="' .$service_status_color_flag . '"><td>failed transfers due to destination</td><td>'.$info["dest_errors"].'</td></tr>\n');
        if($info["source_errors"] == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<tr class="' .$service_status_color_flag . '"><td>failed transfers due to source</td><td>'.$info["source_errors"].'</td></tr>\n');
        if($info["transfer_errors"] == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<tr class="' .$service_status_color_flag . '"><td>failed transfers due to transfer</td><td>'.$info["transfer_errors"].'</td></tr>\n');
        if($info["unknown_errors"] == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<tr class="' .$service_status_color_flag . '"><td>failed transfers due to unknown reasons</td><td>'.$info["unknown_errors"].'</td></tr>\n');
        printf('<tr></tr>\n');

        $frac_dest = 0.;
        $frac_source = 0.;
        $frac_trans = 0.;
        if ($info["total_errors"] != 0){
          $frac_dest = $info["dest_errors"]/$info["total_errors"] *100;
          $frac_source = $info["source_errors"]/$info["total_errors"] *100;
          $frac_trans = $info["transfer_errors"]/$info["total_errors"] *100;
        }
        
        printf('<tr class="' .$info["dest_errors_status"] . '"><td>fraction of destination errors</td><td>'.round($frac_dest).'%%</td></tr>\n');
        printf('<tr class="' .$info["source_errors_status"] . '"><td>fraction of source errors</td><td>'.round($frac_source).'%%</td></tr>\n');
        if ($frac_trans == 0){
        $service_status_color_flag = "success";
        }
        else {
        $service_status_color_flag = "report";
        }
        printf('<tr class="' .$service_status_color_flag . '"><td>fraction of transfer errors</td><td>'.round($frac_trans).'%%</td></tr>\n');
        
        printf('</table><br/>\n');
        }
        $onlyOnce = 1;
        }

        if ($onlyOnce == 0){

        printf('<table class="ErrorLogTable"><tr class="success"><td>No errors detected</td></tr></table>\n');
        
        }

        else{
        printf('
        <input type="button" value="details" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """);" />\n
        <div class="ErrorLogDetailedInfo" id=""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """ style="display:none;">\n');
        printf('<table class="ErrorLogTableDetails">\n');
        printf('<tr><td>node</td><td>failed transfers</td><td>error content</td></tr>\n');
        foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
                printf('<tr><td>'.$info["link_remote_node"].'</td><td class="center">'.$info["file_detail_log_nb"].'</td><td>'.$info["file_detail_log"].'</td></tr>\n');
        
        }
        
        printf('</div></table><br/>\n');
        }
        
        ?>
        """

        return self.PHPOutput(module_content)

    def getInverseDirection(self):

        ## inverse direction!
        if self.phpArgs.has_key("to") and not self.phpArgs.has_key("from"):
            self.inverseDirection = "from"
            self.direction = 'to'
        elif self.phpArgs.has_key("from") and not self.phpArgs.has_key("to"):
            self.inverseDirection = "to"
            self.direction = 'from'
        else:
            print "Error: module PhedexErrorLog needs exactly one direction specified."
            print "aborting ... "
            self.status = -1.
            return -1


    class ErrorLog:

        def __init__(self):
            self.remoteNode = ''
            self.blocks = []
            self.totalErrors = 0
            self.errorDict = {}
            self.destErrors = 0
            self.sourceErrors = 0
            self.unknownErrors = 0
            self.transferErrors = 0

        def countErrors(self, timeThreshold):
            for block in self.blocks:
                for file in block.files:
                    if file.timeDiff < float(timeThreshold):
                        if not self.errorDict.has_key(file.detail_log):
                            self.errorDict[file.detail_log] = 1
                        else:
                            self.errorDict[file.detail_log] += 1

                        self.totalErrors += 1
                        self.specifyError(file)
                        

        def specifyError(self,file):
            reason = file.detail_log.split(" ",1)
            if reason[0] == "SOURCE":
                self.sourceErrors +=1
            elif reason[0] == "TRANSFER":
                self.transferErrors += 1
            elif reason[0] == "DESTINATION":
                self.destErrors += 1
            else:
                self.unknownErrors += 1
            

        class Block:

            def __init__(self):
                self.dataset_name = ''
                self.block_name = ''
                self.files = []

            class File:
                
                def __init__(self):
                    self.file_name = ''
                    self.detail_log = ''
                    self.timeDone = 0.
                    self.timeDiff = 0.

                def getTimeDiff(self,requestTime):
                    ## in hours
                    self.timeDiff = (requestTime - self.timeDone)/3600 
                        
        

    def getErrorFractions(self):

        for link in self.linkList:
            self.globalTotalErrors += link.totalErrors
            self.globalSourceErrors += link.sourceErrors
            self.globalDestErrors += link.destErrors
            self.globalTransferErrors += link.transferErrors
            self.globalUnknownErrors += link.unknownErrors
            

        if not self.globalTotalErrors == 0.:
            self.destErrorFraction = float(self.globalDestErrors)/self.globalTotalErrors
            self.sourceErrorFraction = float(self.globalSourceErrors)/self.globalTotalErrors
        else:
            self.destErrorFraction = 0.
            self.sourceErrorFraction = 0.

            
    def getThresholds(self):

        #try:
        #    self.destCritical = float(self.configService.get("setup","destCritical"))

        #except:
        #    ## if the data is transfered to the node, 10 percent of destination
        #    ## problems raises a critical status. Else, there will be no critical
        #    ## status
        #    if self.inverseDirection == "from":
        #        self.destCritical = 10.
        #    else:
        #        self.destCritical = 100.

        if not float(self.configService.getDefault("setup","destCritical",0)) == 0.:
            self.destCritical = float(self.configService.get("setup","destCritical"))

        else:
            ## if the data is transfered to the node, 10 percent of destination
            ## problems raises a critical status. Else, there will be no critical
            ## status
            if self.inverseDirection == "from":
                self.destCritical = 10.
            else:
                self.destCritical = 100.

        #try:
        #    self.destWarning = float(self.configService.get("setup","destWarning"))

        #except:
        #    ## if the data is transfered to the node, 5 percent of destination
        #    ## problems raises a warning status. Else, 40 percent
        #    if self.inverseDirection == "from":
        #        self.destWarning = 5.
        #    else:
        #        self.destWarning = 40.

        if not float(self.configService.getDefault("setup","destWarning",0)) == 0.:
            self.destWarning = float(self.configService.get("setup","destWarning"))

        else:
            ## if the data is transfered to the node, 5 percent of destination
            ## problems raises a warning status. Else, 40 percent
            if self.inverseDirection == "from":
                self.destWarning = 5.
            else:
                self.destWarning = 40.

        #try:
        #    self.sourceCritical = float(self.configService.get("setup","sourceCritical"))

        #except:
        #    ## if the data is transfered from the node, 10 percent of destination
        #    ## problems raises a critical status. Else, there will be no critical
        #    ## status
        #    if self.inverseDirection == "to":
        #        self.sourceCritical = 10.
        #    else:
        #        self.sourceCritical = 100.

        if not float(self.configService.getDefault("setup","sourceCritical",0)) == 0.:
            self.sourceCritical = float(self.configService.get("setup","sourceCritical"))

        else:
            ## if the data is transfered from the node, 10 percent of destination
            ## problems raises a critical status. Else, there will be no critical
            ## status
            if self.inverseDirection == "to":
                self.sourceCritical = 10.
            else:
                self.sourceCritical = 100.

        #try:
        #    self.sourceWarning = float(self.configService.get("setup","sourceWarning"))
            
        #except:
        #    ## if the data is transfered from the node, 5 percent of source
        #    ## problems raises a warning status. Else, 40 percent
        #    if self.inverseDirection == "to":
        #        self.sourceWarning = 5.
        #    else:
        #        self.sourceWarning = 40.

        if not float(self.configService.getDefault("setup","sourceWarning",0)) == 0.:
            self.sourceWarning = float(self.configService.get("setup","sourceWarning"))
            
        else:
            ## if the data is transfered from the node, 5 percent of source
            ## problems raises a warning status. Else, 40 percent
            if self.inverseDirection == "to":
                self.sourceWarning = 5.
            else:
                self.sourceWarning = 40.

        
    def getStatus(self):

        if int(self.globalTotalErrors) > int(self.errorThreshold):
            if (self.destErrorFraction*100) > self.destCritical or (self.sourceErrorFraction*100) > self.sourceCritical:
                self.status = 0.
            elif (self.destErrorFraction*100) > self.destWarning or (self.sourceErrorFraction*100) > self.sourceWarning:
                self.status = 0.5

            else:
                self.status = 1.
                
        else:
            self.status = 1.


    def initiateVariables(self):
        
        self.globalTotalErrors = 0
        self.globalTransferErrors = 0
        self.globalDestErrors = 0
        self.globalSourceErrors = 0
        self.globalUnknownErrors = 0
        self.clientErrorFraction = 0.
        self.sourceErrorFraction = 0.
        self.destErrorFraction = 0.
        self.globalDict = {}
        self.requestTime = 0.


    def buildDict(self):

        ## the globalDict has as keys the names of the remote nodes. The values are again dictionaries,
        ## which have as keys the detailed_log of the files and as values the number of appearences of
        ## this special detailed_log in this special link
        for link in self.linkList:
            ## if not errors too old
            if not link.totalErrors == 0:
                self.globalDict[link.remoteNode] = link.errorDict

    def fillDatabase(self,details_database,details_db_keys,details_db_values):


	my_subtable_class = self.table_init( details_database, details_db_keys )

        details_db_values['total_errors'] = self.globalTotalErrors
        details_db_values['dest_errors'] = self.globalDestErrors
        details_db_values['source_errors'] = self.globalSourceErrors
        details_db_values['unknown_errors'] = self.globalUnknownErrors
        details_db_values['transfer_errors'] = self.globalTransferErrors

        ## status can only be warning/critical, if number of total errors have
        ## trespassed the error number threshold set in the config
        if int(self.globalTotalErrors) > int(self.errorThreshold):
            if (self.destErrorFraction*100) > self.destCritical:
                details_db_values['dest_errors_status'] = 'critical'
            elif (self.destErrorFraction*100) > self.destWarning:
                details_db_values['dest_errors_status'] = 'warning'
            elif (self.destErrorFraction*100) > 0. :
                details_db_values['dest_errors_status'] = 'report'
            else:
                details_db_values['dest_errors_status'] = 'success'

        
            if (self.sourceErrorFraction*100) > self.sourceCritical:
                details_db_values['source_errors_status'] = 'critical'
            elif (self.sourceErrorFraction*100) > self.sourceWarning:
                details_db_values['source_errors_status'] = 'warning'
            elif (self.sourceErrorFraction*100) > 0. :
                details_db_values['source_errors_status'] = 'report'
            else:
                details_db_values['source_errors_status'] = 'success'

        else:
            if (self.destErrorFraction*100) > 0. :
                details_db_values['dest_errors_status'] = 'report'
            else:
                details_db_values['dest_errors_status'] = 'success'

            if (self.sourceErrorFraction*100) > 0. :
                details_db_values['source_errors_status'] = 'report'
            else:
                details_db_values['source_errors_status'] = 'success'
            

        for node in self.globalDict.keys():
            details_db_values['link_remote_node'] = node
            for error in self.globalDict[node].keys():
                details_db_values['file_detail_log'] = error
                details_db_values['file_detail_log_nb'] = self.globalDict[node][error]

                # store the values to the database
                self.table_fill( my_subtable_class, details_db_values )



