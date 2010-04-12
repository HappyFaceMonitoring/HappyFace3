#from lxml import etree
import lxml.html # for html parsing
import sys

#############################################
# class to parse HTML sources
#############################################
class HTMLParsing():

    # TODO: Error is passed as an exception, therefore remove second return
    # argument.
    # usage of the etree object: http://codespeak.net/lxml/
    def parse_htmlfile_lxml(self, html_file):

        try:
            parser = lxml.html.HTMLParser()
            tree = lxml.html.parse(html_file, parser)
	    return tree,""
        except Exception, ex:
	    raise Exception('Could not parse \"' + html_file + '\" in module ' + self.__module__ + ': ' + str(ex))
