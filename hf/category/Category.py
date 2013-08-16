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
import os
import traceback
import cherrypy as cp
from mako.template import Template
import logging


class Category:
    """
    For the meaning of status values, see ModuleBase docstring.
    """
    def __init__(self, category_name, conf, module_list, run, template):
        self.logger = logging.getLogger(self.__module__+'('+category_name+')')
        self.name = category_name
        self.config = conf
        self.module_list = module_list
        self.accessible_module_list = filter(lambda x: not x.isUnauthorized(),
                                             module_list)
        self.run = run
        self.status = -1
        self.template = template
        try:
            self.algorithm = hf.category.algorithms.worst
            self.algorithm = getattr(hf.category.algorithms,
                                     self.config['algorithm'])
        except AttributeError, e:
            self.logger.warn("Status algorithm '%s' not supported, use 'worst'",
                             self.config['algorithm'])
        except hf.ConfigError, e:
            self.logger.warn("Status algorithm not specified, use 'worst'")

        if not "type" in self.config:
            self.type = "rated"
            self.logger.warn("Category type not specified, using 'rated'")
        else:
            self.type = self.config['type']
        if self.type not in ('rated', 'plots'):
            self.logger.warn("Unknown type '%s', using 'rated'" % self.type)
            self.type = "rated"

        self.status = self.algorithm(self)

        self.data_missing = False
        min_status = 1.0
        for module in self.module_list:
            if module.dataset is None:
                self.data_missing = True
            elif module.dataset['status'] < 0.0:
                self.data_missing = True

    def getStatusIcon(self):
        icon = 'cat_noinfo.png'
        if self.type == 'plots':
            icon = 'cat_avail_plot.png' if self.status > 0.9 else 'cat_unavail_plot.png'
        else:
            if self.status > 0.66:
                icon = 'cat_happy.png'
            elif self.status > 0.33:
                icon = 'cat_neutral.png'
            elif int(self.status) >= 0:
                icon = 'cat_unhappy.png'
            else:
                icon = 'cat_noinfo.png'
        if self.isUnauthorized():
            icon = 'cat_noinfo.png'
        return os.path.join(hf.config.get('paths', 'template_icons_url'), icon)

    def getIndexIcon(self):
        if self.isUnauthorized():
            return os.path.join(hf.config.get('paths', 'template_icons_url'),
                                "index_warn.png")
        return os.path.join(hf.config.get('paths', 'template_icons_url'),
                            "index_warn.png"
                            if self.data_missing
                            else "index_ok.png")

    def getLockIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'),
                            "index_lock.png")

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    @hf.url.absoluteUrl
    def url(self, time=None):
        url = "/category/"+self.name
        if time is not None:
            url += "?date=%s&amp;time=%s" % (time.strftime('%Y-%m-%d'),
                                             time.strftime('%H:%M'))
        return url

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

    def render(self, template_context):
        module_contents = []
        for module in self.module_list:
            module_name = module.instance_name
            try:
                contents = module.render()
            except Exception, e:
                contents = "Rendering module %s failed" % module_name
                self.logger.error("Rendering module %s failed: %s" % (module_name, str(e)))
                self.logger.error(traceback.format_exc())
            module_contents.append(contents)
        template_context['category'] = self
        template_context['category_name'] = self.name
        template_context['category_config'] = self.config
        template_context['category_module_list'] = self.module_list
        template_context['module_contents'] = module_contents
        try:
            return self.template.render_unicode(**template_context)
        except Exception, e:
            self.logger.error("Rendering failed: %s" % str(e))
            self.logger.error(traceback.format_exc())
            raise
