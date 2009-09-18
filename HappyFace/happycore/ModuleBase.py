import os, sys
import ConfigParser

from sqlobject import *		# for SQL database functionality
from threading import Thread	# for threading functionality
from DataBaseLock import *
from ConfigService import *

import re

#########################################################
# basic class for all test modules
#########################################################
class ModuleBase(Thread,DataBaseLock,object):

    def __init__(self, category, timestamp, archive_dir):



        # Configuration Service to read in all config parameters
        self.configService = ConfigService()

        allSubClasses = []
        self.getSubRec([self.__class__],allSubClasses)
        for i in allSubClasses:
            self.configService.addModule(i)

        self.configService.readParameter()


        self.mod_title	 = self.configService.getDefault('setup','mod_title',self.__module__)
	self.mod_type	 = self.configService.getDefault('setup','mod_type','rated')
	self.weight	 = float(self.configService.getDefault('setup','weight',1.0))
	self.definition	 = self.configService.getDefault('setup','definition','')
	self.instruction = self.configService.getDefault('setup','instruction','')


        # Container for download requests
        self.downloadRequest = {}



	Thread.__init__(self)

	lock_obj = DataBaseLock()
	self.lock = lock_obj.lock
	
        self.category = category
	self.timestamp = timestamp
        self.archive_dir = archive_dir

	# pre-defined status value -1 : no info
        self.status = -1
        self.error_message = ""


        # definitions for the database table
	self.database_table = self.__module__ + '_table'

	self.db_keys = {}
	self.db_values = {}

	self.db_keys["module"]		= StringCol()
	self.db_keys["category"]	= StringCol()
	self.db_keys["timestamp"]	= IntCol()
	self.db_keys["status"]		= FloatCol()
	self.db_keys["error_message"]	= StringCol()
	self.db_keys["mod_title"]	= StringCol()
	self.db_keys["mod_type"]	= StringCol()
	self.db_keys["weight"]		= FloatCol()
	self.db_keys["definition"]	= StringCol()
	self.db_keys["instruction"]	= StringCol()

	# create an index for the timestap column for faster access
	self.db_keys["index"] = DatabaseIndex('timestamp')



	


    def getSubRec(self,theClasses,allSubClasses):
        p = re.compile("<class '(\w*).\w*'>")
        subClasses = []
        for c in theClasses:
            theClassMatch = p.match(str(c))
            if theClassMatch:
                theClassName = theClassMatch.group(1)
                if theClassName not in allSubClasses: allSubClasses.insert(0,theClassName)
            if str(c) == "<class 'ModuleBase.ModuleBase'>": continue
            for entry in c.__bases__:
                if c not in subClasses: subClasses.append(entry)

        if len(subClasses) == 0: return 

        else:
            return self.getSubRec(subClasses,allSubClasses)


    def getCssRequests(self):
        return self.configService.getCssRequests()

    def setDownloadService(self,downloadService):
        self.downloadService = downloadService
        

    def getDownloadRequests(self):
        configDownloadRequests = self.configService.getDownloadRequests()
        for tag in configDownloadRequests.keys():
            self.downloadRequest[tag] = configDownloadRequests[tag]
        
        downloadList = []
        for downloadTag in self.downloadRequest:
            downloadList.append(self.downloadRequest[downloadTag])
        return downloadList


    def storeToDB(self):

	# definition of the databases values which should be stored
	self.db_values['module']	= self.__module__
	self.db_values['category']	= self.category
	self.db_values['timestamp']	= self.timestamp
	self.db_values['status']	= self.status
	self.db_values['error_message'] = self.error_message
        self.db_values['mod_title']     = self.mod_title
        self.db_values['mod_type']      = self.mod_type
        self.db_values['weight']        = self.weight
        self.db_values['definition']    = self.definition
        self.db_values['instruction']   = self.instruction

     



		
	db_keys = self.db_keys
	db_values = self.db_values
	tableName = self.database_table

	# lock object enables exclusive access to the database
	self.lock.acquire()
	
	try:
	    class sqlmeta:
	        table = tableName
	        fromDatabase = True

	    DBProxy = type(self.__module__ + "_dbclass",(SQLObject,),dict(sqlmeta = sqlmeta))
		    
	    avail_keys = []
	    for key in DBProxy.sqlmeta.columns.keys():
	        avail_keys.append( re.sub('[A-Z]', lambda x: '_' + x.group(0).lower(), key) )
	    
	    My_DB_Class = type(tableName, (SQLObject,), db_keys)
	    My_DB_Class.createTable(ifNotExists=True)	

	    for key in filter(lambda x: x not in avail_keys, db_keys.keys()):
                if key != "index":
	            try: DBProxy.sqlmeta.addColumn(db_keys[key].__class__(key), changeSchema=True)
		    except: print "Failing at adding new column: \"" + str(key) + "\" in the module " + self.__module__

        except:
	    My_DB_Class = type(tableName, (SQLObject,), db_keys)
	    My_DB_Class.createTable(ifNotExists=True)

        My_DB_Class(**db_values)

	# unlock the database access
	self.lock.release()


    # reading config files and return the corresponding directory structure
    def readConfigFile(self,config_file):

	config = ConfigParser.ConfigParser()
        config.optionxform = str #Needed to enable capital letters

        # try to open standard config file, must be available
        try:
	    config.readfp(open(config_file + '.cfg'))
        except IOError:
            sys.stdout.write('Could not find configuration file ' + config_file + '.cfg, aborting ...\n')
            sys.exit(-1)

        # try to open local config file if available (standard config settings will be overwritten)
	try:
	    config.readfp(open(config_file + '.local'))
        except IOError:
            pass
	
	return config


    # the module frame asks for the following quantities
    # status, error_message, mod_title, mod_type, weight, definition, instruction
    def PHPOutput(self,module_content):

        infobox = """
	<div id=""" + "\\\'" + self.__module__+ "_info\\\'" + """ style="display: none;">
	<table class="HappyDesc">
		<tr><td style="width:20%%">Module File:</td><td>""" + self.__module__ + ".py" + """</td></tr>
		<tr><td style="width:20%%">Module Type:</td><td>' . $data["mod_type"].'</td></tr>
		<tr><td style="width:20%%">Status Value:</td><td>' . number_format($data["status"],1). '</td></tr>
		<tr><td style="width:20%%">Weight:</td><td>' . number_format($data["weight"],1) .'</td></tr>
		<tr><td style="width:20%%">Definition:</td><td>' .$data["definition"]. '</td></tr>
		<tr><td style="width:20%%">Instruction:</td><td>' .$data["instruction"]. '</td></tr>
	</table>
	</div>
	<br />
        """

        output = """
        <?php
	/*** $sql_strings contains all SQL queries, created in SQLCallRoutines.py ***/
	foreach ($dbh->query($sql_command_strings['""" + self.__module__ + """']) as $data)
        {
            $status_symbol = getModStatusSymbol($data["status"], $data["mod_type"]);
            $error_message = "";
            if ( $data['error_message'] != "" ) { $error_message = '<tr><td></td><td><h4 style="color:red;">'. $data["error_message"] .'</h4></td></tr>'; }

	    if ($server_time - $data["timestamp"] < 1800) { $mod_time_message = '<span style="color:#999; font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>'; }
	    else { $mod_time_message = '<span style="color:#FF6666;font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>'; }

	    /*** Get variables for the direct module link ***/

            /*** print the HTML output ***/
            printf('
		<a id="' . $data["module"]. '"></a>
                <table class="main" style="width:1000px;">
                    <tr>
                        <td style="width:64px;"><button class="HappyButton" type="button" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_info\\\'" + """);">' .$status_symbol. '</button></td>
                        <td><strong><a href="?date='.$date_string.'&amp;time='.$time_string.'&amp;t='.$category_id.'&amp;m=""" + self.__module__ + """" style="text-decoration:none;color:#000000;" onfocus="this.blur()">' .$data['mod_title']. '</a><br />' . $mod_time_message . '</strong></td>
		    </tr>
		    '.$error_message.'
                    <tr>
		        <td></td><td>""" + infobox + """');
            ?>
            """ + module_content + """
            <?php
            printf('
              </td>
             </tr>
            </table>
            <br/><hr class="HappyHr"/>
            ');
        }
        ?>
        """
        return output
