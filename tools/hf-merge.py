#!/usr/bin/env python

import os
import sys
import time
import getopt
import shutil
from sqlobject import *

def help():
    print(
    '''hf-merge [options] --into-wrapper=<Path/To/Module.Class> --from-wrapper=<Path/To/Module.Class> --into=<Connect String> <Source Connect String>

    This tool merges one HappyFace instance into another. This can be useful if
    you shut your main instance down for maintenance and run a secondary instance
    during that time. Using this script you can merge the data of the secondary
    instance into the main instance so that you can remove the secondary instance
    afterwards without losing data.

    The connection string has the format:
        scheme://[user[:password]@]host[:port]/database[?parameters]

    Source and more info: http://sqlobject.org/SQLObject.html#declaring-a-connection

    The following options are possible:

    --into=FILE        Database file of the HappyFace instance to merge into
    --start=TIMESTAMP    if given only merge database entries recorded after TIMESTAMP
    --end=TIMESTAMP        if given only merge database entries recorded before TIMESTAMP
    --into-wrapper=<Path/To/Module.Class>   class to use as a wrapper for the input database
    --from-wrapper=<Path/To/Module.Class>   class to use as a wrapper for the output database
    --into-archive=<Path/To/Archive>        destination archive directory
    --from-archive=<Path/To/Archive>        source archive directory
    --no-archive                            does not copy archive, usefull for db-migration

    If --start and/or --end are given then only database entries in the specified
    timerange are merged. If you want to merge the complete database then you do
    not need to specify them. Entries which are already contained in the
    destination database already will not be overwritten. Note that the --into
    option and at least one of --into-wrapper or --from-wrapper is required. If only
    one wrapper is specified, it is used for both databases.
    ''')
    sys.exit(0)

start = -1
end = -1
dest = ''
source = ''
IntoWrapper = None
FromWrapper = None
dest_dirname = None
source_dirname = None
do_not_cpy_archive = False

optlist,args = getopt.getopt(sys.argv[1:], 'h', ['start=', 'end=', 'into-wrapper=', 'from-wrapper=', 'into=', 'from-archive=', 'into-archive=', 'no-archive', 'help'])
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

if '--into-archive' in options:
    dest_dirname = options['--into-archive']
if '--from-archive' in options:
    source_dirname = options['--from-archive']

if '--no-archive' in options:
    do_not_cpy_archive = True
else:
    if dest_dirname is None:
        sys.stderr.write('No destination archive specified. Use --no-archive or specify! Try --help for more information."\n')
        sys.exit(-1)
    if source_dirname is None:
        sys.stderr.write('No source archive specified. Use --no-archive or specify! Try --help for more information."\n')
        sys.exit(-1)

if '--into-wrapper' in options:
    path, modwrapper = os.path.split(options['--into-wrapper'])
    modname, wrapper = os.path.splitext(modwrapper)
    wrapper = wrapper[1:] # remove leading dot
    sys.path.append(path)
    wrapperModule = __import__(modname)
    IntoWrapper = wrapperModule.__dict__[wrapper]
if '--from-wrapper' in options:
    path, modwrapper = os.path.split(options['--from-wrapper'])
    modname, wrapper = os.path.splitext(modwrapper)
    wrapper = wrapper[1:] # remove leading dot
    sys.path.append(path)
    wrapperModule = __import__(modname)
    FromWrapper = wrapperModule.__dict__[wrapper]

if IntoWrapper is None: IntoWrapper = FromWrapper
if FromWrapper is None: FromWrapper = IntoWrapper

if IntoWrapper is None and FromWrapper is None:
    sys.stderr.write('No database wrapper specified. Try --help for more information."\n')
    sys.exit(-1)

if len(args) < 1:
    sys.stderr.write('%s --start=timestamp --end=timestamp --into=<HappyFace Destination Database> <HappyFace Source Database>\n' % sys.argv[0])
    sys.exit(-1)
source = args[0]

source_conn = FromWrapper.connectionForURI(source, '')
dest_conn = IntoWrapper.connectionForURI(dest, '')
dest_conn.autoCommit = False
trans = dest_conn.transaction()
source_wrapper = FromWrapper(source_conn)
dest_wrapper = IntoWrapper(trans)

source_cursor = source_conn.getConnection().cursor()
dest_cursor = dest_conn.getConnection().cursor()

dest_tables = dest_wrapper.listOfTables()
source_tables = source_wrapper.listOfTables()

#print source_tables
#print dest_tables

copied_files = []
n_source_tables = len(source_tables)
index = 0
for table_name in source_tables:
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
    counted_rows = source_cursor.execute("SELECT count(timestamp) FROM %s %s ORDER BY timestamp" % (table_name, where_clause))
    counted_rows = [r[0] for r in counted_rows][0]
    merge_rows = source_cursor.execute("SELECT * FROM %s %s ORDER BY timestamp" % (table_name, where_clause))
    
    
    # Get column names and values and 'unescape' colnames
    columns = map(lambda x: x[0][1:] if x[0][0] == '_' else x[0], merge_rows.description)
    columns = filter(lambda x: x != 'id', columns)
    # col name escaping (see wrapper docs)
    #columns = map(lambda x: '_'+x if x in dest_wrapper.reserved_names else x, columns)

    try:
        # Create table in destination if not present
#        if not table_name in dest_tables:
        meta = type(table_name+"_meta", (), dict(table=table_name, fromDatabase = True))
        SrcTable = type(table_name+"_mainproxy", (SQLObject,), dict(_connection=source_conn, sqlmeta=meta))
        
        table_keys = {}
        for col, col_obj in SrcTable.sqlmeta.columns.iteritems():
            col = styles.mixedToUnder(col)
            if col_obj.__class__.__name__ == "SOCol":
                print "\n\tColumn %s not properly recognized! Use string" % col
                table_keys[col] = StringCol()
            elif col != "datasource":
                table_keys[col] = globals()[col_obj.__class__.__name__[2:]]()
            else:
                table_keys[col] = StringCol() # for some reason never recognized as StringCol (only Col?!)
        
        trans.commit()
        DstTable = dest_wrapper.table_init(table_name, table_keys)
        trans.commit()
        copied_files = []
        dest_tables.append(table_name)
    except Exception,e:
        print "Cannot create table '%s': %s" % (table_name, str(e))
        continue
    
    
    n_rows = 0
    n_total_rows = 0
    create_table = ''
    timestamps = {}
    missing_files = {}
    commit_block_size = 5000
    try:
        for row in merge_rows:
            n_total_rows += 1
            if n_total_rows % 200 == 0:
                print '\r%d/%d %s... %.1f%%, copied rows %i' % (index, n_source_tables, table_name, n_total_rows*100.0 / counted_rows, n_rows),
            try:
                trans.begin()
            except AssertionError:
                pass

            # decorate result with column names
            row = dict((col,row[i+1]) for i,col in enumerate(columns))
            
            values = []
            for value in row.itervalues():
                values.append(value)
            values = values[1:]
                
            if not row['timestamp'] in timestamps:
                # Check whether there is already a
                # corresponding dataset in destination.
                # WARNING: Direct insertion of the timestamp is only
                # used because it is safe in this place and the simplest hack
                dest_row = trans.queryOne("SELECT * FROM %s WHERE timestamp=%i" % (table_name, int(row['timestamp'])))
                timestamps[row['timestamp']] = (dest_row != None)
           
            # Ignore this entry if dataset is present in destination
            if timestamps[row['timestamp']]:
                continue

            # Copy archive files
            columns_archive = filter(lambda x: x.startswith('filename') or x == 'eff_plot' or x == 'rel_eff_plot', columns)
            if do_not_cpy_archive:
                columns_archive = [] # no iterations in following loop

            for column in columns_archive:
                # If this column was newly added then the source
                # database may not contain an entry for it, so
                # skip it in this case.
                if row[column] is None: continue

                timestamp = row['timestamp']
                tm = time.localtime(timestamp)

                year = str(tm.tm_year)
                month = '%02d' % tm.tm_mon
                day = '%02d' % tm.tm_mday

                source_file = os.path.join(source_dirname, str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column])
                dest_file = os.path.join(dest_dirname, str(year) + '/' + str(month) + '/' + str(day) + '/' + str(timestamp) + '/' + row[column])

                try:
                    if not os.path.exists(dest_file):
                        if not os.path.exists(os.path.dirname(dest_file)):
                            os.makedirs(os.path.dirname(dest_file))
                        shutil.copy2(source_file, dest_file)
                        copied_files.append(dest_file)
                except Exception, ex:
                    if not os.path.isfile(dest_file):
                        if timestamp in missing_files:
                            missing_files[timestamp] += 1
                        else:
                            missing_files[timestamp] = 1
                    else:
                        sys.stderr.write('Failed to copy "%s" to "%s": %s\n' % (source_file, dest_file, str(ex)))
                        sys.stderr.write('Rerun the script after fixing the error. Already merged entries will not be merged again.\n')
                        raise ex
                
            n_rows+=1
            
            # Copy database entry
            dest_wrapper.table_fill(DstTable, row)
            
            if n_rows%commit_block_size == 0:
                trans.commit()
                copied_files = []
               
        trans.commit()
        copied_files = []
    except:
        # On error roll back all entries from this dataset so that
        # there are no partly merged datasets in destination.
        print "EXCEPTION! Rollback and delete %i unref. archive files" % len(copied_files)
        trans.rollback()
        trans.begin()
        for f in copied_files:
            os.remove(f)
        raise
    print '\r%d/%d %s... ' % (index, n_source_tables, table_name),
    if n_total_rows > 0:
        sys.stdout.write('merged %d/%d rows%s\n' % (n_rows, n_total_rows, create_table))
    else:
        sys.stdout.write('No entries in specified time range\n')
print missing_files
trans.commit(close=True)
