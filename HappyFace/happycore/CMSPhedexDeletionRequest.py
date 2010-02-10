from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

#
# Friederike Nowak
# University of Hamburg
# 2010/01/21
#

###################################################
#                                                 #
# Parses the Phedex XML Api for deletion requests #
# Note: still too slow for all requests           #
#                                                 #
###################################################

class CMSPhedexDeletionRequest(ModuleBase,PhpDownload):

	def __init__(self,module_options):

		ModuleBase.__init__(self,module_options)
		PhpDownload.__init__(self)

		## get the url
		self.base_url = self.configService.get('setup','base_url')

		## get the instance
		self.instance = self.configService.get('setup','instance')

		## add instance to base_url
		self.base_url += '/'+self.instance+'/deleterequests'

		# definition of the database table keys and pre-defined values
		self.db_keys["details_database"] = StringCol()
		self.db_values["details_database"] = ""

		self.dsTag = 'CMSPhedexDeletionRequest_xml_source'
		self.downloadRequest[self.dsTag] = 'wget|'+self.makeUrl()

	def run(self):
		"""
		Collects the data from the web source. Stores it then into the
		sqlite data base. The overall status has to be determined here.
		"""
		# run the test

		if not self.dsTag in self.downloadRequest:
			err = 'Error: Could not find required tag: '+self.dsTag+'\n'
			sys.stdout.write(err)
			self.error_message +=err
			return -1

		success,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
		source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile)

		if not error_message == "":
			self.error_message += error_message
			return -1

		##############################################################################
		# if xml parsing fails, abort the test;
		# self.status will be pre-defined -1
		if source_tree == "": return

		# parse the details and store it in a special database table
		details_database = self.__module__ + "_table_details"

		self.db_values["details_database"] = details_database

		details_db_keys = {}
		details_db_values = {}

		## define the details_db_keys here
		details_db_keys['req_by'] = StringCol()
		details_db_keys['dataset'] = StringCol()
		details_db_keys['time_diff'] = StringCol()
		details_db_keys['files'] = IntCol()

		my_subtable_class = self.table_init( details_database, details_db_keys )

		## now start parsing the xml tree
		root = source_tree.getroot()

		if root.get("request_timestamp"):
			request_time = float(root.get("request_timestamp"))
		else:
			print "Error: could not get request time at instance "+self.instance+". Aborting."
			return

		for req in root:
			request = {}
			notFinished = False
			creation_time = float(req.get('time_create'))
			for req_el in req:
				if req_el.tag == 'data':
					for data_el in req_el:
						if data_el.tag == 'dbs':
							request['dataset_list'] = []
							datasets = {}
							for dbs_el in data_el:
								if not dbs_el.get('bytes').encode('utf-8') == '' and \
								       not int(dbs_el.get('bytes')) == 0:
									datasets[dbs_el.get('name').encode('utf-8')] = int(dbs_el.get('files').encode('utf-8'))
									request['dataset_list'] = datasets
									notFinished = True
									pass
								pass
							if notFinished:
								request['dbs_url'] = data_el.get('name').encode('utf-8')
								pass
							pass
						pass
					pass
				elif req_el.tag == 'requested_by' and notFinished:
					request['req_by'] = req_el.get('name').encode('utf-8')
					request['req_by_username'] = req_el.get('username').encode('utf-8')
					request['req_by_email'] = req_el.get('email').encode('utf-8')
					for comments in req_el:
						try:
							request['req_by_comment'] = comments.text.encode('utf-8')
						except:
							request['req_by_comment'] = ''
						pass
					pass
				pass
			#print 'new---------------------------------------------'
			#for key in request:
			#	print key, ":\t", request[key]

			try:
                                ## difference between creation time and timestamp in seconds
				## nonsense at the moment
				diff_time = (request_time - creation_time)
				request['time_diff'] = self.formatTime(diff_time)

				details_db_values['req_by'] = request['req_by']
				details_db_values['time_diff'] = request['time_diff']
				for key in request['dataset_list']:
					details_db_values['dataset'] = key
					details_db_values['files'] = request['dataset_list'][key]
					# store the values to the database
					self.table_fill( my_subtable_class, details_db_values )
					pass
			except:
				pass


		## will stay happy
		self.status = 1.

	def output(self):

		"""
		Access data from the sqlite database from here and decide how
		to present it
		"""
		#module_content = """
		#<?php
		#printf('War einmal ein Boomerang,<br />');
		#printf('War um ein Weniges zu lang.<br />');
		#printf('Boomerang flog ein Stueck<br />');
		#printf('Und kehrte nie mehr zurueck.<br />');
		#printf('Publikum noch stundenlang<br />');
		#printf('Wartete auf Boomerang.<br />');
		#?>
		#"""

		module_content = """
		<?php
		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

		printf('<table class="TableData">');
		printf('<tr class="TableHeader"><td>request by</td><td>number of files</td><td>dataset</td></tr>');

		$print = True;
		$req_by = '';
		$time_diff = '';

		foreach ($dbh->query($details_db_sqlquery) as $info)
		{
		$service_status_color_flag = "report";
	
		printf('<tr class="' .$service_status_color_flag . '"><td>' . $info["req_by"] . '</td><td>'.$info["files"].'</td>');
		
		printf('<td class="' .$service_status_color_flag . '">' .$info["dataset"] . '</td>'); 
		printf('</tr>');

		
		}
		printf('</table></br>');
		?>
		"""
		
		return self.PHPOutput(module_content)

	def formatTime(self,time_diff):
		"""
		formats time to a human readable form
		"""
		time_string = ""
		
		d,s = divmod(time_diff,(3600*24))
		h,s = divmod(s,3600)
		m,s = divmod(s,60)
		
		time_string = "%02.fd:%02.fh:%02.fm" % (d, h, m)
		
		return time_string
