"""
Generate a skeleton module configuration
from the hints in the module code.
"""

import hf, sys, traceback
try:
    import argparse
except ImportError:
    import hf.external.argparse as argparse

load_hf_environment = True

def execute():
    parser = argparse.ArgumentParser(description='Get a configuration skeleton for a module')
    parser.add_argument('--no-comment', '-o', action='store_true', help="Disable comments in the generated configuration")
    parser.add_argument('module', help="Name of the module to get the configuration from")
    args = parser.parse_args()
    
    if not hf.module.moduleClassLoaded(args.module):
        print >> sys.stderr, sys.argv[0]+": The module '%s' was not found" % args.module
        sys.exit(-1)
    
    ModuleClass = hf.module.getModuleClass(args.module)
    print '[INSTANCE_NAME]'
    print 'module =', args.module
    print 'name = '
    print 'description = '
    print 'instruction = '
    print 'type = rated'
    print 'weight = 1.0'
    if not args.no_comment and len(ModuleClass.config_hint) > 0:
        print '# ' + ModuleClass.config_hint
    print ''
    print ''
    for key, (descr, default) in ModuleClass.config_keys.iteritems():
        if not args.no_comment and len(descr) > 0:
            print '# ' + '\n# '.join(descr.split('\n'))
        print key, '=', default
        print ''