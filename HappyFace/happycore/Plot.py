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
        

                
    def process(self):

        # run the test


        self.plotPosition = self.configService.getDefault('setup','position','v')


        for tag in self.downloadRequest.keys():
            if tag.find('plot') == 0:
                self.plots[tag] = tag.replace('plot','')

        if len(self.plots) == 0:
	    raise Exception('Could not find download tag(s)')

        plotsList =  self.plots.keys()
        plotsList.sort()
        for tag in plotsList:
            
            ident = self.plots[tag]

            fileType = self.downloadService.getFileType(self.downloadRequest[tag])

            self.configService.addToParameter('setup','source',tag+": "+self.downloadService.getUrlAsLink(self.downloadRequest[tag])+"<br />")


	    try:
	        filenameFullPath = self.archive_dir +"/" + self.__module__+ident+fileType
                self.downloadService.copyFile(self.downloadRequest[tag],filenameFullPath)
                self.status = 1.0
                filename = self.__module__+ident+fileType
	    except Exception, ex:
                self.error_message += str(ex).strip() + "\n"
		filename = ""

	# definition fo the database table values
	    self.db_keys['filename'+ident] = StringCol()
            self.db_values['filename'+ident] = filename

        
    def output(self):

        # this module_content string will be executed by a print('') PHP command
        # all information in the database are available via a $data["key"] call
        mc = []
        plotsList =  self.plots.keys()
        plotsList.sort()
        for tag in plotsList:
            filename = 'filename'+self.plots[tag]
#            url = 'url'+self.plots[tag]
            mc.append("""<a href="' . $archive_dir . '/' . htmlentities($data["""+filename+"""]) . '">""")
	    mc.append(""" <img alt="" src="' . $archive_dir . '/' . htmlentities($data["""+filename+"""]) . '" style="border: none;" />""")
	    mc.append(  '</a>')
            if self.plotPosition == 'v':
                mc.append('<br />')

	module_content = """<?php

	$tm = localtime($data['timestamp']);
	$year = $tm[5] + 1900; // PHP gives year since 1900
	$month = sprintf('%02d', $tm[4] + 1); // PHP uses 0-11, Python uses 1-12
	$day = sprintf('%02d', $tm[3]);
	$archive_dir = "archive/$year/$month/$day/" . $data['timestamp'];

	// Assume old format if archive_dir does not exist
	if(!file_exists($archive_dir))
		$archive_dir = '.';

	print('""" + self.PHPArrayToString(mc) + """');

	?>""";

        return self.PHPOutput(module_content)
