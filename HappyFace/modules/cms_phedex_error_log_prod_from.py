import os, sys

from CMSPhedexErrorLog import *

class cms_phedex_error_log_prod_from(CMSPhedexErrorLog):

    def __init__(self,category,timestamp,archive_dir):

        CMSPhedexErrorLog.__init__(self,category,timestamp,archive_dir)