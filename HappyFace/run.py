#!/usr/bin/env python

# import statements
import sys, os
import traceback
from time import time, localtime, mktime
from stat import *
import signal
import thread
import ConfigParser

# for SQL database functionality
# has to be installed on the running system, 
# package: "python-sqlobject"
from sqlobject import *

# setup search paths for python modules
sys.path.insert(0, os.path.expandvars('./happycore'))
sys.path.insert(0, os.path.expandvars('./modules'))
sys.path.insert(0, os.path.expandvars('./modules/examples'))
if os.path.exists('./local/modules'):
    sys.path.insert(0, os.path.expandvars('./local/modules'))
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
	config.readfp(open('./local/cfg/run.local'))
    except IOError:
        pass

    # get paths from config files
    output_dir	= config.get('setup','output_dir')
    tmp_dir     = config.get('setup','tmp_dir')
    try:
        tmp_keepalive = int(config.get('setup', 'tmp_keepalive'))
    except:
        # default
        tmp_keepalive = 7

    # convert to seconds:
    if tmp_keepalive > 0:
        tmp_keepalive = tmp_keepalive * 24 * 60 * 60

    # create timestamp (unixtime), set seconds to "0"
    time_tuple = localtime() 
    timestamp = int(mktime(time_tuple)) - time_tuple[5]

    # create archive directory for binary files
    archive_dir = output_dir + "/archive/" + str(time_tuple.tm_year) + "/" + ('%02d' % time_tuple.tm_mon) + "/" + ('%02d' % time_tuple.tm_mday) + "/" + str(timestamp)
    try:
        os.system("mkdir -p " + archive_dir)
    except:
        sys.stdout.write('Could not create archive directory ' + archive_dir + ', aborting ...\n')
        sys.exit(-1)

    try: # separate try for finally block so we are compatible with Python 2.4
        try:
            lockfile = output_dir + "/hf.lock"

            def signal_handler(signum, stack):
	        print('HappyFace: Terminating due to signal %s' % str(signum))
	        # Note that this raises an exception so the lock file will be
	        # removed by the finally clause of the outer try block.
	        sys.exit(-2)

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            psid=os.getpid()
            print "Current HappyFace process-id: ",psid
            # Check for lockfile existence
            try:
                ifile=os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(ifile,str(psid)+"\n")
                os.close(ifile)
	    except:
                sys.stdout.write('Lock file exists. Checking age ...\n')
                # Prevent outer try block from removing the lock file 
                age=os.stat(lockfile)[ST_CTIME]
                timestamp = int(mktime(localtime()))
                diff=timestamp-age
                print "Lockfile age: ",diff,"s"
                maxAge=60*5;
                if (diff>maxAge):
                    print "Lock file older than ",maxAge," checking if process still exist..."
                    try:
                        rfile=open(lockfile,'r')
                        opid=rfile.readline()
                        print "Original Happyface: ",opid
                        dingens=os.getpgid(int(opid))
                        print "Original HF process still running, exiting..."
                    except:
                        print "Old HF process does not exist anymore. Removing lockfile..."
                        os.remove(lockfile)
                        lockfile = ''
                        sys.exit(-1)
                    print "Old HF process still running. Exiting here..."
                    lockfile = ''
                    sys.exit(-1)
                else:
                    print "Lockfile not older than ",maxAge,"s letting other HF instance relax..."
                    # Prevent outer try block from removing the lock file
                    lockfile = ''
                    sys.exit(-1)

            # try to initiate / create the database
            database = output_dir + "/HappyFace.db"
            try:
                # has to be the full path
                connection_string = 'sqlite:' + os.getcwd() + "/" + database
                connection = connectionForURI(connection_string)
                sqlhub.processConnection = connection
            except Exception, ex:
                raise Exception('Could not initiate or create the database ' + os.getcwd() + "/" + database + ': ' + str(ex))

            # definition of the global timeout
            timeout        =  int(config.get('setup','timeout_module'))
            timeoutDownload =  int(config.get('setup','timeout_download'))

            # definition of the holdback_time
            holdback_time  =  int(config.get('setup','holdback_time'))

            ##########################################################
            ################ start with the execution ################

            # create options dictionary
            module_options = {}
    
            module_options["timestamp"] = timestamp
            module_options["archive_dir"] = archive_dir
            module_options["holdback_time"] = holdback_time
    
            # dictionary collects the module objects
            modObj_list = {}

            # initialisation of modules
            print "HappyFace: Start with module preparation:"
            moduleCount = 0
            for category in config.get('setup','categories').split(","):
	        for module in config.get(category,'modules').split(","):

	            if module == "": continue

                    # import module class dynamically
                    moduleCount += 1
                    print "  "+str(moduleCount)+": "+module
                    modClass = __import__(module)
	    
                    module_options["category"] = category

                    # create a object of the class dynamically
                    modObj_list[module] = getattr(modClass,module)(module_options)

            print "HappyFace: Module preparation finished."

            # Preparation of Download and CSS Service.
            # Selecting all files for download.
            # Prepare list of needed css files for the webpage.
            downloadService = DownloadService(tmp_dir, tmp_keepalive)
            cssService = CssService(output_dir,'config/modules')
    
            for module in modObj_list.keys():
                for downloadTag in modObj_list[module].getDownloadRequests():
                    downloadService.add(downloadTag)
            
                cssService.add(modObj_list[module].getCssRequests())

            # Start parallel download of all specified files
            downloadService.download(timeoutDownload)

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
	        if timeout == -1:
	            modObj_list[module].join()
		    continue
	
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
                                                        + " aborting ...\n"
                    sys.stdout.write(modObj_list[module].error_message)

                # store results (or pre-defined values if timeout) to DB
                # if enabled, erase old data from the DB
                modObj_list[module].processDB()

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

                    # clear XML cache (note that the cache is invalidated anyway
                    # but this makes sure old cache files are cleaned up in case
	            # they are no longer used, for example if modules are added or removed
                    try:
                        for f in os.listdir(output_dir + '/cache'):
		            try:
		                os.unlink(os.path.join(output_dir, 'cache', f))
			    except Exception, ex:
			        pass
		    except:
		        pass
    
                    # save webpage output file
                    try:
                        f = open(output_dir + '/index.php','w')
                        f.write(webpage_output)
                        f.close()
                    except Exception, ex:
                        raise Exception('Could not create final output ' + output_dir + '/index.php:' + str(ex))

                    print "HappyFace: Web page building finished." 

            print "HappyFace: Output processing finished." 

            # cleanup
            downloadService.clean()

            print "\nDONE!!\n"
        except Exception, ex:
            print str(ex) + '\nAborting ...'
            traceback.print_exc()
    finally:
        if lockfile != '':
            try:
               os.unlink(lockfile)
	    except: 
	       pass

if __name__ == '__main__':
    HappyFace()


