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

import cherrypy as cp
from cherrypy.lib.static import serve_file
import hf, datetime, time, logging, traceback, os, subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from mako.template import Template
from datetime import timedelta
from cherrypy import _cperror

class RootDispatcher(object):
    """
    The main HF Dispatcher
    """
    _cp_config = {
        'tools.cert_auth.on': True,
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf8', 
    }
    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = hf.category.createCategoryObjects()
        self.category = hf.category.Dispatcher(self.category_list)
        self.plot = hf.plotgenerator.Dispatcher(self.category_list)
        self.module_map = {}
        for category in self.category_list:
            for module in category.module_list:
                self.module_map[module.instance_name] = module
        cp.config.update({
            'error_page.default': self.errorPage,
        })

    
    @cp.expose
    def index(self):
        raise cp.HTTPRedirect(hf.url.join(hf.config.get('paths', 'happyface_url'), 'category'))
    
    @cp.expose
    #@cp.tools.caching()
    def static(self, *args):
        #cp.lib.caching.expires(secs=timedelta(365), force=True)
        
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

    def errorPage(self, **kwargs):
        self.logger.debug(_cperror.format_exc())
        try:
            args = {
                "message": kwargs['status'],
                "details": "",
            }
            try:
                template_context, category_dict, run = self.category.prepareDisplay()
                template_context.update(args)
                
                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "error.html")
                template = Template(filename=filename, lookup=hf.template_lookup)
                return template.render_unicode(**template_context)
                
            except Exception, e:
                self.logger.debug("Fancy error page generation failed\n" + traceback.format_exc())
                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "plain_error.html")
                template = Template(filename=filename, lookup=hf.template_lookup)
                return template.render_unicode(**template_context)
                
        except Exception, e:
            self.logger.error(u"error page generation failed: "+unicode(e))
            self.logger.debug(traceback.format_exc())
            return u"""<h1>Error Inception</h1>
            <p>An error occured while displaying an error. Embarrasing.</p>
            <p>Please consult the log files!</p>"""