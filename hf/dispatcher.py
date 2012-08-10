# -*- coding: utf-8 -*-

import cherrypy as cp
import hf, datetime, time, logging, traceback, os, subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from mako.template import Template

class RootDispatcher(object):
    """
    The main HF Dispatcher
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.category = hf.category.Dispatcher()
        self.plot = hf.plotgenerator.Dispatcher()
    
    @cp.expose
    def index(self):
        raise cp.HTTPRedirect(hf.url.join(hf.config.get('paths', 'happyface_url'), 'category'))