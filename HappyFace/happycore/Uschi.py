from XMLParsing import *
from GetData import *
from ModuleBase import *

#############################################
# class for USCHI tests (used at Tier1 GridKa)
#############################################
class Uschi(ModuleBase):

    def __init__(self, category, timestamp, storage_dir):
	ModuleBase.__init__(self, category, timestamp, storage_dir)

	# read class config file
	config = self.readConfigFile('./happycore/Uschi')
        self.readDownloadRequests(config)
	self.addCssFile(config,'./happycore/Uschi')

	# from module specifig config file
	self.testname_string = self.mod_config.get('setup','testname_string')

	# definition of the database table keys and pre-defined values
	self.db_keys['uschi_timestamp'] = StringCol()
	self.db_keys['result'] = IntCol()
	self.db_keys['log'] = StringCol()
	self.db_keys['about'] = StringCol()
	
	self.db_values['uschi_timestamp'] = ""
	self.db_values['result'] = -1
	self.db_values['log'] = ""
	self.db_values['about'] = ""

        self.dsTag = 'uschi_xml'
                
    def run(self):

        ##############################################################################
        # run the test
	# downlaod the XML source file and saves it under: __module__ + "source.xml"

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

        success,uschiFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
	uschi_dom_object,mod_error = XMLParsing().parse_xmlfile_minidom(uschiFile)
        self.error_message += mod_error
        
        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if uschi_dom_object == "": return

	##############################################################################
	# get the last USCHI running time
	root = uschi_dom_object.documentElement
	self.uschi_timestamp = root.getAttribute('time')

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
		
	# replace % in content with %% for the PHP printf command
	self.log = self.log.replace('%','%%')
	self.about = self.about.replace('%','%%')
	
	# definition fo the database table values
	self.db_values['uschi_timestamp'] = self.uschi_timestamp
	self.db_values['result'] = self.result
	self.db_values['log'] = self.log
	self.db_values['about'] = self.about

    def output(self):

        # the module_content string will be executed by a printf('') PHP command
	# all information in the database are available via a $data["key"] call

        module_content = """
        <?php
        printf('
            <table class="UschiTable">
                <tr>
                    <td class="UschiTableHeader">Last USCHI execution: <span style="color:#FF9900"><b>'.$data["uschi_timestamp"].'</b></span></td>
                    <th rowspan="2">error code: '.$data["result"].'</th>
                </tr>
                <tr>
                    <td class="UschiTableInfo">'.$data["about"].'</td>
                </tr>
            </table>
            <br />
            <input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />
            <div class="UschiDetailedInfo" id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">'.$data["log"].'</div>
            <br />
            ');
            ?>

	"""
 
	return self.PHPOutput(module_content)
