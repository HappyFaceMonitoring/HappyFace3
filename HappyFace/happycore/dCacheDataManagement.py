from ModuleBase import *
from sqlobject import *
from DownloadTag import *
from XMLParsing import *
#import GetData
#import xml.sax
#import time
#import bz2
#import os

class dCacheDataManagement(ModuleBase):

    def __init__(self, module_options):
	ModuleBase.__init__(self, module_options)

	self.db_keys["details_database"] = StringCol()
	self.db_keys["chimera_timestamp"] = IntCol()
	self.db_keys["bare_total_files"] = IntCol()
	self.db_keys["bare_total_size"] = FloatCol()
	self.db_keys["bare_on_disk_files"] = IntCol()
	self.db_keys["bare_on_disk_size"] = FloatCol()
	self.db_keys["total_on_disk_files"] = IntCol()
	self.db_keys["total_on_disk_size"] = FloatCol()
	self.db_keys["on_disk_threshold"] = FloatCol()

	# Make sure there are valid values for these columns just in case
	# there is an error before we get to set them.
	self.db_values["details_database"] = ''
	self.db_values["chimera_timestamp"] = 0
	self.db_values["bare_total_files"] = 0
	self.db_values["bare_total_size"] = 0.0
	self.db_values["bare_on_disk_files"] = 0
	self.db_values["bare_on_disk_size"] = 0.0
	self.db_values["total_on_disk_files"] = 0
	self.db_values["total_on_disk_size"] = 0.0
	self.db_values["on_disk_threshold"] = 0.0

	self.warning_limit = int(self.configService.getDefault('setup', 'warning_limit', '-1'))
	self.critical_limit = int(self.configService.getDefault('setup', 'critical_limit', '-1'))
	self.on_disk_threshold = float(self.configService.getDefault('setup', 'on_disk_threshold', '0.95'))

	self.configService.addToParameter('setup', 'definition', 'Warning level depending on timestamp of last chimera dump:')
	self.configService.addToParameter('setup', 'definition', '<br />Warning: &gt;= ' + str(self.warning_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br />Critical: &gt;= ' + str(self.critical_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br />On-disk threshold: ' + str(int(round(self.on_disk_threshold * 100))) + '%')

	self.dsTag = 'xml_source'

    def set_db_value(self, db_values, dataset, value):
        if value in dataset:
	    db_values[value] = dataset[value];
	else:
	    db_values[value] = 0

    def set_db_values(self, db_values, dataset):
	self.set_db_value(db_values, dataset, 'bare_total_files')
	self.set_db_value(db_values, dataset, 'bare_total_size')
	self.set_db_value(db_values, dataset, 'bare_on_disk_files')
	self.set_db_value(db_values, dataset, 'bare_on_disk_size')
	self.set_db_value(db_values, dataset, 'total_on_disk_files')
	self.set_db_value(db_values, dataset, 'total_on_disk_size')

    def process(self):
        details_database = self.__module__ + "_table_details"
	self.db_values['details_database'] = details_database
	self.db_values["on_disk_threshold"] = self.on_disk_threshold

	details_db_keys = {}
	details_db_keys['name'] = StringCol()
	details_db_keys['bare_total_files'] = IntCol()
	details_db_keys['bare_total_size'] = FloatCol()
	details_db_keys["bare_on_disk_files"] = IntCol()
	details_db_keys["bare_on_disk_size"] = FloatCol()
	details_db_keys["total_on_disk_files"] = IntCol()
	details_db_keys["total_on_disk_size"] = FloatCol()

	self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))

	details_table = self.table_init(details_database, details_db_keys)

	dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)

	total = {}
	root = source_tree.getroot()
	details_db_values = []
	cur_timestamp = 0
	for element in root:
	    if element.tag == 'time':
	        cur_timestamp = int(element.text)
	        self.db_values["chimera_timestamp"] = cur_timestamp
	    elif element.tag == 'dataset':
	        details_values = {}
	        details_values['name'] = element.attrib['name']
	        dataset = {}
		for subelement in element:
		    dataset[subelement.tag] = int(subelement.text)
                self.set_db_values(details_values, dataset)
		details_db_values.append(details_values)
	    else:
	        total[element.tag] = int(element.text)
        self.set_db_values(self.db_values, total)

	# We only populate the details table if its content actually changed
	# since the last iteration. To find out we compare the timestamp
	# of the chimera dump. To do so, fetch previous row of main module table
	class main_table(SQLObject):
	    class sqlmeta:
	        table = self.database_table
	        registry = self.__module__
	    timestamp = IntCol()
	    chimera_timestamp = IntCol()

        prev_timestamp = 0
        try:
	    prev_row = list(main_table.select(orderBy=DESC(main_table.q.timestamp))[0:1])
	    if len(prev_row) > 0:
	        prev_timestamp = prev_row[0].chimera_timestamp
	except:
	    pass

	if cur_timestamp == 0 or prev_timestamp == 0 or cur_timestamp > prev_timestamp:
		self.table_fill_many(details_table, details_db_values)
	self.subtable_clear(details_table, [], self.holdback_time)

	if cur_timestamp == 0 or (self.critical_limit != -1 and time.time() - self.critical_limit*3600 > cur_timestamp):
		self.status = 0.0
	elif self.warning_limit != -1 and time.time() - self.warning_limit*3600 > cur_timestamp:
		self.status = 0.5
	else:
		self.status = 1.0

    def output(self):

	html = []
	html.append(  "<p style=\"font-size:large; ' . $gen_color . '\">Chimera dump generated on ' . strftime('%a, %d %b %Y %T %z', $data['chimera_timestamp']) . '</p>")
	html.append(  '<table class="TableData">')
	html.append(  ' <tr class="TableHeader">')
	html.append(  '  <td></td>')
	html.append(  '  <td>Number of Files</td>')
	html.append(  '  <td>Size in GiB</td>')
	html.append(  '  <td>Size in TiB</td>')
	html.append(  '  <td>Size in TB</td>')
	html.append(  ' </tr>')
	html.append(  ' <tr>')
	html.append(  '  <td>Bare total</td>')
	html.append("""  <td>' . $data['bare_total_files'] . '</td>""")
	html.append("""  <td>' . round($data['bare_total_size']/1024.0/1024.0/1024.0, 1) . '</td>""")
	html.append("""  <td>' . round($data['bare_total_size']/1024.0/1024.0/1024.0/1024.0, 1) . '</td>""")
	html.append("""  <td>' . round($data['bare_total_size']/1000.0/1000.0/1000.0/1000.0, 1) . '</td>""")
	html.append(  ' </tr>')
	html.append(  ' <tr>')
	html.append(  '  <td>Bare on disk</td>')
	html.append("""  <td>' . $data['bare_on_disk_files'] . ' (' . ( ($data['bare_total_files'] != 0) ? round($data['bare_on_disk_files']*100.0/$data['bare_total_files']) : 0) . '%)</td>""")
	html.append("""  <td>' . round($data['bare_on_disk_size']/1024.0/1024.0/1024.0, 1) . ' (' . ( ($data['bare_total_size'] != 0) ? round($data['bare_on_disk_size']*100.0/$data['bare_total_size']) : 0) . '%)</td>""")
	html.append("""  <td>' . round($data['bare_on_disk_size']/1024.0/1024.0/1024.0/1024.0, 1) . ' (' . ( ($data['bare_total_size'] != 0) ? round($data['bare_on_disk_size']*100.0/$data['bare_total_size']) : 0) . '%)</td>""")
	html.append("""  <td>' . round($data['bare_on_disk_size']/1000.0/1000.0/1000.0/1000.0, 1) . ' (' . ( ($data['bare_total_size'] != 0) ? round($data['bare_on_disk_size']*100.0/$data['bare_total_size']) : 0) . '%)</td>""")
	html.append(  ' </tr>')
	html.append(  ' <tr>')
	html.append(  '  <td>Total on disk</td>')
	html.append("""  <td>' . $data['total_on_disk_files'] . '</td>""")
	html.append("""  <td>' . round($data['total_on_disk_size']/1024.0/1024.0/1024.0, 1) . '</td>""")
	html.append("""  <td>' . round($data['total_on_disk_size']/1024.0/1024.0/1024.0/1024.0, 1) . '</td>""")
	html.append("""  <td>' . round($data['total_on_disk_size']/1000.0/1000.0/1000.0/1000.0, 1) . '</td>""")
	html.append(  ' </tr>')
	html.append(  '</table>')
	html.append(  '<br />')

	details_begin = []
	details_begin.append("""<input type="button" value="Show/Hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_details\\\');" />""")
	details_begin.append('  <div class="DetailedInfo" id="' + self.__module__+ '_details" style="display:none;">')
	details_begin.append('   <table class="TableDetails" id="' + self.__module__ + '_details_table">')
	details_begin.append('    <tr class="TableHeader">')
	details_begin.append('     <td>Dataset name</td>')
	details_begin.append('     <td>Bare total</td>')
	details_begin.append('     <td>Bare on disk</td>')
	details_begin.append('     <td>Total on disk</td>')
	details_begin.append('    </tr>')

	details_row = []
	details_row.append("""  <tr' . $class_str . '>""")
	details_row.append("""   <td class="dCacheDataManagementDetailsName">' . htmlentities($info['name']) . '</td>""")
	details_row.append("""   <td class="dCacheDataManagementDetailsCell">' . $info['bare_total_files'] . ' files<br/>' . round($info['bare_total_size']/1024.0/1024.0/1024.0,1) . ' GiB</td>""")
	details_row.append("""   <td class="dCacheDataManagementDetailsCell">' . $info['bare_on_disk_files'] . ' files (' . ( ($info['bare_total_files'] != 0) ? round($info['bare_on_disk_files']*100.0/$info['bare_total_files']) : 0) . '%)<br/>' . round($info['bare_on_disk_size']/1024.0/1024.0/1024.0,1) . ' GiB (' . (($info['bare_total_size'] != 0) ? round($info['bare_on_disk_size']*100.0/$info['bare_total_size']) : 0) . '%)</td>""")
	details_row.append("""   <td class="dCacheDataManagementDetailsCell">' . $info['total_on_disk_files'] . ' files<br/>' . round($info['total_on_disk_size']/1024.0/1024.0/1024.0,1) . ' GiB</td>""")
	details_row.append(  '  </tr>')

	details_end = []
	details_end.append(' </table>')
	details_end.append('</div>')
	details_end.append('<script type="text/javascript">')
	details_end.append('  function sortFetch' + self.__module__ + '(a,b)')
	details_end.append('  {')
	details_end.append('    return parseFloat(a.firstChild.nextSibling.nextSibling.nodeValue);')
	details_end.append('  }')
	details_end.append('  function sortFetch' + self.__module__ + '2(a,b)')
	details_end.append('  {')
	details_end.append('    var re = new RegExp("(([0-9]+)\%\)");')
	details_end.append('    var match = re.exec(a.firstChild.nodeValue);')
	details_end.append('    return parseFloat(match[1]);')
	details_end.append('  }')
	details_end.append('')
	details_end.append('  makeTableSortable("' + self.__module__ + '_details_table", [sortFetchText, sortFetch' + self.__module__ + ', sortFetch' + self.__module__ + '2, sortFetch' + self.__module__  + ']);')
	details_end.append('</script>')

	module_content = """<?php


	// Select all records with highest timestamp below $data["timestamp"].
	// Other modules simply use WHERE timestamp=$data['timestamp'] here
	// but we can't do that since we do not update the details table in
	// every iteration.
	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " dat JOIN (SELECT max(timestamp) as mtp FROM " . $data["details_database"] . " WHERE timestamp <= " . $data["timestamp"] . ") t ON dat.timestamp=t.mtp ORDER BY dat.name";

	$gen_color = '';
	if($data['status'] < 1.0)
		$gen_color = 'color: red;';

	print('""" + self.PHPArrayToString(html) + """');

	print('""" + self.PHPArrayToString(details_begin) + """');

	foreach($dbh->query($details_db_sqlquery) as $info)
	{
		$class_str = '';
		$on_disk_ratio = $info['bare_on_disk_files'] * 1.0 / $info['bare_total_files'];
		if($on_disk_ratio > $data['on_disk_threshold'])
			$class_str = ' class="ok"';

		if($info['name'] == 'Unassigned')
			$unassigned = $info;
		else
			print('""" + self.PHPArrayToString(details_row) + """');
	}

	// Show unassigned datasets at the end
	if(isset($unassigned))
	{
		$info = $unassigned;

		$class_str = '';
		if($info['bare_on_disk_files'] * 1.0 / $info['bare_total_files'] > $data['on_disk_threshold'])
			$class_str = ' class="ok"';

		print('""" + self.PHPArrayToString(details_row) + """');
	}

	print('""" + self.PHPArrayToString(details_end) + """');

	?>"""

	return self.PHPOutput(module_content)
