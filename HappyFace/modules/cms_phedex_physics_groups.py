import os, sys

from CMSPhedexPhysicsGroups import *

class cms_phedex_physics_groups(CMSPhedexPhysicsGroups):

    def __init__(self,category,timestamp,archive_dir):

        CMSPhedexPhysicsGroups.__init__(self,category,timestamp,archive_dir)
