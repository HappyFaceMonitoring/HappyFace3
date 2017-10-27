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

"""

.. data:: config
"""

from Category import Category
from dispatcher import Dispatcher, AjaxDispatcher
from CategoryProxy import CategoryProxy
from xml import renderXmlOverview
import algorithms
import hf
from ConfigParser import NoSectionError

config = None


def createCategoryObjects():
    '''
    Generates the category objects from the happyface configuration
    :return:
    :rtype:
    '''
    category_list = []
    used_modules = []
    category_names = hf.category.config.sections()
    if len(hf.config.get('happyface', 'categories')) > 0:
        category_names = hf.config.get('happyface', 'categories').split(',')
    for category in category_names:
        conf = hf.configtools.ConfigDict(hf.category.config.items(category))
        module_conf = {}
        for module in conf["modules"].split(","):
            try:
                if len(module) == 0:
                    continue
                if module in used_modules:
                    raise hf.ConfigError("Module '%s' used second time in category '%s'" % (module, category))
                module_conf[module] = hf.configtools.ConfigDict(hf.module.config.items(module))
                used_modules.append(module)
            except NoSectionError, e:
                msg = "Tried to use module '%s' in category '%s', but it was never mentioned in module configuration"
                raise hf.exceptions.ConfigError(msg % (module, category))
        category_list.append(hf.category.CategoryProxy(category, conf, module_conf))
    return category_list

__all__ = ["Category", "CategoryProxy", "Dispatcher",
           "renderXmlOverview", "algorithms"]
