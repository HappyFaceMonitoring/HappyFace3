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

import hf, os, traceback
from mako.template import Template
import logging
import cherrypy as cp
config = None

class CategoryProxy:
    """
    A run independant Category object.
    Can create run dependant category objects efficently.
    
    For the meaning of status values, see ModuleBase docstring.
    """
    template = None
    
    def __init__(self, name, conf, module_conf):
        self.logger = logging.getLogger(self.__module__+'('+name+')')
        self.name = name
        self.config = conf
        self.module_config = module_conf
        self.module_list = []
        
        if 'access' not in self.config:
            self.config['access'] = 'permod'
        if self.config['access'] not in ['open', 'permod', 'restricted']:
            self.logger.warning("Unknown access option '%s', assume 'permod'" % self.config['access'])
            self.config['access'] = 'permod'
        
        for instance_name in self.config["modules"].split(","):
            if len(instance_name) == 0: continue
            try:
                cfg = self.module_config[instance_name]
                if self.config['access'] == 'open':
                    cfg['access'] = 'open'
                elif self.config['access'] == 'restricted':
                    cfg['access'] = 'restricted'
                hf.module.getModuleClass(cfg["module"])
                ModuleClass = hf.module.getModuleClass(cfg["module"])
                self.module_list.append(hf.module.ModuleProxy(ModuleClass, instance_name, cfg))
            except Exception, e:
                self.logger.error("Cannot add module instance %s: %s" %(instance_name, str(e)))
                self.logger.error(traceback.format_exc())
        
        try:
            filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "category.html")
            self.template = Template(filename=filename, lookup=hf.template_lookup)
        except Exception, e:
            self.logger.error("Cannot load category template: %s" % str(e))
            self.logger.error(traceback.format_exc())
            self.template = None
    
    def isAccessRestricted(self):
        return self.config['access'] != 'open'
    
    def isUnauthorized(self):
        return self.config['access'] == 'restricted' and not cp.request.cert_authorized
    
    def hasUnauthorizedModules(self):
        if self.isUnauthorized():
            return True
        for module in self.module_list:
            if module.isUnauthorized():
                return True
        return False
    
    def prepareAcquisition(self, run):
        '''
        Prepare data acquisition for a certain run.
        
        The ModuleProxy takes care that the call is
        "independant", so we do not need to care here =)
        '''
        for module in self.module_list:
            try:
                module.prepareAcquisition(run)
            except Exception, e:
                self.logger.error("prepareAcquisition() failed on %s: %s" % (module.instance_name, str(e)))
                self.logger.error(traceback.format_exc())
    
    def acquire(self, run):
        '''
        Acquire data and fill tables for a certain run.
        
        The ModuleProxy takes care that the call is
        "independant", so we do not need to care here =)
        '''
        for module in self.module_list:
            try:
                module.acquire(run)
            except Exception, e:
                self.logger.error("acquire() failed on %s: %s" % (module.instance_name, str(e)))
                self.logger.error(traceback.format_exc())
    
    def getCategory(self, run):
        specific_modules = [m.getModule(run) for m in self.module_list]
        category = hf.category.Category(self.name, self.config, specific_modules, run, self.template)
        for s in specific_modules:
            s.category = category
        return category
        