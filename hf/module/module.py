
from sqlalchemy import *
import hf, modules, traceback, os
from mako.template import Template
import pkgutil

# A list of columns
__column_file_list = {}
# all imported module classes
__module_class_list = {}


def getColumnFileReference(table):
    name = table.name if isinstance(table, Table) else table
    return __column_file_list[name] if name in __column_file_list else []
    
def moduleClassLoaded(mod_class):
    return mod_class in __module_class_list

def tryModuleClassImport(mod_class):
    if moduleClassLoaded(mod_class):
        return
    try:
        pymodule = __import__('modules.'+mod_class, globals(), locals(), [], -1)
        if not moduleClassLoaded(mod_class):
            raise hf.ConfigError("Module '%s' not found" % mod_class)
    except ImportError, e:
        raise hf.ConfigError("Cannot import module '%s'" % mod_class)
    except Exception, e:
        # TODO logging
        traceback.print_exc()
        raise hf.ModuleError("Error while importing module '%s'" % mod_class)
    
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
    return __module_class_list[mod_name] if mod_name in __module_class_list else None

def getModuleClassDict():
    return __module_class_list
