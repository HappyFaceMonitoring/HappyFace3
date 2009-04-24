from Plot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class SinglePlot(Plot):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/SinglePlot') # empty
	
	self.url = self.mod_config.get('setup','url')