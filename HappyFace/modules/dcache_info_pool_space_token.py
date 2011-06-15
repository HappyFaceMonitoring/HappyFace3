from ModuleBase import *
from ModuleHelper import *
from lxml import etree as ET


class dcache_info_pool_space_token(ModuleBase, ModuleHelper):

    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)
	
        self.dcache_poolinfo_xml = self.configService.get('downloadservice', 'dcache_poolinfo_xml')
        self.disks               = eval('%s' % self.configService.get('setup', 'spacetokens'))
        self.unit                = self.configService.get('setup','unit')

        try:
            self.global_warning = float(self.configService.get('setup', 'global_warning'))
        except:
            self.error_message += "Setting for global_warning has to be a number.\n"
            self.global_warning = 10

        try:
            self.global_critical = float(self.configService.get('setup', 'global_critical'))
        except:
            self.error_message += "Setting for global_critical has to be a number.\n"
            self.global_critical = 5

        try:
            self.local_warning = float(self.configService.get('setup', 'local_warning'))
        except:
            self.error_message += "Setting for local_warning has to be a number.\n"
            self.local_warning = 10

        try:
            self.local_critical = float(self.configService.get('setup', 'local_critical'))
        except:
            self.error_message += "Setting for local_critical has to be a number.\n"
            self.local_critical = 5


        self.total_size = 0
        self.free_size = 0
        self.used = 0
        self.fromByteToUnit = 0
        
        self.db_keys["message"] = StringCol()
        self.db_values["message"] = ''
        
    def run(self):
        
        content = '\n'.join(self.fetchDownload('dcache_poolinfo_xml'))
        
        if self.unit == 'GiB':
            self.fromByteToUnit = 1024*1024*1024
        elif self.unit == 'TiB':
            self.fromByteToUnit = 1024*1024*1024*1024
        elif self.unit == 'PiB':
            self.fromByteToUnit = 1024*1024*1024*1024*1024
        if self.unit == 'GB':
            self.fromByteToUnit = 1000*1000*1000
        elif self.unit == 'TB':
            self.fromByteToUnit = 1000*1000*1000*1000
        elif self.unit == 'PB':
            self.fromByteToUnit = 1000*1000*1000*1000*1000
        else:
            self.error_message += 'Warning: unknown unit in ' + self.__module__ + '. Must be "GB", "TB", "PB", "GiB", "TiB" or "PiB". Using "GB" ...'
            self.unit = 'GB'
            self.fromByteToUnit = 1000*1000*1000
	
        try:
            result, status = parse_xml(content, self.disks, self.unit, self.fromByteToUnit, self.global_warning, self.global_critical, self.local_warning, self.local_critical)
            
            self.status = status
            if status == -1:
                self.error_message += result
            else:
                self.db_values["message"] = result
        except:
            self.error_message += "Error parsing html data: %s\n" % str(self.dcache_poolinfo_xml)
            self.status = -1;
            
    def output(self):
	
        module_content = '<?php  echo $data["message"]  ?>'
        
        return self.PHPOutput(module_content)


# helper function
def parse_xml(content, disks, unit, fromByteToUnit, global_warning, global_critical, local_warning, local_critical):
    eTree = ET.fromstring(content)
    status = 1.0

    result = '<table class="TableData">\n'
    result += '    <tr><th>Disk name</th><th>Total [%s]</th><th>Free [%s] </th><th>Used [%s]</th><th>Free %%</th></tr>\n' % (unit, unit, unit)
    
    size_sum = 0.0
    free_sum = 0.0
    
    for elt in eTree.getiterator('{http://www.dcache.org/2008/01/Info}reservation'):

        group = elt.findall('{http://www.dcache.org/2008/01/Info}metric')
        for i in group:

            disk_name = i.text
            if disk_name in disks:
                space_tag  = elt.findall('{http://www.dcache.org/2008/01/Info}space/{http://www.dcache.org/2008/01/Info}metric')
                total_size = float(space_tag[0].text)/fromByteToUnit
                free_size  = float(space_tag[1].text)/fromByteToUnit

                used_size  = float(space_tag[3].text)/fromByteToUnit
                proc = 100.*(float(free_size))/(float(total_size))

                size_sum += total_size
                free_sum += free_size
                
                if proc <= local_warning:
                    if proc > local_critical:
                        status = min(status, 0.5)
                        trclass = 'warning'
                    else:
                        status = min(status, 0)
                        trclass = 'critical'
                else:
                    trclass = 'ok'


                proc = format(proc,'.1f')
                used_size  = format(used_size,'.1f')
                total_size = format(total_size,'.1f')
                free_size  = format(free_size,'.1f')

                result +='    <tr class="%s"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n'%(trclass, disk_name,total_size,free_size,used_size,proc)
                
    result += '</table>\n'

    proc = 100.*(float(free_sum))/(float(size_sum))
    if proc <= global_warning:
        if proc > global_critical:
            status = min(status, 0.5)
        else:
            status = min(status, 0)
        result += '<h3><img src="config/images/symbol_failed.png">&nbsp;Only %s%% free space left.</h3>\n' % format(proc,'.1f')
    else:
        result += '<h3><img src="config/images/symbol_ok.png">&nbsp;%s%% free space left.</h3>\n' % format(proc,'.1f')

    return result, status
	   	   

