#!/usr/bin/env python
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

import hf,sys
import os, datetime, time, traceback
import ConfigParser
import logging
import time
from hf.module.database import hf_runs

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
        hf.configtools.readConfigurationAndEnv()
        hf.configtools.setupLogging('acquire_logging_cfg')
        #check for running acquire.py process. acquire.log contains the process id if another process is still running
        try:
            with open("acquire.lock", "r") as fobj:
                checkstring = fobj.readline()
                checkstring = checkstring.strip()
                if os.path.exists("/proc/" + str(checkstring)):
                  logger.error("Another process is still running")
                  sys.exit(1)
            logger.warning("Found acquire.lock but no process was running")
            with open("acquire.lock", "w") as fobj:
                fobj.write(str(os.getpid()))
        except IOError:
            with open("acquire.lock", "w") as fobj:
                fobj.write(str(os.getpid()))
    except Exception,e:
        print "Setting up HappyFace failed"
        traceback.print_exc()
        sys.exit(-1)
    try:
        cfg_dir = None
        try:
            hf.module.importModuleClasses()
            
            hf.database.connect(implicit_execution = True)
            hf.database.metadata.create_all()
            
            category_list = hf.category.createCategoryObjects()
        except hf.exceptions.ModuleProgrammingError, e:
            logger.error("Module Programming Error: %s", str(e))
            logger.error(traceback.format_exc())
            sys.exit(-1)
        except Exception, e:
            logger.error("Setting up HappyFace failed: %s", str(e))
            logger.error(traceback.format_exc())
            sys.exit(-1)
            
        # initialize plotgenerator, even if "the plot generator" is disabled.
        # All we actually do is configuring the matplotlib backend.
        hf.plotgenerator.init()
        
        runtime = datetime.datetime.fromtimestamp(int(time.time()))
        result = hf_runs.insert().values(time=runtime, completed=False).execute()
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
        
        hf_runs.update(hf_runs.c.id == inserted_id).values(completed=True).execute()
        
        # cleanup temporary directory
	hf.downloadService.cleanup()
        
        hf.database.disconnect()
    except Exception, e:
        logger.error("Uncaught HappyFace exception: %s", str(e))
        logger.error(traceback.format_exc())
    finally:
        os.remove("acquire.lock")
        