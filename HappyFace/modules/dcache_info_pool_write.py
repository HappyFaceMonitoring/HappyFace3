import os, sys

from dCacheInfoPool import *

class dcache_info_pool_write(dCacheInfoPool):

    def __init__(self,module_options):

        dCacheInfoPool.__init__(self,module_options)
