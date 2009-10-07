import os, sys

from CMSSiteReadiness import * 

class cms_site_readiness(CMSSiteReadiness):

    def __init__(self,category,timestamp,archive_dir):

        CMSSiteReadiness.__init__(self,category,timestamp,archive_dir)
