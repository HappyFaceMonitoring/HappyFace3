from ModuleBase import *
from XMLParsing import *
from PhpDownload import *

#from time import strftime
import datetime
from operator import itemgetter

class DashboardDatasetUsage(ModuleBase,PhpDownload):

	"""
	Queries the dashboard for usage of all datasets of a
	given site. 
	"""

	def __init__(self,module_options):

		ModuleBase.__init__(self,module_options)
		PhpDownload.__init__(self)

		## get the url
		self.base_url = self.configService.get('setup','base_url')

		### get the site
		#self.sites = self.configService.get( 'phpArgs','sites' )

		## consider dataset usage of the last x days
		self.days = int( self.configService.get( 'setup','days' ) )

		## order most/least used dataset in terms of
		#self.sort_by = self.configService.get( 'setup','sort_by' )

		## can be 'most' or 'least'
		self.usage = self.configService.get( 'setup','usage' )

		## consider the first/last x datasets
		self.n_datasets = int( self.configService.get( 'setup','n_datasets' ) )

		## get the time span for the query
		date1, date2 = self.getTimespan()

		# definition of the database table keys and pre-defined values
		self.db_keys["details_database"] = StringCol()
		self.db_values["details_database"] = ""

		self.dsTag = 'DashboardDatasetUsage_xml_source'
		self.downloadRequest[self.dsTag] = 'wget|' + self.makeUrl() + "&date1=" + date1 + "&date2=" + date2 

	def process(self):
		"""
		Collects the data from the web source. Stores it then into the
		sqlite data base. The overall status has to be determined here.
		"""
		# run the test

		success,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
		source_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile)

		# parse the details and store it in a special database table
		details_database = self.__module__ + "_table_details"

		self.db_values["details_database"] = details_database

		details_db_keys = {}
		details_db_values = {}

		## define details_deb_keys here
		details_db_keys["jobs"] = IntCol()
		details_db_keys["users"] = IntCol()
		details_db_keys["success"] = FloatCol()
		details_db_keys["name"] = StringCol()

		my_subtable_class = self.table_init( details_database, details_db_keys )

		## now start parsing the xml tree
		root = source_tree.getroot()

		dataset_list = []

		### now do something
		for element in root:
			#print element.tag
			if not element.tag == 'inputcollections':
				continue

			for item in element:
				if not item.tag == 'item':
					continue
				dataset = {}
				for i in item:

					if i.tag == 'jobs':
						dataset["jobs"] = int( i.text ) 
					elif i.tag == 'users':
						dataset['users'] = int( i.text )
					elif i.tag == 'success':
						dataset['success'] = float( i.text )
					elif i.tag == 'inputcollection':
						dataset['name'] = str( i.text )
						

				dataset_list.append( dataset )

		rev = False
		if self.usage == 'most':
			rev = True

		## sort the list
		dataset_list_sorted = sorted(dataset_list, key = itemgetter('jobs'), reverse = rev )

		#for d in dataset_list_sorted:
		#	print d[self.sort_by]

		self.fillDatabase( details_db_values, my_subtable_class, dataset_list_sorted )

		# stays happy 
		self.status = self.determineStatus()

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


		begin = []
		begin.append('<table class="TableData">')
		begin.append(' <tr class="TableHeader">')
		begin.append('  <td>dataset</td>')
		begin.append('  <td>number of jobs</td>')
		#begin.append('  <td></td>')
		begin.append(' </tr>')

		info_row = []
		info_row.append(""" <tr class="' .$service_status_color_flag . '">""")
		info_row.append("""  <td>' . $info["name"] . '</td>""")
		info_row.append("""  <td>' . $info["jobs"]. '</td>""")
		info_row.append(  ' </tr>')

		mid = []
		mid.append(  '</table>')
		mid.append(  '<br />');
		mid.append("""<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ "_failed_result" + """\\\');" />""")
		mid.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_failed_result" style="display:none;">')
		mid.append(  ' <table class="TableDetails">')
		mid.append(  '  <tr class="TableHeader">')
		mid.append(  '   <td>dataset</td>')
		mid.append(  '   <td>number of jobs</td>')
		mid.append(  '   <td>number of users</td>')
		mid.append(  '   <td>success</td>')
		mid.append(  '  </tr>')

		detailed_row = []
		detailed_row.append("""  <tr class="' .$service_status_color_flag . '">""")
		detailed_row.append("""   <td>' . $info["name"]   . '</td>""")
		detailed_row.append("""   <td>' . $info["jobs"]  . '</td>""")
		detailed_row.append("""   <td>' . $info["users"]   . '</td>""")
		detailed_row.append("""   <td>' . $info["success"]    . '</td>""")
		detailed_row.append(  '  </tr>');
		
		end = []
		end.append(' </table>')
		end.append('</div>')


		module_content = self.PHPArrayToString(begin) + """<?php

		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];

		$service_status_color_flag = "report";
		
		foreach ($dbh->query($details_db_sqlquery) as $info)
		{		
		print('""" + self.PHPArrayToString(info_row) + """');
		}
		
		print('""" + self.PHPArrayToString(mid) + """');
		
		foreach ($dbh->query($details_db_sqlquery) as $info)
		{
	
		print('""" + self.PHPArrayToString(detailed_row) + """');
		}
		
		print('""" + self.PHPArrayToString(end) + """');
                
		?>"""


		return self.PHPOutput(module_content)

	def getTimespan(self):
		"""
		Gets the dates for the timespan (today, x days in the past)
		"""
		## today
		today = datetime.date.today()
		date2 = str( today.strftime( "%d-%m-%Y" ) )

		timediff = datetime.timedelta( days = -int(self.days) )
		past = today + timediff
		
		date1 = str( past.strftime( "%d-%m-%Y" ) )

		#print "date1:\t", date1
		#print "date2:\t", date2

		return date1, date2

	def determineStatus(self):
		"""
		Determines overall status of the module
		"""
		return 1.

	def fillDatabase( self, details_db_values, my_subtable_class, d_list ):
		"""
		Fills the database
		"""

		counter = 0

		while counter < self.n_datasets:
			## if there are less datasets at the site then you
			## wanted to display
			if counter >= len( d_list ):
				continue

			details_db_values["jobs"] = d_list[counter]["jobs"]
			details_db_values["users"] = d_list[counter]["users"]
			details_db_values["success"] = d_list[counter]["success"]
			details_db_values["name"] = d_list[counter]["name"]

			self.table_fill( my_subtable_class, details_db_values )

			counter += 1
		self.subtable_clear(my_subtable_class, [], self.holdback_time)
		pass
