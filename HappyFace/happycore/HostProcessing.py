# Module that provides some functionality for easier working with hosts.

import subprocess
import os
import re
from threading import Thread
import socket

# class that performs an asynchronous ping
class PingHost(Thread):
    def __init__ (self,host):
        Thread.__init__(self)
        # host is the target of the ping
        self.host = host

        # there are three outputs, status_short, status_long, status_rtt (round trip time)
        self.status_short = 'fail'
        self.status_long = 'Ping not issued.'
        self.status_rtt = 'fail'

    def run(self):

        # start the ping
        try:
            # reset output values before
            self.status_short = 'fail'
            self.status_long = 'Ping test did not complete.'
            self.status_rtt = 'fail'

            # issue double ping
            proc = subprocess.Popen(['ping', '-q', '-c2', self.host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except Exception as e:
            self.status_long = 'Unable to issue ping: ' + e.__str__()
            return

        # fetch output of process
        proc_out = proc.stdout.read().strip()
        proc_err = proc.stderr.read().strip()

        # check output for patterns
        match = re.search('(\d) received', proc_out)
        if match:
            received = int(match.group(1))
        else:
            received = 0

        match = re.search('rtt min/avg/max/mdev = ([0123456789\.,]+)/([0123456789\.,]+)/([0123456789\.,]+)/([0123456789\.,]+) ms', proc_out)
        if match:
            rtt = float(match.group(2))
            self.status_rtt = str(rtt) + 'ms'
        else:
            rtt = 0
            self.status_rtt = 'fail'

        # now, fill the status outputs
        # status_short is always ok or fail
        # status_long contains a longer description with more information
        if received == 2:
            self.status_short = 'ok'
            self.status_long = 'Ping successful.'
            if rtt>0:
                self.status_long += ' RTT: ' + str(rtt) + 'ms'

        elif received == 1:
            self.status_short = 'fail'
            self.status_long = 'One of two pings failed.'
            if proc_err != '':
                self.status_long += 'Error message: ' + proc_err

        else:
            self.status_short = 'fail'
            self.status_long = 'Pings failed.'
            if proc_err != '':
                self.status_long += 'Error message: ' + proc_err


# class that performs an asynchronous name lookup via the host command
class NameHost(Thread):
    def __init__ (self,host):
        Thread.__init__(self)
        # host determines the pc to be looked up
        self.host = host

        #  there are three outputs, a lookup status, a long name (alias) and the ip
        self.name_status = 'fail'
        self.name_long = host
        self.ip = ''

    def run(self):

        # start the lookup
        try:
            # reset output values
            self.name_status = 'fail'
            self.name_long = self.host
            self.ip = ''

            # issue the host lookup
            self.result = socket.gethostbyaddr(self.host)
            self.ip = self.result[2][0]
            self.name_long = self.result[0]
            self.name_status = 'ok'
            return
        except:
            try:
                # sometimes socket.gethostbyaddr will not resolve
                # then, we fall back to the slow method: starting host command
		              proc = subprocess.Popen(['host', self.host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                self.name_status = 'fail'
                self.name_long = self.host
                self.ip = ''
                return

        # fet the output of the process
        proc_out = proc.stdout.read().strip()
        proc_err = proc.stderr.read().strip()

        # ... and retrieve relevant information form the output
        match = re.search('is an alias for (.*).', proc_out)
        if match:
            # if self.host is an alias, the long_name is the original name
            self.name_long = match.group(1)

        # fetch the ip
        match = re.search('has address (\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})', proc_out)
        if match:
            self.ip = match.group(1)
            self.name_status = 'ok'
        else:
            self.ip = ''


# this class provides methods for easy access to files with host lists
# a hostlist is seperated into sections that may contain any number of hostnames
# ex.:
# [nodes]
# node[1...12], config[1...12], encl1
# server[1...4]
# In this example, there is one sections containing 12 hosts node1 to node12
# with coresponding configuration host config1 to config2 and enclosure encl1.
# The section nodes additionally contains the hosts server1 to server4 which do
# not have a configuration host or an enclosure

class HostList:

    def __init__(self, parent):
        # pass a parent object to allow HostList to pass on error/warning messages
        # parent thus has to be derived from ModuleHelper
        self.sections = {}
        self.hostlist = {}
        self.parent = parent

    def __init__(self, parent, hostlist):
        self.sections = {}
        self.hostlist = {}
        self.parent = parent
        self.readHostList(hostlist)

    def readHostList(self, hostlist):
        # read the hostlist with filename given in parameter hostlist

        if os.path.exists(hostlist):
            # open logfile and read lines
            try:
                file = open(hostlist, 'r')
                lines = file.readlines()
                file.close()
                
            except Exception as e:
                self.parent.printError('Unable to open the specified hostlist "%s":\n%s\n' % (hostlist, e.__str__()))
                return
        else:
            # show error
            self.parent.printError('The specified hostlist "%s" does not exist.\n' % hostlist)
            return

        # go through file... we need some status variables
        cursection = ''
        linenumber = 0
        sections = {}
        sectionnumbers = {}
        sectionnumber = 0

        # go through all lines in file consecutively
        for line in lines:
            line = line.strip()
            linenumber += 1

            # ignore comments
            if line.startswith('#'):
                continue
            if line == '':
                continue

            # section definition
            if line.startswith('[') and line.endswith(']'):
                cursection = line[1:-1].strip()

                # only if section for the first time
                if not sectionnumbers.has_key(cursection):
                    # add section and count its number (position of first appearance)
                    sectionnumber += 1
                    sections[cursection] = {}
                    sectionnumbers[cursection] = sectionnumber
            else:
                # lines consist of three parts:
                # short name;ilo name;enclosure name
                line = line.split(',')
                if len(line)>3:
                    self.parent.printError('Warning while reading hostlist "%s": Expecting the character ";" at most three times in line %i.\n' % (hostlist, linenumber))
                elif cursection != '':
                    # fill missing arguments
                    if len(line) < 3:
                        line.extend(['']*(3-len(line)))

                    # add to current section
                    lhosts = self.expandString(line[0])
                    lconfig = self.expandString(line[1])
                    lenclosure = self.expandString(line[2])

                    # make lists equally long by repeating the last entry
                    if len(lconfig) < len(lhosts):
                        lconfig.extend([lconfig[-1]]*(len(lhosts)-len(lconfig)))
                    if len(lenclosure) < len(lhosts):
                        lenclosure.extend([lenclosure[-1]]*(len(lhosts)-len(lenclosure)))

                    # and add info for hosts to current section
                    for i in range(0, len(lhosts)):
                        # gather information for host
                        h = {}
                        h['section'] = cursection
                        h['section_number'] = '0'*(2-len(str(sectionnumbers[cursection])))+str(sectionnumbers[cursection])
                        h['line_number'] = '0'*(3-len(str(linenumber)))+str(linenumber)
                        h['name_short'] = lhosts[i].strip()
                        h['config_name'] = lconfig[i].strip()
                        h['enclosure_name'] = lenclosure[i].strip()

                        sections[cursection][lhosts[i].strip()] = h

                else:
                    self.parent.printError('Warning while reading hostlist "%s": No section specified for host in line %i.\n' % (hostlist, linenumber))

        self.sections = sections
        
        # append all hosts in all sections to hostlist
        self.hostlist = {}
        for s in self.sections:
            for h in self.sections[s]:
                self.hostlist[h] = self.sections[s][h]
        

    def expandString(self, expstring):
        # expands any *[aa...bb]* in the given string to a list of strings
        # ex.: node[1...12] is expanded to node1, node2, node3, ..., node12
        # ex.: n[01...12] is expanded to n01, n02, n03, ..., n09, n10, n11, n12

        # begin with just the entry we already have
        list = [expstring]
        cont = True

        # continue expanding the list as long as changes are made
        while cont == True:
            cont = False

            # in each iteration, we build a new list out of the old one
            list2 = []

            for item in list:
                # search for a pattern like [000...000]
                match = re.search('\[(\d{1,3})\.\.\.(\d{1,3})\]', item)

                if match:
                    # patter found -> expand entry
                    cont = True

                    # beginning index and end index
                    ibegin = int(match.group(1))
                    iend = int(match.group(2))
                    # minimal length of entries (to be filled with zeroes)
                    imin = len(match.group(1))

                    # expand current item
                    for i in range(ibegin, iend+1):
                        # format current entry
                        stri = str(i)
                        if len(stri)< imin:
                            stri = '0'*(imin-len(stri)) + stri

                        # append new item into new list
                        list2.append(item[:match.start()] + stri + item[match.end():])
                else:
                    # if not found -> no changes
                    list2.append(item)

            # replace the old list with the new one
            list = list2

        # return the list of nothing more to expand
        return list

    def getHosts(self, sectionlist = '*'):
        # return a list of all hosts that belong to a section in sectionlist
        # if sectionlist is '*' (default), all hosts in all sections are listed

        if sectionlist == '*':

            return self.hostlist

        else:
            # split sectionlist to an array
            sectionlist = sectionlist.split(',')
            ret = {}

            # go through all listed sections
            for s in sectionlist:

                # skip empty namings
                s = s.strip();
                if s == '':
                    continue;

                if self.sections.has_key(s):
                    # append all hosts in this section to return value
                    for h in self.sections[s]:
                        ret[h] = self.sections[s][h]

                else:
                    self.parent.printError('Warning: Section "%s" was not defined in host list.\n' % s)

            return ret
