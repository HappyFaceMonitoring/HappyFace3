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
from dispatcher import Dispatcher
from CategoryProxy import CategoryProxy
from xml import renderXmlOverview
import algorithms
import hf

config = None

def createCategoryObjects():
    '''
    '''
    category_list = []
    used_modules = []
    category_names = hf.category.config.sections()
    if len(hf.config.get('happyface', 'categories')) > 0:
        category_names = hf.config.get('happyface', 'categories').split(',')
    for category in category_names:
        conf = dict(hf.category.config.items(category))
        module_conf = {}
        for module in conf["modules"].split(","):
            if len(module) == 0: continue
            if module in used_modules:
                raise hf.ConfigError("Module '%s' used second time in category '%s'" % (module, category))
            module_conf[module] = dict(hf.module.config.items(module))
            used_modules.append(module)
        category_list.append(hf.category.CategoryProxy(category, conf, module_conf))
    return category_list

__all__ = ["Category", "CategoryProxy", "Dispatcher", "renderXmlOverview", "algorithms"]