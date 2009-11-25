from GetData import *
import random
import sys
import os
from time import time, localtime, mktime
from DownloadTag import *

class DownloadService(object):

    def __init__(self, subdir):
        self.subdir = subdir
        self.downloadTags = {}
        
        if not os.path.exists(subdir):
            os.mkdir(subdir)



    def add(self, downloadstring):

        tmpString = downloadstring.split(":")
        if len(tmpString) < 3:
            print "DownloadService: "+downloadstring+" does not match format prog:type:args"
            return -1

        prog = tmpString.pop(0)
        filetype = tmpString.pop(0)
        args = ":".join(tmpString)

        if not downloadstring in self.downloadTags:
            self.downloadTags[downloadstring] = DownloadTag(prog,filetype,args,self.subdir)
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
            os.remove(self.downloadTags[i].getFilePath())
            

    def getFileType(self,downloadstring):
        if downloadstring in self.downloadTags:
            fileType =  self.downloadTags[downloadstring].fileType
            if fileType == "":
                return fileType
            else:
                return "."+fileType


    def getFile(self,downloadstring):
        success,error = self.checkDownload(downloadstring)
        if success:
            return error,self.downloadTags[downloadstring].getFilePath()
        else:
            return error,""

    def getUrl(self,downloadstring):
        return self.downloadTags[downloadstring].getUrl()

    def getUrlAsLink(self,downloadstring):
        url = self.downloadTags[downloadstring].getUrl()
        return '<a href="'+url+'">'+url+'<a/>'



    def copyFile(self,downloadstring,destfile):
        success,error = self.checkDownload(downloadstring)
        if success:
            localFile = self.downloadTags[downloadstring].getFilePath()
            ret = os.system('cp '+localFile+' '+destfile)
            return True,""
        else:
            return success,error


    def checkDownload(self,downloadstring):
        success = True
        error = ""
        if downloadstring in self.downloadTags:
            if not self.downloadTags[downloadstring].finished:
                success = False
                error = "Download has not finished in time."
                
            elif not self.downloadTags[downloadstring].success:
                success = False
                error = "Download failed."
            
        else:
            success = False
            error = "Tag \'"+downloadstring+"\' not found."

        return success,error
