import ConfigParser
import sys,os,re



class ConfigService():

    def __init__(self):

        self.configFiles = []
        self.cssFiles = {}

        self.p = re.compile("\.pyc|\.py")


        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str #Needed to enable capital letters




    def addModule(self,name):
        self.configFiles.append(self.p.sub('',sys.modules[name].__file__))




    def readParameter(self):
        for pfile in self.configFiles:
	    self.readConfigFile(pfile)
            

            ## Info for CSS service
	    cssfile =pfile+".css"
            if os.path.isfile(cssfile):
            	self.cssFiles[os.path.basename(cssfile)] = cssfile
                



    def addToParameter(self,sec,par,add):
	currentValue = ""
	try:
		currentValue = self.config.get(sec,par)
	except:
		currentValue = ""

	self.config.set(sec,par,currentValue+add)



    def configMissingParameter(self,sec,par):
        print "Parameter Error!"
        print "The following parameter is not set but required: "+sec+","+par
        print "Possible config files [.cfg,.local]: "+",".join(self.configFiles)
        self.pc()
        sys.exit(-1)



    def get(self,sec,par):
 
        try:
            return self.config.get(sec,par)

        except:
	    self.configMissingParameter(sec,par)


    def getDefault(self,sec,par,default):
        try:
            return self.config.get(sec,par)

        except:
            return default


    def getSection(self,sec):
        parameter = {}
    	if self.config.has_section(sec):
            for i in self.config.items(sec):
                parameter[ i[0] ] = i[1]

        return parameter


    def getCssRequests(self):
        return self.cssFiles


    def getDownloadRequests(self):
       ## Info for Download Service
	downloadRequest = {}
        if self.config.has_section('downloadservice'):
            for i in self.config.items('downloadservice'):
                downloadRequest[i[0]] = i[1]
 
        return downloadRequest



            

    def readConfigFile(self,modulename):
        
        # try to open standard config file, must be available
        try:
	    self.config.readfp(open(modulename + '.cfg'))
        except IOError:
            sys.stdout.write('Could not find configuration file ' + modulename + '.cfg, aborting ...\n')
            sys.exit(-1)

        # try to open local config file if available (standard config settings will be overwritten)
	try:
	    self.config.readfp(open(modulename + '.local'))
        except IOError:
            pass
	


    def pc(self):
        print "Config Files"
        print self.configFiles
        print "Parameter"
        for sec in self.parameter.keys():
            print sec
            for i in self.parameter[sec].keys():
                print " "+i+": "+self.parameter[sec][i]



