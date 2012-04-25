from ModuleBase import *
from sqlobject import *
from DownloadTag import *
from XMLParsing import *
#import GetData
#import xml.sax
#import time
#import bz2
#import os

class CERNdCacheTapeinfo(ModuleBase):

    def __init__(self, module_options):
	ModuleBase.__init__(self, module_options)
	self.db_keys["details_database"] = StringCol()
	self.db_keys["file_timestamp"] = IntCol()
	self.db_keys["used_tape_size"] = FloatCol()
	self.db_keys["total_tape_size"] = FloatCol()
	self.db_keys["used_disk_size"] = FloatCol()
	self.db_keys["total_disk_size"] = FloatCol()

	# Make sure there are valid values for these columns just in case
	# there is an error before we get to set them.
	self.db_values["details_database"] = ''
	self.db_values["file_timestamp"] = 0
	self.db_values["used_tape_size"] = 0.0
	self.db_values["total_tape_size"] = 0.0
	self.db_values["used_disk_size"] = 0.0
	self.db_values["total_disk_size"] = 0.0


	self.warning_limit = int(self.configService.getDefault('setup', 'warning_limit', '-1'))
	self.critical_limit = int(self.configService.getDefault('setup', 'critical_limit', '-1'))
#	self.on_disk_threshold = float(self.configService.getDefault('setup', 'on_disk_threshold', '0.95'))

	self.configService.addToParameter('setup', 'definition', 'Warning level depending on timestamp of last file update:')
	self.configService.addToParameter('setup', 'definition', '<br />Warning: &gt;= ' + str(self.warning_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br />Critical: &gt;= ' + str(self.critical_limit) + ' hours')
#	self.configService.addToParameter('setup', 'definition', '<br />On-disk threshold: ' + str(int(round(self.on_disk_threshold * 100))) + '%')


        self.dsTagut = 'used_tape'
        self.dsTagtt = 'total_tape'
        self.dsTagud = 'used_disk'
        self.dsTagtd = 'total_disk'
   


    def set_db_value(self, db_values, dataset, value):
        if value in dataset:
	    db_values[value] = dataset[value];
	else:
	    db_values[value] = 0

    def set_db_values(self, db_values, dataset):
	self.set_db_value(db_values, dataset, 'used_tape_size')
	self.set_db_value(db_values, dataset, 'total_tape_size')
	self.set_db_value(db_values, dataset, 'used_disk_size')
	self.set_db_value(db_values, dataset, 'total_disk_size')


    def process(self):
        details_database = self.__module__ + "_table_details"
	self.db_values['details_database'] = details_database
#	self.db_values["on_disk_threshold"] = self.on_disk_threshold

	details_db_keys = {}
	details_db_keys['name'] = StringCol()
	details_db_keys['used_tape_size'] = FloatCol()
	details_db_keys['total_tape_size'] = FloatCol()
	details_db_keys['used_disk_size'] = FloatCol()
	details_db_keys['total_disk_size'] = FloatCol()
	self.configService.addToParameter('setup', 'source', self.dsTagut+": "+self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTagut))+"<br />")
	self.configService.addToParameter('setup', 'source', self.dsTagtt+": "+self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTagtt))+"<br />")
	self.configService.addToParameter('setup', 'source', self.dsTagud+": "+self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTagud))+"<br />")
	self.configService.addToParameter('setup', 'source', self.dsTagtd+": "+self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTagtd))+"<br />")

	details_table = self.table_init(details_database, details_db_keys)

	dl_error_ut,sourceFile_ut = self.downloadService.getFile(self.getDownloadRequest(self.dsTagut))
	cur_timestamp = 0
	details_db_values = []
        for line in file(sourceFile_ut):
            if not "T1_DE_KIT" in line:
                continue
            self.db_values["used_tape_size"]=float(line.split()[3])
            cur_timestamp=int(time.mktime(time.strptime(line.split()[0]+" "+line.split()[1], "%Y-%m-%d %H:%M:%S")))
            self.db_values["file_timestamp"] = cur_timestamp

	dl_error_tt,sourceFile_tt = self.downloadService.getFile(self.getDownloadRequest(self.dsTagtt))
        for line in file(sourceFile_tt):
            if not "T1_DE_KIT" in line:
                continue
            self.db_values["total_tape_size"]=float(line.split()[3])
            cur_timestamp=int(time.mktime(time.strptime(line.split()[0]+" "+line.split()[1], "%Y-%m-%d %H:%M:%S")))

	dl_error_ud,sourceFile_ud = self.downloadService.getFile(self.getDownloadRequest(self.dsTagud))
        for line in file(sourceFile_ud):
            if not "T1_DE_KIT" in line:
                continue
            self.db_values["used_disk_size"]=float(line.split()[3])
            cur_timestamp=int(time.mktime(time.strptime(line.split()[0]+" "+line.split()[1], "%Y-%m-%d %H:%M:%S")))


	dl_error_td,sourceFile_td = self.downloadService.getFile(self.getDownloadRequest(self.dsTagtd))
        for line in file(sourceFile_td):
            if not "T1_DE_KIT" in line:
                continue
            self.db_values["total_disk_size"]=float(line.split()[3])
            cur_timestamp=int(time.mktime(time.strptime(line.split()[0]+" "+line.split()[1], "%Y-%m-%d %H:%M:%S")))


	if cur_timestamp == 0 or (self.critical_limit != -1 and time.time() - self.critical_limit*3600 > cur_timestamp):
		self.status = 0.0
	elif self.warning_limit != -1 and time.time() - self.warning_limit*3600 > cur_timestamp:
		self.status = 0.5
	else:
		self.status = 1.0



    def output(self):
        mc_begin = []
        mc_begin.append(  "<p style=\"font-size:large; ' . $gen_color . '\">File dump generated on ' . strftime('%a, %d %b %Y %T %z', $data['file_timestamp']) . '</p>")
        mc_begin.append(  '<table class="TableData">')
        mc_begin.append(  " <tr>")
        mc_begin.append(  '  <td>Used tape in TB</td>')
        mc_begin.append("""  <td>' . $data["used_tape_size"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  '  <td>Total tape in TB</td>')
        mc_begin.append("""  <td>' . $data["total_tape_size"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  '  <td>Used disk in TB</td>')
        mc_begin.append("""  <td>' . $data["used_disk_size"] . '</td>""")
        mc_begin.append(  ' </tr>')
        mc_begin.append(  '  <td>Total disk in TB</td>')
        mc_begin.append("""  <td>' . $data["total_disk_size"] . '</td>""")
        mc_begin.append(  ' </tr>')
        
        mc_begin.append(  '</table>')
        mc_begin.append(  '<br />')



        module_content = """<?php
		$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"] . " ORDER BY speed";
	print('""" + self.PHPArrayToString(mc_begin) + """');
                         ?>"""

	return self.PHPOutput(module_content)
