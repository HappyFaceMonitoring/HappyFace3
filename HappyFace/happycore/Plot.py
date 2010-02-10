from GetData import *
from ModuleBase import *
from DownloadTag import *

#############################################
# class to donwload plots (via WGET command)
# self.url has to be defined by the inhereting module
#############################################

class Plot(ModuleBase):
    
    def __init__(self, module_options):
        ModuleBase.__init__(self, module_options)

        self.plots = {}
        

                
    def run(self):

        # run the test


        self.plotPosition = self.configService.getDefault('setup','position','v')


        for tag in self.downloadRequest.keys():
            if tag.find('plot') == 0:
                self.plots[tag] = tag.replace('plot','')
                


        if len(self.plots) == 0:
            err = 'Error: Could not find download tag(s)\n'
            sys.stdout.write(err)
            self.error_message +=err

        if self.error_message != "":
            sys.stdout.write(self.error_message)
            return -1

        plotsList =  self.plots.keys()
        plotsList.sort()
        for tag in plotsList:
            
            ident = self.plots[tag]

            fileType = self.downloadService.getFileType(self.downloadRequest[tag])

            self.configService.addToParameter('setup','source',tag+": "+self.downloadService.getUrlAsLink(self.downloadRequest[tag])+"<br />")


            filenameFullPath = self.archive_dir +"/" + self.__module__+ident+fileType
            success,stderr = self.downloadService.copyFile(self.downloadRequest[tag],filenameFullPath)
            self.error_message +=stderr
        
            if success == True:
                self.status = 1.0
                filename = "archive/" + str(self.timestamp) + "/" + self.__module__+ident+fileType
            else:
                filename = ""


	# definition fo the database table values
	    self.db_keys['filename'+ident] = StringCol()
            self.db_values['filename'+ident] = filename

        
    def output(self):

        # this module_content string will be executed by a printf('') PHP command
        # all information in the database are available via a $data["key"] call
        mc = []
        plotsList =  self.plots.keys()
        plotsList.sort()
        for tag in plotsList:
            filename = 'filename'+self.plots[tag]
#            url = 'url'+self.plots[tag]
            mc.append("""<a href="' . htmlentities($data["""+filename+"""]) . '">""")
	    mc.append(""" <img alt="" src="' . htmlentities($data["""+filename+"""]) . '" style="border: none;" />""")
	    mc.append(  '</a>')
            if self.plotPosition == 'v':
                mc.append('<br />')
   
	module_content = "<?php printf('" + self.PHPArrayToString(mc) + "'); ?>";
        return self.PHPOutput(module_content)
