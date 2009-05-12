from PhpPlot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlotGridKa(PhpPlot):

    def __init__(self, category, timestamp, archive_dir):

        PhpPlot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/PhpPlotGridKa')
	self.base_url = config.get('setup','base_url')

        if config.has_option('setup','fileextension'):
            self.fileType = config.get('setup','fileextension')

        self.getPhpArgs(config)



        # read module specific phpArgs from modul config file
        self.getPhpArgs(self.mod_config)

        # Create URL from base_url and phpArgs
        self.makeUrl()

