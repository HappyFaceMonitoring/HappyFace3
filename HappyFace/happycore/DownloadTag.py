from GetData import *
import tempfile
import re
import random
import sys
import os
from threading import Thread


class DownloadTag(Thread):


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
        self.error = "Download not finished in time."

        self.dataFetcher = GetData()
        

    def download(self):
        curIndex = 0
        while curIndex < len(self.program):
	    # Load everything but the final file into a temporary directory
	    dest_dir = self.archive_dir
	    if curIndex < len(self.program) - 1:
	        dest_dir = tempfile.gettempdir()

            if self.program[curIndex] == "wget":
                self.success,self.error = self.dataFetcher.getDataWget(self.args[curIndex] ,self.url[curIndex], dest_dir, self.localFile)
            elif self.program[curIndex] == "wgetXmlRequest":
                self.success,self.error = self.dataFetcher.getDataWgetXmlRequest(self.args[curIndex] ,self.url[curIndex], dest_dir, self.localFile)
            else:
                print "DownloadTag: "+self.program+" currently not supported!"
                self.error = self.program+" currently not supported!"
		break

            content = ''
            if curIndex < len(self.program) - 1:
                f = open(dest_dir + '/' + self.localFile)
		content = f.read()
		f.close()
		os.unlink(dest_dir + '/' + self.localFile)

                # Match regex on site content to create new URL. The regexp
		# must contain a group named "url" (?P<url>[...]) which yields
		# the link to follow for the next download.
		match = re.search(self.url[curIndex+1], content)
		if not match:
		    self.success = False
		    self.error = 'The content of the page at ' + self.url[curIndex] + ' does not match on \"' + self.url[curIndex+1] + '\"'
		    break

                # If url does not include schema, use schema and hostname from
		# previous URL.
		self.url[curIndex+1] = match.group('url')
		if not '://' in self.url[curIndex+1]:
		    hit = self.url[curIndex].find('://')
		    if hit != -1:
		        hit = self.url[curIndex].find('/', hit+3)
			if hit != -1:
			    # Get rid of leading slash if any
			    if self.url[curIndex+1][0] == '/':
			        self.url[curIndex+1] = self.url[curIndex+1][1:]

			    self.url[curIndex+1] = self.url[curIndex][:hit] + '/' + self.url[curIndex+1]

            curIndex += 1

    def run(self):
        self.download()
        self.finished = True

    def getFilePath(self):
        return './'+self.archive_dir+'/'+self.localFile

    def getUrl(self):
        return self.url[-1]
