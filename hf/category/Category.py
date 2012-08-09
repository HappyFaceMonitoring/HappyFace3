
import hf, os, traceback
from mako.template import Template
import logging
      
class Category:
    """
    For the meaning of status values, see ModuleBase docstring.
    """
    def __init__(self, category_name, conf, module_list, run):
        self.logger = logging.getLogger(self.__module__+'('+category_name+')')
        self.name = category_name
        self.config = conf
        self.module_list = module_list
        self.run = run
        self.status = -1
        try:
            filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "category.html")
            self.template = Template(filename=filename, lookup=hf.template_lookup)
        except Exception, e:
            self.logger.error("Cannot load category template: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            self.template = None
        try:
            self.algorithm = hf.category.algorithms.worst
            self.algorithm = getattr(hf.category.algorithms, self.config['algorithm'])
        except AttributeError, e:
            self.logger.warn("Status algorithm '%s' not supported, use 'worst'", self.config['algorithm'])
        except KeyError, e:
            self.logger.warn("Status algorithm not specified, use 'worst'")
        
        if not "type" in self.config:
            self.type = "rated"
            self.logger.warn("Category type not specified, using 'rated'")
        else:
            self.type = self.config['type']
        if self.type not in ('rated', 'plots'):
            self.logger.warn("Unknown type '%s', using 'rated'" % self.type)
            self.type = "rated"
            
        self.status = self.algorithm(self)
        
        self.data_missing = False
        min_status = 1.0
        for module in self.module_list:
            if module.dataset is None:
                self.data_missing = True
            elif module.dataset['status'] < 0.0:
                self.data_missing = True
    
    def getStatusIcon(self):
        icon = 'cat_noinfo.png'
        if self.type == 'plots':
            icon = 'cat_avail_plot.png' if self.status > 0.9 else 'cat_unavail_plot.png'
        else:
            if self.status > 0.66:
                icon = 'cat_happy.png'
            elif self.status > 0.33:
                icon = 'cat_neutral.png'
            elif int(self.status) >= 0:
                icon = 'cat_unhappy.png'
            else:
                icon = 'cat_noinfo.png'
        return os.path.join(hf.config.get('paths', 'template_icons_url'), icon)
    
    def getIndexIcon(self):
        return os.path.join(hf.config.get('paths', 'template_icons_url'),
            "index_warn.png" if self.data_missing else "index_ok.png")
        
    def __unicode__(self):
        return self.name
    
    def __str__(self):
        return self.name

    @hf.url.absoluteUrl
    def url(self, time=None):
        url = "/"+self.name
        if time is not None:
            url += "?date=%s&amp;time=%s" % (time.strftime('%Y-%m-%d'), time.strftime('%H:%M'))
        return url
                
    def render(self, template_context):
        module_contents = []
        for module in self.module_list:
            module_name = module.instance_name
            try:
                contents = module.render()
            except Exception, e:
                contents = "Rendering module %s failed" % module_name
                self.logger.error("Rendering module %s failed: %s" % (module_name, str(e)))
                self.logger.debug(traceback.format_exc())
            module_contents.append(contents)
        template_context['category_name'] = self.name
        template_context['category_config'] = self.config
        template_context['category_module_list'] = self.module_list
        template_context['module_contents'] = module_contents
        try:
            return self.template.render(**template_context)
        except Exception, e:
            self.logger.error("Rendering failed: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            raise
