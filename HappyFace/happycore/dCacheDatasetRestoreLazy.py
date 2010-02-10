from ModuleBase import *
from XMLParsing import *
from PhpDownload import *
from time import *


import re ## regular expressions


class dCacheDatasetRestoreLazy(ModuleBase):

	def __init__(self,module_options):

		ModuleBase.__init__(self,module_options)

		self.dsTag = 'lazyqueue'
		self.fileExtension = 'html'

		self.timeLimit  = self.configService.get('setup','stage_max_time')
		self.retryLimit = int(self.configService.get('setup','stage_max_retry'))
		self.voName = self.configService.getDefault('setup','vo','')

		self.detailsTableCutOff = self.configService.getDefault('setup','details_cutoff','')

		self.statusTagsOk   = ['Pool2Pool','Staging']
		self.statusTagsFail = ['Waiting','Suspended','Unknown']


	def run(self):

		"""
		Some Text
		"""
		# run the test

		if not self.dsTag in self.downloadRequest:
			err = 'Error: Could not find required tag: '+self.dsTag+'\n'
			sys.stdout.write(err)
			self.error_message +=err
			return -1


		timeSplit = self.timeLimit.split(":")
		if len(timeSplit) != 3:
			err = 'Error: Wrong stage_max_time format\n'
			sys.stdout.write(err)
			self.error_message +=err
			return -1


		
		timeLimitSeconds = int(timeSplit[0])*60*60+int(timeSplit[1])*60+int(timeSplit[2])


		success,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])

		self.configService.addToParameter('setup',
						  'source',
						  self.downloadService.getUrlAsLink(self.downloadRequest[self.dsTag]))

		if self.detailsTableCutOff != '':
			self.configService.addToParameter('setup',
							  'definition',
							  'Only '+self.detailsTableCutOff+' files listed in details table.<br />')


		if self.voName != '':
			self.configService.addToParameter('setup',
							  'definition',
							  'Only '+self.voName+' pools are considered.<br />')

		source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile,'html')

		if not error_message == "":
			self.error_message += error_message
			return -1






		##############################################################################
		# if xml parsing fails, abort the test;
		# self.status will be pre-defined -1
		if source_tree == "": return



		root = source_tree.getroot()

		tableLines = []
		
		for root_el in filter(lambda x: x.tag=='body', root):
			for body_el in root_el:
				for center_el in filter(lambda x: x.tag=='table',body_el):
					for table_el in filter(lambda x: x.tag=='tbody',center_el):
						for body_el in filter(lambda x: x.tag=='tr', table_el):
							tableLines.append(body_el)
						

		stageRequests = {}
		i=0
		while i < len(tableLines):
			request = {}
			el1 = tableLines[i];
			if len(el1) == 7:
				for tr_el in el1:
					request[tr_el.get('class')] = str(tr_el.text_content())

				el2 = tableLines[i+1];
				if len(el2) == 1:
					for tr_el in el2:
						request[tr_el.get('class')] = str(tr_el.text_content())
					i+=1
			i+=1

			if self.voName != '':
				if request['pool'].count(self.voName) == 0: continue
				

			# Determining waiting time
			time_tuple_now = gmtime(self.timestamp)
			year_now = strftime('%Y',time_tuple_now)
			year_now = str(int(year_now)+1)
			time_tuple_req = strptime(year_now+"."+request['started'],"%Y.%m.%d %H:%M:%S")
			time_diff = self.timestamp - mktime(time_tuple_req)

			# Check if year has been determind correctly by requiring time stamp of staging max one day in future
			if time_diff < -60*60*24:
				year_now = str(int(year_now)-1)
				time_tuple_req = strptime(year_now+"."+request['started'],"%Y.%m.%d %H:%M:%S")
				time_diff = self.timestamp - mktime(time_tuple_req)

			
			request['time'] = int(time_diff)
			request['started_full'] = strftime("%d/%m/%Y %H:%M:%S",time_tuple_req)
			request['status_short'] = request['status'].split(" ")[0]
			
			stageRequests[request['pnfs']] = request


		allRequests = {}
		allRequests['total'] = len(stageRequests)
		allRequests['total_problem'] = 0
		allRequests['hit_retry'] = 0
		allRequests['hit_time']  = 0

		

		for tag in self.statusTagsOk:
			allRequests['status_'+tag.lower()]  = 0
		for tag in self.statusTagsFail:
			allRequests['status_'+tag.lower()]  = 0
			

		
		problemRequests = []

		for reqID in stageRequests.keys():
			req = stageRequests[reqID]
			problemRequest = False
			if int(req['time']) >= timeLimitSeconds:
				allRequests['hit_time']+=1
				problemRequest = True
			if int(req['retries']) >= self.retryLimit:
				allRequests['hit_retry']+=1
				problemRequest = True



			status_found = False
			for status in self.statusTagsOk:
				if req['status_short'] == status:
					allRequests['status_'+status.lower()]+=1
					status_found = True

			for status in self.statusTagsFail:
				if req['status_short'] == status:
					allRequests['status_'+status.lower()]+=1
					status_found = True
					problemRequest = True
									

			if status_found == False:
				allRequests['status_unknown']+=1
				problemRequest = True
								

			if problemRequest == True:
				problemRequests.append(reqID)
				allRequests['total_problem'] +=1



		for key in allRequests:
			key = key.lower()
			self.db_keys[key] = IntCol()
			self.db_values[key] = allRequests[key]



		details_database = self.__module__ + "_table_details"
	
		self.db_keys["details_database"] = StringCol()
		self.db_values["details_database"] = details_database






		self.db_keys["retrylimit"] = IntCol()
		self.db_values["retrylimit"] = self.retryLimit

		self.db_keys["timelimit"] = StringCol()
		self.db_values["timelimit"] = self.timeLimit




		details_db_keys = {}
		details_db_values = {}

		
		# table keys
		details_db_keys["pnfs"] = StringCol()
		details_db_keys["path"] = StringCol()
		details_db_keys["started_full"] = StringCol()
		details_db_keys["retries"] = StringCol()
		details_db_keys["status_short"] = StringCol()

		
		subtable_problems = self.table_init( self.db_values["details_database"], details_db_keys )

		count = 1
		for req in problemRequests:
			for val in ['pnfs','path','started_full','retries','status_short']:
				details_db_values[val] = stageRequests[req][val]
			self.table_fill( subtable_problems, details_db_values )
			if self.detailsTableCutOff != '':
				if count >= int(self.detailsTableCutOff): break
			count+=1


		
		self.limitCritical = self.configService.get('setup','limit_critical')
		self.limitWarning = self.configService.get('setup','limit_warning')
		

		self.configService.addToParameter('setup',
						  'definition',
						  'Warning level depending on number of requests with problems: <br/> Warning: >= '+self.limitWarning+'<br/> Critical: >= '+self.limitCritical)
		


		if len(problemRequests) >= int(self.limitCritical): self.status = 0
		elif len(problemRequests) >= int(self.limitWarning): self.status = 0.5
		else: self.status = 1



	def output(self):

		"""
		Access data from the sqlite database from here and decide how
		to present it
		"""

		mc_begin = []
		mc_begin.append(  '<table class="TableData">')
		mc_begin.append(  " <tr>")
		mc_begin.append(  '  <td class="dCacheDatarestoreLazyFirstCol">Total number of stage requests</td>')
		mc_begin.append("""  <td>' . $data["total"] . '</td>""")
		mc_begin.append(  ' </tr>')
		for tag in self.statusTagsOk:
			mc_begin.append(  " <tr>")
			mc_begin.append(  '  <td class="dCacheDatarestoreLazyFirstCol"> ...  with status '+tag+':</td>')
			mc_begin.append("""  <td>' . $data["status_"""+tag.lower()+""""] . '</td>""")
			mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append(  '  <td class="dCacheDatarestoreLazyFirstCol">Stage request with problems</td>')
		mc_begin.append("""  <td>' . $data["total_problem"] . '</td>""")
		mc_begin.append(  ' </tr>')
		for tag in self.statusTagsFail:
			mc_begin.append(  ' <tr>')
			mc_begin.append(  '  <td class="dCacheDatarestoreLazyFirstCol"> ...  with status '+tag+':</td>')
			mc_begin.append("""  <td>' . $data["status_"""+tag.lower()+""""] . '</td>""")
			mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td class="dCacheDatarestoreLazyFirstCol">... time limit hit ('.$data[timelimit].')</td>""")
		mc_begin.append("""  <td>' . $data["hit_time"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td class="dCacheDatarestoreLazyFirstCol">... retry limit hit ('.$data[retrylimit].')</td>""")
		mc_begin.append("""  <td>' . $data["hit_retry"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  '</table>')
		mc_begin.append(  '<br />')

		# Show/Hide details table
		mc_begin.append("""<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_result\\\');" />""")
		mc_begin.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_result" style="display:none;">')
		mc_begin.append(  ' <table class="TableDetails dCacheDatarestoreLazyTableDetails">')
		mc_begin.append(  '  <tr class="TableHeader">')
		mc_begin.append(  '   <td>pnfsID</td>')
		mc_begin.append(  '   <td>Start</td>')
		mc_begin.append(  '   <td>Retries</td>')
		mc_begin.append(  '   <td>Status</td>')
		mc_begin.append(  '  </tr>')

		mc_detailed_separator = []
		mc_detailed_separator.append('  <tr>')
		mc_detailed_separator.append('   <td class="dCacheDatarestoreLazyRowSeparator" colspan="4"></td>')
		mc_detailed_separator.append('  </tr>')

		mc_detailed_row = []
		mc_detailed_row.append(  '  <tr>')
		mc_detailed_row.append("""   <td>' . $sub_data["pnfs"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["started_full"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["retries"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["status_short"] . '</td>""")
		mc_detailed_row.append(  '  </tr>')
		mc_detailed_row.append(  '  <tr>')
		mc_detailed_row.append("""   <td colspan="4">' . $sub_data["path"] . '</td>""")
		mc_detailed_row.append(  '  </tr>')

		mc_end = []
		mc_end.append(' </table>')
		mc_end.append('</div>')

		module_content = """<?php

		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

		printf('""" + self.PHPArrayToString(mc_begin) + """');

		$first_row = true;
		foreach ($dbh->query($details_db_sqlquery) as $sub_data)
		{
		    if(!$first_row)
		        printf('""" + self.PHPArrayToString(mc_detailed_separator) + """');
		    $first_row = false;
		    printf('""" + self.PHPArrayToString(mc_detailed_row) + """');
		}

		printf('""" + self.PHPArrayToString(mc_end) + """');

		?>"""

		return self.PHPOutput(module_content)



