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

import hf
import sys
import os
import datetime
import time
import traceback
import ConfigParser
import logging


env_loaded = False


def load_env():
    global env_loaded
    env_loaded = True
    try:
        hf.configtools.readConfigurationAndEnv()
        hf.configtools.setupLogging('acquire_logging_cfg')
    except Exception, e:
        print "Setting up HappyFace failed"
        traceback.print_exc()
        sys.exit(-1)

    cfg_dir = None
    try:
        hf.module.importModuleClasses()

        hf.database.connect(implicit_execution=True)
        hf.database.metadata.create_all()

        category_list = hf.category.createCategoryObjects()
    except Exception, e:
        print "Setting up HappyFace failed: %s", str(e)
        print traceback.format_exc()

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
        tool = __import__("hf.tools." + tool_name,
                          fromlist=[hf.tools],
                          globals=globals())
    except ImportError, e:
        logger.error("No tool called %s: %s" % (tool_name, str(e)))
        sys.exit(-1)

    try:
        hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            tool.execute()
        except Exception, e:
            print "Tool execution failed: %s", str(e)
            print traceback.format_exc()

    except Exception, e:
        logger.error("Uncaught HappyFace exception: %s", str(e))
        logger.error(traceback.format_exc())
    finally:
        if env_loaded:
            hf.database.disconnect()
