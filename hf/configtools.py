
import ConfigParser
import os, hf, cherrypy, traceback

def _getCfgInDirectory(dir):
    return sorted(filter(lambda x: x.lower().endswith(".cfg") and os.path.isfile(x), map(lambda x:os.path.join(dir,x), os.listdir(dir))))

def readConfiguration():
    defaults = {}
    
    hf.config = ConfigParser.ConfigParser(defaults=defaults, allow_no_value=True)
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
    
    hf.category.config = ConfigParser.ConfigParser(allow_no_value=True)
    for dirpath, dirnames, filenames in os.walk(hf.config.get("paths", "category_cfg_dir")):
        for filename in filenames:
            if filename.endswith(".cfg"):
                hf.category.config.read(os.path.join(dirpath, filename))
                cherrypy.engine.autoreload.files.add(os.path.join(dirpath, filename))
    
    hf.module.config = ConfigParser.ConfigParser(allow_no_value=True)
    for dirpath, dirnames, filenames in os.walk(hf.config.get("paths", "module_cfg_dir")):
        for filename in filenames:
            if filename.endswith(".cfg"):
                hf.module.config.read(os.path.join(dirpath, filename))
                cherrypy.engine.autoreload.files.add(os.path.join(dirpath, filename))

def importModules():
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

def createCategoryObjects():
    category_list = []
    used_modules = []
    for category in hf.category.config.sections():
        conf = dict(hf.category.config.items(category))
        module_conf = {}
        for module in conf["modules"].split(","):
            if len(module) == 0: continue
            if module in used_modules:
                raise hf.ConfigError("Module '%s' used second time in category '%s'" % (module, category))
            module_conf[module] = dict(hf.module.config.items(module))
            used_modules.append(module)
        category_list.append(hf.category.Category(conf, module_conf))
    return category_list