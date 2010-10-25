#!/usr/bin/env python
from ConfigParser import ConfigParser, NoOptionError
import sqlobject
  
class MailObserver(sqlobject.SQLObject):
    """
    class prototype to
      o store state
      o send notifications if necessary

    Properties:
      o config and section are used to read the config.
      o timestanp, currentState and address are used to
        keep state (and send notifications)
      o happy_face_identifier is used to join with tables
        from the HappyFace.db
    """
    #configuration (set on devirtualization)
    config = None
    section = None
    #default columns
    observedClass = None
    timestamp = sqlobject.IntCol()
    currentStage = sqlobject.StringCol()
    address = sqlobject.StringCol()
    unresolved = sqlobject.BoolCol()

    @classmethod
    def update(self, dryRun = False):
        from time import strptime, mktime
        condition = self.config.get(self.section, "condition")
        initTime = mktime(strptime(self.config.get("general", "initTime"), "%d.%m.%y %H:%M"))
        toNotify = self.observedClass.getNotifyList(condition, initTime)
        #add new occurreces, send notification if necessary 
        for address, observed in toNotify.iteritems():
            timestamp = min([i.timestamp for i in observed]) #since there micght by more than one site we take the min of the observations at each site
            occurrenceSelection = self.select((self.q.address == address) & (self.q.unresolved))
            if occurrenceSelection.count() == 0:
                self(timestamp = timestamp,
                     currentStage = "initial",
                     address= address,
                     unresolved = True)
            if occurrenceSelection.count() == 1:
                if timestamp < occurrenceSelection.getOne().timestamp:
                    raise StandardError, "bad timestamp: '%s' != '%s'"%(timestamp, occurrenceSelection.getOne().timestamp)
                if timestamp > occurrenceSelection.getOne().timestamp:
                    print "WARNING: timestamp propably cut of by time-window..."
                self.processNotification( occurrenceSelection.getOne(), observed, dryRun)
            else:
                raise StandardError, "bad or duplicate occurrence ( %s times) for '%s'"%(occurenceSelection.count(), address)
            
        #mark resolved occurrences
        for occurrence in  self.select(self.q.unresolved):
            if not occurrence.address in toNotify:
                occurrence.unresolved = False

    @classmethod
    def processNotification(self, occurrence, observed, dryRun=False):
        """
        test occurence and send mail if neccesarry
        """
        from time import time
        timestamp = occurrence.timestamp
        duration = (time()-timestamp) / 3600#h
        def periode(x): return float(eval(self.config.get("mail_stage:%s"%x, "periode")))
        stages = sorted( self.config.get(self.section, "stages").split(), key = periode )
        if not occurrence.currentStage == "initial":
            stages = stages[stages.index(occurrence.currentStage)+1:]
            
        for stageName in stages:
            #print occurrence.address, dryRun, stageName, duration, periode(stageName)
            section = "mail_stage:%s"%stageName
            if duration > periode(stageName):
                address = occurrence.address
                if self.config.has_option(section, "address_override"):
                    address = self.config.get(section, "address_override")
                if dryRun:
                    print "dry run mode: would be sending mail to '%s' for '%s'"%(address, section)
                else:
                    if self.sendMail(address, section, observed):
                        occurrence.currentStage = stageName
    
    @classmethod
    def sendMail(self, address, section, observed):
        """
        build mail and send it via smtp server on localhost
        """
        from smtplib import SMTP
        from ConfigParser import InterpolationMissingOptionError
        try:
            from email.mime.text import MIMEText
        except:
            #there is just a very old version of python available :(
            from email.MIMEText import MIMEText
        repMap = {}
        for option in self.config.options(section):
            if not option in ["periode","message_subject","message_template","address_override"]:
                repMap[option] = self.config.get(section,option)
        repMap.update(self.observedClass.getMap(observed))
        try:
            subject = self.config.get(section,"message_subject",vars = repMap)
            templateName = self.config.get(section,"message_template")
            body = self.config.get("message_templates",templateName, vars = repMap)
        except InterpolationMissingOptionError, err:
            print err
            raise KeyError, " choose from: %s"%(repMap.keys())
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = "donotreply@physik.rwth-aachen.de"
        message["To"] = ", ".join(address.split())
        
        server = SMTP('localhost')
        #server.set_debuglevel(1)
        if True in [ i in address for i in ["edelhoff","admin"] ]:
            server.sendmail(message["From"],["matthias.edelhoff@rwth-aachen.de","edelhoff@cern.ch"], message.as_string())
            print "SENDING: '%s'"%address
            print "            ",section
        server.quit()
        return True

def getConnection(config, name):
    """
    get a sqlobject connectioion for an entry in the [general] section of 'config'
    """
    import os
    uri = config.get("general",name)
    if not ":/" in uri:
        uri = "sqlite:%s"%os.path.abspath(uri)
    return sqlobject.connectionForURI(uri)

def dbConnect(config):
    """
    Sets up a global database connection for all db objects.
    This is used for the HappyFace database.
    The state database is cotennected on its own.
    """
    conn = getConnection(config,"happyFaceDbURI")
    sqlobject.sqlhub.processConnection = conn

def makeObservers(config):
    """
    make the observer sate DB classes from MailObserver.
    They are used to keep the state in the stateDB

    One class (and table) is generated per 'mail_observer:' section
    in the configuration.
    """
    from observed.usm import UsmUser
    from observed.usm_grpvo import UsmGroup
    
    result = {}
    conn = getConnection(config, "stateDbURI")
    #TODO: do this automatically
    observedClasses = {"UsmUser":UsmUser, "UsmGroup":UsmGroup}
    
    for section in filter(lambda x: x.startswith("mail_observer:"),
                          config.sections()):
        observedClassName = section.split(":")[1]
        observerName = section.split(":")[2]
        
        members = {"observedClass":observedClasses[observedClassName],
                   "config":config,
                   "section":section,
                   "personalIdentifier":None
                   }
        result[observerName] = type(observerName,
                                    ( MailObserver,),
                                    members)
        result[observerName].sqlmeta.fromDatabase = True
        
        result[observerName]._connection =  conn
        result[observerName].createTable(ifNotExists=True)
        
    return result

def processObservers(observers, dryRun = False ):
    for observerName, observer in observers.iteritems():
        observer.update(dryRun)

def main(argv=None):
    import os, sys
    from optparse import OptionParser
    if argv == None:
        argv = sys.argv[1:]
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config", action="append", default=[],
                              help="configuration to use. Can be used multiple times. Configuration that will be joined")
        parser.add_option("-n", "--dry-run", action="store_true", dest="dryrun", default=False,
                              help="Dry-run mode, no job submission.")

        (opts, args) = parser.parse_args(argv)
        for configFilePath in opts.config:
            if not os.path.exists(configFilePath):
                raise StandardError, "config file '%s' not found"%configFileName
            
        config = ConfigParser()
        config.read(opts.config)
        dbConnect(config)
        observers = makeObservers(config)
        processObservers(observers, opts.dryrun)
        

if __name__ == '__main__':
    mailer = main()
