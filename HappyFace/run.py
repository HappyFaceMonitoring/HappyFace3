#!/usr/bin/env python

import sys, os
from time import time, localtime, mktime
import thread
import ConfigParser


sys.path.insert(0, os.path.expandvars('./happycore'))
sys.path.insert(0, os.path.expandvars('./modules'))
sys.path.insert(0, os.path.expandvars('./webcomposer'))
if os.path.exists('./modules.local'):
    sys.path.insert(0, os.path.expandvars('./modules.local'))

# for SQL database functionality
# has to be installed on the running system, package: "python-sqlobject"
from sqlobject import *

# for output composing from ./composer
from CategoryNavigationTab import *
from CategoryContentTab import *
from FinalOutput import *

from DownloadService import *

##########################################################
# load the config file
# create storage directory for binary files
# initiate the database
# start the execution
# store data to database
# compose the final output index.php
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

    # try to open local config file if available (standard config settings will be overwritten)
    try:
	config.readfp(open('./run.local'))
    except IOError:
        pass

    # relative path of the output directory (index.php, archive, database, ...)
    webpage_dir	= config.get('setup','webpage_dir')
    tmp_dir     = config.get('setup','tmp_dir')
    theme	= config.get('setup','theme')

    # create timestamp (unixtime), set seconds to "0"
    time_tuple = localtime() 
    timestamp = int(mktime(time_tuple)) - time_tuple[5]

    # create archive directory for binary files
    archive_dir = webpage_dir + "/archive/" + str(timestamp)
    try:
        os.system("mkdir -p " + archive_dir)
    except:
        sys.stdout.write('Could not create archive directory ' + archive_dir + ', aborting ...\n')
        sys.exit(-1)

    # try to initiate / create the database
    database = webpage_dir + "/HappyFace.db"
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

    navigation = ""
    content = ""

    # directory collects the module objects
    modObj_list = {}

    print "HappyFace:Start with module preparation."
    moduleCount = 0
    # Initialisation of Modules
    for category in config.get('setup','categories').split(","):
	for module in config.get(category,'modules').split(","):

	    if module == "": continue

            # import module class dynamically
	    modClass = __import__(module)
            moduleCount+=1
       	    # create a object of the class dynamically
       	    modObj_list[module] = getattr(modClass,module)(category, timestamp, archive_dir)
            print "  "+str(moduleCount)+": "+module
    print "HappyFace: Module preparation finished."


    # Preparation of Download Service
    # All files are selected for download
    downloadService = DownloadService(tmp_dir)
    for module in modObj_list.keys():
        for downloadTag in modObj_list[module].getDownloadRequests():
            downloadService.add(downloadTag)


    #Start parallel download of all specified files
    #timeout will come soon
    print "DownloadService: Start file download"
    downloadService.download(timeoutDowload)
    print "DownloadService: Download finished"

    # parallel execution of the modules (threading)
    # see therefore: http://www.wellho.net/solutions/python-python-threads-a-first-example.html
    for module in modObj_list.keys():
        # make downloadService available for each module
        modObj_list[module].setDownloadService(downloadService)
        # execute the object in a thread
        modObj_list[module].start()



    print "HappyFace: Start module processing." 

    # lock object for exclusive database access
    lock = thread.allocate_lock()

    for category in config.get('setup','categories').split(","):

        cat_title	= config.get(category,'cat_title')
        cat_type	= config.get(category,'cat_type')
        cat_algo	= config.get(category,'cat_algo')
        cat_content	= ""

	# wait till all modules are finish OR till the global timeout
	for module in config.get(category,'modules').split(","):

	    if module == "": continue

            start = int(time())
            modObj_list[module].join(timeout)
            timeout -= int(time()) - start
	    if timeout < 1:
		break

	for module in config.get(category,'modules').split(","):

	    if module == "": continue

	    # if the are any running modules: kill them
            if modObj_list[module].isAlive() == True:
                modObj_list[module]._Thread__stop()
                modObj_list[module].error_message += "\nCould not execute module in time, " + modObj_list[module].__module__ + " abborting ...\n"
                sys.stdout.write(modObj_list[module].error_message)

            # store results (or pre-defined values if timeout) to DB
            # collect the output and results of the modules and compose category content
            modObj_list[module].storeToDB(lock)
            cat_content += modObj_list[module].output()

        # collect all navigation and content tabs
        navigation	+= CategoryNavigationTab(category, cat_title, cat_type, cat_algo).output
        content		+= CategoryContentTab(cat_content,config,category,timestamp).output

    print "HappyFace: Module processing finished." 

    # create final PHP/HTML output
    final_output = FinalOutput(config,theme,navigation,content).output

    # save the output file
    try:
        f = open(webpage_dir + '/index.php','w')
        f.write(final_output)
        f.close()
    except:
        sys.stdout.write('Could not create final output ' + webpage_dir + '/index.php , aborting ...\n')
        sys.exit(-1)


    downloadService.clean()

    print "\nDONE!!\n"

##########################################################
###################### here we go ########################
if __name__ == '__main__':
    HappyFace()


