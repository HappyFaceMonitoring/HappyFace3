from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

import re ## regular expressions

#
# Friederike Nowak
# 2009/10/05
#


class CMSSiteReadiness(ModuleBase,PhpDownload):

	def __init__(self,category,timestamp,storage_dir):

		ModuleBase.__init__(self,category,timestamp,storage_dir)
		PhpDownload.__init__(self)

		## get the url
		self.base_url = self.configService.get('setup','base_url')
		self.site = self.configService.get('setup','site')

		if not re.search('T1',self.site) and not re.search('T2',self.site):
			err = 'Error: Must be a T1 or T2 site. Occoured in module '+self.__module()+'\n'
			sys.stdout.write(err)
			self.error_message += err
			return -1
		
		self.fileExtension = self.configService.get('setup','fileextension')
		self.days = int(self.configService.get('setup','days'))
		#self.critical = self.configService.get('setup','critical')
		#self.warning = self.configService.get('setup','warning')

		self.getStatusConditions()
		
		self.readiness = {}
		self.key_list = []

		# definition of the database table keys and pre-defined values
		self.db_keys["details_database"] = StringCol()
		self.db_values["details_database"] = ""

		self.dsTag = 'CMSSiteReadiness_xml_source'
		#self.downloadRequest[self.dsTag] = 'wget:'+self.makeUrl()
		self.downloadRequest[self.dsTag] = 'wget:'+ self.fileExtension + ':' + self.base_url

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
		source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile,'html')

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

		## write global after which the query will work
		details_db_keys["timestamp"] = IntCol()
		details_db_values["timestamp"] = self.timestamp

		details_db_keys['readiness_cond'] = StringCol()
		details_db_keys['cond_color'] = StringCol()
		details_db_keys['cond_value'] = StringCol()

		## create index for timestamp
		details_db_keys["index"] = DatabaseIndex('timestamp')

		## lock object enables exclusive access to the database
		self.lock.acquire()

		Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

		Details_DB_Class.sqlmeta.cacheValues = False
		Details_DB_Class.sqlmeta.fromDatabase = True

		## if table is not existing, create it
		Details_DB_Class.createTable(ifNotExists=True)

		## now start parsing the xml tree
		root = source_tree.getroot()

		### now do something
		siteTable = self.getSiteElements(root)

		#if re.search("T1",self.site):
		#	self.getReadinessT1(siteTable)
		#elif re.seach("T2",self.site):
		#	self.getReadinessT2(siteTable)

		self.getReadiness(siteTable)
		self.makeDatabaseEntries(details_db_keys,details_db_values,Details_DB_Class)

		# unlock the database access
		self.lock.release()

		# always happy for the moment
		self.status = self.determineStatus()

	def output(self):

		"""
		Access data from the sqlite database from here and decide how
		to present it
		"""
		#module_content = """
		#<?php
		#printf('War einmal ein Boomerang,<br>');
		#printf('War um ein Weniges zu lang.<br>');
		#printf('Boomerang flog ein Stueck<br>');
		#printf('Und kehrte nie mehr zurueck.<br>');
		#printf('Publikum noch stundenlang<br>');
		#printf('Wartete auf Boomerang.<br>');
		#?>
		#"""

		module_content = """
		<?php

                $details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

                printf('<table class="CMSSiteReadinessTable">');

		$condition = "start";

                foreach ($dbh->query($details_db_sqlquery) as $info)
                {
                    if ($info["cond_color"] == "green"){
                    $service_status_color_flag = "up";
                }
                    else if ($info["cond_color"] == "red"){
                    $service_status_color_flag = "critical";
                }
                    else if ($info["cond_color"] == "yellow"){
                    $service_status_color_flag = "warning";
                }
		    else if ($info["cond_color"] == "lightgrey"){
		    $service_status_color_flag = "weekend";
	        }
                    else $service_status_color_flag = "undef";

		if($info["readiness_cond"] != $condition){
		    if($condition != "start"){
		        printf('</tr>');
		    }
                    printf('<tr><td>' . $info["readiness_cond"] . '</td>');
		    $condition = $info["readiness_cond"];
		}

		printf('<td class="' .$service_status_color_flag . '">' . $info["cond_value"] . '</td>');
		
	        }

		printf('</tr>');
		printf('</table><br/>');    

		?>
		"""

		return self.PHPOutput(module_content)

	def determineStatus(self):

		"""
		Determines the status of this module
		"""

		critical_counter = 0
		warning_counter = 0

		## look into the last x days

		for entry in self.readiness['Site Readiness Status'][-int(self.critical[0]):]:
			if entry['color'] == 'red':
				critical_counter += 1
			## if you find y critical days in
			## in the x considered:
			if critical_counter >= int(self.critical[1]):
				return 0
		for entry in self.readiness['Site Readiness Status'][-int(self.warning[0]):]:
			if entry['color'] == 'yellow':
				warning_counter += 1
			## same as critical
			if warning_counter >= int(self.warning[1]):
				return 0.5
			
			
		return 1

	def getSiteElements(self, root):
		"""
		Finds the relevant elements in the html tree for the
		given site.
		"""


		for root_el in root:
			if root_el.tag == 'body':
				for body_el in root_el:
					for center_el in body_el:
						if center_el.tag == 'table':
							SiteTable = center_el
							for table_el in center_el:
								if table_el.tag == 'tr':
									for tr_el in table_el:
										if tr_el.tag == 'td':
											for td_el in tr_el:
												if td_el.tag == 'div':
													if td_el.get('id').encode('utf-8') == 'site' and td_el.text_content().encode('utf-8') == self.site:
														#print td_el.text_content().encode('utf-8')
														return SiteTable

		return 0

	def getReadiness(self,siteTable):
		
		"""
		Extracts the site readiness informations out of the site table
		"""


		readiness = {}
		for table_el in siteTable:
			if table_el.tag == 'tr':
				key = None
				entry = {}
				entry_list = []
				for tr_el in table_el:
					if tr_el.tag == 'td':
						for td_el in tr_el:
							if td_el.get('id') == 'daily-metric-header' or \
							       td_el.get('id') == 'metrics-header':
								#print td_el.text_content().encode('utf-8')
								key = td_el.text_content().encode('utf-8').rstrip().rstrip(":")
								entry = {}
								entry_list = []


							if key == None:
								if td_el.get('id') == 'date':
									key = 'date'
									entry = {}
									entry_list = []

								elif td_el.get('id') == 'month':
									key = 'month'
									entry = {}
									entry_list = []

						if not key == None:

							if not key == 'month':

								try:
									entry = {}
									entry['color'] = tr_el.get('bgcolor').encode('utf-8')
									for td_el in tr_el:
										entry['value'] = td_el.text_content().encode('utf-8')

								except:
									pass

							elif key == 'month':
								
								try:
									entry = {}
									entry['color'] = ''
									entry['value'] = ''
									for td_el in tr_el:
										entry['value'] = td_el.text_content().encode('utf-8')

								except:
									pass

						try:
							if not entry['color'] == None and not entry['value'] == None:
								entry_list.append(entry)

						except:
							pass

						## will be overwritten as long as end of
						## list is not reached
						readiness[key] = entry_list
			## dictionarys do not store the order of
			## things, therefore use a list
			self.key_list.append(key)
										
								
								
		self.readiness = readiness
		#print self.readiness
		pass

	def makeDatabaseEntries(self,details_db_keys,details_db_values,Details_DB_Class):

		"""
		Makes the database entries from the readiness dictionary made
		in 'getReadiness'
		"""
		
		for key in self.key_list:
			if not key == None:
				#print key
				details_db_values['readiness_cond'] = key
				list = self.readiness[key]
				#print list[-(self.days):]
			        #print list
			
			        ## get the last x days
				for entry in list[-(self.days):]:
					details_db_values['cond_color'] = entry['color']
					if not re.search('%',entry['value']):
						details_db_values['cond_value'] = entry['value']
					else:
						details_db_values['cond_value'] = re.sub('%','%%',entry['value'])

					Details_DB_Class(**details_db_values)
					
		pass

	def getStatusConditions(self):

		"""
		Reads in the warning/critical conditions and refurbishes
		them
		"""

		try:
			self.critical = self.configService.get('setup','critical').split(':')
			self.warning = self.configService.get('setup','warning').split(':')

		except:
			err = 'Error! Could not read in status conditions in module '+self.__module__+'\n'
			sys.stdout.write(err)
			self.error_message +=err
			return -1


		if int(self.critical[0]) > self.days or int(self.warning[0]) > self.days:
			warn = 'Warning! Number of considered days in status determination is\n'
			warn += 'greater than total number of days read in. Setting number of\n'
			warn += 'considered days to number of total days. Occurred in module \n'
			warn += self.__module__+'\n'
			if int(self.critical[0]) > self.days:
				self.critical[0] = self.days
			if int(self.warning[0]) > self.days:
				self.warning[0] = self.days
			sys.stdout.write(warn)
		

		if int(self.critical[1]) > int(self.critical[0]) or int(self.warning[1]) > int(self.warning[0]):
			warn = 'Warning! Number of critical/warning days greater than considered\n'
			warn += 'days. Setting number of w/c days to considered days. Occurred in\n'
			warn += 'module '+self.__module__+'\n'
			if int(self.critical[1]) > int(self.critical[0]):
				self.critical[1] = int(self.critical[0])
			if int(self.warning[1]) > int(self.warning[0]):
				self.warning[1] = int(self.warning[0])

			sys.stdout.write(warn)
		
		pass
