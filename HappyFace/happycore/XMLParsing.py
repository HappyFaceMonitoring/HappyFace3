from xml.dom.minidom import * # for XML parsing
from lxml import etree
import lxml.html # for html parsing
import sys

#############################################
# class to parse XML sources
#############################################
class XMLParsing():

    def parse_xmlfile_minidom(self,xml_file):

        error_message = ""
	try:
	    dom_object = parse(xml_file)
	except Exception as ex:
            error_message = '\nCould not parse ' + xml_file + ', ' + self.__module__ + ': ' + str(ex) + '\nAborting ...\n'
            sys.stdout.write(error_message)
            dom_object = ""

	# usage of the dom object: http://docs.python.org/library/xml.dom.minidom.html
	return dom_object,error_message


    def parse_xmlfile_lxml(self,file,option='xml'):

        error_message = ""
        if option == 'xml':
            try:
                source_file = open(file)
                tree = etree.parse(source_file)

            except Exception as ex:
                error_message = '\nCould not parse ' + file + ', ' + self.__module__ + ': ' + str(ex) + '\nAborting ...\n'
                sys.stdout.write(error_message)
                tree = ""

        elif option == 'html' :
            try:
                parser = lxml.html.HTMLParser()
                tree = lxml.html.parse(file,parser)
                #tree = lxml.html.fromstring(file)
            except Exception as ex:
                error_message = '\nCould not parse ' + file + ', ' + self.__module__ + ': ' + str(ex) + '\nAborting ...\n'
                sys.stdout.write(error_message)
                tree = ""
        else:
            error_message = '\nParsing option unknown in module ' + self.__module__ + ', aborting ...\n '
            tree = ""
                
        # usage of the etree object: http://codespeak.net/lxml/
        return tree,error_message
            
