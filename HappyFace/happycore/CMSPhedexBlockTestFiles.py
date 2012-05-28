
from ModuleBase import *
from XMLParsing import *

class CMSPhedexBlockTestFiles(ModuleBase):
    def __init__(self,module_options):
        ModuleBase.__init__(self,module_options)
        
        self.dsTag = 'blocktest_xml'
        self.db_keys["failed_blocks_raw"] = IntCol()
        self.db_keys["failed_blocks"] = IntCol()
        self.db_keys["failed_total_files_raw"] = IntCol()
        self.db_keys["failed_total_files"] = IntCol()
        self.db_keys["request_timestamp"] = IntCol()
        self.db_keys["filename_blocktest"] = StringCol()
        self.db_keys["details_database"] = StringCol()
        self.db_keys["input_xml_age_limit"] = IntCol()

        self.details_database = self.__module__ + "_details_database"
        self.status = 1.0
        self.reject_strs=[]
        self.exception_strs=[]


    def process(self):
    
        self.db_values['details_database'] = self.details_database
        self.db_values["failed_blocks_raw"] = 0
        self.db_values["failed_blocks"] = 0
        self.db_values["failed_total_files_raw"] = 0
        self.db_values["failed_total_files"] = 0
        self.db_values["request_timestamp"] = 0
        self.db_values["filename_blocktest"] = ''
        self.db_values["input_xml_age_limit"] = int(self.configService.get("setup", "input_xml_age_limit"))


        try:
            for reject_str in self.configService.get('filter','reject').split(','):
                if len(reject_str.strip('"').strip()) > 0:
                    self.reject_strs.append(reject_str.strip('"').strip());
        except:
            pass

        try:
            for exception_str in self.configService.getSection('filter').get('exception').split(','):
                if len(exception_str.strip('"').strip()) > 0:
                    self.exception_strs.append(exception_str.strip('"'));
        except:
            pass


        
        dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])        
        if dl_error != "":
            self.error_message+= dl_error
            return

        self.configService.addToParameter('setup','source',self.downloadService.getUrlAsLink(self.downloadRequest[self.dsTag]))

        source_tree,xml_error = XMLParsing().parse_xmlfile_minidom(sourceFile)
        self.error_message += xml_error
        
        details_keys = {}
        details_keys['block'] = StringCol()
        details_keys['isfile'] = IntCol()
        details_keys['fails'] = IntCol()
        details_keys['fails_raw'] = IntCol()
        details_keys['filtered'] = IntCol()
        details_keys['time_reported'] = IntCol()
        details_keys['request_timestamp'] = IntCol()
        details_table = self.table_init(self.details_database, details_keys)


        
        for phedex in source_tree.getElementsByTagName('phedex'):
            self.db_values["request_timestamp"] = int(float(phedex.getAttribute('request_timestamp')))
            
        class main_table(SQLObject):
            class sqlmeta:
                table = self.database_table
                registry = self.__module__
            request_timestamp = IntCol()
            failed_blocks_raw = IntCol()
            failed_blocks = IntCol()
            failed_total_files_raw = IntCol()
            failed_total_files = IntCol()
            filename_blocktest = StringCol()

        # see if the XML file has newer testresults than the one in the database
        try:
            previous_result = main_table.select(orderBy=DESC(main_table.q.request_timestamp))[0]
            prev_request_timestamp = previous_result.request_timestamp
        except Exception:
            previous_result = None
            prev_request_timestamp = 0
            
        if prev_request_timestamp < self.db_values["request_timestamp"]:
        #if 0 < self.db_values["request_timestamp"]:
            # keep the raw XML file in the archive and store path in DB
            try:
                filename = self.__module__+'.xml'
                dest_dir = os.path.join(self.archive_dir, filename)
                
                self.downloadService.copyFile(self.downloadRequest[self.dsTag], dest_dir)
            except Exception, ex:
                self.error_message += str(ex).strip() + "\n"
                filename = ''
            
            self.db_values["filename_blocktest"] = filename
            self.archive_columns.append("filename_blocktest")
            
            details_value_list = []

            num_blocks_raw =0 
            num_files_raw = 0
            num_blocks = 0
            num_files = 0

            for block in source_tree.getElementsByTagName('block'):
                block_name = block.getAttribute('name')
                block_time_reported = 0
                akt_files_raw = 0
                akt_files = 0
                num_blocks_raw += 1
                for test in block.getElementsByTagName('test'):
                    block_time_reported = int(float(test.getAttribute('time_reported')))
                    for sub_file in test.getElementsByTagName('file'):
                        akt_files_raw +=1
                        num_files_raw +=1
                        file_name = sub_file.getAttribute('name')
                        filtered_out=0
                        for check_reject in self.reject_strs:
                            if check_reject.strip() in file_name: 
                                filtered_out=1
                        for check_exception in self.exception_strs:
                            if check_exception.strip() in file_name: 
                                filtered_out=0
                        num_files +=1-filtered_out
                        akt_files +=1-filtered_out
                        details_value_list.append({'block': file_name,
                                                   'isfile':  int(1),
                                                   'time_reported':  block_time_reported,
                                                   'fails': num_blocks,
                                                   'fails_raw': num_blocks_raw,
                                                   'filtered': filtered_out,
                                                   'request_timestamp': self.db_values["request_timestamp"]
                                                   })
                block_filtered_out=1
                if akt_files>0:
                    num_blocks += 1
                    block_filtered_out=0
                details_value_list.append({'block': block_name,
                                           'isfile': int(0),
                                           'time_reported': block_time_reported,
                                           'fails': akt_files,
                                           'fails_raw': akt_files_raw,
                                           'filtered':  block_filtered_out,
                                           'request_timestamp': self.db_values["request_timestamp"]
                                        })
                


                    
            self.db_values["failed_blocks_raw"] = num_blocks_raw
            self.db_values["failed_blocks"] = num_blocks
            self.db_values["failed_total_files_raw"] = num_files_raw
            self.db_values["failed_total_files"] = num_files
            
            #print block_details_value_list
            self.table_fill_many(details_table, details_value_list)
            self.subtable_clear(details_table, [], self.holdback_time)
            

        else:
            # we have old data, just copy them all over
            self.db_values['details_database'] = self.details_database
            self.db_values["failed_blocks_raw"] = previous_result.failed_blocks_raw
            self.db_values["failed_blocks"] = previous_result.failed_blocks
            self.db_values["failed_total_files_raw"] = previous_result.failed_total_files_raw
            self.db_values["failed_total_files"] = previous_result.failed_total_files
            self.db_values["request_timestamp"] = previous_result.request_timestamp
            # we do not keep archive file, leave filename empty
            self.db_values["filename_blocktest"] = ''
        
        if self.db_values["failed_total_files"] > 0 or self.db_values["failed_blocks"] > 0:
            self.status = 0.0
    



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

        js.append('</script>')

        
        mc_overview = []
        mc_overview.append('<table class="TableData">')
        mc_overview.append('<tbody>')
        mc_overview.append(' <tr class="TableHeader">')
        mc_overview.append('  <th>Type</th>')
        mc_overview.append('  <th>Request Time</th>')
        mc_overview.append('  <th>Num. Failed Blocks </th>')
        mc_overview.append('  <th>Num. Failed Files </th>')
        mc_overview.append(' </tr>')
        
        mc_overview.append(" <tr>")
        mc_overview.append('  <th>"filtered"</th>')
        mc_overview.append("  <td>'.strftime('%Y-%m-%d %H:%M', $data['request_timestamp']).'</td>")
        mc_overview.append("""  <td>'.$data['failed_blocks'].' <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_fb\\\');" /> </td>""")
        mc_overview.append("""  <td>'.$data['failed_total_files'].' <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_ff\\\');" /> </td>""")
        mc_overview.append(' </tr>')

        mc_overview.append(" <tr>")
        mc_overview.append('  <th>"not filtered"</th>')
        mc_overview.append("  <td>'.strftime('%Y-%m-%d %H:%M', $data['request_timestamp']).'</td>")
        mc_overview.append("""  <td>'.($data['failed_blocks_raw']-$data['failed_blocks']).'  <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_nb\\\');" /> </td>""")
        mc_overview.append("""  <td>'.($data['failed_total_files_raw']-$data['failed_total_files']).'  <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_nf\\\');" />  </td>""")
        mc_overview.append(' </tr>')


        mc_overview.append(" <tr>")
        mc_overview.append('  <th>"witout filter"</th>')
        mc_overview.append("  <td>'.strftime('%Y-%m-%d %H:%M', $data['request_timestamp']).'</td>")
        mc_overview.append("""  <td>'.$data['failed_blocks_raw'].'  <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_rb\\\');" /> </td>""")
        mc_overview.append("""  <td>'.$data['failed_total_files_raw'].'  <input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed_rf\\\');" />  </td>""")
        mc_overview.append(' </tr>')
        
        mc_overview.append('</tbody>')
        mc_overview.append('</table>')
        mc_overview.append('<br />')
        
        mc_detailed_fb_begin = []
        mc_detailed_fb_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_fb" style="display:none;">')
        mc_detailed_fb_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_fb_begin.append('<tbodyfb>')
        mc_detailed_fb_begin.append('  <tr class="TableHeader">')
        mc_detailed_fb_begin.append('   <th>Block</th>')
        mc_detailed_fb_begin.append('   <th>Failed Files</th>')
        mc_detailed_fb_begin.append('   <th>Time Reported</th>')
        mc_detailed_fb_begin.append('  </tr>')



        mc_detailed_fb_row = []
        mc_detailed_fb_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_fb_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_fb_row.append("  <td>'.$detail['fails'].'</td>")
        mc_detailed_fb_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_fb_row.append(' </tr>')
        
        
        mc_detailed_fb_end = []
        mc_detailed_fb_end.append('</tbodyfb>')
        mc_detailed_fb_end.append('</table>')
        mc_detailed_fb_end.append('</div>')

        mc_detailed_ff_begin=[]
        mc_detailed_ff_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_ff" style="display:none;">')
        mc_detailed_ff_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_ff_begin.append('  <tr class="TableHeader">')
        mc_detailed_ff_begin.append('<tbody_d>')
        mc_detailed_ff_begin.append('   <th>File</th>')
        mc_detailed_ff_begin.append('   <th>Block Ref</th>')
        mc_detailed_ff_begin.append('   <th>Time Reported</th>')
        mc_detailed_ff_begin.append('  </tr>')



        mc_detailed_ff_row = []
        mc_detailed_ff_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_ff_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_ff_row.append("  <td>'.$detail['fails'].'</td>")
        mc_detailed_ff_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_ff_row.append(' </tr>')
        mc_detailed_ff_row.append('</tbody_d>')
        
        mc_detailed_ff_end = []
        mc_detailed_ff_end.append('</table>')
        mc_detailed_ff_end.append('</div>')



        mc_detailed_nb_begin = []
      #  mc_detailed_begin.append("""<input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed\\\');" />""")
        mc_detailed_nb_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_nb" style="display:none;">')
        mc_detailed_nb_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_nb_begin.append('<tbodyfb>')
        mc_detailed_nb_begin.append('  <tr class="TableHeader">')
        mc_detailed_nb_begin.append('   <th>Block</th>')
        mc_detailed_nb_begin.append('   <th>Failed Files</th>')
        mc_detailed_nb_begin.append('   <th>Time Reported</th>')
        mc_detailed_nb_begin.append('  </tr>')



        mc_detailed_nb_row = []
        mc_detailed_nb_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_nb_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_nb_row.append("  <td>'.($detail['fails_raw']-$detail['fails']).'</td>")
        mc_detailed_nb_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_nb_row.append(' </tr>')
        
        
        mc_detailed_nb_end = []
        mc_detailed_nb_end.append('</tbodyfb>')
        mc_detailed_nb_end.append('</table>')
        mc_detailed_nb_end.append('</div>')

        mc_detailed_nf_begin=[]
        mc_detailed_nf_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_nf" style="display:none;">')
        mc_detailed_nf_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_nf_begin.append('  <tr class="TableHeader">')
        mc_detailed_nf_begin.append('<tbody_d>')
        mc_detailed_nf_begin.append('   <th>File</th>')
        mc_detailed_nf_begin.append('   <th>Block Ref</th>')
        mc_detailed_nf_begin.append('   <th>Time Reported</th>')
        mc_detailed_nf_begin.append('  </tr>')



        mc_detailed_nf_row = []
        mc_detailed_nf_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_nf_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_nf_row.append("  <td>'.($detail['fails_raw']-$detail['fails']).'</td>")
        mc_detailed_nf_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_nf_row.append(' </tr>')
        mc_detailed_nf_row.append('</tbody_d>')
        
        mc_detailed_nf_end = []
        mc_detailed_nf_end.append('</table>')
        mc_detailed_nf_end.append('</div>')

        mc_detailed_rb_begin = []
      #  mc_detailed_begin.append("""<input type="button" value="show/hide details" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_detailed\\\');" />""")
        mc_detailed_rb_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_rb" style="display:none;">')
        mc_detailed_rb_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_rb_begin.append('<tbodyfb>')
        mc_detailed_rb_begin.append('  <tr class="TableHeader">')
        mc_detailed_rb_begin.append('   <th>Block</th>')
        mc_detailed_rb_begin.append('   <th>Failed Files</th>')
        mc_detailed_rb_begin.append('   <th>Time Reported</th>')
        mc_detailed_rb_begin.append('  </tr>')



        mc_detailed_rb_row = []
        mc_detailed_rb_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_rb_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_rb_row.append("  <td>'.$detail['fails_raw'].'</td>")
        mc_detailed_rb_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_rb_row.append(' </tr>')
        
        
        mc_detailed_rb_end = []
        mc_detailed_rb_end.append('</tbodyfb>')
        mc_detailed_rb_end.append('</table>')
        mc_detailed_rb_end.append('</div>')

        mc_detailed_rf_begin=[]
        mc_detailed_rf_begin.append('<div class="DetailedInfo" id="' + self.__module__+ '_detailed_rf" style="display:none;">')
        mc_detailed_rf_begin.append(' <table class="TableData" id="' + self.__module__ + '_details_table">')
        mc_detailed_rf_begin.append('  <tr class="TableHeader">')
        mc_detailed_rf_begin.append('<tbody_d>')
        mc_detailed_rf_begin.append('   <th>File</th>')
        mc_detailed_rf_begin.append('   <th>Block Ref</th>')
        mc_detailed_rf_begin.append('   <th>Time Reported</th>')
        mc_detailed_rf_begin.append('  </tr>')



        mc_detailed_rf_row = []
        mc_detailed_rf_row.append(" <tr style=\\'background-color:'.$color.'\\'>")
        mc_detailed_rf_row.append("  <td>'.$detail['block'].'</td>")
        mc_detailed_rf_row.append("  <td>'.$detail['fails_raw'].'</td>")
        mc_detailed_rf_row.append("  <td>'.strftime('%Y-%m-%d %H:%M', $detail['time_reported']).'</td>")
        mc_detailed_rf_row.append(' </tr>')
        mc_detailed_rf_row.append('</tbody_d>')
        
        mc_detailed_rf_end = []
        mc_detailed_rf_end.append('</table>')
        mc_detailed_rf_end.append('</div>')






  

        module_content = """<?php
        
        print('""" + self.PHPArrayToString(js) + """');



        
        $prev_timestamp_query = "SELECT timestamp FROM " . $data["details_database"] . " WHERE request_timestamp = " . $data["request_timestamp"];
        $timestamp = 0;
        foreach ($dbh->query($prev_timestamp_query) as $detail)
        {
            $timestamp = $detail['timestamp'];
        }
        $tm = localtime($timestamp);
        $year = $tm[5] + 1900; // PHP gives year since 1900
        $month = sprintf('%02d', $tm[4] + 1); // PHP uses 0-11, Python uses 1-12
        $day = sprintf('%02d', $tm[3]);
        $archive_dir = "archive/$year/$month/$day/" . $timestamp;
        
        if($data["request_timestamp"]+($data['input_xml_age_limit']*24*60*60) < $data["timestamp"])
        {
            print("<p style=\\\"font-size:large; color: red;\\\">Input XML was generated more than ".$data['input_xml_age_limit']." days in the past</p>");
        }
        print('""" + self.PHPArrayToString(mc_overview) + """');

        $details_sqlquery = "SELECT block, isfile, fails, fails_raw, filtered, time_reported FROM " . $data["details_database"] . " WHERE request_timestamp = " . $data["request_timestamp"];
        $groups = array();
        print('""" + self.PHPArrayToString(mc_detailed_fb_begin) + """');
        $color_idx = 0;
        $color = '';
        foreach ($dbh->query($details_sqlquery) as $detail)
        {
         if($detail['filtered'] == 0){
         if($detail['isfile'] == 0){
            print('""" + self.PHPArrayToString(mc_detailed_fb_row) + """');
}}}
        print('""" + self.PHPArrayToString(mc_detailed_fb_end) + """');

        print('""" + self.PHPArrayToString(mc_detailed_ff_begin) + """');
        foreach ($dbh->query($details_sqlquery) as $detail)
        {
         if($detail['filtered'] == 0){
         if($detail['isfile'] == 1)
         {
            print('""" + self.PHPArrayToString(mc_detailed_ff_row) + """');
}}}
        print('""" + self.PHPArrayToString(mc_detailed_ff_end) + """');



        print('""" + self.PHPArrayToString(mc_detailed_nb_begin) + """');
        foreach ($dbh->query($details_sqlquery) as $detail)
        {

         if($detail['filtered'] == 1){
         if($detail['isfile'] == 0){
            print('""" + self.PHPArrayToString(mc_detailed_nb_row) + """');
}}}
        print('""" + self.PHPArrayToString(mc_detailed_nb_end) + """');

        print('""" + self.PHPArrayToString(mc_detailed_nf_begin) + """');
        foreach ($dbh->query($details_sqlquery) as $detail)
        {
         if($detail['filtered'] == 1){
         if($detail['isfile'] == 1)
         {
            print('""" + self.PHPArrayToString(mc_detailed_nf_row) + """');
}}}
        print('""" + self.PHPArrayToString(mc_detailed_nf_end) + """');




        print('""" + self.PHPArrayToString(mc_detailed_rb_begin) + """');
        foreach ($dbh->query($details_sqlquery) as $detail)
        {
         if($detail['isfile'] == 0){
            print('""" + self.PHPArrayToString(mc_detailed_rb_row) + """');
}}
        print('""" + self.PHPArrayToString(mc_detailed_rb_end) + """');

        print('""" + self.PHPArrayToString(mc_detailed_rf_begin) + """');
        foreach ($dbh->query($details_sqlquery) as $detail)
        {
         if($detail['isfile'] == 1)
         {
            print('""" + self.PHPArrayToString(mc_detailed_rf_row) + """');
}}
        print('""" + self.PHPArrayToString(mc_detailed_rf_end) + """');







        ?>"""


        return self.PHPOutput(module_content)
