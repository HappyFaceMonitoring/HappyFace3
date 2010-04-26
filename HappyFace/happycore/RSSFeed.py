from ModuleBase import *
from DownloadTag import *
from RSSParsing import *

import time
import calendar
from datetime import datetime

class RSSFeed(ModuleBase):

    def __init__(self, module_options):
	ModuleBase.__init__(self, module_options)

	# definition of the database table keys and pre-defined values
	self.db_keys["title"] = UnicodeCol()
	self.db_keys["link"] = StringCol()
	self.db_keys["rssfeed_database"] = StringCol()
	self.db_values["title"] = ""
	self.db_values["link"] = ""
	self.db_values["rssfeed_database"] = ""

        self.n_entries = int(self.configService.getDefault('setup', 'n_entries', '-1'))
	self.n_days   = int(self.configService.getDefault('setup', 'n_days', '-1'))
	self.hide_feed_title = int(self.configService.getDefault('setup', 'hide_feed_title', 0))

        self.dsTag = 'feed'

    def process(self):

	rssfeed_db_keys = {}
	rssfeed_db_values = {}

	rssfeed_db_keys["author"] = UnicodeCol()
	rssfeed_db_keys["title"] = UnicodeCol()
	rssfeed_db_keys["link"] = StringCol()
	rssfeed_db_keys["updated"] = IntCol()
	rssfeed_db_keys["content"] = UnicodeCol()

        dl_error,feedFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	feed = RSSParsing().parse_rssfile_feedparser(feedFile)
#	print str(feed.entries)

	self.db_values["title"] = feed.feed.title
	self.db_values["link"] = feed.feed.link
	self.db_values["rssfeed_database"] = self.__module__ + "_table_feed"

	self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))

	subtable_feed = self.table_init(self.db_values["rssfeed_database"], rssfeed_db_keys)

	# Sort entries by pubDate
	feed.entries.sort(lambda x,y: cmp(y.updated_parsed,x.updated_parsed))
	# Get entries
	entries = 0
	for entry in feed.entries:
	    # Skip this entry if updated more than n_days ago
	    if self.n_days != -1:
	        delta_t = datetime.today() - datetime.fromtimestamp(time.mktime(entry.updated_parsed))
		if delta_t.days > self.n_days:
		    continue

	    rssfeed_db_values["author"] = ''
	    if 'author_detail' in entry:
	        rssfeed_db_values["author"] = entry.author_detail.name
	    rssfeed_db_values["title"] = entry.title
	    rssfeed_db_values["link"] = entry.link
	    rssfeed_db_values["updated"] = calendar.timegm(entry.updated_parsed)

	    rssfeed_db_values["content"] = ''
            if 'summary' in entry:
	        rssfeed_db_values["content"] = entry.summary
	    if 'content' in entry:
	        for content in entry.content:
	            rssfeed_db_values["content"] += content.value

            self.table_fill(subtable_feed, rssfeed_db_values)

	    # Stop after having recorded n_entries entries
            entries += 1
	    if self.n_entries != -1 and entries >= self.n_entries:
	        break

	self.status = 1.0

    def output(self):

	mc_begin = []
	if not self.hide_feed_title:
		mc_begin.append("""<h4><a href="' . $data['link'] . '">' . iconv('UTF-8', 'ISO-8859-1//TRANSLIT//IGNORE', $data['title']) . '</a></h4>""")
	mc_none = []
	mc_none.append('<h4>No feed entries available at this time</h4>')

	mc_entry = []
	mc_entry.append(  '<div class="RSSFeedEntry">')
	mc_entry.append(""" <p><span class="RSSFeedEntryTitle"><a href="' . $entry['link'] . '">' . iconv('UTF-8', 'ISO-8859-1//TRANSLIT//IGNORE', $entry['title']) . '</a></span><br />""")
	mc_entry.append(""" <span class="RSSFeedEntryDate">Posted ' . (($entry['author'] != '') ? 'by <strong>' . iconv('UTF-8', 'ISO-8859-1//TRANSLIT//IGNORE', $entry['author']) . '</strong> ' : '') . 'on <strong>' . date('r', $entry['updated']) . '</strong></span></p>""")
	mc_entry.append(  " ' . iconv('UTF-8', 'ISO-8859-1//TRANSLIT//IGNORE', $entry['content']) . '")
	mc_entry.append(  '</div>')

	module_content = """<?php

	$summary_db_sqlquery = "SELECT * FROM " . $data["rssfeed_database"] . " WHERE timestamp = " . $data["timestamp"];

	print('""" + self.PHPArrayToString(mc_begin) + """');

	$count = 0;
	foreach($dbh->query($summary_db_sqlquery) as $entry)
	{
	    print('""" + self.PHPArrayToString(mc_entry) + """');
	    ++$count;
	}

	if(!$count)
		print('""" + self.PHPArrayToString(mc_none) + """');

	?>"""

	return self.PHPOutput(module_content)
