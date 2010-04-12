from ModuleBase import *
from HTMLParsing import *
from PhpDownload import *

## regular expressions
import re

#
# 2009/10/02 Friederike Nowak
#

class CMSPhedexLinks(ModuleBase,PhpDownload):

	def __init__(self,module_options):

		ModuleBase.__init__(self,module_options)
		PhpDownload.__init__(self)

		## get the url
		self.base_url = self.configService.get('setup','base_url')

		self.direction = self.configService.get('setup','direction')

		if not self.direction in ['from','to']:
			err = 'Error: direction unknown. Must be "from" or "to".\n'
			sys.stdout.write(err)
			self.error_message += err
			return -1

		self.getStatusCriteria()

		# definition of the database table keys and pre-defined values
		self.db_keys["details_database"] = StringCol()
		self.db_values["details_database"] = ""

		self.dsTag = 'CMSPhedexLinks_xml_source'
		self.downloadRequest[self.dsTag] = 'wget|'+self.makeUrl()

	def process(self):
		
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
		source_tree, error_message = HTMLParsing().parse_htmlfile_lxml(sourceFile)

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

		## create index for timestamp
		details_db_keys["index"] = DatabaseIndex('timestamp')

		details_db_keys["linked_site"] = StringCol()
		details_db_keys["color"] = StringCol()
		details_db_keys["link_status"] = StringCol()
		details_db_keys["update_source"] = StringCol()
		details_db_keys["update_dest"] = StringCol()

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
		links = self.getLinks(root,details_db_values,Details_DB_Class)
	
		# unlock the database access
		self.lock.release()

		# always happy for the moment
		self.status = self.determineStatus(links)

	def output(self):

		"""
		Access data from the sqlite database from here and decide how
		to present it
		"""

		mc_begin = []
		mc_begin.append('<table class="TableData">')
		mc_begin.append(' <tr class="TableHeader">')
		mc_begin.append('  <td>site</td>')
		mc_begin.append('  <td>status</td>')
		mc_begin.append(' </tr>')

		row_sep = []
		row_sep.append(' <tr><td colspan="2" class="CMSPhedexLinksSeparator"></td></tr>')

		table_row = []
		table_row.append(""" <tr class="' .$service_status_color_flag . '">""")
		table_row.append("""  <td>' . $info["linked_site"] . '</td>""")
		table_row.append("""  <td>' . $info["link_status"] . '</td>""")
		table_row.append(  ' </tr>');

		mc_mid = []
		mc_mid.append(  '</table>')
		mc_mid.append(  '<br />')
		mc_mid.append("""<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_result\\\');" />""")
		mc_mid.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_result" style="display:none;">')
		mc_mid.append(  ' <table class="TableDetails">')
		mc_mid.append(  '  <tr class="TableHeader">')
		mc_mid.append(  '   <td>site</td>')
		mc_mid.append(  '   <td>link_status</td>')
		mc_mid.append(  '   <td>source update</td>')
		mc_mid.append(  '   <td>dest update</td>')
		mc_mid.append(  '  </tr>')

		detailed_row = []
		detailed_row.append("""  <tr class="' .$service_status_color_flag . '">""")
		detailed_row.append("""   <td>' . $info["linked_site"] . '</td>""")
		detailed_row.append("""   <td>' . $info["link_status"] . '</td>""")
		detailed_row.append("""   <td>' . $info["update_source"] . '</td>""")
		detailed_row.append("""   <td>' . $info["update_dest"] . '</td>""")
		detailed_row.append(  '  </tr>');

		mc_end = []
		mc_end.append(' </table>');
		mc_end.append('</div>');

		module_content = """<?php

		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

		print('""" + self.PHPArrayToString(mc_begin) + """');

		$tier = 1;

		foreach ($dbh->query($details_db_sqlquery) as $info)
		{
		    if ($info["color"] == "green")
		        $service_status_color_flag = "ok";
		    else if ($info["color"] == "red")
		        $service_status_color_flag = "critical";
		    else if ($info["color"] == "purple")
		        $service_status_color_flag = "deactivated";
		    else
		        $service_status_color_flag = "undefined";

		    if($tier == 1) {
		        $match = preg_match("/T1/",$info["linked_site"]);
		        if (!$match) {
		            $tier = 2;
		            print('""" + self.PHPArrayToString(row_sep) + """');
		        }
		    }
		    if($tier == 2) {
		        $match = preg_match("/T2/",$info["linked_site"]);
		        if (!$match) {
		            $tier = 3;
		            print('""" + self.PHPArrayToString(row_sep) + """');
		        }
		    }

		    print('""" + self.PHPArrayToString(table_row) + """');
		}

		print('""" + self.PHPArrayToString(mc_mid) + """');

		foreach ($dbh->query($details_db_sqlquery) as $info)
		{
		    if ($info["color"] == "green")
		        $service_status_color_flag = "ok";
	            else if ($info["color"] == "purple")
		        $service_status_color_flag = "deactivated";
		    else if ($info["color"] == "red")
		        $service_status_color_flag = "critical";
		    else
		        $service_status_color_flag = "undefined";

	            print('""" + self.PHPArrayToString(detailed_row) + """');
		}

		print('""" + self.PHPArrayToString(mc_end) + """');

	        ?>"""

		return self.PHPOutput(module_content)


	def determineStatus(self, links):

		"""
		determines global status
		"""

		### if one of the important links is down or
		### does not exsist, status = 0.
		for site in self.important_list:
			try:
				## color
				if links[site][0] == 'red':
					return 0
			except:
				return 0

		### check the critical criteria
		### don't forget to check the exclusion list too
		for tier in self.critical_dict.keys():
			tier_counter = 0
			tier_down_counter = 0
			for site in links.keys():
				if site in self.exclusion_list  :
					continue
				## if you want to exclude a specific tier like, e.g. T3
				if site.split("_")[0] in self.exclusion_list :
					continue
				#if not site in self.exclusion_list and re.search(tier, site):
				if re.search( tier, site ):
					tier_counter += 1
					if links[site][0] == 'red':
						tier_down_counter += 1

		
			if tier_down_counter >= self.critical_dict[tier] and not self.critical_dict[tier] == -1:
				return 0
			elif self.critical_dict[tier] == -1 and tier_down_counter == tier_counter:
				return 0

		### check the warning criteria and the exclusion
		### list
		for tier in self.warning_dict.keys():
			tier_counter = 0
			tier_down_counter = 0
			for site in links.keys():
				if site in self.exclusion_list:
					continue
				## if you want to exclude a specific tier like, e.g. T3
				if site.split("_")[0] in self.exclusion_list:
					continue
				#if not site in self.exclusion_list and re.search(tier,site):
				if re.search( tier,site ):
					tier_counter += 1
					if links[site][0] == 'red':
						tier_down_counter += 1
			if not self.warning_dict[tier] == -1 and tier_down_counter >= self.warning_dict[tier]:
				return 0.5
			elif self.warning_dict[tier] == -1 and tier_down_counter == tier_counter:
				return 0.5
					
		return 1

	

	def getLinks(self, root,details_db_values,Details_DB_Class):

		"""
		This function parses the root file, finds the relevant
		link informations and adds them into the database. Produces
		a  dictionary of the informations mapped to the sites.
		"""

		#linked_sites = []
		links = {}

		ttp = root.find_class("ttp")
		#print 'list lenght:\t', len(ttp)
		for ttp_el in ttp:
			color = ttp_el.get("style").split(':')[1]
			color = color.rstrip(';')
			#print color
			info_list = []
			info_list.append(color.encode("utf-8"))
			tt = ttp_el.find_class("tt")
			for tt_el in tt:
				for div_el in tt_el:
					if div_el.tag == 'p':
						for p_el in div_el:
							if p_el.tag == 'b':
								#print p_el.text_content().encode('utf-8')
								if self.direction == 'from':
									linked_site = p_el.text_content().encode('utf-8').split(' ')[2]
								else:
									linked_site = p_el.text_content().encode('utf-8').split(' ')[0]
					elif div_el.tag == 'span':
						for span_el in div_el:
							if span_el.tag == 'p':
								#print span_el.text_content().encode('utf-8').split('\n')
								info_list.append(span_el.text_content().encode('utf-8').rstrip('\n'))


			#print linked_site
			#print len(info_list)
			#print info_list
			#print color
			if len(info_list) >= 2:
				links[linked_site] = info_list
				details_db_values["linked_site"] = linked_site
				details_db_values["color"] = info_list[0]
				details_db_values["link_status"] = info_list[1]
				if len(info_list) >= 3:
					if not re.search("Source",info_list[2]) == None:
						details_db_values["update_source"] = info_list[2]
						details_db_values["update_dest"] = ''
					else:
						details_db_values["update_dest"] = info_list[2]
						details_db_values["update_source"] = ''
				else:
					details_db_values["update_source"] = ''
					details_db_values["update_dest"] = ''
				if len(info_list) >= 4:
					if not re.search("Destination",info_list[3]) == None:
						details_db_values["update_dest"] = info_list[3]
					else:
						details_db_values["update_source"] = info_list[3]

					
				Details_DB_Class(**details_db_values)
								
		return links


	def getStatusCriteria(self):

		"""
		Reads in the status criteria and refurbishes them
		"""

		self.critical = self.configService.getDefault('setup','critical','T1:1')
		self.warning = self.configService.getDefault('setup','warning','T2:1')

		self.exclusion = self.configService.getDefault('setup','exclusion',None)
		self.important = self.configService.getDefault('setup', 'important',None)


		self.critical_dict = {}
		for entry in self.critical.split(','):
			tier,number = entry.split(':')
			self.critical_dict[tier] = int(number)

		self.warning_dict = {}
		for entry in self.warning.split(','):
			tier,number = entry.split(':')
			self.warning_dict[tier] = int(number)

		self.exclusion_list = []
		if not self.exclusion == None:
			self.exclusion_list = self.exclusion.split(',')
			
		self.important_list = []
		if not self.important == None:
			self.important_list = self.important.split(',')

		pass
