#!/usr/bin/python

import os
import sys
import time
import getopt
import shutil
import sqlite3

def help():
	print(
'''hf-merge [options] --into=<Destination Database File> <Source HappyFace Database File>

This tool merges one HappyFace instance into another. This can be useful if
you shut your main instance down for maintenance and run a secondary instance
during that time. Using this script you can merge the data of the secondary
instance into the main instance so that you can remove the secondary instance
afterwards without losing data.

The following options are possible:

--into=FILE		Database file of the HappyFace instance to merge into
--start=TIMESTAMP	if given only merge database entries recorded after TIMESTAMP
--end=TIMESTAMP		if given only merge database entries recorded before TIMESTAMP

If --start and/or --end are given then only database entries in the specified
timerange are merged. If you want to merge the complete database then you do
not need to specify them. Entries which are already contained in the
destination database already will not be overwritten. Note that the --into
option is required.
''')
	sys.exit(0)

start = -1
end = -1
dest = ''
source = ''

optlist,args = getopt.getopt(sys.argv[1:], 'h', ['start=', 'end=', 'into=', 'help'])
options = dict(optlist)
if '-h' in options or '--help' in options:
	help()
if '--start' in options:
	start = int(options['--start'])
if '--end' in options:
	end = int(options['--end'])
if '--into' in options:
	dest = options['--into']
else:
	sys.stderr.write('No merge destination given. Use --into="<HappyFace.db>"\n')
	sys.exit(-1)

if len(args) < 1:
	sys.stderr.write('%s --start=timestamp --end=timestamp --into=<HappyFace Destination Database> <HappyFace Source Database>\n' % sys.argv[0])
	sys.exit(-1)
source = args[0]

source_dirname = os.path.dirname(source)
source_basename = os.path.basename(source)
dest_dirname = os.path.dirname(dest)
dest_basename = os.path.basename(dest)
if not source_dirname:
	source_dirname = '.'
if not dest_dirname:
	dest_dirname = '.'

source_conn = sqlite3.connect(source_dirname + '/' + source_basename)
source_conn.row_factory = sqlite3.Row
dest_conn = sqlite3.connect(dest_dirname + '/' + dest_basename)
dest_conn.row_factory = sqlite3.Row

dest_tables = dest_conn.execute('SELECT name FROM sqlite_master WHERE type="table"')
source_tables = source_conn.execute('SELECT name,sql FROM sqlite_master WHERE type="table"')
dest_table_names = map(lambda x: x['name'], dest_tables)
source_tables = source_tables.fetchall()
n_source_tables = len(source_tables)
index = 0
for table in source_tables:
	table_name = table['name']

	index+=1
	sys.stdout.write('%d/%d %s... ' % (index, n_source_tables, table_name))
	sys.stdout.flush()

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

	# Order by timestamp so that all entries belonging to a single module
	# dataset are written in a single transaction. When talking about a
	# dataset we refer to all database rows with same timestamp.
	merge_rows = source_conn.execute("SELECT * FROM %s %s ORDER BY timestamp" % (table_name, where_clause))

	n_rows = 0
	n_total_rows = 0
	create_table = ''
	timestamps = {}
	try:
		for row in merge_rows:
			n_total_rows += 1

			# Get column names and values except ID
			columns = map(lambda x: x[0], merge_rows.description)
			columns = filter(lambda x: x != 'id', columns)

			values = []
			for value in row:
				values.append(value)
			values = values[1:]

			# Create table in destination if not present
			if not table_name in dest_table_names:
				create_table = ' CREATE TABLE'
				dest_conn.execute(table['sql'])
				dest_conn.execute('CREATE INDEX %s_index ON %s (timestamp)' % (table_name, table_name))
				dest_table_names.append(table_name)

			if not row['timestamp'] in timestamps:
				# Commit dataset for previous timestamp
				dest_conn.commit()

				# Check whether there is already a
				# corresponding dataset in destination.
				dest_row_cursor = dest_conn.execute("SELECT * FROM %s WHERE timestamp=?" % table_name, [row['timestamp']])
				dest_row = dest_row_cursor.fetchone()
				timestamps[row['timestamp']] = (dest_row != None)

			# Ignore this entry if dataset is present in destination
			if timestamps[row['timestamp']]:
				continue

			column_names = ','.join(columns)
			column_values = ','.join(['?']*len(columns))

			# Copy archive files
			columns = filter(lambda x: x.startswith('filename') or x == 'eff_plot' or x == 'rel_eff_plot', columns)
			for column in columns:
				timestamp = row['timestamp']
				tm = time.localtime(timestamp)

				year = str(tm.tm_year)
				month = '%02d' % tm.tm_mon
				day = '%02d' % tm.tm_mday

				source_file = source_dirname + '/archive/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column]
				dest_file = dest_dirname + '/archive/' + str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column]

				try:
					if not os.path.exists(dest_file):
						if not os.path.exists(os.path.dirname(dest_file)):
							os.makedirs(os.path.dirname(dest_file))
						shutil.copy2(source_file, dest_file)
				except Exception, ex:
					sys.stderr.write('Failed to copy "%s" to "%s": %s\n' % (source_file, dest_file, str(ex)))
					sys.stderr.write('Rerun the script after fixing the error. Already merged entries will not be merged again.\n')
					sys.exit(-1)
			n_rows+=1

			# Copy database entry
			dest_conn.execute("INSERT INTO %s (%s) VALUES (%s)" % (table_name, column_names, column_values), values)

		dest_conn.commit()
	except:
		# On error roll back all entries from this dataset so that
		# there are no partly merged datasets in destination.
		dest_conn.rollback()
		raise

	if n_total_rows > 0:
		sys.stdout.write('merged %d/%d rows%s\n' % (n_rows, n_total_rows, create_table))
	else:
		sys.stdout.write('No entries in specified time range\n')
