import os, sys

from CMSPhedexBlockReplicas import *

class cms_phedex_block_replicas_prod(CMSPhedexBlockReplicas):

    def __init__(self,category,timestamp,archive_dir):

        CMSPhedexBlockReplicas.__init__(self,category,timestamp,archive_dir)
