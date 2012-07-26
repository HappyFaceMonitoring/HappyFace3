"""
 Execute database schema updates
"""

import hf, sys
try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse
from sqlalchemy import *
import code

load_hf_environment = False

def ask(args, message):
    if not args.interactive or args.dry:
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
    parser.add_argument('--verbose', '-v', action='store_true', help="Provide more detailed output")
    parser.add_argument('--force', '-f', action='store_true', help="Do not ask user to perform action. Might cause data loss!")
    parser.add_argument('--interactive', '-i', action='store_true', help="Asks the user before applying any changeset.")
    parser.add_argument('--dry', action='store_true', help="Just provide a summary of what will be done. Superseds any other options.")
    parser.add_argument('--new-only', action='store_true', help="Creates only new tables and does not check for changes in existing ones.")
    args = parser.parse_args()
    
    try:
        from migrate.versioning.util import load_model
        from migrate.versioning import genmodel, schemadiff
    except ImportError, e:
        print 'The sqlalchemy-migrate Python module was not found.\nThis is required for the dbupdate functionallity'
        return
    
    # Setup minimalistic, offline HF environment
    hf.configtools.readConfigurationAndEnv()
    hf.configtools.setupLogging('acquire_logging_cfg')
    hf.configtools.importModules()
    hf.database.connect(implicit_execution=False)
    
    # explicitally create tables, it would be done on next acquire, anyway
    if not args.dry and ask(args, "Create non-existing tables, if any?"):
        if args.verbose: print "Creating non-existing tables, if any"
        hf.database.metadata.create_all(hf.database.engine)
    
    if args.new_only:
        # We're already done!
        return

    # calculate diff using sqlalchemy-migrate magic
    diff = schemadiff.getDiffOfModelAgainstDatabase(hf.database.metadata, hf.database.engine)
    
    # display the diffs
    if len(diff.tablesMissingInDatabase) > 0 and (args.verbose or args.interactive):
        print 'Add tables'
        for t in diff.tablesMissingInDatabase:
            print ' *', t.name
    if len(diff.tablesMissingInModel) > 0 and (args.verbose or args.interactive):
        print 'Remove tables'
        for t in diff.tablesMissingInModel:
            print ' *', t.name
    if len(diff.colDiffs) > 0 and (args.verbose or args.interactive):
        print 'Alter tables'
        for t,changes in diff.colDiffs.iteritems():
            print ' *', t
            if len(changes[0]) > 0:
                print '   add', ', '.join(c.name for c in changes[0])
            if len(changes[1]) > 0:
                print '   delete', ', '.join(c.name for c in changes[1])
            if len(changes[2]) > 0:
                print '   change', ', '.join(c[0].name for c in changes[2])
        
    if not args.dry and ask(args, 'Do you want to apply these changes? Deleting tables and columns is not reversible!'):
        import pdb; pdb.set_trace()
        # sqlite specific!
        # SQlite does not support dropping columns, so migrate creates a new one
        # copies over the data to tmp, drops the old one and recreates the table.
        # This fails if the table is referenced as a ForeignKey table, so we
        # have to disable ForeignKey checks (for SQLite) for this to work...
        if hf.database.engine.url.drivername.startswith('sqlite'):
            hf.database.engine.execute('pragma foreign_keys = off;')
        genmodel.ModelGenerator(diff).applyModel()
    