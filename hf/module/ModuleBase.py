import hf
from mako.template import Template
import logging, traceback

class ModuleBase:
    """
    Base class for HappyFace modules.
    A module provides two core functions:
    1) Acquisition of data through the methods
      1] prepareAcquisition: Specify the files to download
      2] extractData: Return a dictionary with data to fill into the database
      3] fillSubtables: to write the datasets for the modules subtables
    2) Rendering the module by returning a template data dictionary
     in method getTemplateData.
    
    Because thread-safety is required for concurrent rendering, the module itself
    MUST NOT save its state during rendering. The modules functions are internally
    accessed by the ModuleProxy class.
    """
    
    config_defaults = {
        'description': '',
        'instruction': '',
        'type': 'rated'
    }
    
    def __init__(self, instance_name, config, run):
        self.logger = logging.getLogger(self.__module__+'('+instance_name+')')
        self.module_name = self.__class__.module_name
        self.module_table = self.__class__.module_table
        self.instance_name = instance_name
        self.config = config
        self.run = run
    
    def prepareAcquisition(self, run):
        pass
    
    def fillSubtables(self, module_entry_id):
        pass
    
    def getTemplateData(self):
        """
        Override this method if your template requires special
        preprocessing of data or you have data in subtables.
        """
        return {"dataset": self.dataset, "run": self.run}
    
    def render(self):
        module_html = ''
        if self.template is None:
            return '<p class="error">Rendering module %s failed because template was not loaded</p>' % self.instance_name
        try:
            template_data = { 'module': self }
            if self.dataset is None:
                template_data['no_data'] = True
                module_html = self.template.render(**template_data)
            else:
                template_data.update(self.getTemplateData())
                template_data['no_data'] = False
                module_html = self.template.render(**template_data)
        except Exception, e:
            module_html = "<p class='error'>Final rendering of a '%s' module failed completely!</p>" % self.module_name
            self.logger.error("Rendering of module %s failed: %s" %(self.module_name, str(e)))
            self.logger.debug(traceback.format_exc())
        return module_html
        