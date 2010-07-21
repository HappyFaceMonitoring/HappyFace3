import os, sys, re, time
import traceback
import ConfigParser
import GetData

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
	self.plot_blacklist = self.configService.getDefault('setup', 'plot_blacklist', '').split(',')

	self.archive_columns = []
	self.clear_tables = []

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

    def getDownloadRequest(self, downloadTag):
        if not downloadTag in self.downloadRequest:
	    raise Exception('Could not find required download tag: ' + downloadTag)
	return self.downloadRequest[downloadTag]

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

    # This should be used instead of table_fill if many rows are to be inserted
    # since this is much faster than calling table_fill multiple times.
    def table_fill_many(self, My_DB_Class, table_values):
	# lock object enables exclusive access to the database
	self.lock.acquire()

	try:
            for value in table_values:
	        value['timestamp'] = self.timestamp

            # Inserting using SQLObject is quite slow, so we use executemany
	    # directly within a transaction which is faster by at least
	    # a factor 10. See also this for a comparison between various APIs:
	    # http://pyinsci.blogspot.com/2007/07/fastest-python-database-interface.html

	    # TODO: I am not sure how sqlite-specific this code is, maybe
	    # needs to be changed/adapted for other DBMSes if we switch one day.
	    connection = sqlhub.processConnection
            dbObject = connection.getConnection()
	    cursor = dbObject.cursor()

	    name = My_DB_Class.sqlmeta.table
	    columns = My_DB_Class.sqlmeta.columns

	    cursor.execute('BEGIN')
	    cursor.executemany('INSERT INTO ' + name + '(' + ','.join(columns) + ') VALUES (' + ','.join(map(lambda x: ':'+x, columns)) + ')', table_values)
	    cursor.execute('COMMIT')
	finally:
	    self.lock.release()

    # This should be called by modules to set up their subtables for clearing
    # They can't call table_clear directly because they would otherwise exceed
    # the timeout for module processing. Instead this queues the table to be
    # cleared at the end in processDB.
    def subtable_clear(self, DB_Class, archive_columns, holdback_time):
        self.clear_tables.append({'table_class': DB_Class, 'archive_columns': archive_columns, 'holdback_time': holdback_time})

    def table_clear(self, My_DB_Class, archive_columns, holdback_time):

	if holdback_time == -1:
	    return

	time_limit = self.timestamp - 24 * 3600 * holdback_time

	self.lock.acquire()

	try:
		old_data = My_DB_Class.select( My_DB_Class.q.timestamp <= time_limit)

		for row in old_data:
		    for column in archive_columns:
		        file = getattr(row,column)

			# If Download failed the column might be empty. We don't
			# have anything to do in that case.
			if file is None:
			    break

			# Find archive directory for this file
			# TODO: This is a bit of a hack as we are not supposed to know
			# anything about the archive directory structure... should find
			# a better solution for this
			timestamp = row.timestamp
			time_tuple = time.localtime(timestamp)

			output_dir = self.archive_dir
			while os.path.basename(output_dir) != 'archive':
				output_dir = os.path.dirname(output_dir)

			archive_dir = output_dir + "/" + str(time_tuple.tm_year) + "/" + ('%02d' % time_tuple.tm_mon) + "/" + ('%02d' % time_tuple.tm_mday) + "/" + str(timestamp)
			file = archive_dir + '/' + file

			try:
				# Remove archived files
				os.unlink(file)
				# Remove empty directories (note this throws if a
				# directory attempted to be removed is not empty).
				dir = archive_dir
				while dir != output_dir:
					os.rmdir(dir)
					dir = os.path.dirname(dir)
			except:
				pass

		My_DB_Class.deleteMany(My_DB_Class.q.timestamp <= time_limit)
	except Exception, ex:
		print 'Failed to clear table: ' + str(ex)
	        traceback.print_exc()
	finally:
		self.lock.release()

	print 'Table "' + My_DB_Class.sqlmeta.table + '" of module "' + self.__module__ + '" is cleared with a holdback time value of: ' + str(holdback_time) + ' days; clearing all data from before ' + time.strftime("%c", time.localtime(time_limit))

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
	self.table_clear(module_table_class, self.archive_columns, self.holdback_time)
	for table in self.clear_tables:
	    self.table_clear(table['table_class'], table['archive_columns'], table['holdback_time'])

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

    def run(self):
        try:
	    self.process()
	except GetData.DownloadError, ex:
	    self.status = -1.0
	    msg = str(ex).strip()
	    self.error_message = msg
	    sys.stderr.write(self.__module__ + ': ' + msg + '\n' + 'wget output was:\n\n' + ex.stderr + '\n')
	    traceback.print_exc()
	except Exception, ex:
	    self.status = -1.0
	    msg = str(ex).strip()
	    self.error_message = msg
	    sys.stderr.write(self.__module__ + ': ' + msg + '\n')
	    traceback.print_exc()
	    return -1

    def process(self):
        raise Exception("process() not implemented for module " + self.__module__)

    # the module frame asks for the following quantities
    # status, error_message, mod_title, mod_type, weight, definition, instruction
    def PHPOutput(self,module_content):

	variable_list = filter(lambda x: (type(self.db_values[x]) is int or type(self.db_values[x]) is float) and not x in self.plot_blacklist, self.db_values)

	html_begin = []
	html_begin.append(  '<!-- Beginning of module "' + self.__module__ + '" -->')
	html_begin.append("""<a id="' . $data["module"]. '"></a>""")
	html_begin.append("""<table class="main" style="width:1000px;">""")
	html_begin.append(  ' <tr>')
	html_begin.append(  '  <td style="width:64px;">')
	html_begin.append("""   <button class="HappyButton" type="button" onfocus="this.blur()" onclick="show_hide_info(\\\'""" + self.__module__+ """_info\\\', \\\'""" + self.__module__ + """_info_link\\\');">' . $status_symbol . '</button>""")
	html_begin.append(  '  </td>')
	html_begin.append("""  <td><strong><a href="?date='.$date_string.'&amp;time='.$time_string.'&amp;t='.$category.'&amp;m=""" + self.__module__ + """" style="text-decoration:none;color:#000000;" onfocus="this.blur()">' . htmlentities($data['mod_title']) . '</a><br />' . $mod_time_message . ' <span style="color:gray;">-</span> <small><a href="javascript:show_hide_info(\\\'""" + self.__module__ + """_info\\\', \\\'""" + self.__module__ + """_info_link\\\');" class="HappyLink" onfocus="this.blur()" id=\"""" + self.__module__ + """_info_link\">Show module information</a></small></strong></td>""")
	html_begin.append(""" </tr>' . $error_message . '""")
	html_begin.append(  ' <tr>')
	html_begin.append(  '  <td>')
	html_begin.append(  '  </td>')
	html_begin.append(  '  <td>')

	infobox_begin = []
	infobox_begin.append(     '   <div id="' + self.__module__ + '_info" style="display: none;">')
	infobox_begin.append(     '    <table class="HappyDesc">')
	infobox_begin.append(     '     <tr><td style="width:20%">Module File:</td><td>' + self.__module__ + '.py</td></tr>')
	infobox_begin.append(   """     <tr><td style="width:20%">Module Type:</td><td>' . $data["mod_type"] . '</td></tr>""")
	infobox_begin.append(   """     <tr><td style="width:20%">Status Value:</td><td>' . number_format($data["status"],1). '</td></tr>""")
	infobox_begin.append(   """     <tr><td style="width:20%">Weight:</td><td>' . number_format($data["weight"],1) .'</td></tr>""")
	infobox_begin.append(   """     <tr><td style="width:20%">Definition:</td><td>' .$data["definition"]. '</td></tr>""")
	infobox_begin.append(   """     <tr><td style="width:20%">Source:</td><td>' .$data["datasource"]. '</td></tr>""")
	infobox_begin.append(   """     <tr><td style="width:20%">Instruction:</td><td>' .$data["instruction"]. '</td></tr>""")
	infobox_begin.append(     '    </table>')
	infobox_begin.append(     '    <table style="font: bold 0.7em sans-serif; background-color: #ddd; border-left: 1px #999 solid; border-right: 1px #999 solid; border-bottom: 1px #999 solid; text-align: left; width: 800px;">')
	infobox_begin.append(     '      <tr>')
	infobox_begin.append(     '       <td>')

	infobox_end = []
	infobox_end.append(     '      </td>')
	infobox_end.append(     '     </tr>')
	infobox_end.append(     '    </table>')
	infobox_end.append(     '   </div>')
	infobox_end.append(     '   <br />')

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
	        $error_message = '\n <tr><td></td><td><h4 style="color:red;">' . nl2br(htmlentities($data["error_message"])) .'</h4></td></tr>';
	    }
	    if ($server_time - $data["timestamp"] < 1800)
	    {
	        $mod_time_message = '<span style="color:#999; font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>';
	    }
	    else
	    {
	        $mod_time_message = '<span style="color:#FF6666;font: bold 0.7em sans-serif;">' . date("D, d. M Y, H:i", $data["timestamp"]) . '</span>';
	    }

	    /*** print the HTML output ***/
	    print('""" + self.PHPArrayToString(html_begin) + """');
	    print('""" + self.PHPArrayToString(infobox_begin) + """');
	    print_plot_timerange_selection('""" + self.__module__ + """', '', '', '', 0, 0, array('""" + "','".join(variable_list) + """'), 'status', time() - 48*60*60, time(), 0, 0, true);
	    print('""" + self.PHPArrayToString(infobox_end) + """');

	    ?>""" + module_content + """<?php

	    print('""" + self.PHPArrayToString(html_end) + """');
	}

	?>"""

	self.indentation = 8
        return output
