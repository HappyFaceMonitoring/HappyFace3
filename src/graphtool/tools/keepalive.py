import time, popen2, sys, os, logging, re, signal

from graphtool.base.xml_config import XmlConfig
from logging.handlers import RotatingFileHandler

# Log initialization
# create log handler
logHandler = RotatingFileHandler("Keepalive.log", \
                                     "a", 10000, 3)

# define log format
logFormatter = logging.Formatter("%(asctime)s:%(message)s")
logHandler.setFormatter(logFormatter)
logging.getLogger().addHandler(logHandler)
logging.getLogger().setLevel(logging.INFO)

def getattr( dom, attr, default=None ):
  value = dom.getAttribute(attr)
  if len(value) == 0: return default
  return value

class Keepalive( XmlConfig ):

    def __init__( self, *args, **kw ):
        self.apps = []
        super( Keepalive, self ).__init__( *args, **kw )
        for app in self.apps:
            app.execute()

    def parse_dom( self ):
        super( Keepalive, self ).parse_dom()
        for app_dom in self.dom.getElementsByTagName('application'):
            app = Application( dom=app_dom )
            self.apps.append( app )

class Application( XmlConfig ):

    def __init__( self, *args, **kw ):
        self.tests = []
        self.isalive, self.term, self.kill, self.start = None, None, None, None
        super( Application, self ).__init__( *args, **kw )

    def parse_dom( self ):
        super( Application, self ).parse_dom()
        self.max_attempts = getattr(self.dom, 'attempts', 3)
        try: self.max_attempts = int(self.max_attempts)
        except: self.max_attempts = 3
        for test_dom in self.dom.getElementsByTagName('test'):
            test = RunCommand( dom=test_dom )
            self.tests.append( test )
        for isalive_dom in self.dom.getElementsByTagName('isalive'):
            self.isalive = RunCommand( dom=isalive_dom )
        for term_dom in self.dom.getElementsByTagName('term'):
            self.term = RunCommand( dom=term_dom )
        for kill_dom in self.dom.getElementsByTagName('kill'):
            self.kill = RunCommand( dom=kill_dom )
        for start_dom in self.dom.getElementsByTagName('start'):
            self.start = RunCommand( dom=start_dom )

    def execute( self, attempt=1 ):
        has_failed = False
        for test in self.tests:
            logging.info("Running test:\n%s" % test.cmdStr)
            if not test.execute():
                has_failed = True
                logging.warning("Test failed!")
                break
            else:
                logging.info("Test passed.")

        if not has_failed: 
            logging.info("No tests have failed; application OK.")
            return
        
        logging.warning("Some test has failed.  Attempting to fix.")

        if self.isalive.execute():
            logging.info("Application still alive; will attempt to kill first.")
            self.term.execute()
            time.sleep( self.term.timeout )
            if self.isalive.execute():
                logging.warning("Unable to terminate app!  Trying a stronger signal")
                self.kill.execute()
        else:
            logging.info("Application is dead.")


        logging.info("Starting the application; attempt %i." % attempt)
        self.start.execute() 
        logging.info("App started; now sleeping for %i seconds" % self.start.timeout )
        time.sleep( self.start.timeout )
        if attempt != self.max_attempts:
            logging.info("Starting test cycle again.")
            self.execute( attempt+1 )
        else:
            logging.error("Unable to restore application after %i attempts" % attempt)

class RunCommand( XmlConfig ):

    def __init__( self, *args, **kw ):
        super( RunCommand, self ).__init__( *args, **kw )
        
    def parse_dom( self ):
        super( RunCommand, self ).parse_dom()
        textNode = self.dom.firstChild
        assert textNode.nodeType == textNode.TEXT_NODE 
        self.cmdStr = str(textNode.data)
        try:
            self.timeout = int(getattr(self.dom,'timeout',120))
        except:
            self.timeout = 120
        self.output_regexp = getattr(self.dom,'output','.*')

    def execute( self ):
        output, exitCode = executeCommand( self.cmdStr, timeOut = self.timeout )
        if exitCode != 0: return False
        if re.search( self.output_regexp, output ): return True
        logging.info( "Regexp %s did not match output %s" % (self.output_regexp, output ) )
        return False

##########################################################################
# execute a command, provided by Carlos Kavka 
##########################################################################

def executeCommand(command, timeOut = 1200):
    """
    _executeCommand_

     execute a command, waiting at most timeOut seconds for successful
     completation.

    Arguments:

      command -- the command
      timeOut -- the timeout in seconds

    Return:

      the exit code or -1 if did not finish on time.

    """
    startTime = time.time()

    # build script file if necessary
    if command.find('\n') != -1:

        try:
            try:
                os.remove('script.sh')
            except:
                pass 
            aFile = open('script.sh', 'w')
            command = '#!/bin/bash\n' + command
            aFile.write(command + '\n')
            aFile.close()
            os.chmod('script.sh', 0755)
        except (IOError, OSError), msg:
            logging.error("Cannot generate execution script: " + str(msg))
            return
 
        command = 'bash -c ./script.sh'

    # run command
    job = popen2.Popen4(command)
    output = job.fromchild

    # get exit code (if ready)
    exitCode = job.poll()

    # wait for it to finish
    while exitCode == -1:

        # check timeout
        if (time.time() - startTime) > timeOut:
            logging.critical("Timeout exceded for command")

            # exceeded, kill the process
            try:
                os.kill(job.pid, signal.SIGKILL)

            # oops, cannot kill it
            except OSError:
                logging.critical("Cannot kill process")
            # abandon execution
            return -1

        # wait a second
        time.sleep(1)

        # get exit status
        exitCode = job.poll()

    try:
        out = output.read()
        output.close()

    # does not work, ignore
    except IOError, ie:
        logging.info( "Caught an error trying to get output: %s" % str(ie) )

    # return exit code
    return out, exitCode 
