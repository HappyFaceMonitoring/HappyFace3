import hf
import logging, traceback, os
from mako.template import Template

class ModuleProxy:
    """
    The access class to actual instances of the module class.
    
    Since the module instances have to be independant and thread-safe
    for rendering, the common state is stored in the proxy, which
    creates a specific, run-time dependant module object for rendering.
    """
    
    def __init__(self, ModuleClass, instance_name, config):
        self.logger = logging.getLogger(self.__module__+'('+instance_name+')')
        self.ModuleClass = ModuleClass
        self.module_name = ModuleClass.module_name
        self.module_table = ModuleClass.module_table
        self.instance_name = instance_name
        self.config = config
        self.acquisitionModules = {}
        # check if instance is in database and of correct type
        instance = hf.module.database.module_instances.select(hf.module.database.module_instances.c.instance==instance_name).execute().fetchone()
        if instance is None:
            hf.module.database.module_instances.insert().values(instance=instance_name, module=self.module_name).execute()
        elif instance["module"] != self.module_name:
            raise hf.ConsistencyError("The module type of instance '%s' changed" % instance_name)
        
        # get the common module template
        try:
            filename = os.path.join(hf.hf_dir, hf.config.get("paths", "module_template_dir"), self.module_name+".html")
            self.template = Template(filename=filename, lookup=hf.template_lookup)
        except Exception, e:
            self.logger.error("Cannot create template, " + str(e))
            self.logger.debug(traceback.format_exc())
            self.template = None
        
    def prepareAcquisition(self, run):
        # create module instance solely for that purpose
        module = self.getModule(run)
        self.acquisitionModules[run['id']] = module
        try:
            module.prepareAcquisition()
        except Exception, e:
            module.logger.error("prepareAcquisition() failed: %s" % str(e))
            module.debug(traceback.format_exc())
    
    def acquire(self, run):
        module = self.acquisitionModules[run['id']]
        try:
            self.acquisitionModules[run['id']] = module
            self.conn = hf.database.engine.connect()
            data = {"instance": self.instance_name,
                    "run_id": run["id"],
                    "status": 1.0,
                    "error_string": "",
                    "source_url": "",
                    "description": self.config["description"],
                    "instruction": self.config["instruction"]
                    }
            d = module.extractData()
            data.update(d)
            
            result = module.module_table.insert().values(**data).execute()
            
            # compatibility between different sqlalchemy versions
            try:
                inserted_id = result.inserted_primary_key[0]
            except AttributeError:
                inserted_id = result.last_inserted_ids()[0]
            module.fillSubtables(inserted_id)
        except Exception, e:
            module.logger.error("data acquisition failed: %s" % str(e))
            module.logger.debug(traceback.format_exc())
        finally:
            del self.acquisitionModules[run['id']]
    
    def getModule(self, run):
        """
        Generate a module instance object for a specific
        HappyFace run.
        """
        module = self.ModuleClass(self.instance_name, self.config, run)
        module.template = self.template
        module.dataset = self.module_table.select(self.module_table.c.run_id==run["id"])\
                .where(self.module_table.c.instance==self.instance_name)\
                .execute()\
                .fetchone()
        return module
        
    