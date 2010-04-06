from lxml import etree
import lxml.html # for html parsing
import sys

#############################################
# class to parse HTML sources
#############################################
class HTMLParsing():

    def parse_htmlfile_lxml(self,file):

        error_message = ""
        try:
            parser = lxml.html.HTMLParser()
            tree = lxml.html.parse(file,parser)
            #tree = lxml.html.fromstring(file)
        except Exception, ex:
            error_message = '\nCould not parse ' + file + ', ' + self.__module__ + ': ' + str(ex) + '\nAborting ...\n'
            sys.stdout.write(error_message)
            tree = ""

        # usage of the etree object: http://codespeak.net/lxml/
        return tree,error_message
            
