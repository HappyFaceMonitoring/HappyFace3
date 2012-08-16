# -*- coding: utf-8 -*-

import cherrypy as cp
from cherrypy.lib.static import serve_file
import hf, datetime, time, logging, traceback, os, subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from mako.template import Template
from datetime import timedelta

class RootDispatcher(object):
    """
    The main HF Dispatcher
    """
    _cp_config = { 'tools.cert_auth.on': True }
    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = hf.category.createCategoryObjects()
        self.category = hf.category.Dispatcher(self.category_list)
        self.plot = hf.plotgenerator.Dispatcher(self.category_list)
        self.module_map = {}
        for category in self.category_list:
            for module in category.module_list:
                self.module_map[module.instance_name] = module
    
    @cp.expose
    def index(self):
        raise cp.HTTPRedirect(hf.url.join(hf.config.get('paths', 'happyface_url'), 'category'))
    
    @cp.expose
    @cp.tools.caching()
    def static(self, *args):
        cp.lib.caching.expires(secs=timedelta(365), force=True)
        
        path = os.path.join(hf.hf_dir, hf.config.get('paths', 'static_dir'), *args)
        # archive/Y/M/D/H/M/file -> 7
        if len(args) == 7 and args[0] == 'archive':
            authorized = self.archiveFileAuthorized(args[6])
            if authorized:
                return serve_file(path)
            else:
                raise cp.HTTPError(status=403, message="You are not allowed to access this resource.")
        else:
            return serve_file(path)
    
    def archiveFileAuthorized(self, filename):
        for instance, module in self.module_map.iteritems():
            if filename.startswith(instance):
                return not module.isUnauthorized()
        self.logger.warning("""Unable to map file '%s' to module!
Perhaps the corresponding module was removed from the HF config or the file does not start with the module instance name (this is an error in the module).""")
        return False
