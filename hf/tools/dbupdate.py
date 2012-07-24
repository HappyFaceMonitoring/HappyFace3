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

def compare(args, hf_table, db_table):
    if args.verbose: print "Compare '%s' tables" % (hf_table.name)

def execute():
    parser = argparse.ArgumentParser(description='Update the database schema as neccessary')
    parser.add_argument('--verbose', '-v', action='store_true', help="Provide more detailed output")
    parser.add_argument('--force', '-f', action='store_true', help="Do not ask user to perform action. Might cause data loss!")
    parser.add_argument('--interactive', '-i', action='store_true', help="Asks the user before applying any changeset.")
    parser.add_argument('--dry', action='store_true', help="Just provide a summary of what will be done. Superseds any other options.")
    parser.add_argument('--new-only', action='store_true', help="Creates only new tables and does not check for changes in existing ones.")
    args = parser.parse_args()
    
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
    
    modules = hf.module.getModuleClassDict()
    
    # Use all database tables via reflection in another,
    # separate metadata object
    server_metadata = MetaData(bind=hf.database.engine, reflect=True)
    
    # Now compare each of the tables
    for name, hf_table in hf.database.metadata.tables.iteritems():
        if name not in server_metadata.tables:
            print """FATAL: '%s' was not found on database server!
            If you are in a dry run or skipped the creation of non-existant tables, this should not be a big problem. Just run this tool with the --new-only option, it is quite safe, anyway.
            
            In case the problem persists, there is something strange going on."""
            return
        compare(args, hf_table, server_metadata.tables[name])
        
    