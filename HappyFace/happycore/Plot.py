from GetData import *
from ModuleBase import *
from DownloadTag import *

#############################################
# class to donwload plots (via WGET command)
# self.url has to be defined by the inhereting module
#############################################

class Plot(ModuleBase):
    
    def __init__(self, category, timestamp, archive_dir):
        ModuleBase.__init__(self, category, timestamp, archive_dir)


        # definition of the database table keys and pre-defined values
	self.db_keys['url'] = StringCol()
	self.db_keys['filename'] = StringCol()
	
	self.db_values['url'] = ""
	self.db_values['filename'] = ""

        self.plotTag = 'plot'

        
                
    def run(self):

        # run the test

        if not self.plotTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.plotTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1


        fileType = self.downloadService.getFileType(self.downloadRequest[self.plotTag])

        filenameFullPath = self.archive_dir +"/" + self.__module__+fileType
        success,stderr = self.downloadService.copyFile(self.downloadRequest[self.plotTag],filenameFullPath)
        self.error_message +=stderr
        
	if success == True:
	    self.status = 1.0
	    filename = "archive/" + str(self.timestamp) + "/" + self.__module__+fileType
	else:
	    filename = ""


	# definition fo the database table values
        # self.db_values['url'] = self.url.replace('&','&amp;').replace('%','%%') # the replacement ensures the XHTML validation by W3C / printf() PHP command

	self.db_values['filename'] = filename
	self.db_values['url'] = filename
        
    def output(self):

        # this module_content string will be executed by a printf('') PHP command
        # all information in the database are available via a $data["key"] call
        module_content = """
        <?php
        printf('
        <a href="' .$data["url"]. '"><img alt="" src="' .$data["filename"]. '" style="border: 0px solid;" /></a>
        ');
        ?>
        """
        
        return self.PHPOutput(module_content)
