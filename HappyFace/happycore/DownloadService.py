from GetData import *
import random
import sys
import os
from time import time, localtime, mktime
from DownloadTag import *



#############################################
# class to donwload plots (via WGET command)
# self.url has to be defined by the inhereting module
#############################################
class DownloadService():

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
        else:
            print "DownloadService: Tag already scheduled for download."
            print "    "+downloadstring
        

    def download(self,timeout):
        resttime = timeout
        for i in self.downloadTags.keys():
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

        


    def clean(self):
        if len(self.downloadTags.keys()) > 0:
            print "DownloadService: deleting tmp files"
        for i in self.downloadTags.keys():
            os.remove(self.downloadTags[i].getFilePath())
            
    def getFile(self,downloadstring):
        if downloadstring in self.downloadTags:
            return self.downloadTags[downloadstring].success,self.downloadTags[downloadstring].getFilePath()
        else:
            return False,""

    def getFileType(self,downloadstring):
        if downloadstring in self.downloadTags:
            fileType =  self.downloadTags[downloadstring].fileType
            if fileType == "":
                return fileType
            else:
                return "."+fileType


    def copyFile(self,downloadstring,destfile):
        if downloadstring in self.downloadTags:
            if self.downloadTags[downloadstring].success:
                localFile = self.downloadTags[downloadstring].getFilePath()
                ret = os.system('cp '+localFile+' '+destfile)
                return True,""
            else:
                return False,"Download failed for \'"+downloadstring+"\'."
                

        else:
            return False,"Tag \'"+downloadstring+"\' not found."


