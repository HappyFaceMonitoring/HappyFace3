
import ConfigParser
import os, hf, cherrypy, traceback
from mako.lookup import TemplateLookup

def _getCfgInDirectory(dir):
    return sorted(filter(lambda x: x.lower().endswith(".cfg") and os.path.isfile(x), map(lambda x:os.path.join(dir,x), os.listdir(dir))))

def readConfiguration():
    '''
    Read configuration files for HappyFace from defaultconf directory and subsequently from
    the local HappyFace config directory. The HappyFace config is then accessible by hf.config
    
    Also, read category and module config in hf.category.config and hf.module.config and create
    a template lookup object in hf.template_lookup with the appropriate paths from the configuration.
    '''
    defaults = {}
    
    hf.config = ConfigParser.ConfigParser(defaults=defaults)
    for file in _getCfgInDirectory(os.path.join(hf.hf_dir, "defaultconfig")):
        print file
        try:
            hf.config.read(file)
        except Exception, e:
            # TODO logging
            traceback.print_exc()
    for file in _getCfgInDirectory(os.path.join(hf.hf_dir, hf.config.get("paths", "local_happyface_cfg_dir"))):
        try:
            hf.config.read(file)
        except Exception, e:
            # TODO logging
            traceback.print_exc()
    
    directories = [hf.config.get("paths", "hf_template_dir"), hf.config.get("paths", "module_template_dir")]
    directories = map(lambda x: os.path.join(hf.hf_dir, x), directories)
    hf.template_lookup = TemplateLookup(directories=directories, module_directory=hf.config.get("paths", "template_cache_dir"))
    
    hf.category.config = ConfigParser.ConfigParser()
    for dirpath, dirnames, filenames in os.walk(hf.config.get("paths", "category_cfg_dir")):
        for filename in filenames:
            if filename.endswith(".cfg"):
                hf.category.config.read(os.path.join(dirpath, filename))
                cherrypy.engine.autoreload.files.add(os.path.join(dirpath, filename))
    
    hf.module.config = ConfigParser.ConfigParser(defaults=hf.module.ModuleBase.config_defaults)
    for dirpath, dirnames, filenames in os.walk(hf.config.get("paths", "module_cfg_dir")):
        for filename in filenames:
            if filename.endswith(".cfg"):
                hf.module.config.read(os.path.join(dirpath, filename))
                cherrypy.engine.autoreload.files.add(os.path.join(dirpath, filename))

def importModules():
    '''
    
    '''
    used_modules = []
    for category in hf.category.config.sections():
        conf = dict(hf.category.config.items(category))
        for module in conf["modules"].split(","):
            if len(module) == 0: continue
            if module in used_modules:
                raise hf.ConfigError("Module '%s' used second time in category '%s'" % (module, category))
            try:
                hf.module.tryModuleClassImport(hf.module.config.get(module, "module"))
            except ConfigParser.NoSectionError, e:
                raise hf.ConfigError("Referenced module %s from category %s was never configured" % (module, category))
