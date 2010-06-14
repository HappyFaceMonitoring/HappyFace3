from xml.dom.minidom import * # for XML parsing
from lxml import etree
import xml.sax # for sequential XML parsing
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

    # Allows for sequential XML parsing using a SAX parser
    # See http://docs.python.org/library/xml.sax.html
    def parse_xmlfile_sax(self, xml_filename_or_stream, handler, error_handler = xml.sax.ErrorHandler()):
        try:
	    xml.sax.parse(xml_filename_or_stream, handler, error_handler)
        except Exception, ex:
	    if isinstance(xml_filename_or_stream, basestring):
	        raise Exception('Could not parse XML file \"' + xml_filename_or_stream + '\": ' + str(ex))
	    else:
	        raise Exception('Could not parse XML file \"' + xml_filename_or_stream.name + '\": ' + str(ex))

