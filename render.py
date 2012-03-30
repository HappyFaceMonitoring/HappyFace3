#!/usr/bin/env python

import os,sys
print sys.path
print os.getcwd()
os.chdir(os.path.dirname(__file__))
sys.path.append(os.path.dirname(__file__))

import hf, cherrypy, logging
import ConfigParser
import atexit

logger = logging.getLogger(__name__)


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

if __name__ == '__main__':
    cherrypy.quickstart(root=hf.dispatcher.CategoryDispatcher(), script_name="/", config=cp_config)
    hf.database.disconnect()
else:
    cherrypy.config.update({'environment': 'embedded'})
    if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
        cherrypy.engine.start(blocking=False)
        atexit.register(cherrypy.engine.stop)
    application = cherrypy.Application(root=hf.dispatcher.CategoryDispatcher(), script_name="/", config=cp_config)
