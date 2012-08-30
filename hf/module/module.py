
from sqlalchemy import *
import hf, modules, traceback, os
from mako.template import Template
import pkgutil

# A list of columns
__column_file_list = {}
# all imported module classes
__module_class_list = {}


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
    module_paths = [os.path.join(hf.hf_dir, "modules")]
    exclude = ['.git', '.svn']
    for path in module_paths:
        subdirs = [d for d in\
            (os.path.join(path, p) for p in os.listdir(path) if p not in exclude)\
            if os.path.isdir(d)]
        module_paths.extend(subdirs)
    for imp, name, ispkg in pkgutil.iter_modules(path=module_paths):
        if ispkg:
            continue
        imported_modules = __module_class_list.keys()
        
        loader = imp.find_module(name)
        loader.load_module(name)
        
        new_modules = [mod for mod in __module_class_list.keys() if mod not in imported_modules]
        for mod in new_modules:
            __module_class_list[mod].filepath = loader.filename
        

def getModuleClass(mod_name):
    """
    Get the module class for a given module name.
    :param mod_name: Name of the module
    :ptype mod_name: string
    """
    return __module_class_list[mod_name] if mod_name in __module_class_list else None

