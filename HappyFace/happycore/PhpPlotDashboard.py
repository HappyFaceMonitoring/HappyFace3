from PhpPlot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlotDashboard(PhpPlot):

    def __init__(self, category, timestamp, archive_dir):

        PhpPlot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/PhpPlotDashboard')
	self.base_url = config.get('setup','base_url')
        self.getPhpArgs(config)

   
        self.base_url = self.base_url+"/"+self.mod_config.get('setup','base_url_add')

        # read module specific phpArgs from modul config file
        self.getPhpArgs(self.mod_config)

        # Create URL from base_url and phpArgs
        self.makeUrl()

