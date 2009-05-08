import subprocess # for traping errors of subprocesses like WGET
import sys


#############################################
# class to donwload external data
#############################################
class GetData():

    # execute the WGET command to load and store an imagefile and return the stored filename (with relative path)
    def getDataWget(self, url, path, file):

        retcode = subprocess.call(["wget","-q","--output-document=" + path + "/"  + file, url])
        success = False
        stderr = ""

        if retcode == 0:
            success =  True
            stderr = ""

        else:
#            self.error_message += '\nCould not download ' + self.url + ', ' + self.__module__ + ' abborting ...\n'
#            sys.stdout.write(self.error_message)
            stderr = '\nCould not download ' + url + ', ' +path+' , '+path + ' abborting ...\n'
            sys.stdout.write(stderr)
            success = False
        return success,stderr
    
