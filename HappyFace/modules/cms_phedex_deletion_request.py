import os, sys

from CMSPhedexDeletionRequest import * 

class cms_phedex_deletion_request(CMSPhedexDeletionRequest):

    def __init__(self,category,timestamp,archive_dir):

        CMSPhedexDeletionRequest.__init__(self,category,timestamp,archive_dir)
