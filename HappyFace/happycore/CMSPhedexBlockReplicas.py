from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

#
# Friederike Nowak
# University of Hamburg
# 2009/06/22
#
# 2009/09/18, Volker Buege:
#             Module ported to new config service
#             Module now inhertis from PhpDownload to avoid code doubling
#
# ToDo:

######################################################
#                                                    #
# Uses the informations about the block replicas     #
# on a site provided by the phedex API. Informations #
# about resident blocks are displayed only if        #
# they are in the transfer phase or if there is a    #
# mismatch between block size and resident size.     #
#                                                    #
######################################################

class CMSPhedexBlockReplicas(ModuleBase,PhpDownload):

    def __init__(self,module_options):


        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)
	PhpDownload.__init__(self)

        ## get the instance
        self.instance = self.configService.get('setup','instance')

        # definition of the database table keys and pre-defined values
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.dsTag = 'cmsPhedexBlockReplicas_xml_source'

	self.base_url += '/'+self.instance+'/blockreplicas'

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

        self.downloadRequest[self.dsTag] = 'wget|'+self.fileType+'||'+self.base_url+'/'+self.instance+'/blockreplicas'+"?"+"&".join(argList)




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

        details_db_keys['block_bytes'] = IntCol()
        details_db_keys['block_files'] = IntCol()
        details_db_keys['block_name'] = StringCol()
        details_db_keys['rep_bytes'] = IntCol()
        details_db_keys['rep_files'] = IntCol()
        details_db_keys['rep_group'] = StringCol()
        details_db_keys['block_status'] = FloatCol()
        details_db_keys['dataset_name'] = StringCol()

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
        entry = False

        self.status = 1

        for block in root:
            if block.tag == "block":

                dataset_name,block_number = block.get('name').split('#')

                current_block = self.Block()
                current_block.block_bytes = int(block.get('bytes'))
                current_block.block_files = int(block.get('files'))
                current_block.block_name = block_number
                current_block.dataset_name = dataset_name

                ## for one node in the cfg, there can be only one replica
                ## per block
                for replica in block:
                    if replica.tag == "replica":

                        current_block.complete = self.isComplete(str(replica.get('complete')))
                        current_block.rep_bytes = int(replica.get('bytes'))
                        current_block.rep_files = int(replica.get('files'))
                        current_block.rep_group = str(replica.get('group'))

                ## if block is not alright, make an entry in the database
                current_block.checkBlock()

                ## "not alright" means not complete
                if not current_block.ok:
                    
                    details_db_values['dataset_name'] = current_block.dataset_name
                    details_db_values['block_name'] = current_block.block_name
                    details_db_values['block_bytes'] = current_block.block_bytes
                    details_db_values['block_files'] = current_block.block_files
                    details_db_values['block_status'] = current_block.block_status
                    details_db_values['rep_bytes'] = current_block.rep_bytes
                    details_db_values['rep_files'] = current_block.rep_files
                    details_db_values['rep_group'] = current_block.rep_group

                    Details_DB_Class(**details_db_values)

                    entry = True

                    del current_block
                    


        ## if everything is ok, fill in a dummy block for technical reasons
        if not entry:
            
            dummy_block = self.Block()
            dummy_block.block_name = 'dummy'
            
            details_db_values['dataset_name'] = dummy_block.dataset_name
            details_db_values['block_name'] = dummy_block.block_name
            details_db_values['block_bytes'] = dummy_block.block_bytes
            details_db_values['block_files'] = dummy_block.block_files
            details_db_values['block_status'] = dummy_block.block_status
            details_db_values['rep_bytes'] = dummy_block.rep_bytes
            details_db_values['rep_files'] = dummy_block.rep_files
            details_db_values['rep_group'] = dummy_block.rep_group

                       
            Details_DB_Class(**details_db_values)

            del dummy_block
            
        # unlock the database access
	self.lock.release()

        ## status is always happy, because for no there is no
        ## critical /warnig block_status
        self.status = 1.


    def output(self):

        module_content = """
        <?php
        $details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

        $dummy = false;
        foreach ($dbh->query($details_db_sqlquery) as $info){
          if ($info["block_name"] == "dummy"){
            $dummy = true;
          }
        }

        if(!$dummy){
          print('<table class="TableData">');
          print('<tr="TableHeader"><td>dataset</td><td>block</td><td>resident size [MB]</td></tr>');

          foreach ($dbh->query($details_db_sqlquery) as $info)
       	  {
               if ($info["block_status"] == 2){
                    $service_status_color_flag = "report";
          }  
               else if ($info["block_status"] == 0){
                    $service_status_color_flag = "critical";
          }
               else $service_status_color_flag = "undefined";

          $rep_size = round($info["rep_bytes"]/(1024*1024*1024),2);

          print('<tr class="' .$service_status_color_flag . '"><td>'.$info["dataset_name"].'</td><td>' . $info["block_name"] . '</td><td>'.$rep_size.'</td></tr>');
          }
          
          print('</table><br/>');

          
          print('<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """);" />
          <div class="DetailedInfo" id=""" + "\\\'" + self.__module__+ "_failed_result\\\'" + """ style="display:none;">');

          print('<table class="TableDetails">');
          print('<tr class="TableHeader"><td>dataset</td><td>block</td><td>block files</td><td>resident files</td><td>block size [MB]</td><td>resident size [MB]</td><td>group</td></tr>');

          foreach ($dbh->query($details_db_sqlquery) as $info)
          {
               if ($info["block_status"] == 2){
                  $service_status_color_flag = "report";
          }
               else if ($info["block_status"] == 0){
                  $service_status_color_flag = "critical";
          }
               else $service_status_color_flag = "undefined";

          $rep_size = round($info["rep_bytes"]/(1024*1024*1024),2);
          $block_size = round($info["block_bytes"]/(1024*1024*1024),2);

          print('<tr class="' .$service_status_color_flag . '"><td>'.$info["dataset_name"].'</td><td>' . $info["block_name"] . '</td><td>'.$info["block_files"].'</td><td>'.$info["rep_files"].'</td><td>' .$block_size . '</td><td>'.$rep_size.'</td><td>'.$info["rep_group"].'</td></tr>');
          }
          print('</table>');
        
    
        print('</div><br/>');
        }
        else{
          print('All is fine.');
        }
        
        ?>
        """

        return self.PHPOutput(module_content)


    class Block:

        def __init__(self):
            self.block_files = 0
            self.block_bytes = 0
            self.block_name = ''
            self.dataset_name = ''
            self.rep_files = 0
            self.rep_bytes = 0
            self.rep_group = ''
            self.ok = True
            self.block_status = -1
            self.complete = True
        
        def checkBlock(self):
            
            ## if a block is not complete, than it could be either in
            ## the transfer phase or it could be broken 
            if not self.complete:
                self.ok = False
                self.block_status = 2

            else:
                self.block_status = 1


    def isComplete(self,string):
        complete = False
        if string == 'y':
            complete = True

        return complete
            

