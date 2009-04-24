from XMLParsing import *
from GetData import *

#############################################
# class for USCHI tests (used at Tier1 GridKa)
#############################################
class Uschi(XMLParsing,GetData):

    def __init__(self, category, timestamp, storage_dir):
	XMLParsing.__init__(self, category, timestamp, storage_dir)

	# read class config file
	config = self.readConfigFile('./happycore/Uschi')
	
	self.source_url = config.get('setup','source_url')
	self.source_path = config.get('setup','source_path')

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

    def run(self):

        ##############################################################################
        # run the test
	# downlaod the XML source file and saves it under: __module__ + "source.xml"
	if self.getDataWget(self.source_url,self.source_path,self.__module__ + "source.xml") == False:
	    return
	
	# parse the XML source file
	uschi_dom_object = self.parse_xmlfile_minidom(self.source_path + "/" + self.__module__ + "source.xml")

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
            <table class="uschi">
                <tr>
                    <td><div style="text-align:center;"><strong>last USCHI execution: </strong>'.$data["uschi_timestamp"].'</div></td>
                    <th rowspan="2"><div style="text-align:center;"><strong>error code: '.$data["result"].'</strong></div></th>
                </tr>
                <tr>
                    <td><i>'.$data["about"].'</i></td>
                </tr>
            </table>
            <br />
            <input type="button" value="show/hide results" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />
            <div id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">'.$data["log"].'</div>
            <br />
            ');
            ?>

	"""
 
	return self.PHPOutput(module_content)
