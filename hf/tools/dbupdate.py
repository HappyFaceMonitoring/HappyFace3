# -*- coding: utf-8 -*-
#
# Copyright 2012 Institut für Experimentelle Kernphysik - Karlsruher Institut für Technologie
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
 Execute database schema updates
"""

import hf
import sys
import traceback
from string import strip

try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse
from sqlalchemy import *
import code

#load_hf_environment = False

def ask(args, message):
    if not args.interactive or args.force or args.dry:
        return True
    print message,
    while 1:
        print "[y/N] ",
        line = sys.stdin.readline()
        if line.lower()[0] == 'y':
            return True
        elif line.lower()[0] == 'n' or len(line) == 1:
            return False
    return True


def execute():
    parser = argparse.ArgumentParser(description='Update the database schema as neccessary')
    #parser.add_argument('--verbose', '-v', action='store_true', help="Provide more detailed output")
    parser.add_argument('--force', '-f', action='store_true', help="Do not ask user to perform action. Might cause data loss!")
    parser.add_argument('--interactive', '-i', action='store_true', help="Asks the user before applying any changeset.")
    parser.add_argument('--dry', action='store_true', help="Just provide a summary of what will be done. Superseds any other options.")
    parser.add_argument('--new-only', action='store_true', help="Creates only new tables and does not check for changes in existing ones.")
    args = parser.parse_args()

    args.interactive = not (args.force or args.dry)

    #try:
    #import migrate
    #except ImportError, e:
    #print 'The sqlalchemy-migrate Python module was not found.\nThis is required for the dbupdate functionallity'
    #traceback.print_exc()
    #return
    #from migrate.versioning.util import load_model
    #from migrate.versioning import genmodel, schemadiff
    #from migrate.changeset import schema
    import db_difftools

    # Setup minimalistic, offline HF environment
    hf.configtools.readConfigurationAndEnv()
    hf.configtools.setupLogging('acquire_logging_cfg')
    hf.module.importModuleClasses()
    hf.database.connect(implicit_execution=True)

    # calculate diff using sqlalchemy-migrate magic
    diff = db_difftools.DbDiff(hf.database.metadata,
                                                    hf.database.engine)
    if args.dry:
        print "Dry run! Database will be unchanged"
    tablesRemoveFromDb, tablesAddToDb, tablesAlterInDb = diff.tables_to_operate()
    #import pdb; pdb.set_trace()
    tables = ''
    if len(tablesAddToDb) > 0:
        tables = "\033[1m" + '\033[0m, \033[1m'.join(t.name for t in tablesAddToDb) + '\033[0m'
    if not args.interactive:
        print "\033[1m\033[32mAdd\033[0m table(s) " + tables
    if ask(args, "\033[1m\033[32mAdd\033[0m table(s) " + tables + "?"):
        hf.database.metadata.create_all(bind=hf.database.engine, tables=tablesAddToDb)
    deleted_tables = []
    if not args.new_only and len(tablesRemoveFromDb) > 0:
        tables = "\033[1m" + '\033[0m, \033[1m'.join(t.name for t in tablesRemoveFromDb) + '\033[0m'
        if not args.interactive:
            print "\033[1m\033[31mDrop\033[0m table(s) " + tables
        if ask(args, "\033[1m\033[31mDrop\033[0m table(s) " + tables + "?\n\033[1m\033[31mWARNING\033[0m Not reversible! Procede?"):
            deleted_tables = [t.name for t in tablesRemoveFromDb]
            hf.database.metadata.drop_all(bind=hf.database.engine, tables=tablesRemoveFromDb)

    for table_name, [db_table, table_diff] in tablesAlterInDb.iteritems():
        if table_name in deleted_tables:
            continue
        if not args.interactive:
            print "\033[1m\033[33malter\033[0m table \033[1m%s\033[0m" % table_name
        if not ask(args, "Do \033[1m\033[33malterations\033[0m in table \033[1m%s\033[0m?" % table_name):
            continue
        drop, add, alter = table_diff.columns_to_operate()
        #import pdb; pdb.set_trace()
        '''Due to many incompatibilities regarding all possible sql backends
        add drop and alter is reduced to the drop function, which is accessible 
        in all backends. therefor add and alter will result in constructing a new table with
        additional and altered columns.'''
        changes = ''
        drops = ''
        temp_name = '__temp_%s' % table_name
        copy_list = [c.name for c in db_table.columns]
        alter_list = [c[0].name for c in alter]
        if len(add) > 0:
            changes += '\n * \033[1m\033[32madd\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c.name for c in add) + '\033[0m'
        if len(drop) > 0:
            drops += '\n * \033[1m\033[31mdrop\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c.name for c in drop) + '\033[0m'
            drop_list = [c.name for c in drop]
        if len(alter) > 0:
            changes += '\n * \033[1m\033[33malter\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c[0].name for c in alter) + '\033[0m'
        if len(changes) > 0:
            changes = changes[1:]

        message = 'Do you really want to drop those columns?\n'
        print drops
        if len(drop) > 0 and not args.interactive:
            print drops
        if len(drop) > 0 and ask(args, message):
            copy_list = set(copy_list) - set(drop_list)

        message = '''\033[1m\033[31mATTENTION\033[0m
Due to SQL-Backend restrictions, we can only alter the table as a whole, so you have to accept all changes or none!
%s
Do you want to apply these changes? \033[1m\033[31mWARNING\033[0m Not reversible!''' % changes
        if not args.interactive:
            print changes
        if not ask(args, message):
            continue

        new_db_columns = []
        for col_name in copy_list:
            #import pdb; pdb.set_trace()
            if col_name in alter_list:
                c_type = map(strip, alter[col_name].strip().split('=>'))[1]
                c_null = db_table.columns[col_name].nullable
                c_key = db_table.columns[col_name].primary_key
                new_db_columns.append(Column(col_name, c_type, nullable=c_null, primary_key=c_key))
            else:
                c_type = db_table.columns[col_name].type
                c_null = db_table.columns[col_name].nullable
                c_key = db_table.columns[col_name].primary_key
                new_db_columns.append(Column(col_name, c_type, nullable=c_null, primary_key=c_key))

        copy_string = ', '.join(copy_list)
        connection = diff.conn.connect()
        trans = connection.begin()
        try:
            connection.execute('CREATE TEMPORARY TABLE %s as SELECT %s from %s' % (temp_name, copy_string, table_name))
            #connection.execute('pragma foreign_keys = off;')
            hf.database.metadata.drop_all(bind=hf.database.engine, tables=[db_table])
            #import pdb; pdb.set_trace()
            db_table = Table(table_name, hf.database.metadata, *new_db_columns, extend_existing=True)
            hf.database.metadata.create_all(bind=hf.database.engine, tables=[db_table])
            connection.execute('INSERT INTO %s (%s) SELECT %s FROM %s' % (table_name, copy_string, copy_string, temp_name))
            connection.execute('DROP TABLE %s' % temp_name)
            #connection.execute('pragma foreign_keys = on;')
            trans.commit()
        except:
            trans.rollback()
            raise

        
        

    if args.dry:
        print "Dry run completed"
    else:
        print "Database update done!"
