#!/usr/bin/python

import getopt
import sys
import time
import re
import os

class Lister:
    def __init__(self):
        pass    
    def __repr__(self):
        return ("<Instance of %s, address %s:\n%s>" %
                (self.__class__.__name__,       # my class's name
                 id(self),                      # my address
                 self.attrnames()) )            # name = value list
    def attrnames(self):
        """
        Lister.attrnames:
        """
        result = ''
        for attr in self.__dict__.keys():      # scan instance namespace dict
            if attr[:2] == '__':
                result = result+"\tattribute: %s=<built-in>\n" % attr
            else:
                result = result + \
                         "\tattribute: %s=%s\n" % (attr,  self.__dict__[attr])
        return result

class Agent(Lister):
    def __init__(self):
        self.recent_time = -1
        self.rss = 0.0
        self.vsize = 0.0
        self.dstime = 0.0
        self.dutime = 0.0

def parse_line(line):
    match = re.match("(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): (\w*)\[(\d*)\]: AGENT_STATISTICS RSS=(\d*(\.\d*)?) VSize=(\d*(\.\d*)?) Stime=(\d*(\.\d*)?) Utime=(\d*(\.\d*)?) dRSS=(-?\d*(\.\d*)?) dVSize=(-?\d*(\.\d*)?) dStime=(\d*(\.\d*)?) dUtime=(\d*(\.\d*)?)", line)

    if not match:
        #print "NRDEBUG: line doesn't match: " + line
        return None
    try:
        tm = time.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(tm)
    except:
        print "NRDEBUG: exception while getting  timestamp"
        return None

    service = match.group(2)
    pid = int(match.group(3))

    rss = float(match.group(4))
    vsize = float(match.group(6))
    stime = float(match.group(8))
    utime = float(match.group(10))
    drss = float(match.group(12))
    dvsize = float(match.group(14))
    dstime = float(match.group(16))
    dutime = float(match.group(18))

    return {'time': timestamp,
            'service': service,
            'pid': pid,
            'rss': rss,
            'vsize': vsize,
            'stime': stime,
            'utime': utime,
            'drss': drss,
            'dvsize': dvsize,
            'dstime': dstime,
            'dutime': dutime}

def parse_log(log, timep, agents):
    min_time = time.time() - timep
    for line in log:
        res = parse_line(line)
        # We only care about AGENT_STATISTICS lines
        if not res:
            continue
        if res['time'] < min_time:
            continue

        if not res['service'] in agents:
            agents[res['service']] = Agent()

        # Use most recent sizes, accumulate time over the period given by timep
        if res['time'] > agents[res['service']].recent_time:
            agents[res['service']].recent_time = res['time']
            agents[res['service']].rss = res['rss']
            agents[res['service']].vsize = res['vsize']
        agents[res['service']].dstime += res['dstime']
        agents[res['service']].dutime += res['dutime']

def usageError ( message, programName) :
    print "Usage error: ", message, \
          "\nTry \'" + programName + " -h\' for help"
    sys.exit ( 2 )
def usage():
    print  """ 
    logparse.py  -  parses phedex  agent  log file to get agent load statistics.
    OPTIONS: 
    -h                                - print help message and exit  
    --xml-format                      - produce output in xml format
      Default:  ascii text
    --log-file=<filename>             - read from filename 
      Default filename: """+logfile+"""
    --time-period=<number of seconds> - change time period
      Default: """+str(timep)+""" sec (""" "%.2f hours)" % (timep/3600.)

if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:],"h",["xml-format","log-file=","time-period="])
    except getopt.error:
        usageError(sys.exc_info()[1], os.path.basename(sys.argv[0]))
    # Defaults: 
    timep = 12*60*60 # accumalte utime and stime for 12 hours
    opts,args = getopt.getopt(sys.argv[1:],"h",["xml-format","log-file=","time-period="])
    logfile = '/home/cmssgm/phedex/instance/Prod_KIT/logs/watchdog'
    # logfile = 'log'
    format=''
    for o, a in opts:
        if o == "-h":
            usage(); sys.exit()
        if o == "--log-file":
            logfile = a            
        if o == "--xml-format":
            format = "xml" 
        if o == "--time-period":
            timep = int(a)

    agents = {}
    logtime=time.ctime(os.path.getmtime(logfile))    
    parse_log(file(logfile), timep, agents)

    if format=="xml":
        print '<agents_statistics date="%s" timeInterval="%.2f hours"  />' % (logtime,timep/3600)
        print '<agents>'
        for agent in agents:
            print  '<agent name="%s">'  % (agent)
            print '  <rss>%.2f</rss>'  % agents[agent].rss
            print '  <vsize>%.2f</vsize> ' % agents[agent].vsize
            print '  <dutime>%.2f</dutime>'  % agents[agent].dstime
            print '  <dstime>%.2f</dstime>'   % agents[agent].dutime
            print '</agent>'
        print '</agents>'
        print '</agents_statistics>'
    else:
        print  ' Agents statistics: \n  Time Interval:  %.2f hours\n  Log File:       %s \n  Checked on:     %s \n'  % (timep/3600,logfile,logtime)
        print 'RSS       VSize     dStime    dUtime    Agent Name'
        for agent in agents:
            print '%8.3f  %8.3f  %8.3f  %8.3f  %s' % (agents[agent].rss, agents[agent].vsize, agents[agent].dstime, agents[agent].dutime, agent)
