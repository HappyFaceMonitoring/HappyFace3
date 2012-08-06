
from sqlalchemy import *
import hf, modules, traceback, os
from mako.template import Template

# A list of columns
__column_file_list = {}
# all imported module classes
__module_class_list = {}

def generateModuleTable(module_class, tabname, columns):
    table = Table("module_"+tabname, hf.database.metadata,
        *([
            Column('id', Integer, Sequence(tabname+'_id_seq'), primary_key=True),
            Column('instance', Text, ForeignKey("module_instances.instance")),
            Column('run_id', Integer, ForeignKey("hf_runs.id")),
            Column('status', Float),
            Column('description', Text),
            Column('instruction', Text),
            Column('error_string', Text),
            Column('source_url', Text),
        ] + columns))
    module_class.module_table = table
    module_class.subtables = {}
    table.module_class = module_class
    return table
        
def generateModuleSubtable(tabname, module_table, columns):
    table = Table("module_sub_"+tabname, hf.database.metadata,
        *([
            Column('id', Integer, Sequence("module_"+module_table.name+"_sub_"+tabname+'_id_seq'), primary_key=True),
            Column('parent_id', Integer, ForeignKey(module_table.c.id)),
        ] + columns))
    module_table.module_class.subtables["module_sub_"+tabname] = table
    table.module_class = module_table.module_class
    return table

def addColumnFileReference(table, column):
    name = table.name if isinstance(table, Table) else table
    __column_file_list[name] = __column_file_list[name]+[column] if name in __column_file_list else [column]

def getColumnFileReference(table):
    name = table.name if isinstance(table, Table) else table
    return __column_file_list[name] if name in __column_file_list else []

def addModuleClass(mod_class):
    mod_name = mod_class.__module__.split(".")[-1]
    mod_class.module_name = mod_name
    __module_class_list[mod_name] = mod_class
    
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
    
def getModuleClass(mod_name):
    return __module_class_list[mod_name] if mod_name in __module_class_list else None

def getModuleClassDict():
    return __module_class_list
