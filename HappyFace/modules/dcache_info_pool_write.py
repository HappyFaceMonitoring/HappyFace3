import os, sys

from dCacheInfoPool import *

class dcache_info_pool_write(dCacheInfoPool):

    def __init__(self,category,timestamp,storage_dir):

        dCacheInfoPool.__init__(self,category,timestamp,storage_dir)
