from GetData import *
import tempfile
import re
import random
import sys
import os
from threading import Thread


class DownloadTag(Thread):

    class MatchFailedError(Exception):
        def __init__(self, url, regexp, content):
	    self.url = url
	    self.regexp = regexp
	    # Store content so the error handler can do stuff depending on the
	    # download content.
	    self.content = content
	def __str__(self):
            return 'The content of the page at \"' + self.url + '\" does not match on \"' + self.regexp + '\"'


    def __init__(self,program,fileType, args, url,subdir):
        Thread.__init__(self)
        self.args = args
        self.url = url
        self.program = program
        self.fileType = fileType
        self.localFile = str(random.randint(1,100000000000000))+".download"
        self.archive_dir = subdir

        self.success = False
        self.finished = False
        self.error = None
        self.curIndex = 0
	self.keep = False

        self.dataFetcher = GetData()

    def setKeep(self):
        self.keep = True
    def getKeep(self):
        return self.keep

    def download(self):
        while self.curIndex < len(self.program):
	    # Load everything but the final file into a temporary directory
	    dest_dir = self.archive_dir
	    if self.curIndex < len(self.program) - 1:
	        dest_dir = tempfile.gettempdir()

            if self.program[self.curIndex] == "local":
	        self.dataFetcher.getDataLocal(self.args[self.curIndex], self.url[self.curIndex], dest_dir, self.localFile)
            elif self.program[self.curIndex] == "wget":
                self.dataFetcher.getDataWget(self.args[self.curIndex] ,self.url[self.curIndex], dest_dir, self.localFile)
            elif self.program[self.curIndex] == "wgetXmlRequest":
                self.dataFetcher.getDataWgetXmlRequest(self.args[self.curIndex] ,self.url[self.curIndex], dest_dir, self.localFile)
            else:
	        raise Exception(self.program+" currently not supported!")

            content = ''
            if self.curIndex < len(self.program) - 1:
                f = open(dest_dir + '/' + self.localFile)
		content = f.read()
		f.close()
		os.unlink(dest_dir + '/' + self.localFile)

                # Match regex on site content to create new URL. The regexp
		# must contain a group named "url" (?P<url>[...]) which yields
		# the link to follow for the next download.
		match = re.search(self.url[self.curIndex+1], content)
		if not match:
		    raise DownloadTag.MatchFailedError(self.url[self.curIndex], self.url[self.curIndex+1], content)

                # If url does not include schema, use schema and hostname from
		# previous URL.
		self.url[self.curIndex+1] = match.group('url')
		if not '://' in self.url[self.curIndex+1]:
		    hit = self.url[self.curIndex].find('://')
		    if hit != -1:
		        hit = self.url[self.curIndex].find('/', hit+3)
			if hit != -1:
			    # Get rid of leading slash if any
			    if self.url[self.curIndex+1][0] == '/':
			        self.url[self.curIndex+1] = self.url[self.curIndex+1][1:]

			    self.url[self.curIndex+1] = self.url[self.curIndex][:hit] + '/' + self.url[self.curIndex+1]

            self.curIndex += 1

    def run(self):
        try:
            self.download()
	    self.success = True
	except Exception, ex:
	    self.success = False
	    # Store exception, will be rethrown in main thread when trying
	    # to access downloaded data, also see DownloadService.
	    self.error = ex
        self.finished = True

    def getFilePath(self):
        return os.path.join(self.archive_dir, self.localFile)

    def getUrl(self):
        # Final URL has not yet been resolved, maybe because the regex did not match
        if self.curIndex < len(self.url)-1:
	    return None

        return self.url[-1]
