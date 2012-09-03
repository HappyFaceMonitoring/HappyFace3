"""
The very core of HappyFace are modules doing the actual work.
All of them derive from :class:`ModuleBase`, and any other

.. data:: config

    A config parser instance with the aggregated data
    from all module configuration files. It is created and populated
    at initialization by :func:`hf.configtools.readConfigurationAndEnv`.
    
    Since this module variable is used by most category related methods,
    it is important to initialize it early.

"""
from module import getColumnFileReference, moduleClassLoaded, \
    importModuleClasses, getModuleClass
from ModuleBase import ModuleBase
from ModuleProxy import ModuleProxy
import database

config = None

__all__ = ["ModuleBase", "ModuleProxy", "database", "config",
    "getColumnFileReference", "moduleClassLoaded",
    "importModuleClasses", "getModuleClass"]

