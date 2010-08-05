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

def callWithTimeoutChristophe(timeout, *args):
    old = signal.getsignal(signal.SIGCHLD)
    try:
        signal.signal(signal.SIGCHLD, lambda x, y: 0)
        pid = os.spawnlp(os.P_NOWAIT, args[0], *args)
        time.sleep(timeout)
        xpid, status = os.waitpid(pid, os.WNOHANG)
        if xpid == 0:
            os.kill(pid, signal.SIGTERM)
            xpid, status = os.waitpid(pid, 0)
    finally:
        signal.signal(signal.SIGCHLD, old)

    return status



def callWithTimeout(timeout, command, arg=""):
    old = signal.getsignal(signal.SIGCHLD)
    try:
        signal.signal(signal.SIGCHLD, lambda x, y: 0)
        proc = popen2.Popen3([command,arg],True)
        pid = proc.pid
        time.sleep(timeout)
        xpid, status = os.waitpid(pid, os.WNOHANG)
        if xpid == 0:
            os.kill(pid, signal.SIGTERM)
            xpid, status = os.waitpid(pid, 0)
    finally:
        signal.signal(signal.SIGCHLD, old)

    return status,proc.fromchild.readlines()

# Check whether the given chk_group is a subgroup of group
def checkGroup(chk_group, group, group_table):
    while chk_group != group:
        if chk_group == None or chk_group not in group_table:
	    return False
        chk_group = group_table[chk_group]
    return True

if __name__ == '__main__':

    theQstatCommand = '/usr/pbs/bin/qstat -f'
    theLogFile      = '/tmp/qstat.log'
    theXMLFile      = '/tmp/qstat.xml'
#    theLockFile     = '/tmp/qstatXMLdump.lock'

    # Map of group to parent group
    exprJobSummary  = {'all': None,
                       'cms': 'all',
		       'cmsproduction': 'cms',
		       'cmsother': 'cms',
		       'dcms': 'cms',
		       'cmsmcp': 'cmsproduction',
		       'cmst1p': 'cmsproduction'}

    exprJobDetails  = ['cms']

# Check if process is already running
#    if os.path.exists(theLockFile):
#        print "qstatXMLdump.py: process locked by "+theLockFile
#        print "                 Exit with code 1"
#        sys.exit(1)
        

# Create lock file for this job
#    open(theLockFile,'w').close()


    theQstatInfo = {}

    theQstatInfo["start"] = time.strftime("%a, %d %b %Y, %H:%M:%S")
    print "qstatXMLdump.py: Starting qstat"

#    status,out = callWithTimeout(180,'qstat','-f')

    status = 0

    os.system(theQstatCommand+' > '+theLogFile)
    out = open(theLogFile).readlines()

    if status != 0 :
        print "qstatXMLdump.py: "+theQstatCommand+" with exitcode != 0."
        sys.exit(1)
    else:
        print "qstatXMLdump.py: "+theQstatCommand+" finished."

    theQstatInfo["end"]   = time.strftime("%a, %d %b %Y, %H:%M:%S")


    print "qstatXMLdump.py: start processing."
    
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
            theJobInfo[theJobId]['created'] = fileLine.split(" = ")[1]

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
                    elif theJobInfo[job]['state'] == "pending":
                        jobSummary[expr]['pending'] += 1
                    elif theJobInfo[job]['state'] == "held":
                        jobSummary[expr]['held'] += 1
                        
                if 'cpueff' in theJobInfo[job].keys():
                    if float(theJobInfo[job]['cpueff']) <=theMinRatio:
                        jobSummary[expr]['ratio'+str(theMinRatio)] += 1

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

    batchSystem = doc.createElement("additional")
    batchSystem.setAttribute('batchsystem', 'PBS')
    jobInfo.appendChild(batchSystem)

    qstatInfo = doc.createElement("qstatinfo")
    for tag in theQstatInfo:
        qstatInfo.setAttribute(tag,str(theQstatInfo[tag]))
    batchSystem.appendChild(qstatInfo)
    


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
            for tag in theJobInfo[job]:
	        element = doc.createElement(tag)
	        node = doc.createTextNode(str(theJobInfo[job][tag]))
	        element.appendChild(node)
                jobNode.appendChild(element)

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
    
# Remove lock file    
#    os.remove(theLockFile)
    
