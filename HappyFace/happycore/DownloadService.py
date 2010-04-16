from GetData import *
import random
import sys
import os
from time import time, localtime, mktime
from DownloadTag import *
from HTMLOutput import *

class DownloadService(HTMLOutput):

    def __init__(self, subdir):
        HTMLOutput.__init__(self)

        self.subdir = subdir
        self.downloadTags = {}

        if not os.path.exists(subdir):
            os.mkdir(subdir)



    def add(self, downloadstring):

        tmpString = downloadstring.split("|")
        if len(tmpString) == 0 or len(tmpString) % 4 != 0:
            print "DownloadService: "+downloadstring+" does not match format prog|type|args|url|[...]"
            return -1

        prog = tmpString[0::4]
	filetype = tmpString[1::4]
	args = tmpString[2::4]
	url = tmpString[3::4]

        if not downloadstring in self.downloadTags:
            self.downloadTags[downloadstring] = DownloadTag(prog,filetype,args,url,self.subdir)
#            print "DownloadService: adding "+downloadstring
        else:
            print "DownloadService: Tag already scheduled for download."
            print "    "+downloadstring
        

    def download(self,timeout):
        print "DownloadService: Start file download:"
        resttime = timeout
        print "DownloadService: Download tags:"
        counter = 0
        for i in self.downloadTags.keys():
            counter+= 1
            print "  "+str(counter)+" "+i
            self.downloadTags[i].start()
        for i in self.downloadTags.keys():
	    if resttime == -1:
	        self.downloadTags[i].join()
		continue
		
            start = int(time())
            self.downloadTags[i].join(resttime)
            resttime -= int(time()) - start
	    if resttime < 1:
		break

        for i in self.downloadTags.keys():
            if self.downloadTags[i].isAlive() == True:
                self.downloadTags[i]._Thread__stop()
                print "DownloadService: Download not finished after "+str(timeout)+"s: "+i

        print "DownloadService: Download finished."


    def clean(self):
        if len(self.downloadTags.keys()) > 0:
            print "DownloadService: deleting tmp files"
        for i in self.downloadTags.keys():
	    try:
                os.remove(self.downloadTags[i].getFilePath())
	    except:
	        # Ignore errors here, for example the file might not be
		# present if the Download failed
	        pass

    def getFileType(self,downloadstring):
        if downloadstring in self.downloadTags:
            fileType =  self.downloadTags[downloadstring].fileType[-1]
            if fileType == "":
                return fileType
            else:
                return "."+fileType

    # TODO: Error is passed as an exception, therefore remove first return
    # argument.
    def getFile(self,downloadstring):
        self.checkDownload(downloadstring)
        return "",self.downloadTags[downloadstring].getFilePath()

    def getUrl(self,downloadstring):
        return self.downloadTags[downloadstring].getUrl()

    def getUrlAsLink(self,downloadstring):
        url = self.downloadTags[downloadstring].getUrl()
        return '<a href="' + self.EscapeHTMLEntities(url) + '">' + self.EscapeHTMLEntities(url) + '</a>'



    def copyFile(self,downloadstring,destfile):
        self.checkDownload(downloadstring)
        localFile = self.downloadTags[downloadstring].getFilePath()
	# TODO: Use python file copy function instead
        ret = os.system('cp '+localFile+' '+destfile)

    def checkDownload(self,downloadstring):
        if downloadstring in self.downloadTags:
            if not self.downloadTags[downloadstring].finished:
	        raise Exception('Download has not finished in time.')
            elif not self.downloadTags[downloadstring].success:
	        raise Exception('Download failed.')

        else:
            raise Exception("Tag '"+downloadstring+"' not found.")
