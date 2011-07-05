from ModuleBase import *
from ModuleHelper import *
from HostProcessing import *

import time
import sys

        
class hwpingtest(ModuleBase, ModuleHelper):

    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self, module_options)
        self.status = 1
        
        # prepare pbs info source
        self.prepareInput('pbsinfo', 'pbs')
        
        # number of warnings before module status set to warning/critical
        self.warningcount = self.configGetInt('hosts', 'warningcount', 4)
        self.criticalcount = self.configGetInt('hosts', 'criticalcount', 10)

        # read hostlist given in config
        self.hostlist = HostList(self, self.configService.get('hosts','hostlist'))

        # sections of relevant hosts
        self.criticalhosts = self.hostlist.getHosts(self.configService.get('hosts','criticalhosts'))
        self.warninghosts = self.hostlist.getHosts(self.configService.get('hosts','warninghosts'))
        self.ignorehosts = self.hostlist.getHosts(self.configService.get('hosts','ignorehosts'))
        self.allhosts = self.hostlist.getHosts(self.configService.get('hosts','criticalhosts')+','+self.configService.get('hosts','warninghosts')+','+self.configService.get('hosts','ignorehosts'))

        # read display configuration from config file
        self.display = self.readTableConfig('display')

        # fetch some debug flags
        # fast pings triggers smaller waiting times which can cause inaccuracy
        self.fastpings = self.configGetBool('debug', 'fastpings', '0')

        # statusbar displays a bar that
        self.statusbar = self.configGetBool('debug', 'statusbar', '0')
        
        # definition of the database keys and pre-defined values
        # possible format: StringCol(), IntCol(), FloatCol(), ...
        self.db_keys['host_status'] = StringCol()
        self.db_values['host_status'] = ''

    def printstatusbar(self, status):
        # print a status bar (empty if status = 0, full if status = 1)
        if self.statusbar:
            if self.laststatus != int(status*20):
                self.laststatus = int(status*20)
                sys.stdout.write('hwpingtest [' + '#'*int(status*20) + ' '*(20-int(status*20)) + ']\r')
                sys.stdout.flush()

    def run(self):
        # variables for status bar (current status and max status)
        stat = 0.0
        maxstat = len(self.allhosts)+90
        self.laststatus = 0

        # fetch additional pbs info
        pbsinfo = self.fetchInput('pbsinfo', 'pbs')
        pbs = []

        # if pbsinfo was not given, the array will be empty and this will
        # be skipped automatically
        pbsmalformed = False
        for entry in pbsinfo:
            # a line in pbs info has the format
            # computername          state                  description
            # we will split the line at spaces 

            # strip empty lines
            entry = entry.strip()
            if entry == '':
                continue

            info = []
            spacepos = entry.find(' ')
            if spacepos < 0:
                if pbsmalformed == False:
                    self.printError('The PBS information seems to be malformed.')
                    pbsmalformed = True
                continue

            # fetch computer name
            info.append(entry[0:spacepos])
            entry = (entry[spacepos:]).strip()
            
            spacepos = entry.find(' ')
            if spacepos < 0:
                # fetch state
                info.append(entry)
                # fetch description (empty in this case)
                info.append('')
            else:
                # fetch state
                info.append(entry[0:spacepos])
                # fetch description
                info.append((entry[spacepos:]).strip())
                
            # append info to array
            pbs.append(info)
            

        # go through all hosts
        for h in self.allhosts:
            host = self.allhosts[h]

            # perform an asynchronous ping on host to check status
            host['status_short'] = 'fail'
            host['status_long'] = 'fail'
            host['status_rtt'] = 'fail'

            host['pingaling'] = PingHost(host['name_short'])
            host['pingaling'].start()

            # perform asynchronous host resulution of host name, config name, enclosure name
            host['naming'] = NameHost(host['name_short'])
            host['naming'].start()

            if host['config_name'] != '':
                host['config_naming'] = NameHost(host['config_name'])
                host['config_naming'].start()

            if host['enclosure_name'] != '':
                host['enclosure_naming'] = NameHost(host['enclosure_name'])
                host['enclosure_naming'].start()

            # to avoid starting to many pings at the same time,
            # we take a short break
            if self.fastpings:
                time.sleep(0.03)
            else:
                time.sleep(0.08)

            stat += 1
            self.printstatusbar(stat/maxstat)

        # wait some seconds for all asynchronous requests to finish
        for i in range(0, 40):
            stat += 1
            self.printstatusbar(stat/maxstat)
            if self.fastpings:
                time.sleep(0.06)
            else:
                time.sleep(0.10)

        secondtime = False
        # fetch results
        for h in self.allhosts:
            host = self.allhosts[h]
            
            # fetch ping result
            host['pingaling']._Thread__stop()
            host['status_short'] = host['pingaling'].status_short
            host['status_long'] = host['pingaling'].status_long
            host['status_rtt'] = host['pingaling'].status_rtt
            
            # fetch naming result
            host['naming']._Thread__stop()
            host['ip'] = host['naming'].ip
            host['name_long'] = host['naming'].name_long
            host['name_status'] = host['naming'].name_status

            domainend = host['name_long'].find('.')
            if domainend < 0:
                host['name_indomain'] = host['name_long']
                host['name_domain'] = ''
            else:
                host['name_indomain'] = host['name_long'][0:domainend]
                host['name_domain'] = host['name_long'][domainend+1:]


            if len(pbs) == 0:
                host['pbs_state'] = 'no info'
                host['pbs_description'] = 'No PBS info.'
            else:
                host['pbs_state'] = 'online'
                host['pbs_description'] = 'online'


            # search for pbs info in pbs array
            for info in pbs:
                if ((len(host['name_long']) > 0) and (host['name_long'] == info[0])) or ((len(host['name_indomain']) > 0) and (host['name_indomain'] == info[0])) or ((len(host['name_short']) > 0) and (host['name_short'] == info[0])):
                    host['pbs_state'] = info[1]
                    host['pbs_description'] = info[2]

                    # empty description -> use state for description
                    if host['pbs_description'].strip() == '':
                        host['pbs_description'] = host['pbs_state']
                    
                    break

            # fetch config naming result if it was required
            if host['config_name'] != '':
                host['config_naming']._Thread__stop()
                
                if host['config_naming'].name_status == 'ok':
                    host['config_ip'] = host['config_naming'].ip
                    host['config_name_long'] = host['config_naming'].name_long
                else:
                    host['config_ip'] = ' '
                    host['config_name_long'] = ' '
            else:
                host['config_ip'] = ' '
                host['config_name_long'] = ' '

            # fetch enclosure naming result if it was required
            if host['enclosure_name'] != '':
                host['enclosure_naming']._Thread__stop()

                if host['enclosure_naming'].name_status == 'ok':
                    host['enclosure_ip'] = host['enclosure_naming'].ip
                    host['enclosure_name_long'] = host['enclosure_naming'].name_long
                else:
                    host['enclosure_ip'] = ' '
                    host['enclosure_name_long'] = ' '
            else:
                host['enclosure_ip'] = ' '
                host['enclosure_name_long'] = ' '

            # ping failures?
            if host['status_short'] == 'fail':
                # try a second time
                host['pingaling'] = PingHost(host['name_short'])
                host['pingaling'].start()
                secondtime = True
                
                if self.fastpings:
                    time.sleep(0.06)
                else:
                    time.sleep(0.15)
                
        # if any host failed, check failed hosts again
        if secondtime:
            # wait some seconds for all asynchronous requests to finish
            for i in range(0, 50):
                stat += 1
                self.printstatusbar(stat/maxstat)
                if self.fastpings:
                    time.sleep(0.06)
                else:
                    time.sleep(0.10)

            # search for hosts that failed the first time
            for h in self.allhosts:
                host = self.allhosts[h]

                if host['status_short'] == 'fail':
                    # this was a host that failed
                    # get the status of the second try
                    # and kill any remaining pings
                    host['pingaling']._Thread__stop()
                    host['status_short'] = host['pingaling'].status_short
                    host['status_long'] = host['pingaling'].status_long
                    host['status_rtt'] = host['pingaling'].status_rtt

        
        # finished!
        self.printstatusbar(1)

        
        ################################################
        # all data has been gathered -- output follows

        self.db_values['host_status'] = self.packArray(self.allhosts)

        # we still need to determine the status of the module...
        # therefore, go through all hosts and count how many are offline
        offlinecount = 0
        for h in self.allhosts:
            host = self.allhosts[h]

            if (host['status_short'] != 'ok') and (host['name_short'] not in self.ignorehosts):
                offlinecount += 1
                if host['name_short'] in self.criticalhosts:
                    self.status = 0

        if offlinecount >= self.warningcount:
            self.status = min(self.status, 0.5)
        if offlinecount >= self.criticalcount:
            self.status = min(self.status, 0)
        
    def output(self):
        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call

        # data will be parsed first
        # the first lines up to double new lines consist of the available fields
        # after that, for each host, these fields are repeated, one field per line
        module_content = """<?php

        // create array of critical hosts
        $criticalhosts = array("""

        bfirst = True
        for host in self.criticalhosts:
            if bfirst == False:
                 module_content += ','
            bfirst = False
            module_content += self.toPHPStr(host)

        module_content += """);

        // unpack stored information from database into var $ilos (and $keys)
        """ + self.unpackArrayPHP('$data["host_status"]', '$hosts', '$keys') + """

        // create raw view from $hosts
        """ + self.rawDataPHP('$hosts', '$div_raw') + """

        // create table views from $hosts
        // sort first
        """ + self.sortTablePHP(self.display, '$hosts') + """

        // create tables
        """ + self.beginTablePHP(self.display, '$tableall') + """
        """ + self.beginTablePHP(self.display, '$tableoffline') + """


        $tableofflinecount = 0;
        $tableallcount = 0;

        // build all tables
        foreach ($hosts as $host)
        {
            // determine status of current host/row
            if($host['status_short'] == 'ok')
                $tclass = 'ok';
            else if(in_array($host['name_short'], $criticalhosts))
            {
                $tclass = 'critical';
                $tableofflinecount += 1;
            }
            else
            {
                $tclass = 'warning';
                $tableofflinecount += 1;
            }

            if(($host['status_short'] != 'ok') or (($host['pbs_state'] != 'online') and ($host['pbs_state'] != 'no info')))
            {
            """ + self.addRowPHP(self.display, '$tclass', '$host', '$tableoffline') + """
            }

            """ + self.addRowPHP(self.display, '$tclass', '$host', '$tableall') + """
            $tableallcount += 1;

        }
        
        // close tables
        """ + self.endTablePHP(self.display, '$tableall') + """
        """ + self.endTablePHP(self.display, '$tableoffline') + """
        
        if($tableallcount == 0)
            $tableall = '""" + self.htmlMessage('There are no nodes.', 'error') + """';

        if($tableofflinecount == 0)
            $tableoffline = '""" + self.htmlMessage('No nodes are offline.', 'ok') + """';
        else if($tableofflinecount < """ +  str(self.warningcount) + """)
            $tableoffline .= '""" + self.htmlMessage('\'.$tableofflinecount.\' nodes are offline.', 'ok') + """';
        else if($tableofflinecount < """ +  str(self.criticalcount) + """)
            $tableoffline .= '""" + self.htmlMessage('\'.$tableofflinecount.\' nodes are offline.', 'warning') + """';
        else
            $tableoffline .= '""" + self.htmlMessage('\'.$tableofflinecount.\' nodes are offline.', 'error') + """';

        $offlinedescription = 'offline nodes ('.$tableofflinecount.')';
        $alldescription = 'all nodes ('.$tableallcount.')';
        $rawdescription = 'raw data view';

        """ + self.showDivDropDownPHP([('hwpings_div_offline', '$offlinedescription', '$tableoffline'),('hwpings_div_all', '$alldescription', '$tableall'),('hwpings_div_raw', '$rawdescription', '$div_raw')]) + """

	?>"""

        return self.PHPOutput(module_content)    
