#!/usr/bin/env python

import hf,sys
import os, datetime, time, traceback
import ConfigParser
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s TOOL [options]\nUse the 'help'-tool for more information\n" % sys.argv[0]
        sys.exit(-1)
    
    tool_name = sys.argv[1]
    sys.argv[0] += ' ' + sys.argv[1]
    del sys.argv[1]

    import hf.tools
    try:
        tool = __import__("hf.tools."+tool_name, fromlist=[hf.tools], globals=globals())
    except ImportError,e:
        logger.error("No tool called %s: %s" % (tool_name, str(e)))
        sys.exit(-1)
    
    try:
        hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
        if tool.load_hf_environment:
            try:
                hf.configtools.readConfigurationAndEnv()
                hf.configtools.setupLogging('acquire_logging_cfg')
            except Exception,e:
                print "Setting up HappyFace failed"
                traceback.print_exc()
                sys.exit(-1)

            cfg_dir = None
            try:
                hf.configtools.importModules()
                
                hf.database.connect(implicit_execution = True)
                hf.database.metadata.create_all()
                
                category_list = hf.category.createCategoryObjects()
            except Exception, e:
                print "Setting up HappyFace failed: %s", str(e)
                print traceback.format_exc()
        try:
            tool.execute()
        except Exception, e:
            print "Tool execution failed: %s", str(e)
            print traceback.format_exc()
        
    except Exception, e:
        logger.error("Uncaught HappyFace exception: %s", str(e))
        logger.debug(traceback.format_exc())
    finally:
        if tool.load_hf_environment:
            hf.database.disconnect()