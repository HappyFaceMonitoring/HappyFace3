from Category import Category
from CategoryProxy import CategoryProxy

import hf

config = None

def createCategoryObjects():
    '''
    '''
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
        category_list.append(hf.category.CategoryProxy(category, conf, module_conf))
    return category_list
