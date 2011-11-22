
from ModuleBase import *
from XMLParsing import *
import re

class T1Prodmon(ModuleBase):
    def __init__(self,module_options):
        ModuleBase.__init__(self,module_options)
        
        self.site_list = dict(
            (site.strip(), {})
            for site in self.configService.get("setup", "sites").split(',')
        )
        
        for name, info in self.site_list.iteritems():
            info['name'] = self.configService.get("setup", name+"_name")
            info['source'] = self.configService.get("downloadservice", name+"_source_xml")
            info['t1prod'] = self.configService.get("setup", name+"_t1production")
            info['prod'] = self.configService.get("setup", name+"_production")
            info['other'] = self.configService.get("setup", name+"_other")
        
        self.db_keys["details_database"] = StringCol()
        self.db_keys["site_list"] = StringCol()
        
        self.status = 1.0

        self.details_database = self.__module__ + "_details_database"
    
    def process(self):
        self.db_values["details_database"] = self.details_database
        self.db_values["site_list"] = ','.join(self.site_list.iterkeys())
        
        details_keys = {}
        details_keys['site'] = StringCol()
        details_keys['t1prod_total'] = IntCol()
        details_keys['t1prod_running'] = IntCol()
        details_keys['t1prod_bad'] = IntCol()
        details_keys['prod_total'] = IntCol()
        details_keys['prod_running'] = IntCol()
        details_keys['prod_bad'] = IntCol()
        details_keys['other_total'] = IntCol()
        details_keys['other_running'] = IntCol()
        details_keys['other_bad'] = IntCol()
        details_table = self.table_init(self.details_database, details_keys)
        
        details_value_list = []
        for name, info in self.site_list.iteritems():
            try:
                dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[name+"_source_xml"])
                if dl_error != "":
                    raise Exception(dl_error)
                source_tree,xml_error = XMLParsing().parse_xmlfile_minidom(sourceFile)
                self.error_message += xml_error
                regexT1Prod = re.compile(info["t1prod"])
                regexProd = re.compile(info["prod"])
                regexOther = re.compile(info["other"])
                t1prodTotal = 0
                t1prodRunning = 0
                t1prodBad = 0
                prodTotal = 0
                prodRunning = 0
                prodBad = 0
                otherTotal = 0
                otherRunning = 0
                otherBad = 0
                for summary in source_tree.getElementsByTagName('summary'):
                    group = summary.getAttribute('group')
                    if re.match(regexT1Prod, group):
                        t1prodTotal += int(summary.getElementsByTagName('jobs')[0].firstChild.data)
                        t1prodRunning += int(summary.getElementsByTagName('running')[0].firstChild.data)
                        t1prodBad += int(summary.getElementsByTagName('ratio10')[0].firstChild.data)
                    elif re.match(regexProd, group):
                        prodTotal += int(summary.getElementsByTagName('jobs')[0].firstChild.data)
                        prodRunning += int(summary.getElementsByTagName('running')[0].firstChild.data)
                        prodBad += int(summary.getElementsByTagName('ratio10')[0].firstChild.data)
                    elif re.match(regexOther, group):
                        otherTotal += int(summary.getElementsByTagName('jobs')[0].firstChild.data)
                        otherRunning += int(summary.getElementsByTagName('running')[0].firstChild.data)
                        otherBad += int(summary.getElementsByTagName('ratio10')[0].firstChild.data)
                details_value_list.append({
                    'site': info['name'],
                    't1prod_total': t1prodTotal,
                    't1prod_running': t1prodRunning,
                    't1prod_bad': t1prodBad,
                    'prod_total': prodTotal,
                    'prod_running': prodRunning,
                    'prod_bad': prodBad,
                    'other_total': otherTotal,
                    'other_running': otherRunning,
                    'other_bad': otherBad,
                })
            except Exception, e:
                self.error_message += "%s not included because of Exception: %s" % (info["name"], str(e))
        self.table_fill_many(details_table, details_value_list)
        self.subtable_clear(details_table, [], self.holdback_time)
    
    def output(self):
        js = []
        js.append('<script type="text/javascript">')
        js.append('function ' + self.__module__ + '_plot_button(pool, job)')
        js.append('{')
        js.append('  document.getElementById("' + self.__module__ + '_constraint").value = "job=" + job + ";pool=" + pool;')
        js.append('  document.getElementById("' + self.__module__ + '_extra_title").value = "Pool: " + pool + ",  Job: " + job;')
        js.append('}')
        js.append('function ' + self.__module__ + '_plot_summary_button(job)')
        js.append('{')
        js.append('  document.getElementById("' + self.__module__ + '_sum_constraint").value = "job=" + job')
        js.append('  document.getElementById("' + self.__module__ + '_sum_extra_title").value = "Job: " + job;')
        js.append('}')
       
        js.append('''
        // hide all pools from the table where the given job is not queueing
        function '''+self.__module__ + '''_hide_pools_from_table(show_only_job)
        {
            var table = document.getElementById("'''+self.__module__ + '''_details_table").getElementsByTagName("tbody")[0];
            var rows = table.rows;
            var tag = "tag"+show_only_job;
            document.getElementById("''' + self.__module__+ '''_detailed").setAttribute("style", "");
            
            for(var i=0; rows[i]; i++)
            {
                if(rows[i].getAttribute("class").indexOf("TableHeader") != -1)
                    continue;
                if(show_only_job == "")
                    rows[i].setAttribute("style", "");
                else
                {
                    if(rows[i].getAttribute("class").indexOf(tag) == -1)
                        rows[i].setAttribute("style", "display:none");
                    else
                        rows[i].setAttribute("style", "");
                }
            }
        }
        ''')
        js.append('</script>')
        
        mc_table_begin = []
        mc_table_begin.append('<form method="get" action="plot_generator.php" onsubmit="javascript:submitFormToWindow(this);">')
        mc_table_begin.append(  "<h4>'.$title.'</h4>")
        mc_table_begin.append(  '<table style="font: bold 0.7em sans-serif; width:800px; background-color: #ddd; border: 1px #999 solid;">')
        mc_table_begin.append(  ' <tr>')
        mc_table_begin.append(  '  <td>Start:</td>')
        mc_table_begin.append(  '  <td>')
        mc_table_begin.append("""   <input name="date0" type="text" size="10" style="text-align:center;" value="' . strftime("%Y-%m-%d", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        mc_table_begin.append("""   <input name="time0" type="text" size="5" style="text-align:center;" value="' . strftime("%H:%M", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        mc_table_begin.append(  '  </td>')
        mc_table_begin.append(  '  <td>End:</td>')
        mc_table_begin.append(  '  <td>')
        mc_table_begin.append("""   <input name="date1" type="text" size="10" style="text-align:center;" value="' . $date_string . '" />""")
        mc_table_begin.append("""   <input name="time1" type="text" size="5" style="text-align:center;" value="' . $time_string . '" />""")
        mc_table_begin.append(  '  </td>')
        mc_table_begin.append(  '  <td align="right">')
        mc_table_begin.append(  '   <input type="checkbox" name="renormalize" value="1" style="vertical-align: middle; margin: 0px;" />&nbsp;Show Trend plot')
        mc_table_begin.append(  '   <input type="hidden" name="module" value="'+ self.__module__ + '" />')
        mc_table_begin.append(  '   <input type="hidden" name="subtable" value="" />')
        mc_table_begin.append(  '   <input type="hidden" name="variables" value="active,max,queued" />')
        mc_table_begin.append(  '   <input type="hidden" name="squash" value="1" />')
        mc_table_begin.append(  '   <input type="hidden" name="legend" value="right" />')
        mc_table_begin.append(  '   <input type="hidden" id="'+self.__module__ + '_sum_constraint' + '" name="constraint" value="" />')
        mc_table_begin.append(  '   <input type="hidden" id="'+self.__module__ + '_sum_extra_title' + '" name="extra_title" value="" />')
        mc_table_begin.append(  '  </td>')
        mc_table_begin.append(  ' </tr>')
        mc_table_begin.append(  '</table>')
        mc_table_begin.append('<table class="TableData">')
        mc_table_begin.append('<tbody>')
        
        #mc_table_head.append(' <tr class="TableHeader">')
        #mc_table_head.append('  <th>Group</th>')
        #mc_table_head.append('  <th>Total Jobs</th>')
        #mc_table_head.append('  <th>Running Jobs</th>')
        #mc_table_head.append('  <th>Jobs with wallratio < 10%</th>')
        #mc_table_head.append(' </tr>')
        
        #mc_table_row.append(" <tr>")
        #mc_table_row.append("  <td><strong>T1 Production</strong></td>")
        #mc_table_row.append("  <td>'.$overview['t1prod_total'].'</td>")
        #mc_table_row.append("  <td>'.$overview['t1prod_running'].'</td>")
        #mc_table_row.append("  <td>'.$overview['t1prod_bad'].'</td>")
        #mc_table_row.append(' </tr>')
        
        mc_table_end = []
        mc_table_end.append('</tbody>')
        mc_table_end.append('</table>')
        mc_table_end.append('</form>')
        mc_table_end.append('<br />')
        
        mc_detailed_begin = []
        mc_detailed_begin.append("""<input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed\\\');" />""")
        mc_detailed_begin.append('<form method="get" action="plot_generator.php" onsubmit="javascript:submitFormToWindow(this);">')
        mc_detailed_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed" style="display:none;">')
        mc_detailed_begin.append(  ' <table style="font: bold 0.7em sans-serif; width:800px; background-color: #ddd; border: 1px #999 solid;">')
        mc_detailed_begin.append(  '  <tr>')
        mc_detailed_begin.append(  '   <td>Start:</td>')
        mc_detailed_begin.append(  '   <td>')
        mc_detailed_begin.append("""    <input name="date0" type="text" size="10" style="text-align:center;" value="' . strftime("%Y-%m-%d", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        mc_detailed_begin.append("""    <input name="time0" type="text" size="5" style="text-align:center;" value="' . strftime("%H:%M", strtotime("$date_string $time_string") - 48*60*60) . '" />""")
        mc_detailed_begin.append(  '   </td>')
        mc_detailed_begin.append(  '   <td>End:</td>')
        mc_detailed_begin.append(  '   <td>')
        mc_detailed_begin.append("""    <input name="date1" type="text" size="10" style="text-align:center;" value="' . $date_string . '" />""")
        mc_detailed_begin.append("""    <input name="time1" type="text" size="5" style="text-align:center;" value="' . $time_string . '" />""")
        mc_detailed_begin.append(  '   </td>')
        mc_detailed_begin.append(  '   <td align="right">')
        mc_detailed_begin.append(  '    <input type="checkbox" name="renormalize" value="1" style="vertical-align: middle; margin: 0px;" />&nbsp;Show Trend plot')
        mc_detailed_begin.append(  '    <input type="hidden" name="module" value="'+ self.__module__ + '" />')
        mc_detailed_begin.append(  '    <input type="hidden" name="subtable" value="" />')
        mc_detailed_begin.append(  '    <input type="hidden" name="variables" value="active,max,queued" />')
        mc_detailed_begin.append(  '    <input type="hidden" name="squash" value="1" />')
        mc_detailed_begin.append(  '    <input type="hidden" name="legend" value="right" />')
        mc_detailed_begin.append(  '    <input type="hidden" id="'+self.__module__ + '_constraint' + '" name="constraint" value="" />')
        mc_detailed_begin.append(  '    <input type="hidden" id="'+self.__module__ + '_extra_title' + '" name="extra_title" value="" />')
        mc_detailed_begin.append(  '   </td>')
        mc_detailed_begin.append(  '  </tr>')
        mc_detailed_begin.append(  ' </table>')
        mc_detailed_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_begin.append('  <tr class="TableHeader">')
        mc_detailed_begin.append('   <th>Site</th>')
        mc_detailed_begin.append('   <th>Group</th>')
        mc_detailed_begin.append('   <th>Total Jobs</th>')
        mc_detailed_begin.append('   <th>Running Jobs</th>')
        mc_detailed_begin.append('   <th>wallratio &lt; 10%</th>')
        mc_detailed_begin.append('  </tr>')

        mc_detailed_row = []
        mc_detailed_row.append(" <tr>")
        mc_detailed_row.append("  <td rowspan=\"3\"><strong>'.$site['site'].'</strong></td>")
        mc_detailed_row.append("  <td>T1 Production</td>")
        mc_detailed_row.append("  <td>'.$site['t1prod_total'].'</td>")
        mc_detailed_row.append("  <td>'.$site['t1prod_running'].'</td>")
        mc_detailed_row.append("  <td>'.$site['t1prod_bad'].'</td>")
        mc_detailed_row.append(' </tr>')
        
        mc_detailed_row.append(" <tr>")
        mc_detailed_row.append("  <td>Production</td>")
        mc_detailed_row.append("  <td>'.$site['prod_total'].'</td>")
        mc_detailed_row.append("  <td>'.$site['prod_running'].'</td>")
        mc_detailed_row.append("  <td>'.$site['prod_bad'].'</td>")
        mc_detailed_row.append(' </tr>')
        
        mc_detailed_row.append(" <tr>")
        mc_detailed_row.append("  <td>Other</td>")
        mc_detailed_row.append("  <td>'.$site['other_total'].'</td>")
        mc_detailed_row.append("  <td>'.$site['other_running'].'</td>")
        mc_detailed_row.append("  <td>'.$site['other_bad'].'</td>")
        mc_detailed_row.append(' </tr>')
        
        
        mc_detailed_end = []
        mc_detailed_end.append('</table>')
        mc_detailed_end.append('</form>')

        module_content = """<?php
      
        function """+self.__module__+"""_create_row($jobTypeSuffix, $title, $dataset)
        {
            print("<tr><th>$title</th>");
            $sum = 0;
            foreach($dataset as $site)
            {
                $sum += $site[$jobTypeSuffix];
                print("<td>".$site[$jobTypeSuffix]."</td>");
            }
            print("<td>".$sum."</td></tr>");
        }
        
        $job_categories = array("total"=>"All Jobs", "running"=>"Running Jobs", "bad"=>"Jobs with wallratio &lt; 10%");
        foreach($job_categories as $suf=>$title)
        {
            $jobs_query = "SELECT site, t1prod_$suf as t1prod, prod_$suf as prod, other_$suf as other, (t1prod_$suf+prod_$suf+other_$suf) as total FROM ".$data["details_database"]." WHERE timestamp = ".$data["timestamp"]." GROUP BY site ORDER BY site";
            $sth = $dbh->prepare($jobs_query);
            $sth->execute();
            $dataset = $sth->fetchall();
            print('"""+self.PHPArrayToString(mc_table_begin)+"""');
            print("<tr><th>Role</th>");
            foreach($dataset as $site)
                print("<th>".$site['site']."</th>");
            print("<th>Total</th></tr>");
            """+self.__module__+"""_create_row('t1prod', 't1production', $dataset);
            """+self.__module__+"""_create_row('prod', 'production', $dataset);
            """+self.__module__+"""_create_row('other', 'other', $dataset);
            """+self.__module__+"""_create_row('total', 'Total', $dataset);
            print('"""+self.PHPArrayToString(mc_table_end)+"""');
        }

        ?>"""
        return self.PHPOutput(module_content)