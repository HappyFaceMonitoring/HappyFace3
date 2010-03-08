import sys,os


#############################################
# class to donwload external data
#############################################
class GetData(object):

# execute the WGET command to load and store an imagefile and return the stored filename (with relative path)
    def getDataWget(self, args, url, path, file):

        cmd = 'wget -q --output-document=' + path + "/" + file + " " + args + " "  + "\'"+url+"\'"
	retcode = os.system(cmd)
        success = False
        stderr = ""

        if retcode == 0:
            success =  True
            stderr = ""

        else:
            stderr = '\nCould not download ' + url + ', abborting ...\n'
            sys.stdout.write(stderr)
            success = False
        return success,stderr

# execute the Wget with special parameters to load and XML file
    def getDataWgetXmlRequest(self,args,url,path,file):

        cmd = 'wget -q --header="Accept: text/xml" --output-document=' + path + "/" + file + " " + args\
 +" " +  "\'"+url+"\'"
	retcode = os.system(cmd)
        success = False
        stderr = ""

        if retcode == 0:
            success =  True
            stderr = ""

        else:
            stderr = '\nCould not download ' + url + ', abborting ...\n'
            sys.stdout.write(stderr)
            success = False
        return success,stderr
