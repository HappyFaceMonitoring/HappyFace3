#!/usr/bin/env python
#

# Volker.Buege@cern.ch (VMB)
# Universitaet Karlsruhe
# 17.12.2008

# ToDo:
# 

# Changes:
#
# Armin Burgmeier <armin@arbur.net> 19.07.2010:
#   Changed output to match the new common XML format
#
# Armin Scheurer <armin.scheurer@cern.ch> 05.11.2010:
#   Write different xml files, if more than one batch 
#   server is specified. In such a case write as well
#   a combined xml file.

import sys
import os
import time
import signal
import string
import popen2
import ConfigParser
from xml.dom.minidom import Document

pwfile = ConfigParser.ConfigParser()
try:
	pwfile.readfp(open('/home/cmssgm/vobox-tools/monitoring/qstatXMLdump.pwd'))
except IOError:
	sys.stdout.write('Could not find password file!\n')
	sys.exit(1)

theUploadPw = pwfile.get('upload','pw')

def getSeconds(inString):
    fields = string.split(inString,":")
    if len(fields) != 3:
        print "Wrong time format in def getSeconds"
        sys.exit(1)
    return (int(fields[0])*24+int(fields[1]))*60+int(fields[2])                       

def uploadFile(theFile):
    theServer = 'http://'+theUploadPw+'@www-ekp.physik.uni-karlsruhe.de/~happyface/upload/in/uploadFile.php'
    theCommand = 'curl -F \"Datei=@'+theFile+'\" '+theServer
    if os.system(theCommand) == 0:
        print "qstatXMLdump.py: Upload successful: "+theFile
    else:
        print "qstatXMLdump.py: Upload error: "+theFile
        sys.exit(1)

# Check whether the given chk_group is a subgroup of group
def checkGroup(chk_group, group, group_table):
    while chk_group != group:
        if chk_group == None or chk_group not in group_table:
	    return False
        chk_group = group_table[chk_group]
    return True

def createXMLFile(theLogFile, theXMLFile, startTime, stopTime):

    print "qstatXMLdump.py: start processing."
    
    theQstatInfo = {}
    theQstatInfo["start"] = startTime
    theQstatInfo["end"] = stopTime

    out = open(theLogFile).readlines()

    theJobInfo = {}
    theJobId = ""
    i = 0
    for fileLine in out:
        fileLine = fileLine.replace("\n","")
        if fileLine.count('Job Id'):
            theJobId = fileLine
            theJobInfo[theJobId] = {}
            theJobInfo[theJobId]['id'] = fileLine.split(": ")[1]

        if fileLine.count('Job_Owner'):
            theSplit = fileLine.split(" = ")[1].split("@")
            theJobInfo[theJobId]['user'] = theSplit[0]
            theJobInfo[theJobId]['ce'] = theSplit[1]
            
        if fileLine.count('resources_used.cpupercent'):
            theJobInfo[theJobId]['cpupercent'] = fileLine.split(" = ")[1]

        if fileLine.count('resources_used.cput'):
            theJobInfo[theJobId]['cputime'] = getSeconds(fileLine.split(" = ")[1])

        if fileLine.count('resources_used.ncpus'):
            theJobInfo[theJobId]['ncpus'] = fileLine.split(" = ")[1]

        if fileLine.count('resources_used.walltime'):
            theJobInfo[theJobId]['walltime'] = getSeconds(fileLine.split(" = ")[1])

        if fileLine.count('job_state'):
            state = fileLine.split(" = ")[1]
            if state == 'R':
                theJobInfo[theJobId]['state'] = 'running'
            elif state == 'Q':
                theJobInfo[theJobId]['state'] = 'pending'
	    elif state == 'H':
                theJobInfo[theJobId]['state'] = 'held'
	    elif state == 'E':
                theJobInfo[theJobId]['state'] = 'exited'
	    elif state == 'W':
                theJobInfo[theJobId]['state'] = 'waiting'
	    elif state == 'S':
                theJobInfo[theJobId]['state'] = 'suspended'
	    else:
                theJobInfo[theJobId]['state'] = state # fallback

        if fileLine.count('queue'):
            theJobInfo[theJobId]['queue'] = fileLine.split(" = ")[1]

        if fileLine.count('ctime'):
            theJobInfo[theJobId]['created'] = int(time.mktime(time.strptime(fileLine.split(" = ")[1], '%a %b %d %H:%M:%S %Y')))
        if fileLine.count('start_time') or fileLine.count('stime'):
            theJobInfo[theJobId]['start'] = int(time.mktime(time.strptime(fileLine.split(" = ")[1], '%a %b %d %H:%M:%S %Y')))
	    theJobInfo[theJobId]['end'] = 'n/a' # We do not record finished jobs (yet)

        if fileLine.count('exec_host'):
            theJobInfo[theJobId]['exec_host'] = fileLine.split(" = ")[1]

    for job in theJobInfo:
        if 'walltime' in theJobInfo[job].keys() and 'cputime' in theJobInfo[job].keys():
            wallSec = theJobInfo[job]['walltime']
            cputSec = theJobInfo[job]['cputime']
            cpuwallratio = 0

            if wallSec >= 180:
                cpuwallratio = round((float(cputSec)/wallSec*100),2)
            else:
                if 'cpupercent' in theJobInfo[job].keys():
                    cpuwallratio = theJobInfo[job]['cpupercent']

        
            theJobInfo[job]['cpueff'] = str(cpuwallratio)

	# Set group by prefix of user
	if theJobInfo[job]['user'].startswith('cmsmcp'):
	    theJobInfo[job]['group'] = 'cmsmcp'
	elif theJobInfo[job]['user'].startswith('cmst1p'):
	    theJobInfo[job]['group'] = 'cmst1p'
	elif theJobInfo[job]['user'].startswith('dcms'):
	    theJobInfo[job]['group'] = 'dcms'
	elif 'cms' in theJobInfo[job]['user']:
	    theJobInfo[job]['group'] = 'cmsother'
	else:
	    theJobInfo[job]['group'] = 'all'

    jobSummary = {}
    theMinRatio = 10

    for expr in exprJobSummary:
        jobSummary[expr] = {}
        jobSummary[expr]['jobs'] = 0
        jobSummary[expr]['running'] = 0
        jobSummary[expr]['ncpus'] = 0
        jobSummary[expr]['pending'] = 0
        jobSummary[expr]['held'] = 0
        jobSummary[expr]['walltime'] = 0
        jobSummary[expr]['cputime'] = 0
        jobSummary[expr]['ratio'+str(theMinRatio)] = 0
        for job in theJobInfo:
            if checkGroup(theJobInfo[job]['group'], expr, exprJobSummary):
                jobSummary[expr]['jobs'] += 1
                if 'state' in theJobInfo[job].keys():
                    if theJobInfo[job]['state'] == "running":
                        jobSummary[expr]['running'] += 1
                        if 'ncpus' in theJobInfo[job].keys() and int(theJobInfo[job]['ncpus']) > 0:
                          jobSummary[expr]['ncpus'] += int(theJobInfo[job]['ncpus'])
                        else:
                          jobSummary[expr]['ncpus'] += 1
                    elif theJobInfo[job]['state'] == "pending":
                        jobSummary[expr]['pending'] += 1
                    elif theJobInfo[job]['state'] == "held":
                        jobSummary[expr]['held'] += 1
                        
                if 'cpueff' in theJobInfo[job].keys():
                    if float(theJobInfo[job]['cpueff']) <=theMinRatio:
                        jobSummary[expr]['ratio'+str(theMinRatio)] += 1
                if jobSummary[expr]['ncpus'] < jobSummary[expr]['running']:
                    print "WARNING: cores < running jobs:", jobSummary[expr]['ncpus'], "<", jobSummary[expr]['running']

		if 'walltime' in theJobInfo[job].keys():
		    jobSummary[expr]['walltime'] += theJobInfo[job]['walltime']
		if 'cputime' in theJobInfo[job].keys():
		    jobSummary[expr]['cputime'] += theJobInfo[job]['cputime']

        if jobSummary[expr]['walltime'] > 0:
            jobSummary[expr]['cpueff'] = round(float(jobSummary[expr]['cputime'])/jobSummary[expr]['walltime']*100, 2);

    print "qstatXMLdump.py: processing finished."
    print "qstatXMLdump.py: start xml output."

    doc = Document()
    
    jobInfo = doc.createElement("jobinfo")
    doc.appendChild(jobInfo)

    header = doc.createElement("header")

    batch = doc.createElement("batch")
    text = doc.createTextNode("PBS")
    batch.appendChild(text)
    header.appendChild(batch)

    date = doc.createElement("date")
    text = doc.createTextNode(str(int(theQstatInfo['start'])))
    date.appendChild(text)
    header.appendChild(date)

    site = doc.createElement("site")
    text = doc.createTextNode("T1_DE_KIT")
    site.appendChild(text)
    header.appendChild(site)

    jobInfo.appendChild(header)

    # Only job details for cms jobs written out
    jobDetails = doc.createElement("jobs")
    jobInfo.appendChild(jobDetails)
    jobDetails.setAttribute('group',string.join(exprJobDetails,","))

    for job in theJobInfo:
        userin = False
        for groupname in exprJobDetails:
            if checkGroup(theJobInfo[job]['group'], groupname, exprJobSummary):
                userin = True

        if userin:
            jobNode = doc.createElement("job")
	    group = None
	    state = None
            for tag in theJobInfo[job]:
	        element = doc.createElement(tag)
	        node = doc.createTextNode(str(theJobInfo[job][tag]))
	        element.appendChild(node)
                jobNode.appendChild(element)
		if tag == 'state': state = str(theJobInfo[job][tag])
		if tag == 'group': group = str(theJobInfo[job][tag])
	    if group is not None: jobNode.setAttribute('group', group)
	    if state is not None: jobNode.setAttribute('status', state)

            jobDetails.appendChild(jobNode)
   
    jobSum = doc.createElement("summaries")
    jobInfo.appendChild(jobSum)

    for vo in jobSummary:
        summary = doc.createElement('summary')
	summary.setAttribute('group', vo)
	if vo in exprJobSummary:
	    if exprJobSummary[vo] is not None:
	        summary.setAttribute('parent', exprJobSummary[vo])
        for entry in jobSummary[vo]:
	    element = doc.createElement(entry)
	    node = doc.createTextNode(str(jobSummary[vo][entry]))
	    element.appendChild(node)
            summary.appendChild(element)
 
        jobSum.appendChild(summary)
             
    # Print our newly created XML
    # print doc.toprettyxml(indent="  ")

    outXMLfile = open(theXMLFile,'w')
    outXMLfile.write(doc.toprettyxml(indent="  "))
    outXMLfile.close()

    print "qstatXMLdump.py: xml output finished."

    uploadFile(theXMLFile)
    

if __name__ == '__main__':

    theBatchServers = 'lrms3 lrms1'
    theLockFile     = '/tmp/qstatXMLdump.lock'

    # Map of group to parent group
    exprJobSummary  = {'all': None,
                       'cms': 'all',
		       'cmsproduction': 'cms',
		       'cmsother': 'cms',
		       'dcms': 'cms',
		       'cmsmcp': 'cmsproduction',
		       'cmst1p': 'cmsproduction'}

    exprJobDetails  = ['cms']

    print "qstatXMLdump.py: Initializing..."
    print "qstatXMLdump.py: Servers to query: "+theBatchServers

#    print "qstatXMLdump.py: Checking lockfile... "
    # Check if process is already running
#    if os.path.exists(theLockFile):
#        print "qstatXMLdump.py: process locked by "+theLockFile
#        print "                 Exit with code 1"
#        sys.exit(1)
        
#    print "qstatXMLdump.py: Creating lockfile: "+theLockFile
    # Create lock file for this job
#    open(theLockFile,'w').close()

    # Execute qstat commands
    servers = string.split(theBatchServers," ")

    combinedStartTime = time.time() #time.strftime("%a, %d %b %Y, %H:%M:%S")

    for server in servers:
	print "qstatXMLdump.py: Create output for server: "+server
	theQstatCommand = '/usr/pbs/bin/qstat -f @'+server
	theLogFile      = '/tmp/qstat_'+server+'.log'
	theXMLFile      = '/tmp/qstat_'+server+'.xml'

        startTime = time.time() #time.strftime("%a, %d %b %Y, %H:%M:%S")
	os.system(theQstatCommand+' > '+theLogFile)
        stopTime  = time.time() #strftime("%a, %d %b %Y, %H:%M:%S")

	createXMLFile(theLogFile, theXMLFile, startTime, stopTime)
    
    combinedStopTime = time.time() #time.strftime("%a, %d %b %Y, %H:%M:%S")

    # Create combined information (all servers)
    print "qstatXMLdump.py: Create combined output for all servers..."
    theCombinedLogFile = '/tmp/qstat.log'
    theCombinedXMLFile = '/tmp/qstat.xml'

    os.system('rm -f '+theCombinedLogFile)
    for server in servers:
	os.system('cat /tmp/qstat_'+server+'.log >> '+theCombinedLogFile)

    createXMLFile(theCombinedLogFile, theCombinedXMLFile, combinedStartTime, combinedStopTime)

#    print "qstatXMLdump.py: Removing lockfile: "+theLockFile
    # Remove lock file    
#    os.remove(theLockFile)

    print "qstatXMLdump.py: Done."

