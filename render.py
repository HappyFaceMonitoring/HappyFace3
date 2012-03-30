#!/usr/bin/env python

import hf, cherrypy
import os, logging
import ConfigParser

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
    hf.configtools.readConfigurationAndEnv()
    hf.configtools.setupLogging('render_logging_cfg')
    cp_config = {}
    for section in hf.config.sections():
        if section == "global" or section.startswith("/"):
            config = dict(hf.config.items(section))
            for key,val in config.iteritems():
                try:
                    config[key] = eval(val)
                except ValueError:
                    pass
            cp_config[section] = config
    cherrypy.config.update(cp_config)
    
    hf.configtools.importModules()
    
    hf.database.connect(implicit_execution = True)
    
    cherrypy.quickstart(root=hf.dispatcher.CategoryDispatcher(), script_name="/", config=cp_config)
    hf.database.disconnect()
    