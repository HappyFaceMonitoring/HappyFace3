from Plot import *
from PhpDownload import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlotDashboard(Plot,PhpDownload):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
        PhpDownload.__init__(self)
   
        self.base_url = self.base_url+"/"+self.configService.get('setup','base_url_add')

        self.downloadRequest['plot'] = 'wget:'+self.makeUrl()

