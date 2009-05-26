from xml.dom.minidom import * # for XML parsing
from lxml import etree


#############################################
# class to parse XML sources
#############################################
class XMLParsing():

    def parse_xmlfile_minidom(self,xml_file):

	try:
	    dom_object = parse(xml_file)
	except:
            self.error_message += '\nCould not parse ' + xml_file + ', ' + self.__module__ + ' aborting ...\n'
            sys.stdout.write(self.error_message)
            dom_object = ""

	# usage of the dom object: http://docs.python.org/library/xml.dom.minidom.html
	return dom_object


    def parse_xmlfile_lxml(self,xml_file):

	try:
	    source_file = open(xml_file)
	    tree = etree.parse(source_file)
	except:
            self.error_message += '\nCould not parse ' + xml_file + ', ' + self.__module__ + ' aborting ...\n'
            sys.stdout.write(self.error_message)
            tree = ""

	# usage of the etree object: http://codespeak.net/lxml/
	return tree
