
import hf, os, traceback
from mako.template import Template

config = None

class Category:
    template = None
    
    def __init__(self, conf, module_conf):
        self.config = conf
        self.module_config = module_conf
        self.module_list = []
        try:
            if Category.template is None:
                template_file = os.path.join(hf.config.get("paths", "hf_template_dir"), "category.html")
                Category.template = Template(filename=template_file, module_directory=hf.config.get("paths", "template_cache_dir"))
        except Exception, e:
            # TODO logging?
            raise
        
        for instance_name in self.config["modules"].split(","):
            if len(instance_name) == 0: continue
            try:
                cfg = self.module_config[instance_name]
                hf.module.tryModuleClassImport(cfg["module"])
                module = hf.module.getModuleClass(cfg["module"])(instance_name, cfg)
                self.module_list.append(module)
            except Exception, e:
                # TODO logging
                traceback.print_exc()
                pass
    
    def prepareAcquisition(self, run):
        for module in self.module_list:
            try:
                module.prepareAcquisition(run)
            except Exception, e:
                # TODO logging
                traceback.print_exc()
                pass
    
    def acquire(self, run):
        for module in self.module_list:
            try:
                module.acquire(run)
            except Exception, e:
                # TODO logging
                traceback.print_exc()
                pass
    
    def render(self, run):
        module_contents = {}
        for module in self.module_list:
            module_name = module.instance_name
            try:
                contents = module.render(run)
            except Exception, e:
                # TODO logging
                contents = "Rendering module %s failed" % module_name
                traceback.print_exc()
            module_contents[module_name] = contents
        return Category.template.render(category = self.config, run = run, module_contents = module_contents)