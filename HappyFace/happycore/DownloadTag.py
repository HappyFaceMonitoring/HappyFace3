from GetData import *
import random
import sys
import os
from threading import Thread


class DownloadTag(Thread):


    def __init__(self,program,fileType,url,subdir):
        Thread.__init__(self)
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
        if self.program == "wget":
            self.success,self.error = self.dataFetcher.getDataWget(self.url, self.archive_dir, self.localFile)
        elif self.program == "wgetXmlRequest":
            self.success,self.error = self.dataFetcher.getDataWgetXmlRequest(self.url, self.archive_dir, self.localFile)
        else:
            print "DownloadTag: "+self.program+" currently not supported!"



    def run(self):
        self.download()
        self.finished = True

    def getFilePath(self):
        return './'+self.archive_dir+'/'+self.localFile
