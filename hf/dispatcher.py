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
    
    @cp.expose
    def index(self):
        raise cp.HTTPRedirect(hf.url.join(hf.config.get('paths', 'happyface_url'), 'category'))
    
    @cp.expose
    @cp.tools.caching()
    def static(self, *args):
        cp.lib.caching.expires(secs=timedelta(365), force=True)
        
        path = os.path.join(hf.hf_dir, hf.config.get('paths', 'static_dir'), *args)
        if len(args) > 0 and args[0] == 'archive':
            return serve_file(path)
            #raise cp.HTTPError(status=403, message="You are not allowed to access this resource.")
        else:
            return serve_file(path)