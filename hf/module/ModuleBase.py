import hf
from mako.template import Template
import logging, traceback, os

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
    
    table = None
    subtables = {}
    
    def __init__(self, instance_name, config, run, dataset, template):
        self.logger = logging.getLogger(self.__module__+'('+instance_name+')')
        self.module_name = self.__class__.module_name
        self.module_table = self.__class__.module_table
        self.instance_name = instance_name
        self.config = config
        self.run = run
        self.dataset = dataset
        self.template = template
    
    def prepareAcquisition(self):
        pass
    
    def fillSubtables(self, module_entry_id):
        pass
    
    def getTemplateData(self):
        """
        Override this method if your template requires special
        preprocessing of data or you have data in subtables.
        """
        return {"dataset": self.dataset, "run": self.run}
        
    def __unicode__(self):
        return self.instance_name
    
    def __str__(self):
        return self.instance_name
    
    def getStatusString(self):
        icon = 'unhappy'
        if self.dataset is None:
            icon = 'unhappy' if type == 'rated' else 'unavail_plot'
        else:
            if type == 'rated':
                if self.dataset['status'] > 0.66:
                    icon = 'happy'
                elif self.dataset['status'] > 0.33:
                    icon = 'neutral'
                else:
                    icon = 'unhappy'
            else:
                icon = 'avail_plot' if self.dataset['status'] > 0.9 else 'unavail_plot'
        return icon
    
    def url(self):
        # something along ?date=2012-03-24&amp;time=17:20&amp;t=batchsys&amp;m=${module.instance_name}
        return "#%s" % self.instance_name
        
    def getStatusIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'), 'mod_'+self.getStatusString()+'.png')
    
    def getNavStatusIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'), 'nav_'+self.getStatusString()+'.png')
    
    def render(self):
        module_html = ''
        if self.template is None:
            return '<p class="error">Rendering module %s failed because template was not loaded</p>' % self.instance_name
        try:
            template_data = { 'module': self, 'run': self.run, 'hf': hf }
            if self.dataset is None:
                template_data['no_data'] = True
                module_html = self.template.render(**template_data)
            else:
                template_data.update(self.getTemplateData())
                template_data['no_data'] = False
                module_html = self.template.render(**template_data)
        except Exception, e:
            module_html = "<p class='error'>Final rendering of '%s' failed completely!</p>" % self.instance_name
            self.logger.error("Rendering of module %s failed: %s" %(self.module_name, str(e)))
            self.logger.debug(traceback.format_exc())
        return module_html
        