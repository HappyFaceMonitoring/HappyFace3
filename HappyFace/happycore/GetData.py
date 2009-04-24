import subprocess # for traping errors of subprocesses like WGET

from ModuleBase import *

#############################################
# class to donwload external data
#############################################
class GetData(ModuleBase):

    def __init__(self, category, timestamp, archive_dir):
        ModuleBase.__init__(self, category, timestamp, archive_dir)

        # read class config file
	config = self.readConfigFile('./happycore/GetData') # empty


    # execute the WGET command to load and store an imagefile and return the stored filename (with relative path)
    def getDataWget(self, url, path, file):

        retcode = subprocess.call(["wget","-q","--output-document=" + path + "/"  + file, url])

        if retcode == 0: return True

        else:
            self.error_message += '\nCould not download ' + self.url + ', ' + self.__module__ + ' abborting ...\n'
            sys.stdout.write(self.error_message)
            return False
