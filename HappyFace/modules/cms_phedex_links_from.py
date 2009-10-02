import os, sys

from CMSPhedexLinks import * 

class cms_phedex_links_from(CMSPhedexLinks):

    def __init__(self,category,timestamp,archive_dir):

        CMSPhedexLinks.__init__(self,category,timestamp,archive_dir)
