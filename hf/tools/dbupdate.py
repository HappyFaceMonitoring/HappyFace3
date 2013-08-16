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

try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse
from sqlalchemy import *
import code

load_hf_environment = False


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
    #parser.add_argument('--interactive', '-i', action='store_true', help="Asks the user before applying any changeset.")
    parser.add_argument('--dry', action='store_true', help="Just provide a summary of what will be done. Superseds any other options.")
    parser.add_argument('--new-only', action='store_true', help="Creates only new tables and does not check for changes in existing ones.")
    args = parser.parse_args()

    args.interactive = not (args.force or args.dry)

    try:
        import migrate
    except ImportError, e:
        print 'The sqlalchemy-migrate Python module was not found.\nThis is required for the dbupdate functionallity'
        traceback.print_exc()
        return
    from migrate.versioning.util import load_model
    from migrate.versioning import genmodel, schemadiff
    from migrate.changeset import schema

    # Setup minimalistic, offline HF environment
    hf.configtools.readConfigurationAndEnv()
    hf.configtools.setupLogging('acquire_logging_cfg')
    hf.module.importModuleClasses()
    hf.database.connect(implicit_execution=True)

    # calculate diff using sqlalchemy-migrate magic
    diff = schemadiff.getDiffOfModelAgainstDatabase(hf.database.metadata,
                                                    hf.database.engine)

    if args.dry:
        print "Dry run! Database will be unchanged"

    # compatibility with newer versions of sqlalchemy-migrate
    if not hasattr(diff, "tablesMissingInDatabase"):
        diff.tablesMissingInDatabase = diff.tables_missing_from_B
    if not hasattr(diff, "tablesMissingInModel"):
        diff.tablesMissingInModel = diff.tables_missing_from_A
    if not hasattr(diff, "tablesWithDiff"):
        diff.tablesWithDiff = diff.tables_different.values()
    #import pdb; pdb.set_trace()

    # create missing tables
    if len(diff.tablesMissingInDatabase) > 0:
        tables = "\033[1m" + '\033[0m, \033[1m'.join(t.name for t in diff.tablesMissingInDatabase) + '\033[0m'
        if not args.interactive:
            print "\033[1m\033[32mAdd\033[0m table(s) " + tables
        if ask(args, "\033[1m\033[32mAdd\033[0m table(s) " + tables + "?"):
            hf.database.metadata.create_all(bind=hf.database.engine, tables=diff.tablesMissingInDatabase)

    # delete residual tables
    deleted_tables = []
    if not args.new_only and len(diff.tablesMissingInModel) > 0:
        tables = "\033[1m" + '\033[0m, \033[1m'.join(t.name for t in diff.tablesMissingInModel) + '\033[0m'
        if not args.interactive:
            print "\033[1m\033[31mDrop\033[0m table(s) " + tables
        if ask(args, "\033[1m\033[31mDrop\033[0m table(s) " + tables + "?\n\033[1m\033[31mWARNING\033[0m Not reversible! Procede?"):
            hf.database.metadata.drop_all(bind=hf.database.engine, tables=diff.tablesMissingInModel)

    # apply changes in a table
    # This code was heavily influenced by the original
    # sqlalchemy migrate function:
    # migrate.versioning.genmodel.ModelGenerator.applyModel()
    # as it didn't work with sqlite foreign keys very well.
    for model_table in diff.tablesWithDiff:
        if model_table.name in deleted_tables:
            continue
        if not args.interactive: print "\033[1m\033[33malter\033[0m table \033[1m%s\033[0m" % model_table.name
        if not ask(args, "Do \033[1m\033[33malterations\033[0m in table \033[1m%s\033[0m?" % model_table.name):
            continue
        db_table = diff.reflected_model.tables[model_table.name]
        add, drop, alter = diff.colDiffs[model_table.name]
        # SQLite cannot alter/change columns
        if (len(alter) > 0 or len(drop)) \
            and diff.conn.url.drivername.startswith('sqlite'):
            # to get this working with ForeignKeys, we disable foreign keys

            changes = ''
            if len(add) > 0:
                changes += '\n * \033[1m\033[32madd\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c.name for c in add) + '\033[0m'
            if len(drop) > 0:
                changes += '\n * \033[1m\033[31mdrop\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c.name for c in drop) + '\033[0m'
            if len(alter) > 0:
                changes += '\n * \033[1m\033[33malter\033[0m column(s) \033[1m' + '\033[0m, \033[1m'.join(c[0].name for c in alter) + '\033[0m'
            if len(changes) > 0:
                changes = changes[1:]

            if args.new_only:
                for col in add:
                    if not args.interactive: print " \033[1m\033[32madd\033[0m column '%s'" % col.name
                    if not ask(args, " \033[1m\033[32madd\033[0m column '%s'?" % col.name):
                        if not args.dry: model_table.columns[col.name].create()
                continue

            message = '''\033[1m\033[31mATTENTION\033[0m
Due to SQLite language restrictions, we canonly alter the table as a whole, so you have to accept all changes or none!
%s
Do you want to apply these changes? \033[1m\033[31mWARNING\033[0m Not reversible!''' % changes
            if not args.interactive: print changes
            if not ask(args, message):
                continue

            # <COPY> All rights and hail to the SQLAlchemy Migrate project
            # Sqlite doesn't support drop column, so you have to
            # do more: create temp table, copy data to it, drop
            # old table, create new table, copy data back.
            #
            # I wonder if this is guaranteed to be unique?
            temp_name = '_temp_%s' % model_table.name

            def getCopyStatement():
                preparer = diff.conn.engine.dialect.preparer
                common_cols = []
                for model_col in model_table.columns:
                    if model_col.name in db_table.columns:
                        common_cols.append(model_col.name)
                common_cols_str = ', '.join(common_cols)
                return 'INSERT INTO %s (%s) SELECT %s FROM %s' % \
                    (model_table.name, common_cols_str, common_cols_str, temp_name)
            if not args.dry:
                # Move the data in one transaction, so that we don't
                # leave the database in a nasty state.
                connection = diff.conn.connect()
                trans = connection.begin()
                try:
                    connection.execute(
                        'CREATE TEMPORARY TABLE %s as SELECT * from %s' % \
                            (temp_name, model_table.name))

                    connection.execute('pragma foreign_keys = off;') # added by Gregor Vollmer

                    # make sure the drop takes place inside our
                    # transaction with the bind parameter
                    model_table.drop(bind=connection)
                    model_table.create(bind=connection)
                    connection.execute(getCopyStatement())
                    connection.execute('DROP TABLE %s' % temp_name)
                    connection.execute('pragma foreign_keys = on;') # added by Gregor Vollmer
                    trans.commit()
                except:
                    trans.rollback()
                    raise
            # </COPY>
        else:
            # "just do everything"
            for col in add:
                if not args.interactive: print " \033[1m\033[32madd\033[0m column '%s'" % col.name
                if ask(args, " \033[1m\033[32madd\033[0m column '%s'?" % col.name):
                    if not args.dry: model_table.columns[col.name].create()
            if not args.new_only:
                for col in drop:
                    if not args.interactive: print " \033[1m\033[31mdrop\033[0m column '%s'" % col.name
                    if ask(args, " \033[1m\033[31mdrop\033[0m column '%s'? \033[1m\033[31mWARNING\033[0m Not reversible!" % col.name):
                        if not args.dry: db_table.columns[col.name].drop()
                for model_col, database_col, model_decl, database_decl in alter:
                    if not args.interactive: print " \033[1m\033[33malter\033[0m column '%s'" % model_col.name
                    if ask(args, " \033[1m\033[33malter\033[0m column '%s'? \033[1m\033[31mWARNING\033[0m Not reversible!" % model_col.name):
                        if not args.dry: database_col.alter(model_col)

    if args.dry:
        print "Dry run completed"
    else:
        print "Database update done!"
