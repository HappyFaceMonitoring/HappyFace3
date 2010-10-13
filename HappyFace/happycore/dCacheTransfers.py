from ModuleBase import *
import math

class dCacheTransfers(ModuleBase):

	def __init__(self,module_options):

		ModuleBase.__init__(self,module_options)

		self.db_keys['details_database'] = StringCol()
		self.db_keys['speed_average'] = FloatCol()
		self.db_keys['speed_stdev'] = FloatCol()
		self.db_keys['below_speed_warning_limit'] = IntCol()
		self.db_keys['below_speed_critical_limit'] = IntCol()
		self.db_keys['exceed_time_warning_limit'] = IntCol()
		self.db_keys['exceed_time_critical_limit'] = IntCol()
		self.db_keys['total_transfers'] = IntCol()
		self.db_keys['warning_transfers'] = IntCol()
		self.db_keys['critical_transfers'] = IntCol()
		self.db_values['details_database'] = ''
		self.db_values['speed_average'] = 0.0
		self.db_values['speed_stdev'] = 0.0
		self.db_values['below_speed_warning_limit'] = 0
		self.db_values['below_speed_critical_limit'] = 0
		self.db_values['exceed_time_warning_limit'] = 0
		self.db_values['exceed_time_critical_limit'] = 0
		self.db_values['total_transfers'] = 0
		self.db_values['warning_transfers'] = 0
		self.db_values['critical_transfers'] = 0

		self.dsTag = 'transfers'
		self.fileExtension = 'txt'

		self.speed_warning_limit = int(self.configService.getDefault('setup', 'speed_warning_limit', '500'))
		self.speed_critical_limit = int(self.configService.getDefault('setup', 'speed_critical_limit', '200'))
		self.time_warning_limit = int(self.configService.getDefault('setup', 'time_warning_limit', '72'))
		self.time_critical_limit = int(self.configService.getDefault('setup', 'time_critical_limit', '96'))
		self.rating_ratio = float(self.configService.getDefault('setup', 'rating_ratio', '0.1'))
		self.rating_threshold = int(self.configService.getDefault('setup', 'rating_threshold', '10'))

	def process(self):

		self.db_values['details_database'] = self.__module__ + '_table_details'

		details_db_keys = {}
		details_db_value_list = []

		details_db_keys['protocol'] = StringCol()
		details_db_keys['pnfsid'] = StringCol()
		details_db_keys['pool'] = StringCol()
		details_db_keys['host'] = StringCol()
		details_db_keys['status_text'] = StringCol()
		details_db_keys['since'] = IntCol()
		details_db_keys['transferred'] = IntCol()
		details_db_keys['speed'] = FloatCol()
		details_db_keys['status'] = FloatCol()

		success,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))

		self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))

		# TODO: Add definition
		self.configService.addToParameter('setup', 'definition', 'Speed warning limit: ' + str(self.speed_warning_limit) + ' KiB/s<br/>')
		self.configService.addToParameter('setup', 'definition', 'Speed critical limit: ' + str(self.speed_critical_limit) + ' KiB/s<br/>')
		self.configService.addToParameter('setup', 'definition', 'Time warning limit: ' + str(self.time_warning_limit) + ' hours<br/>')
		self.configService.addToParameter('setup', 'definition', 'Time critical limit: ' + str(self.time_critical_limit) + ' hours<br/>')
		self.configService.addToParameter('setup', 'definition', 'Rating threshold: ' + str(self.rating_threshold) + ' transfers<br/>')
		self.configService.addToParameter('setup', 'definition', 'Rating ratio: ' + str(round(self.rating_ratio*100)) + '% <br/>')

		details_table = self.table_init(self.db_values["details_database"], details_db_keys)

		n_warnings = n_critical = n_total = 0
		n_time_warning = n_time_critical = 0
		n_speed_warning = n_speed_critical = 0
		speed_sum = speed_sqr_sum = 0
		for line in file(sourceFile):
			fields = line.split(' ')
			if len(fields) < 16:
				continue

			protocol = fields[3]
			# Use only dcap-3 transfers for now
			if protocol != 'dcap-3': continue

			# TODO: GFtp-1 have 18 fields since status are 3 strings

			pnfsid = fields[6]
			pool = fields[7]
			host = fields[8]
			status_text = fields[9]
			since = int(fields[10]) # in ms
			transferred = int(fields[13]) # in Bytes
			speed = float(fields[14]) # in Bytes/ms (!!)

			speed_sum += speed
			speed_sqr_sum += speed*speed

			status = 1.0
			if speed*1000.0/1024.0 < self.speed_critical_limit:
				status = min(status, 0.0)
				n_speed_critical += 1
				n_speed_warning += 1
			elif speed*1000.0/1024.0 < self.speed_warning_limit:
				status = min(status, 0.5)
				n_speed_warning += 1

			if since/1000.0/60.0/60.0 >= self.time_critical_limit:
				status = min(status, 0.0)
				n_time_critical += 1
				n_time_warning += 1
			elif since/1000.0/60.0/60.0 >= self.time_warning_limit:
				status = min(status, 0.5)
				n_time_warning += 1

			if status < 1.0: n_warnings += 1
			if status < 0.5: n_critical += 1
			n_total += 1

			details_db_values = {}
			details_db_values['protocol'] = protocol
			details_db_values['pnfsid'] = pnfsid
			details_db_values['pool'] = pool
			details_db_values['host'] = host
			details_db_values['status_text'] = status_text
			details_db_values['since'] = since
			details_db_values['transferred'] = transferred
			details_db_values['speed'] = speed
			details_db_values['status'] = status
			details_db_value_list.append(details_db_values)

		if n_total > 0:
			self.db_values['speed_average'] = speed_sum / n_total
		else:
			self.db_values['speed_average'] = 0.0

		if n_total > 1:
			self.db_values['speed_stdev'] = math.sqrt(1.0/(n_total-1.0) * (speed_sqr_sum - speed_sum*speed_sum/n_total))
		else:
			self.db_values['speed_stdev'] = self.db_values['speed_average']

		self.db_values['below_speed_warning_limit'] = n_speed_warning
		self.db_values['below_speed_critical_limit'] = n_speed_critical
		self.db_values['exceed_time_warning_limit'] = n_time_warning
		self.db_values['exceed_time_critical_limit'] = n_time_critical
		self.db_values['total_transfers'] = n_total
		self.db_values['warning_transfers'] = n_warnings
		self.db_values['critical_transfers'] = n_critical

		self.table_fill_many(details_table, details_db_value_list)
		self.subtable_clear(details_table, [], self.holdback_time)

		self.status = 1.0
		if n_total >= self.rating_threshold:
			if float(n_critical)/n_total > self.rating_ratio:
				self.status = 0.0
			elif float(n_warnings)/n_total > self.rating_ratio:
				self.status = 0.5
			
	def output(self):

		mc_begin = []
		mc_begin.append(  '<table class="TableData">')
		mc_begin.append(  " <tr>")
		mc_begin.append(  '  <td>Total number of transfers</td>')
		mc_begin.append("""  <td>' . $data["total_transfers"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  " <tr>")
		mc_begin.append(  '  <td>Speed average [KiB/s]</td>')
		mc_begin.append("""  <td>' . round($data["speed_average"]) . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  " <tr>")
		mc_begin.append(  '  <td>Standard deviation of speed distribution [KiB/s]</td>')
		mc_begin.append("""  <td>' . round($data["speed_stdev"]) . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append(  '  <td>Number of transfers with warnings</td>')
		mc_begin.append("""  <td>' . $data["warning_transfers"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td>... due to time limit</td>""")
		mc_begin.append("""  <td>' . $data["exceed_time_warning_limit"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td>... due to speed limit</td>""")
		mc_begin.append("""  <td>' . $data["below_speed_warning_limit"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append(  '  <td>Number of critical transfers</td>')
		mc_begin.append("""  <td>' . $data["critical_transfers"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td>... due to time limit</td>""")
		mc_begin.append("""  <td>' . $data["exceed_time_critical_limit"] . '</td>""")
		mc_begin.append(  ' </tr>')
		mc_begin.append(  ' <tr>')
		mc_begin.append("""  <td>... due to speed limit</td>""")
		mc_begin.append("""  <td>' . $data["below_speed_critical_limit"] . '</td>""")
		mc_begin.append(  ' </tr>')

		mc_begin.append(  '</table>')
		mc_begin.append(  '<br />')

		# Show/Hide details table
		mc_begin.append("""<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_result\\\');" />""")
		mc_begin.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_result" style="display:none;">')
		mc_begin.append(  ' <table class="TableDetails" id="' + self.__module__ + '_details_table">')
		mc_begin.append(  '  <tr class="TableHeader">')
		mc_begin.append(  '   <td>pnfsID</td>')
		mc_begin.append(  '   <td>Pool</td>')
		mc_begin.append(  '   <td>Host</td>')
		mc_begin.append(  '   <td>Status</td>')
		mc_begin.append(  '   <td>Time</td>')
		mc_begin.append(  '   <td>Trans. [GiB]</td>')
		mc_begin.append(  '   <td>Speed [KiB/s]</td>')
		mc_begin.append(  '  </tr>')

		mc_detailed_row = []
		mc_detailed_row.append("""  <tr class="' . $status_color . ' dCacheTransfersDetailsRow">""")
		mc_detailed_row.append("""   <td>' . $sub_data["pnfsid"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["pool"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["host"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $sub_data["status_text"] . '</td>""")
		mc_detailed_row.append("""   <td>' . $since_text . '</td>""")
		mc_detailed_row.append("""   <td>' . round($sub_data["transferred"]/1024.0/1024.0/1024.0, 1) . '</td>""")
		mc_detailed_row.append("""   <td>' . round($sub_data["speed"]*1000.0/1024.0) . '</td>""")
		mc_detailed_row.append(  '  </tr>')

		mc_end = []
		mc_end.append(' </table>')
		mc_end.append('</div>')
		mc_end.append('<script type="text/javascript">')
		mc_end.append('  makeTableSortable("' + self.__module__ + '_details_table", [sortFetchText, sortFetchText, sortFetchText, sortFetchText, sortFetchTime, sortFetchNumeric, sortFetchNumeric]);')
		mc_end.append('</script>')


		module_content = """<?php

		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"] . " ORDER BY speed";

		print('""" + self.PHPArrayToString(mc_begin) + """');

		foreach ($dbh->query($details_db_sqlquery) as $sub_data)
		{
		    $status_color = 'ok';
		    if($sub_data['status'] < 0.5)
		        $status_color = 'critical';
		    else if($sub_data['status'] < 1.0)
		        $status_color = 'warning';

		    $days = $sub_data['since']/1000/60/60/24;
		    $hours = $sub_data['since']/1000/60/60%24;
		    $minutes = $sub_data['since']/1000/60%60;
		    $seconds = $sub_data['since']/1000%60;
		    $since_text = sprintf('%d d %02d:%02d:%02d', $days, $hours, $minutes, $seconds);
		    print('""" + self.PHPArrayToString(mc_detailed_row) + """');
		}

		print('""" + self.PHPArrayToString(mc_end) + """');

		?>"""

		return self.PHPOutput(module_content)
