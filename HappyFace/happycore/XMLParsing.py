from xml.dom.minidom import * # for XML parsing
from lxml import etree
import sys

#############################################
# class to parse XML sources
#############################################
class XMLParsing():

    # TODO: Error is passed as an exception, therefore remove second return
    # argument.
    # usage of the dom object: http://docs.python.org/library/xml.dom.minidom.html
    def parse_xmlfile_minidom(self, xml_file):

	try:
	    dom_object = parse(xml_file)
	    return dom_object,""
	except Exception, ex:
	    raise Exception('Could not parse XML file \"' + xml_file + '\": ' + str(ex))

    # TODO: Error is passed as an exception, therefore remove second return
    # argument.
    # usage of the etree object: http://codespeak.net/lxml/
    def parse_xmlfile_lxml(self, xml_file):

        try:
            source_file = open(xml_file)
            tree = etree.parse(source_file)
            return tree,""
        except Exception, ex:
	    raise Exception('Could not parse XML file \"' + xml_file + '\": ' + str(ex))
