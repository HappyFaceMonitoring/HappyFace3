from ModuleBase import *
from XMLParsing import *


class JobsStatisticsSummary(ModuleBase):

    def __init__(self,module_options): 
        ModuleBase.__init__(self,module_options)

        self.min_jobs = int(self.configService.get("setup","min_jobs"))
        self.warning_limit = float(self.configService.get("setup","warning_limit"))
        self.critical_limit = float(self.configService.get("setup","critical_limit"))

        self.groups = self.configService.get("setup", "groups").split(',')
	self.rating_groups = self.configService.get("setup", "rating_groups").split(',')

	if len(self.groups) == 0 or self.groups[0] == '':
		self.groups = None

        self.db_keys["groups_database"] = StringCol()
        self.db_values["groups_database"] = ""
        
        self.dsTags = {}
        sites = self.configService.getSection('Sites')

        for site in sites.keys():
            dsTag = 'xml_source_' + site
            url = sites[site]
            self.dsTags[dsTag] = {}
            self.dsTags[dsTag]['site'] = site
            self.downloadRequest[dsTag] = 'wget|xml||' + url

    def process(self):

        self.configService.addToParameter('setup', 'definition', '<br />Warning limit: ' + str(self.warning_limit))
        self.configService.addToParameter('setup', 'definition', '<br />Critical limit: ' + str(self.critical_limit))
        self.configService.addToParameter('setup', 'definition', '<br />Minimum number of jobs for rating: ' + str(self.min_jobs))

        if self.rating_groups is not None:
	        self.configService.addToParameter('setup', 'definition', '<br />Rated group(s): ' + ', '.join(self.rating_groups))

        self.status = 1.0
        
        # Obtain group summaries
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

        try:
            first_iteration = True
            for tag in self.dsTags.keys():
                    site = self.dsTags[tag]['site']
                    if not first_iteration:
                            self.configService.addToParameter('setup', 'source', '<br/>')
                    first_iteration = False
                            
                    self.configService.addToParameter('setup', 'source', site + ': ' + self.downloadService.getUrlAsLink(self.getDownloadRequest(tag)))

            for tag in self.dsTags.keys():
                site = self.dsTags[tag]['site']
                dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(tag))
                source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)
                root = source_tree.getroot()

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
                                            if subchild.tag == 'jobs' and subchild.text is not None:
                                                    total = int(subchild.text.strip())
                                            if subchild.tag == 'running' and subchild.text is not None:
                                                    running = int(subchild.text.strip())
                                            if subchild.tag == 'pending' and subchild.text is not None:
                                                    pending = int(subchild.text.strip())
                                            if subchild.tag == 'waiting' and subchild.text is not None:
                                                    waiting = int(subchild.text.strip())
                                            if subchild.tag == 'ratio10' and subchild.text is not None:
                                                    ratio10 = int(subchild.text.strip())
                                    
                                    for values in groups_db_value_list:
                                            if values["groupname"] == group and values["parentgroup"] == parent:
                                                    values["total"] += total
                                                    values["pending"] += pending
                                                    values["running"] += running
                                                    values["waiting"] += waiting
                                                    values["ratio10"] += ratio10
                                                    values["status"] = 1.0
                                                    break
                                    else:
                                        groups_db_values = {}
                                        groups_db_values["groupname"] = group
                                        groups_db_values["parentgroup"] = parent
                                        groups_db_values["total"] = total
                                        groups_db_values["running"] = running
                                        groups_db_values["pending"] = pending
                                        groups_db_values["waiting"] = waiting
                                        groups_db_values["ratio10"] = ratio10
                                        groups_db_values["status"] = 1.0
                                        groups_db_value_list.append(groups_db_values)

                                                           
        finally:
            # determine status
            for values in groups_db_value_list:
                running = values["running"]
                ratio10 = values["ratio10"]
                
                status = 1.0
                if running >= self.min_jobs and ratio10 >= running*self.warning_limit:
                    status = 0.5
                if running >= self.min_jobs and ratio10 >= running*self.critical_limit:
                    status = 0.0
                values["status"] = status
                
                if self.rating_groups is None or group in self.rating_groups:
                    if status < self.status:
                        self.status = status

            self.table_fill_many(groups_table, groups_db_value_list)
            self.subtable_clear(groups_table, [], self.holdback_time)

    def output(self):

        old_result_warning_message = []
        old_result_warning_message.append("<p style=\"font-size:large; color: red;\">Input XML was generated more than ' . $data['old_result_warning_limit'] . ' hours in the past</p>")
        old_result_critical_message = []
        old_result_critical_message.append("<p style=\"font-size:large; color: red;\">Input XML was generated more than ' . $data['old_result_critical_limit'] . ' hours in the past</p>")

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
        begin.append(  ' <table style="font: bold 0.7em sans-serif; width:800px; background-color: #ddd; border: 1px #999 solid;">')
        begin.append(  '  <tr>')
        begin.append(  '   <td>Start:</td>')
        begin.append(  '   <td>')
        begin.append("""    <input name="date0" type="text" size="10" style="text-align:center;" value="' . strftime("%Y-%m-%d", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        begin.append("""    <input name="time0" type="text" size="5" style="text-align:center;" value="' . strftime("%H:%M", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        begin.append(  '   </td>')
        begin.append(  '   <td>End:</td>')
        begin.append(  '   <td>')
        begin.append("""    <input name="date1" type="text" size="10" style="text-align:center;" value="' . $date_string . '" />""")
        begin.append("""    <input name="time1" type="text" size="5" style="text-align:center;" value="' . $time_string . '" />""")
        begin.append(  '   </td>')
        begin.append(  '   <td align="right">')
        begin.append(  '    <input type="checkbox" name="renormalize" value="1" style="vertical-align: middle; margin: 0px;" />&nbsp;Show Trend plot')
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

        module_content = """<?php

        if(isset($data['old_result_critical_limit']) && isset($data['old_result_warning_limit']))
        {
                if($data['timestamp'] - $data['result_timestamp'] > $data['old_result_critical_limit']*3600)
                        print('""" + self.PHPArrayToString(old_result_critical_message) + """');
                elseif($data['timestamp'] - $data['result_timestamp'] > $data['old_result_warning_limit']*3600)
                        print('""" + self.PHPArrayToString(old_result_warning_message) + """');
        }

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

        ?>"""

        return self.PHPOutput(module_content)
    
