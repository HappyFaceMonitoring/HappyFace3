#!/usr/bin/env python

import hf,sys
import os, datetime, time, traceback
import ConfigParser
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print "Usage: %s TOOL [options]\nUse the 'help'-tool for more information\n" % sys.argv[0]
        sys.exit(-1)
    try:
        hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
        hf.configtools.readConfigurationAndEnv()
        hf.configtools.setupLogging('acquire_logging_cfg')
    except Exception,e:
        print "Setting up HappyFace failed"
        traceback.print_exc()
        sys.exit(-1)
    try:
        
        cfg_dir = None
        try:
            hf.configtools.importModules()
            
            hf.database.connect(implicit_execution = True)
            hf.database.metadata.create_all()
            
            category_list = hf.category.createCategoryObjects()
        except Exception, e:
            logger.error("Setting up HappyFace failed: %s", str(e))
            logger.debug(traceback.format_exc())
        
        import hf.tools
        try:
            tool = __import__("hf.tools."+sys.argv[1], fromlist=[hf.tools], globals=globals())
        except ImportError:
            logger.error("No tool called %s" % sys.argv[1])
            sys.exit(-1)
        
        try:
            tool.execute(sys.argv)
        except Exception, e:
            logger.error("HappyFace Tool execution failed: %s", str(e))
        
    except Exception, e:
        logger.error("Uncaught HappyFace exception: %s", str(e))
        logger.debug(traceback.format_exc())
    finally:
        hf.database.disconnect()