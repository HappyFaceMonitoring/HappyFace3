
class ConfigError(Exception):
    pass

class ConsistencyError(Exception):
    pass

class ModuleError(Exception):
    pass

class ModuleRuntimeError(Exception):
    pass

class ModuleProgrammingError(Exception):
    def __init__(self, module, msg):
        self.module = module
        super(ModuleProgrammingError, self).__init__(msg)
    
    def __str__(self):
        return "%s: %s" % (self.module, super(ModuleProgrammingError, self).__str__())