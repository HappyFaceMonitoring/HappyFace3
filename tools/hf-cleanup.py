#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import re
import itertools
from sqlobject import *
import ConfigParser

def help():
	print(
'''hf-cleanup [options] <HappyFace directory>

This script performs three steps to clean up the HappyFace database:
1) It removes old entries of existing modules
2) It removes any remaining data belonging to modules no longer in use
3) It optimizes the database file (SQLite only, using VACUUM command)

Possible options are:

--start=TIMESTAMP	if given only erase database entries recorded after TIMESTAMP
--end=TIMESTAMP		if given only erase database entries recorded before TIMESTAMP
--modules=MODULES	specifies a comma-separated list of modules to clean up
--force                 cleanup tables that are not correctly referenced

All three options only affect the first of the three steps explained above.
If TIMESTAMP for --start or --end is lower then it is interpreted as the
number of days since the time of executing the script. If either --start or
--end are not given then they are taken as 0 or the current time, respectively.
If --modules is not given then all modules are cleaned up. However, for each
module and for each of the three steps there will be a confirmation prompt to
explicitely confirm deletion of data.

WARNING: This means that if you run hf-cleanup without --start and without
--end then it will erase the entire database for selected modules (if
confirmed at the prompt).

Examples:

./hf-cleanup 
Erases the complete HappyFace database.

./hf-cleanup --modules=qstat ../HappyFace
Erases all entries for the qstat module from the HappyFace database.

./hf-cleanup --end=100 ../HappyFace
Removes all entries from the HappyFace database that are older than 100 days.

./hf-cleanup --end=1279626292 ../HappyFace
Removes all entries from the HappyFace database from before
Tue Jul 20 13:45 CEST 2010.

./hf-cleanup --modules=none ../HappyFace
Skips the first of the three steps (this could also be achieved by answering q
at the first prompt).''')

	sys.exit(0)

def cleanup_table(conn, hfdir, table_name, start, end, drop, recurse_subtables):
	"""Remove all entries between start and end in table_name. Also cleanup
	   plots in archive directory"""

	print 'Cleaning ' + table_name + '...'
	
        # remeber that we cleaned this table globally
        #global cleaned_table_list
        visited_table_list.append(table_name)

        # Construct WHERE clause to query the data in the specified range
        table = sqlbuilder.table.__getattr__(table_name)
        where_clause = sqlbuilder.SQLTrueClauseClass()
        if start >= 0:
            where_clause = where_clause & (table.timestamp >= start)
        if end >= 0:
            where_clause = where_clause & (table.timestamp <= end)
        
	cursor = conn.cursor()
	
	class sqlmeta:
		table = table_name
		fromDatabase = True

	DBProxy = type(table_name + "_DBProxy",(SQLObject,),dict(sqlmeta = sqlmeta))
	columns = [k.dbName for k in DBProxy.sqlmeta.columnList if k!='index']
        
        select_query = sqlbuilder.Select([table.__getattr__(col) for col in columns], where=where_clause)
        rows = sqlhub.processConnection.queryAll(sqlhub.processConnection.sqlrepr(select_query))
	
	# Remember all subtables so we can also clear them in the end
	subtables = []
	for row in rows:
		row = dict( itertools.izip(columns, row) )
		for column in columns:
			if column.startswith('filename') or column == 'eff_plot' or column == 'rel_eff_plot':
				timestamp = row['timestamp']
				tm = time.localtime(timestamp)

				year = str(tm.tm_year)
				month = '%02d' % tm.tm_mon
				day = '%02d' % tm.tm_mday

				if row[column] is not None:
					output_dir = hfdir + '/archive'
					archive_dir = output_dir + '/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp)
					source_file = archive_dir + '/' + row[column]
					try:
						os.unlink(source_file)
						dir = archive_dir
						while dir != output_dir:
							os.rmdir(dir)
							dir = os.path.dirname(dir)
					except Exception as ex:
						# Ignore if file does not exist in archive directory...
						# maybe a previous run of the script removed it
						# but it was interrupted before it could clear up
						# the DB entries
						pass
			if 'database' in column and not row[column] in subtables:
				if row[column] is not None and row[column] != '':
					subtables.append(row[column])

	if not drop:
		result = cursor.execute("DELETE FROM %s WHERE %s" % (table_name, where_clause))
	else:
		result = cursor.execute("DROP TABLE %s" % (table_name))
	conn.commit()

	if recurse_subtables:
	    for subtable in subtables:
		cleanup_table(conn, hfdir, subtable, start, end, drop, recurse_subtables)
		

start = -1
end = -1
modules = ''
source = ''
force_cleanup = False

optlist,args = getopt.getopt(sys.argv[1:], 'h', ['start=', 'end=', 'modules=', 'help', 'force'])
options = dict(optlist)
if '-h' in options or '--help' in options:
	help()
if '--start' in options:
	start = int(options['--start'])

	# If start or end are very low we interpret them as number of days
	# from today, not as a timestamp
	if start < 1000000:
		start = time.time() - start*60*60*24
if '--end' in options:
	end = int(options['--end'])

	# If start or end are very low we interpret them as number of days
	# from today, not as a timestamp
	if end < 1000000:
		end = time.time() - end*60*60*24
if '--modules' in options:
	modules = options['--modules']

if '--force' in options:
    force_cleanup = True

if len(args) != 1:
	sys.stderr.write('%s [--start=timestamp or number of days from today] [--end=timestamp or number of days from today] [--modules=module1,module2,...] <HappyFace Database>\n' % sys.argv[0])
	sys.exit(-1)

allowed_modules = []
if modules != '':
	allowed_modules = modules.split(',')

source = args[0]
dirname = source

sys.path.insert(0, os.path.join(os.getcwd(), dirname))
sys.path.insert(0, os.path.join(os.getcwd(), dirname, "happycore"))

# cfg files to examine if module is not explicitely given, in increasing order of priority
cfg_files = [os.path.join(dirname, 'run.cfg'),
             os.path.join(dirname, 'local/cfg/run.local')]

config = ConfigParser.ConfigParser()
for file in cfg_files:
	try: config.readfp(open(file))
	except IOError:
		print "Cannot read cfg file %s" % file

# try to initiate / create the database
connection_string = config.get('setup', 'db_connection')
# fetch special directory path
result = re.match(r'(\w+://)\./(.+)', connection_string)
if result is not None:
    connection_string = result.group(1) + os.path.join(os.getcwd(), config.get("setup", "output_dir"), result.group(2))
sqlhub.processConnection = connectionForURI(connection_string)
conn = sqlhub.processConnection.getConnection()
cursor = conn.cursor()

# get database wrapper
dbWrapperModule = __import__(config.get('setup', 'db_wrapper_module'))
dbWrapper = dbWrapperModule.__dict__[config.get('setup', 'db_wrapper_class')]()

categories = []
modules = {}
module_list = []
for file in cfg_files:
	try:
		section = None
		for line in open(file):
			# For some reason the trailing newline character is
			# not stripped away with strip()
			if line[-1] == "\n":
				line = line[:-1]
			line.strip()

			if line == '' or line.startswith('#'):
				continue
			elif line.startswith('['):
				section = line[1:-1].strip()
			elif section is not None:
				key,value = map(lambda x: x.strip(), line.split('=', 1))
				if section == 'setup' and key == 'categories':
					categories = map(lambda x: x.strip(), value.split(','))
				elif key == 'modules':
					modules[section] = map(lambda x: x.strip(), value.split(','))
					module_list.extend(modules[section])

					# Restrict module map to allowed modules
					if len(allowed_modules) > 0:
						modules[section] = filter(lambda x: x in allowed_modules, modules[section])
	except:
		pass

# we will remember all tables that were cleared here
visited_table_list = []

# TODO: Avoid code duplication below
answers = ['a','q','c','s','y','n', '?']
all = False
none = False
for category in categories:
	print 'Category "' + category + '":'
	all_cat = False
	for module in modules[category]:
		answer = None
		while (not all and not all_cat) and not answer in answers:
			sys.stdout.write('\tClean up module "' + module + '"? [' + ''.join(answers) + '] ')
			answer = sys.stdin.readline()
			if answer == '': answer = '?'
			if answer[-1] == '\n': answer = answer[:-1]

			if answer == '?':
			    print 'a: Clean up all modules'
			    print 'q: Do not clean up any module'
			    print 'c: Clean up all modules in this category'
			    print 's: Skip all modules in this category'
			    print 'y: Clean up this module'
			    print 'n: Do not clean up this module'
			    answer = None
                
                if none:
                    visited_table_list.append(module + '_table')
                    break
                
		if all or all_cat:
			cleanup_table(conn, dirname, module + '_table', start, end, False, True)
		elif answer == 'q':
			none = True
			visited_table_list.append(module + '_table')
			break
		elif answer == 'a':
			all = True
			cleanup_table(conn, dirname, module + '_table', start, end, False, True)
		elif answer == 'c':
			all_cat = True
			cleanup_table(conn, dirname, module + '_table', start, end, False, True)
		elif answer == 's':
			break
		elif answer == 'y':
			cleanup_table(conn, dirname, module + '_table', start, end, False, True)
                else:
                    visited_table_list.append(module + '_table')
	if(none): break

# Check for tables not associated with a module
table_list = dbWrapper.listOfTables()
answers = ['a','q','y','n', '?']

all = False
n_rows = 0
print 'Tables no longer referenced in configuration:'
for table in table_list:

	has_module = True
	for module in module_list:
		if table.startswith(module + '_'):
			has_module = False
			break

	if has_module:
		n_rows += 1
		answer = None
		while not all and not answer in answers:
			sys.stdout.write('\tDrop table "' + table + '"? [' + ''.join(answers) + '] ')
			answer = sys.stdin.readline()
			if answer == '': answer = '?'
			if answer[-1] == '\n': answer = answer[:-1]

			if answer == '?':
			    print 'a: Drop all unreferenced tables'
			    print 'q: Do not drop any unreferenced table'
			    print 'y: Drop this table'
			    print 'n: Do not drop this table'
			    answer = None

		if all:
			cleanup_table(conn, dirname, table, -1, -1, True, False)
		elif answer == 'q':
			break
		elif answer == 'a':
			all = True
			cleanup_table(conn, dirname, table, -1, -1, True, False)
		elif answer == 'y':
			cleanup_table(conn, dirname, table, -1, -1, True, False)

if n_rows == 0:
	print '\tNone'


# are there still unvisited tables left in the database?
unvisited_table_list = [tbl for tbl in table_list if tbl not in visited_table_list]
if len(unvisited_table_list) > 0 and not force_cleanup:
    print """WARNING: The following %i tables exist in the database
and follow *not* the module paradigm for subtables!
Please contact the responsible module developer.""" % len(unvisited_table_list)
    for tbl in unvisited_table_list:
        print "\t- " + tbl
    print "\nHint: Use the --force argument to cleanup these tables, too"
elif len(unvisited_table_list) > 0 and force_cleanup:
    print "There are %i not correctly referenced tables, cleaning up now" % len(unvisited_table_list)
    all = False
    for table in unvisited_table_list:
        answer = None
        while (not all) and not answer in answers:
            sys.stdout.write('\tClean up table "' + table + '"? [' + ''.join(answers) + '] ')
            answer = sys.stdin.readline()
            if answer == '': answer = '?'
            if answer[-1] == '\n': answer = answer[:-1]

            if answer == '?':
                print 'a: Clean up all unreferenced tables'
                print 'q: Do not clean up any unreferenced table'
                print 'y: Clean up this unreferenced table'
                print 'n: Do not clean up this unreferenced table'
                answer = None

        if all or all_cat:
                cleanup_table(conn, dirname, table, start, end, False, False)
        elif answer == 'q':
                break
        elif answer == 'a':
                all = True
                cleanup_table(conn, dirname, table, start, end, False, False)
        elif answer == 'y':
                cleanup_table(conn, dirname, table, start, end, False, False)
    
# Only ask for VACUUM with SQLite
if config.get("setup", "db_connection").find("sqlite") != -1:
    answers = ['y','n', '?']
    answer = None
    while answer not in answers:
            sys.stdout.write('VACUUM? [' + ''.join(answers) + '] ')
            answer = sys.stdin.readline()
            if answer == '': answer = '?'
            if answer[-1] == '\n': answer = answer[:-1]

            if answer == '?':
                print 'y: Run the SQLite VACUUM command to free disk space'
                print 'n: Do not run the VACUUM command'
                answer = None

    if answer == 'y':
            cursor = conn.cursor()
            cursor.execute('VACUUM')
