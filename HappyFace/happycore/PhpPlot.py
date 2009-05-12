from Plot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlot(Plot):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/PhpPlot') #empty

        
        self.base_url = ""
        self.phpArgs = {}
        self.fileType = ""

        if config.has_option('setup','fileextension'):
            self.fileType = config.get('setup','fileextension')
            
        

    def getPhpArgs(self, config):
        for i in config.items('phpArgs'):
            self.phpArgs[i[0]] = i[1]


    def makeUrl(self):
        if len(self.phpArgs) == 0:
            print "PhpPlot Error: makeUrl called without phpArgs"
            sys.exit()
        if self.base_url == "":
            print "PhpPlot Error: makeUrl called without base_url"
            sys.exit()

            
        argList = []
        for i in self.phpArgs:
            argList.append(i+'='+self.phpArgs[i])

        argList.sort()
        self.downloadRequest['plot'] = 'wget:'+self.fileType+':'+self.base_url+"?"+"&".join(argList)

