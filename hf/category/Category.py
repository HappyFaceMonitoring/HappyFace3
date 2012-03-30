
import hf, os, traceback
from mako.template import Template
import logging
      
class Category:
    def __init__(self, category_name, conf, module_list, run):
        self.logger = logging.getLogger(self.__module__+'('+category_name+')')
        self.name = category_name
        self.config = conf
        self.module_list = module_list
        self.run = run
        try:
            filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "category.html")
            self.template = Template(filename=filename, lookup=hf.template_lookup)
        except Exception, e:
            self.logger.error("Cannot load category template: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            self.template = None
                
    def render(self, template_context):
        module_contents = {}
        for module in self.module_list:
            module_name = module.instance_name
            try:
                contents = module.render()
            except Exception, e:
                contents = "Rendering module %s failed" % module_name
                self.logger.error("Rendering module %s failed: %s" % (module_name, str(e)))
                self.logger.debug(traceback.format_exc())
            module_contents[module_name] = contents
        template_context['category_name'] = self.name
        template_context['category_config'] = self.config
        template_context['category_module_list'] = self.module_list
        template_context['run'] = self.run
        template_context['module_contents'] = module_contents
        try:
            return self.template.render(**template_context)
        except Exception, e:
            self.logger.error("Rendering failed: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            raise