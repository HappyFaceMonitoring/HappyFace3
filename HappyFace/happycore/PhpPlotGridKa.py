from Plot import *
from PhpDownload import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlotGridKa(Plot,PhpDownload):

    def __init__(self, module_options):

        Plot.__init__(self, module_options)
        PhpDownload.__init__(self)

        self.downloadRequest['plot'] = 'wget|'+self.makeUrl()
