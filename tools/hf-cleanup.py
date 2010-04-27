#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import sqlite3

def cleanup_table(conn, hfdir, table_name, start, end, drop):
	"""Remove all entries between start and end in table_name. Also cleanup
	   plots in archive directory"""

	print 'Cleaning ' + table_name + '...'

	# Construct WHERE clause to query the data in the specified range
	start_cond = ''
	end_cond = ''
	if start >= 0:
		start_cond = 'timestamp>=%d' % start
	if end >= 0:
		end_cond = 'timestamp<=%d' % end

	where_clause = ''
	if start_cond and end_cond:
		where_clause = 'WHERE %s AND %s' % (start_cond, end_cond)
	elif start_cond:
		where_clause = 'WHERE %s' % start_cond
	elif end_cond:
		where_clause = 'WHERE %s' % end_cond

	rows = conn.execute("SELECT * FROM %s %s ORDER BY timestamp" % (table_name, where_clause))

	# Remember all subtables so we can also clear them in the end
	subtables = []
	for row in rows:

		# Get column names and values except ID
		columns = map(lambda x: x[0], rows.description)

		for column in columns:
			if column.startswith('filename') or column == 'eff_plot' or column == 'rel_eff_plot':
				timestamp = row['timestamp']
				tm = time.localtime(timestamp)

				year = str(tm.tm_year)
				month = '%02d' % tm.tm_mon
				day = '%02d' % tm.tm_mday

				if row[column] is not None:
					source_file = hfdir + '/archive/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column]
					try:
						os.unlink(source_file)
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
		result = conn.execute("DELETE FROM %s %s" % (table_name, where_clause))
	else:
		result = conn.execute("DROP TABLE %s" % (table_name))
	conn.commit()

	for subtable in subtables:
		cleanup_table(conn, hfdir, subtable, start, end)

start = -1
end = -1
modules = ''
source = ''

optlist,args = getopt.getopt(sys.argv[1:], [], ['start=', 'end=', 'modules='])
options = dict(optlist)
if '--start' in options:
	start = int(options['--start'])
if '--end' in options:
	end = int(options['--end'])
if '--modules' in options:
	modules = options['--modules']

if len(args) != 1:
	sys.stderr.write('%s [--start=timestamp] [--end=timestamp] [--modules=module1,module2,...] <HappyFace Database>\n' % sys.argv[0])
	sys.exit(-1)

allowed_modules = []
if modules != '':
	allowed_modules = modules.split(',')

source = args[0]
dirname = os.path.dirname(source)
conn = sqlite3.connect(source)
conn.row_factory = sqlite3.Row

# cfg files to examine if module is not explicitely given, in increasing order of priority
cfg_files = [dirname + '/../HappyFace/run.cfg',
             dirname + '/../HappyFace/local/cfg/run.local']

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

# TODO: "?" answer
answers = ['a','q','c','s','y','n']
all = False
for category in categories:
	print 'Category "' + category + '":'
	all_cat = False
	for module in modules[category]:
		answer = None
		while (not all and not all_cat) and not answer in answers:
			sys.stdout.write('\tClean up module "' + module + '"? [' + ''.join(answers) + '] ')
			answer = sys.stdin.readline()
			if answer == '': answer = 'q'
			if answer[-1] == '\n': answer = answer[:-1]

		if all or all_cat:
			cleanup_table(conn, dirname, module + '_table', start, end, False)
		elif answer == 'q':
			# TODO: Break out of both loops so we do the unused tables check below
			sys.exit(0)
		elif answer == 'a':
			all = True
			cleanup_table(conn, dirname, module + '_table', start, end, False)
		elif answer == 'c':
			all_cat = True
			cleanup_table(conn, dirname, module + '_table', start, end, False)
		elif answer == 's':
			break
		elif answer == 'y':
			cleanup_table(conn, dirname, module + '_table', start, end, False)

# Check for tables not associated with a module
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
rows = cursor.fetchall() # Fetch all to avoid a lock on the table

answers = ['a','q','y','n'] # TODO: Add "?" answer

all = False
print 'Tables no longer referenced in configuration:'
for row in rows:
	table = row['name']

	has_module = True
	for module in module_list:
		if table.startswith(module + '_'):
			has_module = False
			break

	if has_module:
		answer = None
		while not all and not answer in answers:
			sys.stdout.write('\tDrop table "' + table + '"? [' + ''.join(answers) + '] ')
			answer = sys.stdin.readline()
			if answer == '': answer = 'q'
			if answer[-1] == '\n': answer = answer[:-1]

		if all:
			cleanup_table(conn, dirname, table, -1, -1, True)
		elif answer == 'q':
			break
		elif answer == 'a':
			all = True
			cleanup_table(conn, dirname, table, -1, -1, True)
		elif answer == 'y':
			cleanup_table(conn, dirname, table, -1, -1, True)
