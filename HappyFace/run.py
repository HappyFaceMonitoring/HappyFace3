#!/usr/bin/env python

# import statements
import sys, os
from time import time, localtime, mktime
import thread
import ConfigParser

# for SQL database functionality
# has to be installed on the running system, 
# package: "python-sqlobject"
from sqlobject import *

# setup search paths for python modules
sys.path.insert(0, os.path.expandvars('./happycore'))
sys.path.insert(0, os.path.expandvars('./modules'))
if os.path.exists('./modules.local'):
    sys.path.insert(0, os.path.expandvars('./modules.local'))
sys.path.insert(0, os.path.expandvars('./output/web'))

# import output module, e.g. website creator
from WebCreator import *

# import HappyFace services
from DownloadService import *
from CssService import *

##########################################################
# load the config file
# create storage directory for binary files
# initiate the database
# start the execution
# store data to database
# initiate the output creation module
##########################################################

def HappyFace():

    # load the config file
    config = ConfigParser.ConfigParser()

    # try to open standard config file, must be available
    try:
	config.readfp(open('./run.cfg'))
    except IOError:
        sys.stdout.write('Could not find configuration file run.cfg, aborting ...\n')
        sys.exit(-1)

    # try to open local config file if available.
    # default config settings in run.cfg will be overwritten
    try:
	config.readfp(open('./run.local'))
    except IOError:
        pass

    # get paths from config files
    output_dir	= config.get('setup','output_dir')
    tmp_dir     = config.get('setup','tmp_dir')

    # create timestamp (unixtime), set seconds to "0"
    time_tuple = localtime() 
    timestamp = int(mktime(time_tuple)) - time_tuple[5]

    # create archive directory for binary files
    archive_dir = output_dir + "/archive/" + str(timestamp)
    try:
        os.system("mkdir -p " + archive_dir)
    except:
        sys.stdout.write('Could not create archive directory ' + archive_dir + ', aborting ...\n')
        sys.exit(-1)

    # try to initiate / create the database
    database = output_dir + "/HappyFace.db"
    try:
        # has to be the full path
        connection_string = 'sqlite:' + os.getcwd() + "/" + database
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
    except:
        sys.stdout.write('Could not initiate or create the database ' + os.getcwd() + "/" + database + ', aborting ...\n')
        sys.exit(-1)

    # definition of the global timeout
    timeout        =  int(config.get('setup','timeout_module'))
    timeoutDowload =  int(config.get('setup','timeout_download'))

    ##########################################################
    ################ start with the execution ################

    # directory collects the module objects
    modObj_list = {}

    # initialisation of modules
    print "HappyFace: Start with module preparation:"
    moduleCount = 0
    for category in config.get('setup','categories').split(","):
	for module in config.get(category,'modules').split(","):

	    if module == "": continue

            # import module class dynamically
	    modClass = __import__(module)
            moduleCount += 1

       	    # create a object of the class dynamically
       	    modObj_list[module] = getattr(modClass,module)(category, timestamp, archive_dir)
            print "  "+str(moduleCount)+": "+module

    print "HappyFace: Module preparation finished."

    # Preparation of Download and CSS Service.
    # Selecting all files for download.
    # Prepare list of needed css files for the webpage.
    downloadService = DownloadService(tmp_dir)
    cssService = CssService(output_dir,'config/modules')
    
    for module in modObj_list.keys():
        for downloadTag in modObj_list[module].getDownloadRequests():
            downloadService.add(downloadTag)
            
        cssService.add(modObj_list[module].getCssRequests())

    # Start parallel download of all specified files
    downloadService.download(timeoutDowload)

    # parallel execution of the modules (threading)
    # see therefore: http://www.wellho.net/solutions/python-python-threads-a-first-example.html
    for module in modObj_list.keys():
        # make downloadService available for each module
        modObj_list[module].setDownloadService(downloadService)
        # execute the object in a thread
        modObj_list[module].start()

    print "HappyFace: Start module processing." 

    # wait till all modules are finished OR till the global timeout
    for module in modObj_list.keys():
        start = int(time())
        modObj_list[module].join(timeout)
        timeout -= int(time()) - start
        if timeout < 1:
            break


    for module in modObj_list.keys():
        if modObj_list[module].isAlive() == True:
            modObj_list[module]._Thread__stop()
            modObj_list[module].error_message += "\nCould not execute module in time, "\
                                                 + modObj_list[module].__module__ \
                                                 + " abborting ...\n"
            sys.stdout.write(modObj_list[module].error_message)

        # store results (or pre-defined values if timeout) to DB
        # collect the output and results of the modules and compose category content
        modObj_list[module].storeToDB()

    print "HappyFace: Module processing finished." 

    # create final PHP/HTML output

    print "HappyFace: Start output processing:" 
    for type in config.get('setup','output_types').split(","):
	if type == "web":
	     print "HappyFace: Start building web page:" 

	     theFinalWebOutput = WebCreator(config,modObj_list,timestamp)
	     theFinalWebOutput.setCss(cssService.getCssWebDirFiles())
	     webpage_output = theFinalWebOutput.getOutput()

	     # sync the module css files to the wepage directory
	     cssService.syncCssFiles()
    
	     # save webpage output file
             try:
                  f = open(output_dir + '/index.php','w')
                  f.write(webpage_output)
                  f.close()
             except:
                  sys.stdout.write('Could not create final output ' + output_dir + '/index.php , aborting ...\n')
                  sys.exit(-1)

             print "HappyFace: Web page building finished." 

    print "HappyFace: Output processing finished." 

    # cleanup
    downloadService.clean()

    print "\nDONE!!\n"

if __name__ == '__main__':
    HappyFace()


