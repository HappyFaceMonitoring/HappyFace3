from Plot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class MultiPlot(Plot):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
	
