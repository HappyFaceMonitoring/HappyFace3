#!/usr/bin/env python

import hf,sys
import os, datetime, time, traceback
import ConfigParser
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
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
        
        runtime = datetime.datetime.fromtimestamp(int(time.time()))
        result = hf.module.database.hf_runs.insert().values(time=runtime).execute()
        try:
            inserted_id = result.inserted_primary_key[0]
        except AttributeError:
            inserted_id = result.last_inserted_ids()[0]
        run = {"id": inserted_id, "time":runtime}
        
        logger.info("Prepare data acquisition")
        for category in category_list:
            logger.info("Prepare category %s..." % category.config["name"])
            category.prepareAcquisition(run)
        
        logger.info("Download files...")
        try:
            hf.downloadService.performDownloads(runtime)
            logger.info("Download done")
        except Exception, e:
            logger.warn("Downloading of all files failed")
            
        logger.info("Acquire data and fill database")
        for category in category_list:
            logger.info("Acquire in category %s..." % category.config["name"])
            category.acquire(run)
        
        # cleanup temporary directory
        hf.downloadService.cleanup()
        
        hf.database.disconnect()
    except Exception, e:
        logger.error("Uncaught HappyFace exception: %s", str(e))
        logger.debug(traceback.format_exc())