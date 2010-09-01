from ModuleBase import *
from XMLParsing import *

class JobsStatistics(ModuleBase):

    def __init__(self,module_options):

        ModuleBase.__init__(self,module_options)

        self.min_jobs = int(self.configService.get("setup","min_jobs"))
        self.warning_limit = float(self.configService.get("setup","warning_limit"))
        self.critical_limit = float(self.configService.get("setup","critical_limit"))

	self.groups = self.configService.get("setup", "groups").split(',')
	self.rating_groups = self.configService.get("setup", "rating_groups").split(',')

	if len(self.groups) == 0 or self.groups[0] == '':
		self.groups = None
	if len(self.rating_groups) == 0 or self.rating_groups[0] == '':
		self.rating_groups = None

	self.db_keys["groups_database"] = StringCol()
	self.db_keys["details_database"] = StringCol()
	self.db_keys["details_group"] = StringCol()
	self.db_values["groups_database"] = ""
	self.db_values["details_database"] = ""
	self.db_values["details_group"] = ""

        self.dsTag = 'xml_source'

    def process(self):

	self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))
	self.configService.addToParameter('setup', 'definition', '<br />Warning limit: ' + str(self.warning_limit))
	self.configService.addToParameter('setup', 'definition', '<br />Critical limit: ' + str(self.critical_limit))
	self.configService.addToParameter('setup', 'definition', '<br />Minimum number of jobs for rating: ' + str(self.min_jobs))

	if self.rating_groups is not None:
	    self.configService.addToParameter('setup', 'definition', '<br />Rated group(s): ' + ', '.join(self.rating_groups))

        dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)

	root = source_tree.getroot()

	groups_database = self.__module__ + "_table_groups"
	self.db_values["groups_database"] = groups_database

	groups_db_keys = {}
	groups_db_value_list = []

	# Note simply "group" doesn't work since it's a reserved SQL keyword
	groups_db_keys["groupname"] = StringCol()
	groups_db_keys["parentgroup"] = StringCol()
	groups_db_keys["total"] = IntCol()
	groups_db_keys["running"] = IntCol()
	groups_db_keys["pending"] = IntCol()
	groups_db_keys["waiting"] = IntCol()
	groups_db_keys["ratio10"] = IntCol()
	groups_db_keys["status"] = FloatCol()

	groups_table = self.table_init(groups_database, groups_db_keys)

	self.status = 1.0
	for element in root:
	    if element.tag == "summaries":
		for child in element:
		    if child.tag == "summary":
		        group = 'all'
			parent = ''
		        if 'group' in child.attrib:
			    group = child.attrib['group']
			if 'parent' in child.attrib:
			    parent = child.attrib['parent']

			if self.groups is not None and group not in self.groups:
			    continue

			total = 0
			running = 0
			pending = 0
			waiting = 0
			ratio10 = 0
			for subchild in child:
			    if subchild.tag == 'jobs':
			        total = int(subchild.text.strip())
			    if subchild.tag == 'running':
			        running = int(subchild.text.strip())
			    if subchild.tag == 'pending':
			        pending = int(subchild.text.strip())
			    if subchild.tag == 'waiting':
			        waiting = int(subchild.text.strip())
			    if subchild.tag == 'ratio10':
			        ratio10 = int(subchild.text.strip())

			status = 1.0
		        if running >= self.min_jobs and ratio10 >= running*self.warning_limit:
		            status = 0.5
			if running >= self.min_jobs and ratio10 >= running*self.critical_limit:
			    status = 0.0

			if self.rating_groups is None or group in self.rating_groups:
			    if status < self.status:
			        self.status = status

			groups_db_values = {}
			groups_db_values["groupname"] = group
			groups_db_values["parentgroup"] = parent
			groups_db_values["total"] = total
			groups_db_values["running"] = running
			groups_db_values["pending"] = pending
			groups_db_values["waiting"] = waiting
			groups_db_values["ratio10"] = ratio10
			groups_db_values["status"] = status
			groups_db_value_list.append(groups_db_values)
			
	self.table_fill_many(groups_table, groups_db_value_list)
	self.subtable_clear(groups_table, [], self.holdback_time)

	# Write details
	details_database = self.__module__ + "_table_details"
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_value_list = []

	# Note simply "group" doesn't work since it's a reserved SQL keyword
	details_db_keys["user"] = StringCol()
	details_db_keys["total"] = IntCol()
	details_db_keys["running"] = IntCol()
	details_db_keys["pending"] = IntCol()
	details_db_keys["waiting"] = IntCol()
	details_db_keys["ratio100"] = IntCol()
	details_db_keys["ratio80"] = IntCol()
	details_db_keys["ratio30"] = IntCol()
	details_db_keys["ratio10"] = IntCol()
	details_db_keys["status"] = FloatCol()

	details_table = self.table_init(details_database, details_db_keys)

	users = {}
	for element in root:
	    if element.tag == "jobs":
	        group = ''
		if 'group' in element.attrib:
		    group = element.attrib['group']
		self.db_values["details_group"] = group

		for child in element:
		    if child.tag == "job":
		        user = ''
		        state = ''
			cpueff = 0.0

			for subchild in child:
			    if subchild.tag == 'user':
			        user = subchild.text.strip()
			    if subchild.tag == 'state':
			        state = subchild.text.strip()
			    if subchild.tag == 'cpueff':
			        cpueff = float(subchild.text.strip())

			if user == '' or state == '': continue
			if user not in users:
				users[user] = { 'total': 0, 'running': 0, 'pending': 0, 'waiting': 0, 'ratio100': 0, 'ratio80': 0, 'ratio30': 0, 'ratio10': 0 };

			users[user]['total'] += 1
			if state == 'running': users[user]['running'] += 1
			elif state == 'pending': users[user]['pending'] += 1
			elif state == 'waiting': users[user]['waiting'] += 1

			if cpueff > 80: users[user]['ratio100'] += 1
			elif cpueff > 30: users[user]['ratio80'] += 1
			elif cpueff > 10: users[user]['ratio30'] += 1
			else: users[user]['ratio10'] += 1

	        # There should only be one jobs entry
	        break

	# Do user rating
	for user in users:
	    users[user]['user'] = user

	    status = 1.0
	    if users[user]['running'] >= self.min_jobs and users[user]['ratio10'] >= users[user]['running']*self.warning_limit:
	        status = 0.5
	    if users[user]['running'] >= self.min_jobs and users[user]['ratio10'] >= users[user]['running']*self.critical_limit:
	        status = 0.0
	    users[user]['status'] = status

	self.table_fill_many(details_table, users.values())
	self.subtable_clear(details_table, [], self.holdback_time)

    def output(self):

	# JavaScript for plotting functionality

	js = []
	js.append('<script type="text/javascript">')
	js.append('function ' + self.__module__ + '_get_list_of_checked_elements(id)')
	js.append('{')
	js.append('  elems = new Array();')
	js.append('  for(var i = 0;;++i)')
	js.append('  {')
	js.append('    var elem = document.getElementById("' + self.__module__ + '_" + id + "_" + i);')
	js.append('    if(!elem) break;')
	js.append('    if(elem.checked) elems.push(elem.value);')
	js.append('  }')
	js.append('  return elems.join(",");')
	js.append('}')
	js.append('')
	js.append('function ' + self.__module__ + '_toggle_checked_elements(id)')
	js.append('{')
	js.append('  for(var i = 0;;++i)')
	js.append('  {')
	js.append('    var elem = document.getElementById("' + self.__module__ + '_" + id + "_" + i);')
	js.append('    if(!elem) break;')
	js.append('    elem.checked = !elem.checked;')
	js.append('  }')
	js.append('}')
	js.append('')
	js.append('function ' + self.__module__ + '_toggle_button()')
	js.append('{')
	js.append('  ' + self.__module__ + '_toggle_checked_elements("constraint");')
	js.append('  ' + self.__module__ + '_toggle_checked_elements("variable");')
	js.append('}')
	js.append('')
	js.append('function ' + self.__module__ + '_col_button(variable)')
	js.append('{')
	js.append('  var groups = ' + self.__module__ + '_get_list_of_checked_elements("constraint");')
	js.append('  document.getElementById("' + self.__module__ + '_constraint").value = "groupname=" + groups;')
	js.append('  document.getElementById("' + self.__module__ + '_variables").value = variable;')
	js.append('}')
	js.append('')
	js.append('function ' + self.__module__ + '_row_button(group)')
	js.append('{')
	js.append('  var variables = ' + self.__module__ + '_get_list_of_checked_elements("variable");')
	js.append('  if(variables == "") variables = "total,running,ratio10";')
	js.append('  document.getElementById("' + self.__module__ + '_constraint").value = "groupname=" + group;')
	js.append('  document.getElementById("' + self.__module__ + '_variables").value = variables;')
	js.append('}')
	js.append('')
	js.append('function ' + self.__module__ + '_both_button(group)')
	js.append('{')
	js.append('  var groups = ' + self.__module__ + '_get_list_of_checked_elements("constraint");')
	js.append('  var variables = ' + self.__module__ + '_get_list_of_checked_elements("variable");')
	js.append('  if(variables == "") variables = "total,running,ratio10";')
	js.append('  document.getElementById("' + self.__module__ + '_constraint").value = "groupname=" + groups;')
	js.append('  document.getElementById("' + self.__module__ + '_variables").value = variables;')
	js.append('}')
	js.append('</script>')

	begin = []
	begin.append(  '<form method="get" action="plot_generator.php" onsubmit="javascript:submitFormToWindow(this);">')
	begin.append(  ' <table style="font: bold 0.9em sans-serif; width:800px; background-color: #ddd; border: 1px #999 solid;">')
	begin.append(  '  <tr>')
	begin.append(  '   <td>Start:</td>')
	begin.append(  '   <td>')
	begin.append("""    <input name="date0" type="text" size="10" style="text-algin:center;" value="' . strftime("%Y-%m-%d", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
	begin.append("""    <input name="time0" type="text" size="5" style="text-algin:center;" value="' . strftime("%H:%M", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
	begin.append(  '   <td>End:</td>')
	begin.append(  '   <td>')
	begin.append("""    <input name="date1" type="text" size="10" style="text-algin:center;" value="' . $date_string . '" />""")
	begin.append("""    <input name="time1" type="text" size="5" style="text-algin:center;" value="' . $time_string . '" />""")
	begin.append(  '   </td>')
	begin.append(  '   <td>')
	begin.append(  '    <input type="checkbox" name="renormalize" value="1" />Show Trend plot')
	begin.append(  '   </td>')
	begin.append(  '   <td>')
	begin.append(  '    <input type="hidden" name="module" value="' + self.__module__ + '" />')
	begin.append(  '    <input type="hidden" name="subtable" value="' + self.__module__ + '_table_groups" />')
	begin.append(  '    <input type="hidden" id="' + self.__module__ + '_constraint" name="constraint" value="" />')
	begin.append(  '    <input type="hidden" id="' + self.__module__ + '_variables" name="variables" value="" />')
	begin.append(  '    <input type="hidden" id="' + self.__module__ + '_squash" name="squash" value="1" />')
	begin.append(  '   </td>')
	begin.append(  '  </tr>')
	begin.append(  ' </table>')
	begin.append(  ' <table class="TableData">')
	begin.append(  '  <tr class="TableHeader">')
	begin.append(  '   <td>Group</td>')
	begin.append("""   <td><input type="checkbox" id=\"""" + self.__module__ + """_variable_0" value="total" checked="checked" />Total jobs</td>""")
	begin.append("""   <td><input type="checkbox" id=\"""" + self.__module__ + """_variable_1" value="running" checked="checked" />Running jobs</td>""")
	begin.append("""   <td><input type="checkbox" id=\"""" + self.__module__ + """_variable_2" value="ratio10" checked="checked" />Jobs with wallratio &lt; 10%</td>""")
	begin.append(  '   <td>Plot jobs</td>')
	begin.append(  '  </tr>')
	begin.append(  '  <tr class="TableHeader">')
	begin.append(  '   <td><input type="button" value="Toggle Selection" onfocus="this.blur()" onclick="' + self.__module__ + '_toggle_button()" /></td>')
	begin.append("""   <td><button onfocus="this.blur()" onclick=\"""" + self.__module__ + """_col_button(\\\'total\\\')">Plot Col</button></td>""")
	begin.append("""   <td><button onfocus="this.blur()" onclick=\"""" + self.__module__ + """_col_button(\\\'running\\\')">Plot Col</button></td>""")
	begin.append("""   <td><button onfocus="this.blur()" onclick=\"""" + self.__module__ + """_col_button(\\\'ratio10\\\')">Plot Col</button></td>""")
	begin.append("""   <td><button onfocus="this.blur()" onclick=\"""" + self.__module__ + """_both_button()">Plot Selected</button></td>""")
	begin.append(  '  </tr>')

	row = []
	row.append(  """  <tr class="' . $status_class . '">""")
	row.append(  """   <td style="padding-left: ' . ($indentation*15) . 'px;"><input type="checkbox" id=\"""" + self.__module__ + """_constraint_' . $i . '" value="' . $info['groupname'] . '" checked="checked" />' . $info['groupname'] . '</td>""")
	row.append(    "   <td>' . $info['total'] . '</td>")
	row.append(    "   <td>' . $info['running'] . '</td>")
	row.append(    "   <td>' . $info['ratio10'] . '</td>")
	row.append(  """   <td><button onfocus="this.blur()" onclick=\"""" + self.__module__ + """_row_button(\\\'' . $info['groupname'] . '\\\')">Plot Row</button></td>""")
	row.append(    '  </tr>')

	end = []
	end.append(    ' </table>')
	end.append(    '</form>')
	end.append(    '<br />')

	details_begin = []
	details_begin.append("""<input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__ + """_details\\\');" />""")
	details_begin.append(  '<div class="DetailedInfo" id="' + self.__module__ + '_details" style="display:none;">')
	details_begin.append(  " ' . (($data['details_group'] != '') ? ('<p>Note: This table shows users of the group <strong>' . htmlentities($data['details_group']) . '</strong> only</p>') : ('')) . '")
	details_begin.append(  ' <table class="TableDetails">')
	details_begin.append(  '  <tr class="TableHeader">')
	details_begin.append(  '   <td>User</td>')
	details_begin.append(  '   <td>Total</td>')
	details_begin.append(  '   <td>Running</td>')
	details_begin.append(  '   <td>Waiting</td>')
	details_begin.append(  '   <td>Queued</td>')
	details_begin.append(  '   <td>Eff. > 80%</td>')
	details_begin.append(  '   <td>80% > Eff. > 30%</td>')
	details_begin.append(  '   <td>30% > Eff. > 10%</td>')
	details_begin.append(  '   <td>10% > Eff.</td>')
	details_begin.append(  '  </tr>')

	details_row = []
	details_row.append( """ <tr class="' . $status_class . '">""")
	details_row.append(    "  <td>' . htmlentities($info['user']) . '</td>")
	details_row.append(    "  <td>' . $info['total'] . '</td>")
	details_row.append(    "  <td>' . $info['running'] . '</td>")
	details_row.append(    "  <td>' . $info['waiting'] . '</td>")
	details_row.append(    "  <td>' . $info['pending'] . '</td>")
	details_row.append(    "  <td>' . $info['ratio100'] . '</td>")
	details_row.append(    "  <td>' . $info['ratio80'] . '</td>")
	details_row.append(    "  <td>' . $info['ratio30'] . '</td>")
	details_row.append(    "  <td>' . $info['ratio10'] . '</td>")
	details_row.append(    ' </tr>')

	details_end = []
	details_end.append(    ' </table>')
	details_end.append(    '</div>')
	details_end.append(    '<br />')

	module_content = """<?php

	print('""" + self.PHPArrayToString(js) + """');
	print('""" + self.PHPArrayToString(begin) + """');

	$details_db_sqlquery = "SELECT * FROM " . $data["groups_database"] . " WHERE timestamp = " . $data["timestamp"];

	$groups = array();
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		if($info['status'] >= 1.0)
			$status_class = 'ok';
		else if($info['status'] >= 0.5)
			$status_class = 'warning';
		else
			$status_class = 'critical';

		$info['children'] = array();
		$groups[$info['groupname']] = $info;
	}

	// Build hierarchy
	foreach($groups as $name=>$group)
	{
		if($group['parentgroup'] != '')
			$groups[$group['parentgroup']]['children'][] = $group['groupname'];
	}

	function """ + self.__module__ + """_show_group($groups, $group, $i, $indentation)
	{
		$info = $groups[$group];

		if($info['status'] >= 1.0)
			$status_class = 'ok';
		else if($info['status'] >= 0.5)
			$status_class = 'warning';
		else
			$status_class = 'critical';

		print('""" + self.PHPArrayToString(row) + """');

		++$i;

		foreach($info['children'] as $child)
			$i = """ + self.__module__ + """_show_group($groups, $child, $i, $indentation+1);
		return $i;
	}

	$i = 0;
	foreach($groups as $name=>$info)
	{
		if($info['parentgroup'] == '')
			$i = """ + self.__module__ + """_show_group($groups, $name, $i, 0);
	}

	print('""" + self.PHPArrayToString(end) + """');

	print('""" + self.PHPArrayToString(details_begin) + """');

	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		if($info['status'] >= 1.0)
			$status_class = 'ok';
		else if($info['status'] >= 0.5)
			$status_class = 'warning';
		else
			$status_class = 'critical';

		print('""" + self.PHPArrayToString(details_row) + """');
	}

	print('""" + self.PHPArrayToString(details_end) + """');

	?>"""

	return self.PHPOutput(module_content)
