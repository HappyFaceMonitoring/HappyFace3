#!/usr/bin/env python

import hf, cherrypy
import os
import ConfigParser


if __name__ == '__main__':
    hf.hf_dir = os.path.dirname(os.path.abspath(__file__))
    hf.configtools.readConfiguration()
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
    category_list = hf.configtools.createCategoryObjects()
    
    cherrypy.quickstart(root=hf.dispatcher.CategoryDispatcher(category_list), script_name="/", config=cp_config)
    hf.database.disconnect()
    