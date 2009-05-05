import os, sys
import ConfigParser

from sqlobject import *		# for SQL database functionality
from threading import Thread	# for threading functionality

#########################################################
# basic class for all test modules
#########################################################
class ModuleBase(Thread,object):

    def __init__(self, category, timestamp, archive_dir):

	Thread.__init__(self)

        # read class config file
        config = self.readConfigFile('./happycore/ModuleBase') # empty

        self.category = category
	self.timestamp = timestamp
        self.archive_dir = archive_dir

	# pre-defined status value -1 : no info
        self.status = -1
        self.error_message = ""

	# read module specific config file, check where the module is stored
	if os.path.isfile('./modules/' + self.__module__ + '.py') == True:
	    module_config_file = './modules/' + self.__module__
	if os.path.isfile('./modules.local/' + self.__module__ + '.py') == True:
	    module_config_file = './modules.local/' + self.__module__
        self.mod_config = self.readConfigFile(module_config_file)
        self.mod_config

	self.mod_title		= self.mod_config.get('setup','mod_title',self.__module__)
	self.mod_type		= self.mod_config.get('setup','mod_type',"rated")
	self.weight		= float(self.mod_config.get('setup','weight',1.0))
	self.definition		= self.mod_config.get('setup','definition',"")
	self.instruction	= self.mod_config.get('setup','instruction',"")

        # definitions for the database table
	self.database = self.__module__ + '_table'
	
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
	
    def storeToDB(self,lock):

	# definition of the databases values which should be stored
	self.db_values['module']	= self.__module__
	self.db_values['category']	= self.category
	self.db_values['timestamp']	= self.timestamp
	self.db_values['status']	= self.status
	self.db_values['error_message'] = self.error_message
	self.db_values['mod_title']	= self.mod_title
	self.db_values['mod_type']	= self.mod_type
	self.db_values['weight']	= self.weight
	self.db_values['definition']	= self.definition
	self.db_values['instruction']	= self.instruction

	# lock object enables exclusive access to the database
	lock.acquire()

	# create dynamically a SQLObject Class
	# the name of the class corresponds to the table name in the DB
	# table name = self.database; structure = self.db_keys
        My_DB_Class = type(self.database, (SQLObject,), self.db_keys )
	
	My_DB_Class.sqlmeta.cacheValues = False
	My_DB_Class.sqlmeta.fromDatabase = True
	#My_DB_Class.sqlmeta.lazyUpdate = True

	# if table is not existing, create it
        My_DB_Class.createTable(ifNotExists=True)
	
	# store the values self.db_values to the database
	My_DB_Class(**self.db_values)
	
	# unlock the database access
	lock.release()


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
	<table class="desc">
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

            /*** print the HTML output ***/
            printf('
		<a id="' . $data["module"]. '"></a>
                <table class="main" style="width:1000px;">
                    <tr>
                        <td style="width:64px;"><button class="button" type="button" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_info\\\'" + """);">' .$status_symbol. '</button></td>
                        <td><strong>' .$data['mod_title']. '<br />' . $mod_time_message . '</strong></td>
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
            <br/><hr/>
            ');
        }
        ?>
        """
        return output
