from ModuleBase import *
from InputService import *
import urllib,json

class atlas_ddm_deletion(ModuleBase):
    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        ModuleBase.__init__(self,module_options)

        self.db_keys["ddm_del"] = StringCol()
        self.db_values["ddm_del"] = ''


    def run(self):
        dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest["jsonfile"])
        if dl_error != "": #download error
            print "json file download error: "+dl_error
            self.status = -1.
        else:
            self.status = 1.0
            print "sourceFile: "+sourceFile
            jsonSource = open(sourceFile).read()
            bouricot_source_list=json.loads(jsonSource)
            res = ""
            for item in bouricot_source_list:
                res += item['pk'] + ';' +\
                    str(item['fields']['datasets_to_delete']) + ';' +\
                    str(item['fields']['waiting']) + ';' +\
                    str(item['fields']['resolved']) + ';' +\
                    str(item['fields']['queued']) + ';' +\
                    str(item['fields']['datasets']) + ';' +\
                    str(item['fields']['files_to_delete']) + ';' +\
                    str(item['fields']['files']) + ';' +\
                    str(item['fields']['gbs_to_delete']) + ';' +\
                    str(item['fields']['gbs']) + ';' +\
                    str(item['fields']['errors']) + ';'
            self.db_values["ddm_del"] = res[:-1] # remove last ';'
            print res


    def output(self):

        module_content = """
                            <?php
                                 print ('<table class="TableData">
                                                 <tr class="TableHeader">
                                                     <th>Space Tokens</th> 
                                                     <th colspan="5">Datasets</th>
                                                     <th colspan="2">Files</th>
                                                     <th colspan="2">GBs</th>
                                                     <th>Error</th>
                                                 </tr>
                                                 <tr>
                                                     <td></td>
                                                     <td>To delete</td>
                                                     <td>Waiting</td>
                                                     <td>Resolved</td>
                                                     <td>Queued</td>
                                                     <td>Deleted</td>
                                                     <td>To delete</td>
                                                     <td>Deleted</td>
                                                     <td>To delete</td>
                                                     <td>Deleted</td>
                                                     <td></td>
                                                 </tr>');
                                  $arr = explode(";",$data["ddm_del"]);
                                  $num_spacetokens = intval(sizeof($arr) / 11);
                                  for ($s = 0; $s < $num_spacetokens; $s++) {
                                     if ($arr[($s*11+10)]==0) print('<tr class="ok">');
                                     else print('<tr class="warning">');
                                     for ($i = 0; $i < 11; $i++) {                                          
                                         print('<td>' . $arr[($s*11+$i)] . '</td>');
                                     }
                                     print ('</tr>');
                                  }
                                  print ('</table>');
                           ?>

"""
        return self.PHPOutput(module_content)
