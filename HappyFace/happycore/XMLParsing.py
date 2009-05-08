from xml.dom.minidom import * # for XML parsing


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
