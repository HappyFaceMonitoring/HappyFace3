import sys
import os
import filecmp


class CssService():

    def __init__(self, webDir, subDir):
        self.webDir = webDir
        self.subDir = subDir
        self.dirPath = self.webDir+"/"+self.subDir

        self.cssFiles = {}

        if not os.path.exists(self.dirPath): os.mkdir(self.dirPath)


    def add(self,css):
        for i in css.keys():
            print "CssService: Adding css file"
            print "    "+css[i]
            self.cssFiles[i] = css[i]

        

    def syncCssFiles(self):
        removalList = self.getFileListeRemove()
        for i in self.getFileListeRemove():
            print "CssService: Removing file from css web dir"
            print "    "+i
            os.system('rm -f '+i)
        for i in self.getFileListCopy():
            print "CssService: Adding file to css web dir"
            print "    "+i
            os.system('cp -f '+i+' '+self.dirPath)

    def getFileListeRemove(self):
        removalList = []
        for theFile in os.listdir(self.dirPath):
            if theFile == '.svn':continue
            if not theFile in self.cssFiles: removalList.append(self.dirPath+'/'+theFile)
        return removalList

        

    def getFileListCopy(self):
        cpList = []
        existingFiles = os.listdir(self.dirPath)
        for theFile in self.cssFiles.keys():
            if existingFiles.count(theFile) == 0:
                cpList.append(self.cssFiles[theFile])
            else:
                if self.hasChanged(self.cssFiles[theFile],self.dirPath+"/"+theFile):
                    cpList.append(self.cssFiles[theFile])
        return cpList


    def hasChanged(self,file1,file2):
        if open(file1).read() == open(file2).read():
            return False
        
        else:
            return True
        
    def getCssWebDirFiles(self):
        theList = []
        for i in self.cssFiles.keys():
            theList.append(self.subDir+"/"+i)
        return theList
