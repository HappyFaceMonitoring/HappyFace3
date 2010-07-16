import sys,os
import shlex
import shutil
import subprocess
import re

class DownloadError(Exception):
    def __init__(self, url, http_errcode, stderr):
	self.url = url
	self.http_errcode = http_errcode
	self.stderr = stderr
    def __str__(self):
	return 'Could not download "' + self.url + '"'

#############################################
# class to download external data
#############################################
class GetData(object):

# copy a local file from a relative or absolute path
    def getDataLocal(self, args, url, path, file):
        # Ignore args
	try:
	    shutil.copy2(url, path + '/' + file)
	except Exception as ex:
	    raise Exception('Could not copy from ' + url + ': ' + str(ex))

# execute the WGET command to load and store an imagefile and return the stored filename (with relative path)
    def getDataWget(self, args, url, path, file):

	cmd = 'wget --output-document=' + path + "/" + file + " " + args + " "  + "\'"+url+"\'"
	process = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
	stderr = process.communicate()[1]

        if process.returncode != 0:
	    # Find the HTTP error code from output
	    match = re.search('ERROR ([0-9][0-9][0-9])', stderr)
	    http_errcode = 0
	    if match: http_errcode = int(match.group(1))

	    raise DownloadError(url, http_errcode, stderr)

# execute the Wget with special parameters to load an XML file
    def getDataWgetXmlRequest(self,args,url,path,file):

        cmd = 'wget --header="Accept: text/xml" --output-document=' + path + "/" + file + " " + args + " " +  "\'"+url+"\'"
	process = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE)
	stderr = process.communicate()[1]

        if process.returncode != 0:
	    # Find the HTTP error code from output
	    match = re.search('ERROR ([0-9][0-9][0-9])', stderr)
	    http_errcode = 0
	    if match: http_errcode = int(match.group(1))

	    raise DownloadError(url, http_errcode, stderr)
