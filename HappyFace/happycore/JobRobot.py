from ModuleBase import *
from HTMLParsing import *
import time

class JobRobot(ModuleBase):

    def __init__(self,module_options):
        ModuleBase.__init__(self,module_options)

        self.db_keys["submitted"] = IntCol()
        self.db_keys["aborted"] = IntCol()
        self.db_keys["errors"] = IntCol()
        self.db_keys["success"] = IntCol()
        self.db_keys["efficiency"] = IntCol()

        self.db_values["submitted"] = 0
        self.db_values["aborted"] = 0
        self.db_values["errors"] = 0
        self.db_values["success"] = 0
        self.db_values["efficiency"] = 0

        self.status = 1.0

        self.base_url  = self.configService.get('setup','base_url')
        self.site  = self.configService.get('setup','site')
    
        time_string = str(time.localtime()[0]%100) + str(time.localtime()[1]).zfill(2) + str(time.localtime()[2]).zfill(2)
        source_url = self.base_url + 'summary_'+ time_string + '.html'
        self.dsTag = 'JobRobot_source'
        self.downloadRequest[self.dsTag] = 'wget|'+ 'html' + '||' + source_url
        self.configService.addToParameter('setup', 'source', self.site + ': ' + '<a href="'+source_url+'">'+source_url+'</a>')


    def process(self):

        success,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))

        source_tree, error_message = HTMLParsing().parse_htmlfile_lxml(sourceFile)
        root = source_tree.getroot()

        # works but ugly
        for root_el in root:
            if root_el.tag == 'body':
                for body_el in root_el:
                    for center_el in body_el:
                        if center_el.tag == 'center':
                            for table_el in center_el:
                                if table_el.tag == 'table':
                                    for td_el in table_el:
                                        if td_el.tag == 'tr':
                                            if self.site in td_el[0].text_content():
                                                submitted = int(td_el[1].text_content().strip(' '))
                                                aborted = int(td_el[2].text_content().strip(' '))
                                                errors = int(td_el[3].text_content().strip(' '))
                                                success = int(td_el[4].text_content().strip(' '))
                                                efficiency = int(td_el[5].text_content().strip('% '))

        self.db_values["submitted"] = submitted
        self.db_values["aborted"] = aborted
        self.db_values["errors"] = errors
        self.db_values["success"] = success
        self.db_values["efficiency"] = efficiency

        if efficiency <= 90:
            self.status = 0



    def output(self):

        mc_begin = []
        mc_begin.append('<table class="TableData">')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Submitted</td>')
        mc_begin.append("""  <td>' . $data["submitted"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Aborted</td>')
        mc_begin.append("""  <td>' . $data["aborted"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Errors</td>')
        mc_begin.append("""  <td>' . $data["errors"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Success</td>')
        mc_begin.append("""  <td>' . $data["success"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Efficiency</td>')
        mc_begin.append("""  <td>' . $data["efficiency"] . '</td>""")
        mc_begin.append(  ' </tr>')

        module_content = """<?php

        print('""" + self.PHPArrayToString(mc_begin) + """');

        ?>"""
        return self.PHPOutput(module_content)
