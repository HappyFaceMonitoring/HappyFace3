from xml.dom.minidom import * # for XML parsing

from ModuleBase import *

#############################################
# class to parse XML sources
#############################################
class XMLParsing(ModuleBase):

    def __init__(self, category, timestamp, archive_dir,):
        ModuleBase.__init__(self, category, timestamp, archive_dir)

	# read class config file
        config = self.readConfigFile('./happycore/XMLParsing') # empty


    def parse_xmlfile_minidom(self,xml_file):

	try:
	    dom_object = parse(xml_file)
	except:
            self.error_message += '\nCould not parse ' + xml_file + ', ' + self.__module__ + ' aborting ...\n'
            sys.stdout.write(self.error_message)
            dom_object = ""

	# usage of the dom object: http://docs.python.org/library/xml.dom.minidom.html
	return dom_object
