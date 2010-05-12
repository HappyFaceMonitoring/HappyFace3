import sys,os
import shlex
import subprocess

class DownloadError(Exception):
    def __init__(self, url, stderr):
	self.url = url
	self.stderr = stderr
    def __str__(self):
	return 'Could not download "' + self.url + '"'

#############################################
# class to download external data
#############################################
class GetData(object):

# execute the WGET command to load and store an imagefile and return the stored filename (with relative path)
    def getDataWget(self, args, url, path, file):

	cmd = 'wget --output-document=' + path + "/" + file + " " + args + " "  + "\'"+url+"\'"
	process = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
	stderr = process.communicate()[1]

        if process.returncode != 0:
	    raise DownloadError(url, stderr)

# execute the Wget with special parameters to load an XML file
    def getDataWgetXmlRequest(self,args,url,path,file):

        cmd = 'wget --header="Accept: text/xml" --output-document=' + path + "/" + file + " " + args + " " +  "\'"+url+"\'"
	process = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
	stderr = process.communicate()[1]

        if process.returncode != 0:
	    raise DownloadError(url, stderr)
