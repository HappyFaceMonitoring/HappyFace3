import rss.feedparser

#############################################
# class to parse news feeds
#############################################
class RSSParsing():

    # usage of the returned object: http://www.feedparser.org/
    def parse_rssfile_feedparser(self, rss_file):

	try:
	    return rss.feedparser.parse(rss_file)
	except Exception, ex:
	    raise Exception('Could not parse \"' + rss_file + '\" in module ' + self.__module__ + ': ' + str(ex))
