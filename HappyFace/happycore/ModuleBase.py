import os, sys, re
import ConfigParser

from HTMLOutput import *

from sqlobject import *		# for SQL database functionality
from threading import Thread	# for threading functionality
from DataBaseLock import *
from ConfigService import *

#########################################################
# basic class for all test modules
#########################################################
class ModuleBase(Thread,DataBaseLock,HTMLOutput):

    def __init__(self, module_options):
	HTMLOutput.__init__(self, 8)

        # Configuration Service to read in all config parameters
        self.configService = ConfigService()

        allSubClasses = []
        self.getSubRec([self.__class__],allSubClasses)
        for i in allSubClasses:
            self.configService.addModule(i)

        self.configService.readParameter()

        # Container for download requests
        self.downloadRequest = {}

	Thread.__init__(self)

	lock_obj = DataBaseLock()
	self.lock = lock_obj.lock
	
        self.category = module_options["category"]
	self.timestamp = module_options["timestamp"]
        self.archive_dir = module_options["archive_dir"]
	self.holdback_time = int( self.configService.getDefault('setup','holdback_time',module_options["holdback_time"]) )


	# pre-defined status value -1 : no info
        self.status = -1
        self.error_message = ""

        # definitions for the database table
	self.database_table = self.__module__ + '_table'

	self.db_keys = {}
	self.db_values = {}

	self.db_keys["module"]		= StringCol()
	self.db_keys["category"]	= StringCol()
	self.db_keys["status"]		= FloatCol()
	self.db_keys["error_message"]	= StringCol()
	self.db_keys["mod_title"]	= StringCol()
	self.db_keys["mod_type"]	= StringCol()
	self.db_keys["weight"]		= FloatCol()
	self.db_keys["definition"]	= StringCol()
	self.db_keys["instruction"]	= StringCol()
	self.db_keys["datasource"]	= StringCol()


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


    def table_init(self,tableName,table_keys):

	# timestamp will always be saved
    	table_keys["timestamp"] = IntCol()

	# create an index for the timestap column for faster access
	table_keys["index"] = DatabaseIndex('timestamp')
	
	# lock object enables exclusive access to the database
	self.lock.acquire()
	
	try:
	    class sqlmeta:
	        table = tableName
	        fromDatabase = True

	    DBProxy = type(tableName + "_DBProxy",(SQLObject,),dict(sqlmeta = sqlmeta))
		    
	    avail_keys = []
	    for key in DBProxy.sqlmeta.columns.keys():
	        avail_keys.append( re.sub('[A-Z]', lambda x: '_' + x.group(0).lower(), key) )
	    
	    My_DB_Class = type(tableName, (SQLObject,), table_keys)
	    My_DB_Class.createTable(ifNotExists=True)	

	    for key in filter(lambda x: x not in avail_keys, table_keys.keys()):
                if key != "index":
	            try: DBProxy.sqlmeta.addColumn(table_keys[key].__class__(key), changeSchema=True)
		    except: print "Failing at adding new column: \"" + str(key) + "\" in the module " + self.__module__

        except:
	    My_DB_Class = type(tableName, (SQLObject,), table_keys)
	    My_DB_Class.createTable(ifNotExists=True)

	# unlock the database access
	self.lock.release()
	
	return My_DB_Class

    def table_fill(self,My_DB_Class,table_values):
	table_values["timestamp"] = self.timestamp

	# lock object enables exclusive access to the database
	self.lock.acquire()

	try:
	    My_DB_Class(**table_values)
	finally:
	    # unlock the database access
	    self.lock.release()

    def table_clear(self, My_DB_Class, holdback_time):

	if holdback_time == -1:
	    return

	time_limit = self.timestamp - 24 * 3600 * holdback_time

	self.lock.acquire()

	old_data = My_DB_Class.select( My_DB_Class.q.timestamp <= time_limit)

	for row in old_data:
	    My_DB_Class.delete(row.id)

	self.lock.release()

	print self.__module__ + " is cleared with a holdback time value of: " + str(holdback_time) + " days."

    def processDB(self):

	# definition of the databases values which should be stored
	self.db_values['module']	= self.__module__
	self.db_values['category']	= self.category
	self.db_values['status']	= self.status
	self.db_values['error_message'] = self.error_message

        self.db_values['mod_title']     =  self.configService.getDefault('setup','mod_title',self.__module__)
        self.db_values['mod_type']      =  self.configService.getDefault('setup','mod_type','rated')
        self.db_values['weight']        =  float(self.configService.getDefault('setup','weight',1.0))
        self.db_values['definition']    =  self.configService.getDefault('setup','definition','')
        self.db_values['instruction']   = self.configService.getDefault('setup','instruction','')

        self.db_values['datasource']    = self.configService.getDefault('setup','source','').replace('%','&#37;')
	
	# init and storage the module specific information into the module table
	module_table_class = self.table_init( self.database_table, self.db_keys )
	self.table_fill( module_table_class, self.db_values )
	self.table_clear(module_table_class, self.holdback_time)

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

	plot_values = ""
	for value in self.db_values:
	    if (type(self.db_values[value]) is int) or (type(self.db_values[value]) is float):
		plot_values += '<option value="' + value + '">' + value + '</option>'
    
	html_begin = []
	html_begin.append(  '<!-- Beginning of module "' + self.__module__ + '" -->')
	html_begin.append("""<a id="' . $data["module"]. '"></a>""")
	html_begin.append("""<table class="main" style="width:1000px;">""")
	html_begin.append(  ' <tr>')
	html_begin.append(  '  <td style="width:64px;">')
	html_begin.append("""   <button class="HappyButton" type="button" onfocus="this.blur()" onclick="show_hide_info(\\\'""" + self.__module__+ """_info\\\', \\\'""" + self.__module__ + """_info_link\\\');">' .$status_symbol. '</button>""")
	html_begin.append(  '  </td>')
	html_begin.append("""  <td><strong><a href="?date='.$date_string.'&amp;time='.$time_string.'&amp;t='.$category_id.'&amp;m=""" + self.__module__ + """" style="text-decoration:none;color:#000000;" onfocus="this.blur()">' . htmlentities($data['mod_title']) . '</a><br />' . $mod_time_message . ' <span style="color:gray;">-</span> <small><a href="javascript:show_hide_info(\\\'""" + self.__module__ + """_info\\\', \\\'""" + self.__module__ + """_info_link\\\');" class="HappyLink" onfocus="this.blur()" id=\"""" + self.__module__ + """_info_link\">Show module information</a></small></strong></td>""")
	html_begin.append(""" </tr>'.$error_message.'""")
	html_begin.append(  ' <tr>')
	html_begin.append(  '  <td>')
	html_begin.append(  '  </td>')
	html_begin.append(  '  <td>')

	infobox = []
	infobox.append(     '   <div id="' + self.__module__ + '_info" style="display: none;">')
	infobox.append(     '    <table class="HappyDesc">')
	infobox.append(     '     <tr><td style="width:20%">Module File:</td><td>' + self.__module__ + '.py</td></tr>')
	infobox.append(   """     <tr><td style="width:20%">Module Type:</td><td>' . $data["mod_type"] . '</td></tr>""")
	infobox.append(   """     <tr><td style="width:20%">Status Value:</td><td>' . number_format($data["status"],1). '</td></tr>""")
	infobox.append(   """     <tr><td style="width:20%">Weight:</td><td>' . number_format($data["weight"],1) .'</td></tr>""")
	infobox.append(   """     <tr><td style="width:20%">Definition:</td><td>' .$data["definition"]. '</td></tr>""")
	infobox.append(   """     <tr><td style="width:20%">Source:</td><td>' .$data["datasource"]. '</td></tr>""")
	infobox.append(   """     <tr><td style="width:20%">Instruction:</td><td>' .$data["instruction"]. '</td></tr>""")
	infobox.append(     '    </table>')

	infobox.append(     '    <form id="' + self.__module__ + '_PlotForm" action="plot_generator.php" method="get" onsubmit="javascript: submitFormToWindow(this)">')
	infobox.append(     '     <table style="font: bold 0.7em sans-serif; width:800px; background-color: #ddd; border-left: 1px #999 solid; border-right: 1px #999 solid; border-bottom: 1px #999 solid; text-align: center;">')
	infobox.append(     '      <tr>')
	infobox.append(     '       <td>Start:</td>')
	infobox.append(     '       <td>')
	infobox.append(   """        <input name="date0" type="text" size="10" style="text-align:center;" value="' . strftime("%Y-%m-%d", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
	infobox.append(   """        <input name="time0" type="text" size="5" style="text-align:center;" value="' . strftime("%H:%M", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
	infobox.append(     '       </td>')
	infobox.append(     '       <td>End:</td>')
	infobox.append(     '       <td>')
	infobox.append(   """        <input name="date1" type="text" size="10" style="text-align:center;" value="' . $date_string .'" />""")
	infobox.append(   """        <input name="time1" type="text" size="5" style="text-align:center;" value="' . $time_string . '" />""")
	infobox.append(     '       </td>')
	infobox.append(     '       <td>Variable:</td>')
	infobox.append(     '       <td>')
	infobox.append(     '        <select name="variables">')
	infobox.append(     '         ' + plot_values)
	infobox.append(     '        </select>')
	infobox.append(     '       </td>')
	infobox.append(     '       <td>')
	infobox.append(   """        <input type="hidden" name="module" value="' . $data["module"] . '" />""")
	infobox.append(   """        <div><button onclick="javascript: submitform()" onfocus="this.blur()">Show Plot</button></div>""")
	infobox.append(     '       </td>')
	infobox.append(     '      </tr>')
	infobox.append(     '     </table>')
	infobox.append(     '    </form>')
	infobox.append(     '   </div>')
	infobox.append(     '   <br />')

	#for i in infobox:
	#	html_begin.append('   ' + i)
	#html_begin.append(  "'); ?>")

	# module content goes between html_begin and html_end

	html_end = []
	html_end.append(  '  </td>')
	html_end.append(  ' </tr>')
	html_end.append(  '</table>')
	html_end.append(  '<br />')
	html_end.append(  '<!-- End of module "' + self.__module__ + '" -->')
	html_end.append(  '')
	html_end.append(  '<hr class="HappyHr" />')
	html_end.append(  '')

	# Indentation=8 is default and used for the module content. We use indentation 5
	# for the wrapper HTML in which the module's content is inserted and which produces
	# three more levels of indentation.
	self.indentation = 5
	output = """<?php

	/*** $sql_strings contains all SQL queries, created in SQLCallRoutines.py ***/
	foreach ($dbh->query($sql_command_strings['""" + self.__module__ + """']) as $data)
	{
	    $status_symbol = getModStatusSymbol($data["status"], $data["mod_type"]);
	    $error_message = "";
	    if ( $data['error_message'] != "" )
	    {
	        $error_message = '\n <tr><td></td><td><h4 style="color:red;">' . htmlentities($data["error_message"]) .'</h4></td></tr>';
	    }
	    if ($server_time - $data["timestamp"] < 1800)
	    {
	        $mod_time_message = '<span style="color:#999; font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>';
	    }
	    else
	    {
	        $mod_time_message = '<span style="color:#FF6666;font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>';
	    }

	    /*** Get variables for the direct module link ***/

	    /*** print the HTML output ***/
	    print('""" + self.PHPArrayToString(html_begin) + """');
	    print('""" + self.PHPArrayToString(infobox) + """');

	    ?>""" + module_content + """<?php

	    print('""" + self.PHPArrayToString(html_end) + """');
	}

	?>"""

	self.indentation = 8
        return output
