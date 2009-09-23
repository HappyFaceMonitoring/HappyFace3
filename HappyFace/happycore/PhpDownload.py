import sys

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpDownload():

    def __init__(self):

        self.fileType = self.configService.get('setup','fileextension')
        self.phpArgs =  self.configService.getSection('phpArgs')
        self.base_url = self.configService.get('setup','base_url')
	## if last char of url is "/", remove it
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]


	

    def getPhpArgs(self, config):
        print "Warning - Do not use the function getPhpArgs."
#        self.phpArgs = self.configService.getSection('phpArgs')
#        for i in config.items('phpArgs'):
#            self.phpArgs[i[0]] = i[1]


    def makeUrl(self):
        if len(self.phpArgs) == 0:
            print "PhpPlot Error: makeUrl called without phpArgs"
            sys.exit()
        if self.base_url == "":
            print "PhpPlot Error: makeUrl called without base_url"
            sys.exit()

	## if last char of url is "/", remove it
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]


            
        argList = []
#        for i in self.phpArgs:
#            argList.append(i+'='+self.phpArgs[i])

        # expand multiple arguments of php args
        # test = 1,5,7 --> test1,test5,test7
        for i in self.phpArgs:
	    for j in self.phpArgs[i].split(","):
		argList.append(i+'='+j)



        argList.sort()
        downloadString = self.fileType+':'+self.base_url+"?"+"&".join(argList)

        return downloadString

#        self.downloadRequest['plot'] = 'wget:'+self.fileType+':'+self.base_url+"?"+"&".join(argList)


  # add plot/wgetXmlRequest/... to function list
  #argList.sort()
  #      self.downloadRequest[self.dsTag] = 'wgetXmlRequest:'+self.fileType+':'+self.base_url+"?"+"&".join(argList)
