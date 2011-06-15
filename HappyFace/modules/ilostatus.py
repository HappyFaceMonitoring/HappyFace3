from ModuleBase import *
from ModuleHelper import *
from HostProcessing import *
from lxml import etree


class ilostatus(ModuleBase, ModuleHelper):

    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self, module_options)
        self.status = 1
        
        # number of warnings before module status set to warning/critical
        self.warningcount = self.configGetInt('setup', 'warningcount', 10)
        self.criticalcount = self.configGetInt('setup', 'criticalcount', 20)

        # read hostlist given in config
        self.hostlist = HostList(self, self.configService.get('hosts','hostlist'))

        # sections of relevant hosts from hostlist file
        self.ilohosts = self.hostlist.getHosts(self.configService.get('hosts','ilohosts'))

        # collect corresponding ilos of ilohosts
        self.ilos = {}
        self.enclosures = {}
        for h in self.ilohosts:
            host = self.ilohosts[h]

            if(host['config_name'] != '') and (host['config_name'] not in self.ilos):
                ilo = {}
                # store the information about this ilo
                ilo['name_short'] = host['config_name']
                ilo['host_name'] = host['name_short']
                ilo['section'] = host['section']
                ilo['section_number'] = host['section_number']
                ilo['line_number'] = host['line_number']
                ilo['enclosure_name'] = host['enclosure_name']

                if (host['enclosure_name'] not in self.enclosures.keys()) and (host['enclosure_name'] != ''):
                    enc = {}
                    enc['name_short'] = host['enclosure_name']
                    self.enclosures[host['enclosure_name']] = enc

                self.ilos[host['config_name']] = ilo

        # read display configuration from config file
        self.display = self.readTableConfig('display')

        # read sort order (including tokens)
        # example: %section_number%;%name_long%
        self.sortorder = self.configService.getDefault('display', 'sort', '%section_number%;%name_long%')
        
        # definition of the database keys and pre-defined values
        self.db_keys['message'] = StringCol() # for storing query errors, etc
        self.db_values['message'] = ''
        self.db_keys['ilos'] = StringCol() # for storing information about all ilos
        self.db_values['ilos'] = ''
        self.db_keys['enclosures'] = StringCol() # for storing information about all ilos
        self.db_values['enclosures'] = ''
        
    def run(self):
        
        result = ''
        warningcount = 0

        # first, ping all enclosures and all ilos
        for i in self.ilos:
            ilo = self.ilos[i]

            # perform an asynchronous ping on host to check status
            ilo['ping_status_short'] = 'fail'
            ilo['ping_status_long'] = 'fail'
            ilo['ping_status_rtt'] = 'fail'

            ilo['pingaling'] = PingHost(ilo['name_short'])
            ilo['pingaling'].start()

            # asynchronous naming
            ilo['naming'] = NameHost(ilo['name_short'])
            ilo['naming'].start()

            ilo['ilo_status_short'] = 'not available'
            ilo['ilo_status_long'] = 'not available'
            ilo['access_status_short'] = 'not available'
            ilo['access_status_long'] = 'not available'
            ilo['class'] = 'undefined'
            
            # to avoid starting to many pings at the same time,
            # we take a short break
            time.sleep(0.08)
            
        for e in self.enclosures:
            enc = self.enclosures[e]
            
            enc['ping_status_short'] = 'fail'
            enc['ping_status_long'] = 'fail'
            enc['ping_status_rtt'] = 'fail'

            enc['pingaling'] = PingHost(enc['name_short'])
            enc['pingaling'].start()

            # asynchronous naming
            enc['naming'] = NameHost(enc['name_short'])
            enc['naming'].start()

            # to avoid starting to many pings at the same time,
            # we take a short break
            time.sleep(0.08)

        # wait for all pings and namings to finish
        time.sleep(8)

        # fetch results
        for i in self.ilos:
            ilo = self.ilos[i]

            # fetch ping result
            ilo['pingaling']._Thread__stop()
            ilo['ping_status_short'] = ilo['pingaling'].status_short
            ilo['ping_status_long'] = ilo['pingaling'].status_long
            ilo['ping_status_rtt'] = ilo['pingaling'].status_rtt

            # fetch naming result
            ilo['naming']._Thread__stop()
            ilo['ip'] = ilo['naming'].ip
            ilo['name_long'] = ilo['naming'].name_long
            ilo['name_status'] = ilo['naming'].name_status

            domainend = ilo['name_long'].find('.')
            if domainend < 0:
                ilo['name_indomain'] = ilo['name_long']
                ilo['name_domain'] = ''
            else:
                ilo['name_indomain'] = ilo['name_long'][0:domainend]
                ilo['name_domain'] = ilo['name_long'][domainend+1:]

        for e in self.enclosures:
            enc = self.enclosures[e]

            # fetch ping result
            enc['pingaling']._Thread__stop()
            enc['ping_status_short'] = enc['pingaling'].status_short
            enc['ping_status_long'] = enc['pingaling'].status_long
            enc['ping_status_rtt'] = enc['pingaling'].status_rtt

            # fetch naming result
            enc['naming']._Thread__stop()
            enc['ip'] = enc['naming'].ip
            enc['name_long'] = enc['naming'].name_long
            enc['name_status'] = enc['naming'].name_status

            domainend = enc['name_long'].find('.')
            if domainend < 0:
                enc['name_indomain'] = enc['name_long']
                enc['name_domain'] = ''
            else:
                enc['name_indomain'] = enc['name_long'][0:domainend]
                enc['name_domain'] = enc['name_long'][domainend+1:]

        checkedencips = []
        
        # now, access the pingable enclosures
        ekeys = self.enclosures.keys()

        for e in ekeys:
            enc = self.enclosures[e]

            if enc['ip'] in checkedencips:
                # delete double enclosures (different name but same ip)
                del self.enclosures[e]
                continue
            elif enc['ip'] != '':
                checkedencips.append(enc['ip'])

            # skip unreachable enclosures
            if (enc['ip'] == '') or (enc['ping_status_short'] == 'fail'):
                result += self.htmlMessage('The enclosure %s does not respond to pings.</h3>\n' % enc['name_long'], 'error')
                warningcount += 4 # four points for a non-responding enclosure
                del self.enclosures[e]
                continue

            # query xml data
            queryurl = 'https://%s/xmldata?item=all' % enc['ip']
            # start download
            enc['site'] = elinksDownload(queryurl)

            time.sleep(0.08)

        
        # wait for all downloads to finish
        time.sleep(8)

        # and fetch their output
        for e in self.enclosures:
            enc = self.enclosures[e]
            
            try:
                if enc['site'].status_short == 'ok':
                    root = etree.fromstring(enc['site'].content)
                else:
                    root = ''

                if root == '':
                    result += self.htmlMessage('Could not query enclosure %s</h3>\n' % enc['name_long'], 'error')
                    warningcount += 4 # four points for a non-responding enclosure
                    continue

            except Exception as ex:
                result += self.htmlMessage('Could not query enclosure %s: %s</h3>\n' % (enc['name_long'], ex.__str__()), 'error')
                warningcount += 4 # four points for a non-responding enclosure
                continue

            # query blades
            blades = root.findall('INFRA2/BLADES/BLADE')

            # go through all blades and find blades with errors
            for blade in blades:
                stat = blade.find('STATUS').text

                # for each blade, search for corresponding ilo entry
                for i in self.ilos:
                    ilo = self.ilos[i]
                    # check for matching ip
                    if (blade.find('MGMTIPADDR').text == ilo['ip']) or (blade.find('MGMTIPADDR').text == ilo['name_short']):
                        # we have found the corresponding ilo, now fetch data
                        ilo['ilo_status_short'] = stat
                        
                        if stat.lower() not in ['ok', 'no_error', 'not_tested', 'not_relevant']:
                            if stat.lower() != 'degraded':
                                self.status = min(0, self.status)
                                ilo['class'] = 'critical'
                            else:
                                ilo['class'] = 'warning'
                        else:
                            ilo['class'] = 'ok'

                        # determine errors for blade
                        errors = []
                        context = etree.iterwalk(blade.find('DIAG'))
                        for action, elem in context:
                            if elem.tag == 'DIAG':
                                continue
                            if elem.text.lower() not in ['ok', 'no_error', 'not_tested', 'not_relevant']:
                                if elem.tag.lower() != 'degraded':
                                    ilo['class'] = 'critical'
                                errors.append(elem.tag)

                        # store a long version of the status
                        ilo['ilo_status_long']  = ', '.join(errors)
                        if ilo['ilo_status_long'] == '':
                            ilo['ilo_status_long'] = 'ok'
                        
                        # count all warnings
                        if ilo['class'] != 'ok':
                            warningcount += 1

                        # store information about the querying success
                        ilo['access_status_short'] = enc['site'].status_short
                        ilo['access_status_long'] = enc['site'].status_long    

        # check for module status
        if warningcount >= self.warningcount:
            self.status = min(self.status, 0.5)
        if warningcount >= self.criticalcount:
            self.status = min(self.status, 0)

        # create db entries for php readout
        self.db_values['message'] = result
        self.db_values['ilos'] = self.packArray(self.ilos)
        self.db_values['enclosures'] = self.packArray(self.enclosures)

    def output(self):

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call

        module_content = """<?php

        // unpack stored information from database into var $ilos (and $keys)
        """ + self.unpackArrayPHP('$data["ilos"]', '$ilos', '$keys') + """
        """ + self.unpackArrayPHP('$data["enclosures"]', '$enclosures', '$enckeys') + """

        // create raw view from $ilos
        """ + self.rawDataPHP('$ilos', '$div_raw') + """
        """ + self.rawDataPHP('$enclosures', '$div_encraw') + """

        // create table views from $ilos
        // sort first
        """ + self.sortTablePHP(self.display, '$ilos') + """

        // create tables
        """ + self.beginTablePHP(self.display, '$tableall') + """
        """ + self.beginTablePHP(self.display, '$tablewarning') + """

        // go through all entries
        $allcount = 0;
        $warningcount = 0;
        foreach ($ilos as $ilo)
        {
            $tclass = $ilo['class'];
            if(($tclass != 'ok') && ($tclass != 'undefined'))
            {
            """ + self.addRowPHP(self.display, '$tclass', '$ilo', '$tablewarning') + """
                $warningcount += 1;
            }
            
            """ + self.addRowPHP(self.display, '$tclass', '$ilo', '$tableall') + """

            $allcount += 1;
        }

        // close tables
        """ + self.endTablePHP(self.display, '$tableall') + """
        """ + self.endTablePHP(self.display, '$tablewarning') + """

        $warningdescription = 'ILOs with warnings/errors ('.$warningcount.')';
        $alldescription = 'all ILOs ('.$allcount.')';
        $rawilodescription = 'raw ILO data view';
        $rawencdescription = 'raw enclosure data view';

        """ + self.showDivDropDownPHP([('ilostatus_div_warning', '$warningdescription', '$tablewarning'),('ilostatus_div_all', '$alldescription', '$tableall'),('ilostatus_div_raw', '$rawilodescription', '$div_raw'),('ilostatus_div_encraw', '$rawencdescription', '$div_encraw')]) + """

        print($data["message"]);

        ?>"""
        
        return self.PHPOutput(module_content)
