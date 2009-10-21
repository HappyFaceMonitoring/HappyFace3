from Plot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class SinglePlot(Plot):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
	
        self.singlePlotTag = 'plot'
        configDownloadRequests = self.configService.getDownloadRequests()
        if not configDownloadRequests.has_key('plot'):
            err = 'Error in '+ self.__module__+': Could not find download tag plot.\n'
            sys.stdout.write(err)
            self.error_message +=err

        elif len(configDownloadRequests) > 1:
            err = 'Error '+ self.__module__+': Found more than 1 download for SinglePlot.\n'
            sys.stdout.write(err)
            self.error_message +=err

