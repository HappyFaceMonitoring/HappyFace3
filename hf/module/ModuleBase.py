import hf
from mako.template import Template
import logging, traceback, os
from sqlalchemy import Integer, Float, Numeric

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
    
    The status of the module represents a quick overview over the current module
    status and fitness.
    * 0.66 <= status <= 1.0  The module is happy/normal operation
    * 0.33 <= status < 0.66  Neutral, there are things going wrong slightly.
    * 0.0  <= status < 0.33  Unhappy, something is very wrong with the monitored modules
    * status = -1            An error occured during module execution
    * status = -2            Data could not be retrieved (download failed etc.)
    
    The category status is calculated with a user specified algorithm from the statuses
    of the modules in the category. If there is missing data or an error, the category
    index icon is changed, too.
    
    In practice, there is no "visual" difference between status -1 and -2, but there might
    be in future.
    """
    
    config_defaults = {
        'description': '',
        'instruction': '',
        'type': 'rated',
        'weight': '1.0',
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
        self.category = None # set by CategoryProxy.getCategroy() after creating specific module instances
        
        if not "type" in self.config:
            self.type = "unrated"
            self.logger.warn("Module type not specified, using 'unrated'")
        else:
            self.type = self.config['type']
        if self.type not in ('rated', 'plots', 'unrated'):
            self.logger.warn("Unknown module type '%s', using 'unrated'" % self.type)
            self.type = "unrated"
            
        if not "weight" in self.config:
            self.weight = 0.0
            self.logger.warn("Module weight not specified, ignore in calculations")
        else:
            try:
                self.weight = float(self.config['weight'])
            except Exception:
                self.logger.warn("Module weight not numeric, using 0.0")
    
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
            icon = 'unhappy' if self.type == 'rated' else 'unavail_plot'
        else:
            if self.type == 'rated':
                if self.dataset['status'] > 0.66:
                    icon = 'happy'
                elif self.dataset['status'] > 0.33:
                    icon = 'neutral'
                else:
                    icon = 'unhappy'
            else:
                icon = 'avail_plot' if self.dataset['status'] > 0.9 else 'unavail_plot'
        return icon
    
    def url(self, only_anchor=True, time=None):
        # something along ?date=2012-03-24&amp;time=17:20&amp;t=batchsys&amp;m=${module.instance_name}
        return ('' if only_anchor else self.category.url(time=time)) + u"#" + self.instance_name
        
    def getStatusIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'), 'mod_'+self.getStatusString()+'.png')
    
    def getNavStatusIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'), 'nav_'+self.getStatusString()+'.png')
        
    def getPlotableColumns(self):
        blacklist = ['id', 'run_id', 'instance', 'description', 'instruction', 'error_string', 'source_url']
        types = [Integer, Float, Numeric]
        def isnumeric(cls):
            for t in types:
                if isinstance(cls,t):
                    return True
            return False
        numerical_cols = filter(lambda x: isnumeric(x.type), self.module_table.columns)
        return [col.name for col in numerical_cols if col.name not in blacklist]
    
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
        