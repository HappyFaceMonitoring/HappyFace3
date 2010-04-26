#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import sqlite3

def cleanup_table(conn, hfdir, table_name, start, end):
	"""Remove all entries between start and end in table_name. Also cleanup
	   plots in archive directory"""

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
		columns = map(lambda x: x[0], merge_rows.description)

		for column in columns:
			if column.startswith('filename') or column == 'eff_plot' or column == 'rel_eff_plot':
				timestamp = row['timestamp']
				tm = time.localtime(timestamp)

				year = str(tm.tm_year)
				month = '%02d' % tm.tm_mon
				day = '%02d' % tm.tm_mday

				source_file = hfdir + '/archive/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column]
				try:
					os.unlink(source_file)
				except Exception as ex:
					# Ignore if file does not exist in archive directory...
					# maybe a previous run of the script removed it
					# but it was interrupted before it could clear up
					# the DB entries
					pass
			if 'database' in column and not column in subtables:
				subtables.append(column)

	rows = conn.execute("DELETE FROM %s %s ORDER BY timestamp" % (table_name, where_clause))
	for subtable in subtables:
		cleanup_table(conn, hfdir, subtable, start, end)

start = -1
end = -1
module = ''
source = ''

optlist,args = getopt.getopt(sys.argv[1:], [], ['start=', 'end=', 'module='])
options = dict(optlist)
if '--start' in options:
	start = int(options['--start'])
if '--end' in options:
	end = int(options['--end'])
if '--module' in options:
	dest = options['--module']

if len(args) < 1:
	sys.stderr.write('%s --start=timestamp --end=timestamp --module=<HappyFace module> <HappyFace Database>\n' % sys.argv[0])
	sys.exit(-1)

source = args[0]
dirname = os.path.dirname(source)

# cfg files to examine if module is not explicitely given, in increasing order of priority
cfg_files = [dirname + '/../HappyFace/run.cfg',
             dirname + '/../HappyFace/local/cfg/run.local']

categories = []
modules = {}
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
	except:
		pass

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
			print 'Process ' + module
		elif answer == 'q':
			sys.exit(0)
		elif answer == 'a':
			all = True
		elif answer == 'c':
			all_cat = True
		elif answer == 's':
			break
		elif answer == 'y':
			print 'Process ' + module
