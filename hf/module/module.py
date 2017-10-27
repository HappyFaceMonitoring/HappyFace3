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

"""This file contains the main functions and variables that let the acquire and render scripts interface with the
happyface framework"""

from sqlalchemy import *
import hf
import traceback
import os
import logging
import sys
from mako.template import Template
import pkgutil

# A list of columns
__column_file_list = {}
# all imported module classes
__module_class_list = {}

logger = logging.getLogger(__file__)


def getColumnFileReference(table):
    """
    Get a list of columns for a table that point to a file in the
    archive directory.
    :param table: Table to get the file columns for
    :ptype table: string or Table
    :returns: list of column names
    """
    name = table.name if isinstance(table, Table) else table
    return __column_file_list[name] if name in __column_file_list else []


def moduleClassLoaded(mod_class):
    return mod_class in __module_class_list


def importModuleClasses():
    """ We look for modules and if we find them instantiate them"""
    #here we build the list of modules we want to load
    module_paths = [os.path.join(hf.hf_dir, "modules")]
    exclude = ['.git', '.svn']
    try:
        for path in module_paths:
            subdirs = [d for d in
                       (os.path.join(path, p)
                        for p in os.listdir(path)
                        if p not in exclude)
                       if os.path.isdir(d)]
            module_paths.extend(subdirs)
    except OSError:
        logger.error("Cannot find modules directory!")
        logger.error(traceback.format_exc())
        sys.exit()
    # here we start loading the modules
    for imp, name, ispkg in pkgutil.iter_modules(path=module_paths):
        if ispkg:
            continue
        imported_modules = __module_class_list.keys()

        loader = imp.find_module(name)
        loader.load_module(name)

        new_modules = [mod
                       for mod in __module_class_list.keys()
                       if mod not in imported_modules]
        for mod in new_modules:
            __module_class_list[mod].filepath = loader.filename


def getModuleClass(mod_name):
    """
    Get the module class for a given module name.
    :param mod_name: Name of the module
    :ptype mod_name: string
    """
    if mod_name not in __module_class_list:
        raise hf.ConfigError("Module class {0} not found".format(mod_name))
    return __module_class_list[mod_name]
