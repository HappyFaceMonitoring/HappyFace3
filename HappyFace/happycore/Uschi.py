from XMLParsing import *
from GetData import *
from ModuleBase import *

#############################################
# class for USCHI tests (used at Tier1 GridKa)
#############################################
class Uschi(ModuleBase):

    def __init__(self, module_options):
	ModuleBase.__init__(self, module_options)

	# definition of the database table keys and pre-defined values
	self.db_keys['uschi_timestamp'] = StringCol()
	self.db_keys['uschi_timestamp_module'] = StringCol()
	self.db_keys['frequency'] = IntCol()
	self.db_keys['frequency_module'] = IntCol()
	self.db_keys['result'] = IntCol()
	self.db_keys['log'] = StringCol()
	self.db_keys['about'] = StringCol()
	
	self.db_values['uschi_timestamp'] = ""
	self.db_values['uschi_timestamp_module'] = ""
	self.db_values['frequency'] = -1
	self.db_values['frequency_module'] = -1
	self.db_values['result'] = -1
	self.db_values['log'] = ""
	self.db_values['about'] = ""

        self.dsTag = 'uschi_xml'
                
    def run(self):

	self.testname_string = self.configService.get('setup','testname_string')


        ##############################################################################
        # run the test
	# downlaod the XML source file and saves it under: __module__ + "source.xml"

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

        dl_error,uschiFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
        if dl_error != "":
            self.error_message+= dl_error
            return

	uschi_dom_object,xml_error = XMLParsing().parse_xmlfile_minidom(uschiFile)
        self.error_message += xml_error
        
        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if uschi_dom_object == "": return

	##############################################################################
	# get the last USCHI running time
	root = uschi_dom_object.documentElement
	self.uschi_timestamp = root.getAttribute('time')

	# get the execution frequency of USCHI (in minutes)
	self.frequency = int(root.getAttribute('frequency'))

	self.log = ""
	self.about = ""

	# get the test specific information (result, log, about)
	tests = uschi_dom_object.getElementsByTagName('test')
	for sec in tests:
            if sec.getAttribute('name') == self.testname_string:

		# test logic
		self.result = int(sec.getAttribute('result'))
		if (self.result == 0): self.status = 1.0 # happy
		elif (self.result == 1): self.status = 0.5 # neutral
		elif (self.result == 2): self.status = 0.0 # unhappy

		# get the last test execution time of the module
		self.uschi_timestamp_module = sec.getAttribute('time')

		# get frequency of the module (in minutes)
		self.frequency_module = int(sec.getAttribute('frequency'))

                # get the "log" and "about" information of the test
		log_data = sec.getElementsByTagName('log')
		about_data = sec.getElementsByTagName('about')
		for info in log_data:
		    log_list = info.firstChild.data.splitlines()
		    for line in log_list:
			self.log += '<p>' + line + '</p>' # add <p> tags for HTML output
		for info in about_data:
		    about_list = info.firstChild.data.splitlines()
		    for line in about_list:
			self.about += line
		
	# definition fo the database table values
	self.db_values['uschi_timestamp'] = self.uschi_timestamp
	self.db_values['uschi_timestamp_module'] = self.uschi_timestamp_module
	self.db_values['frequency'] = self.frequency
	self.db_values['frequency_module'] = self.frequency_module
	self.db_values['result'] = self.result
	self.db_values['log'] = self.log
	self.db_values['about'] = self.about

    def output(self):

        # the module_content string will be executed by a print('') PHP command
	# all information in the database are available via a $data["key"] call

        mc = []
        mc.append(  '<table class="TableData">')
        mc.append(  ' <tr>')
        mc.append(  '  <td class="UschiTableHeader">')
        mc.append(  '   <table class="UschiSubTable">')
        mc.append(  '    <tr>')
        mc.append(  '     <td class="UschiSubTableHeaderLeft">')
        mc.append("""      Last USCHI execution (every '.$data["frequency"].' minutes):""")
        mc.append(  '     </td>')
        mc.append(  '     <td class="UschiSubTableHeaderRight">')
        mc.append("""      '.$data["uschi_timestamp"].'""")
        mc.append(  '     </td>')
        mc.append(  '    </tr>')
        mc.append(  '   </table>')
        mc.append(  '  </td>')
        mc.append("""  <th rowspan="3">error code: '.$data["result"].'</th>""")
        mc.append(  ' </tr>')
        mc.append(  ' <tr>')
        mc.append(  '  <td class="UschiTableHeader">')
        mc.append(  '   <table class="UschiSubTable">')
        mc.append(  '    <tr>')
        mc.append(  '     <td class="UschiSubTableHeaderLeft">')
        mc.append("""      Last Module execution (every '.$data["frequency_module"].' minutes):""")
        mc.append(  '     </td>')
        mc.append(  '     <td class="UschiSubTableHeaderRight">')
        mc.append("""      '.$data["uschi_timestamp_module"].'""")
        mc.append(  '     </td>')
        mc.append(  '    </tr>')
        mc.append(  '   </table>')
        mc.append(  '  </td>')
        mc.append(  ' </tr>')
        mc.append(  ' <tr>')
        mc.append("""  <td class="UschiTableInfo">'.$data["about"].'</td>""")
        mc.append(  ' </tr>')
        mc.append(  '</table>')
        mc.append(  '<br />')
        mc.append("""<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />""")
        mc.append("""<div class="DetailedInfo" id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">'.$data["log"].'</div>""")
        mc.append(  '<br />')

        module_content = "<?php print('" + self.PHPArrayToString(mc) + "'); ?>"
	return self.PHPOutput(module_content)
