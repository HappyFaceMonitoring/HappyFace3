
from sqlalchemy import *
import hf, modules, traceback, os
from mako.template import Template

# A list of columns
__column_file_list = {}
# all imported module classes
__module_class_list = {}

class ModuleBase:
    # ModuleBase-wide template
    template = None
    
    def __init__(self, instance_name, config):
        self.module_name = self.__class__.module_name
        instance = hf.module.database.module_instances.select(hf.module.database.module_instances.c.instance==instance_name).execute().fetchone()
        if instance is None:
            hf.module.database.module_instances.insert().values(instance=instance_name, module=self.module_name).execute()
        elif instance["module"] != self.module_name:
            raise hf.ConsistencyError("The module type of instance '%s' changed" % instance_name)
        self.instance_name = instance_name
        self.config = config
        self.status = 1.0
        self.error_string = ""
        template_cache = hf.config.get("paths", "template_cache_dir")
        try:
            if ModuleBase.template is None:
                shared_template_name = os.path.join(hf.config.get("paths", "hf_template_dir"), "module_base.html")
                ModuleBase.template = Template(filename=shared_template_name, module_directory=template_cache)
        except Exception, e:
            self.error_string += "Shared module template initialization failed.\n"
            ModuleBase.template = None
            # TODO logging
            traceback.print_exc()
        try:
            template_file = os.path.join(hf.config.get("paths", "module_template_dir"), self.module_name+".html")
            self.template = Template(filename=template_file, module_directory=template_cache)
        except Exception, e:
            self.error_string += "Template initialization failed.\n"
            # TODO logging
            traceback.print_exc()
    
    def prepareAcquisition(self, run):
        pass
    
    def fillSubtables(self, module_entry_id):
        pass
    
    def getTemplateData(self, run, dataset):
        return {"dataset": dataset, "run": run}
    
    def acquire(self, run):
        try:
            self.conn = hf.database.engine.connect()
            data = {"instance": self.instance_name,
                    "run_id": run["id"],
                    "status": self.status,
                    "error_string": self.error_string,
                    "source_url": "",
                    "description": self.config["description"],
                    "instruction": self.config["instruction"]
                    }
            data.update(self.extractData())
            
            result = self.module_table.insert().values(**data).execute()
            try:
                inserted_id = result.inserted_primary_key[0]
            except AttributeError:
                inserted_id = result.last_inserted_ids()[0]
            self.fillSubtables(inserted_id)
        except Exception, e:
            # TODO logging
            traceback.print_exc()
            pass
    
    def render(self, run):
        mod_contents = ""
        try:
            dataset = self.module_table.select(self.module_table.c.run_id==run["id"]).where(self.module_table.c.instance==self.instance_name).execute().fetchone()
            if dataset is None:
                self.error_string += "No data at this time.\n"
            else:
                template_data = self.getTemplateData(run, dataset)
                mod_contents = self.template.render(**template_data)
        except Exception, e:
            self.error_string += "Rendering module contents failed.\n"
            # TODO logging
            traceback.print_exc()
        module_html = ""
        try:
            module_html = ModuleBase.template.render(instance_name = self.instance_name,
                    run = run,
                    config = self.config,
                    contents = mod_contents,
                    error_string = self.error_string,
                    dataset = dataset)
        except Exception, e:
            # TODO logging
            module_html = "<h3>Final rendering of a '%s' module failed completely!</h3>" % self.module_name
            traceback.print_exc()
        return module_html
        

def generateModuleTable(tabname, columns):
    return Table("module_"+tabname, hf.database.metadata,
        *([
            Column('id', Integer, Sequence(tabname+'_id_seq'), primary_key=True),
            Column('instance', Integer, ForeignKey("module_instances.instance")),
            Column('run_id', Integer, ForeignKey("hf_runs.id")),
            Column('status', Float),
            Column('description', Text),
            Column('instruction', Text),
            Column('error_string', Text),
            Column('source_url', Text),
        ] + columns))
        
def generateModuleSubtable(tabname, module_table, columns):
    return Table("module_sub_"+tabname, hf.database.metadata,
        *([
            Column('id', Integer, Sequence(tabname+'_id_seq'), primary_key=True),
            Column('parent_id', Integer, ForeignKey(module_table.c.id)),
        ] + columns))

def addColumnFileReference(table, column):
    name = table.tabname if isinstance(table, Table) else table
    __column_file_list[name] = __column_file_list[name]+[column] if name in __column_file_list else [column]

def getColumnFileReference(table):
    name = table.tabname if isinstance(table, Table) else table
    return __column_file_list[table]

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
