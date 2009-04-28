#!/usr/bin/env python

import sys, os
from time import time
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
    theme	= config.get('setup','theme')

    # create timestamp (unixtime[sec]) 
    timestamp = int(time())

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

    ##########################################################
    ################ start with the execution ################

    navigation = ""
    content = ""

    # directory collects the module objects
    modObj_list = {}

    # parallel execution of the modules (threading)
    # see therefore: http://www.wellho.net/solutions/python-python-threads-a-first-example.html
    for category in config.get('setup','categories').split(","):
	for module in config.get(category,'modules').split(","):

	    if module == "": continue

            # import module class dynamically
	    modClass = __import__(module)

       	    # create a object of the class dynamically
       	    modObj_list[module] = getattr(modClass,module)(category, timestamp, archive_dir)

       	    # execute the object in a thread
	    modObj_list[module].start()

    # lock object for exclusive database access
    lock = thread.allocate_lock()

    # definition of the global timeout
    timeout	= int(config.get('setup','timeout'))

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
        content		+= CategoryContentTab(cat_content,timestamp).output

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

    print "\nDONE!!\n"

##########################################################
###################### here we go ########################
if __name__ == '__main__':
    HappyFace()


