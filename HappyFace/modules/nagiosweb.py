from ModuleBase import *
from ModuleHelper import *


class nagiosweb(ModuleBase, ModuleHelper):

    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)
        self.status = 1
        
        # prepare pbs info source
        self.prepareInput('nagios', 'source')

        # read display configuration from config file
        self.display = self.readTableConfig('display')

        # definition of the database keys and pre-defined values
        self.db_keys['nagios_list'] = StringCol()
        self.db_values['nagios_list'] = ''

    def run(self):
        
        # fetch additional pbs info
        nagiosinfo = self.fetchInput('nagios', 'source')
        nagiosinfo = ' '.join(nagiosinfo).replace('\n',' ').replace('\r',' ')

        # all content of the table with class 'status' is parsed into arrays
        tableParser = TableParser(nagiosinfo, 'status')

        # we only need to fetch the arrays content now
        self.services = {}
        curhost_name = ''
        curhost_link = ''

        for entry in tableParser.table:
            
            # only select valid entries
            if len(entry) < 7:
                continue

            # build a new service fromt the entry's infos
            service = {}

            # read info about host from first column
            # if first column is empty, keep old host's info
            if len(entry[0]) > 1:
                host = ContentParser(entry[0][0])
                if host.content.strip() != '':
                    curhost_name = host.content.strip()
                    curhost_link = host.url[0]

            service['host_name'] = curhost_name
            service['host_link'] = curhost_link

            # read info about service from second column
            ser = ContentParser(entry[1][0])

            service['service_name'] = ser.content.strip()
            service['service_link'] = ser.url[0]

            # read info about service status from third and seventh column
            service['status_short'] = entry[2]
            service['status_long'] = entry[6]

            # read more info about state
            service['status_lastcheck'] = entry[3]
            service['status_duration'] = entry[4]
            service['status_attempt'] = entry[5]

            # add to array
            self.services[(service['host_name']+'-'+service['service_name'])] = service
            
        
        ################################################
        # all data has been gathered -- output follows

        self.db_values['nagios_list'] = self.packArray(self.services)

        # now, determine the status of the module
        for s in self.services:
            service = self.services[s]

            if service['status_short'].lower() == 'critical':
                # critical services give critical status, except for time outs
                if service['status_long'].lower().find('service check timed out') >= 0:
                    self.status = min(self.status, 0.5)
                else:
                    self.status = min(self.status, 0)

            elif service['status_short'].lower() != 'ok':
                self.status = min(self.status, 0.5)
        
    def output(self):
        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call

        # data will be parsed first
        # the first lines up to double new lines consist of the available fields
        # after that, for each service, these fields are repeated, one field per line
        module_content = """<?php

        // unpack stored information from database into var $ilos (and $keys)
        """ + self.unpackArrayPHP('$data["nagios_list"]', '$services', '$keys') + """

        // create raw view from $services
        """ + self.rawDataPHP('$services', '$div_raw', '$_keys', 'service_name') + """

        // create table views from $services
        // sort first
        """ + self.sortTablePHP(self.display, '$services') + """
        
        // create tables
        """ + self.beginTablePHP(self.display, '$tableall') + """
        """ + self.beginTablePHP(self.display, '$tableoffline') + """

        $tableofflinecount = 0;
        $tableallcount = 0;

        // build all tables
        foreach ($services as $service)
        {
            // determine status of current service
            if($service['status_short'] == 'OK')
                $tclass = 'ok';
            else if(($service['status_short'] == 'CRITICAL') && (strpos(strtolower($service['status_long']), 'service check timed out') === false) )
            {
                $tclass = 'critical';
                $tableofflinecount += 1;
            }
            else
            {
                $tclass = 'warning';
                $tableofflinecount += 1;
            }

            if($service['status_short'] != 'OK')
            {
            """ + self.addRowPHP(self.display, '$tclass', '$service', '$tableoffline') + """
            }
            """ + self.addRowPHP(self.display, '$tclass', '$service', '$tableall') + """
            $tableallcount += 1;
        }

        // close tables
        """ + self.endTablePHP(self.display, '$tableall') + """
        """ + self.endTablePHP(self.display, '$tableoffline') + """


        if($tableallcount == 0)
            $tableall = '""" + self.htmlMessage('There are no services.', 'error') + """';

        if($tableofflinecount == 0)
            $tableoffline = '""" + self.htmlMessage('All services are ok.', 'ok') + """';
        else
            $tableoffline .= '""" + self.htmlMessage('\'.$tableofflinecount.\' services are not ok.', 'warning') + """';
        
        $offlinedescription = 'failed services ('.$tableofflinecount.')';
        $alldescription = 'all services ('.$tableallcount.')';
        $rawdescription = 'raw data view';
        
        """ + self.showDivDropDownPHP([('nagiosweb_div_offline', '$offlinedescription', '$tableoffline'),('nagiosweb_div_all', '$alldescription', '$tableall'),('nagiosweb_div_raw', '$rawdescription', '$div_raw')]) + """
        
	?>"""

        return self.PHPOutput(module_content)
