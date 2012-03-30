
import hf, os, traceback
from mako.template import Template
import logging
config = None

class CategoryProxy:
    """
    A run independant Category object.
    Can create run dependant category objects efficently.
    """
    template = None
    
    def __init__(self, name, conf, module_conf):
        self.logger = logging.getLogger(self.__module__+'('+name+')')
        self.name = name
        self.config = conf
        self.module_config = module_conf
        self.module_list = []
        
        for instance_name in self.config["modules"].split(","):
            if len(instance_name) == 0: continue
            try:
                cfg = self.module_config[instance_name]
                hf.module.tryModuleClassImport(cfg["module"])
                ModuleClass = hf.module.getModuleClass(cfg["module"])
                self.module_list.append(hf.module.ModuleProxy(ModuleClass, instance_name, cfg))
            except Exception, e:
                self.logger.error("Cannot add module instance %s: %s" %(instance_name, str(e)))
                self.logger.debug(traceback.format_exc())
    
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
                self.logger.debug(traceback.format_exc())
    
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
                self.logger.debug(traceback.format_exc())
    
    def getModule(self, run):
        specific_modules = [m.getModule(run) for m in self.module_list]
        return hf.category.Category(self.name, self.config, specific_modules, run)
        