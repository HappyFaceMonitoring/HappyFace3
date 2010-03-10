##############################################
# Qstat test
# at the moment experimental
# the plot creating part has to be rewritten!!!
##############################################

from ModuleBase import *
from XMLParsing import *

from numpy import array
import numpy as np
import matplotlib
matplotlib.use("cairo.png")
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure


class Qstat(ModuleBase):

    def __init__(self,module_options):

        ModuleBase.__init__(self,module_options)

        self.warning_limit = float(self.configService.get("setup","warning_limit"))
        self.critical_limit = float(self.configService.get("setup","critical_limit"))
        self.min_cmsprd_jobs = float(self.configService.get("setup","min_cmsprd_jobs"))

	self.db_keys["starttime"] = StringCol()
	self.db_keys["endtime"] = StringCol()
	
	self.db_keys["all_total"] = IntCol()
	self.db_keys["all_running"] = IntCol()
	self.db_keys["all_ratio10"] = IntCol()

	self.db_keys["cms_total"] = IntCol()
	self.db_keys["cms_running"] = IntCol()
	self.db_keys["cms_ratio10"] = IntCol()
	
	self.db_keys["cmsprd_total"] = IntCol()
	self.db_keys["cmsprd_running"] = IntCol()
	self.db_keys["cmsprd_ratio10"] = IntCol()

	self.db_keys["eff_plot"] = StringCol()
	self.db_keys["rel_eff_plot"] = StringCol()

	self.db_keys["details_database"] = StringCol()


	self.db_values["starttime"] = ""
	self.db_values["endtime"] = None

	self.db_values["all_total"] = None
	self.db_values["all_running"] = None
	self.db_values["all_ratio10"] = None

	self.db_values["cms_total"] = None
	self.db_values["cms_running"] = None
	self.db_values["cms_ratio10"] = None
	
	self.db_values["cmsprd_total"] = None
	self.db_values["cmsprd_running"] = None
	self.db_values["cmsprd_ratio10"] = None

	self.db_values["eff_plot"] = ""
	self.db_values["rel_eff_plot"] = ""
	
	self.db_values["details_database"] = ""

        self.dsTag = 'qstat_xml_source'

    def run(self):

        if not self.dsTag in self.downloadRequest:
            err = 'Error: Could not find required tag: '+self.dsTag+'\n'
            sys.stdout.write(err)
            self.error_message +=err
            return -1

	self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.downloadRequest[self.dsTag]))
	self.configService.addToParameter('setup', 'definition', '<br />Warning limit: ' + str(self.warning_limit))
	self.configService.addToParameter('setup', 'definition', '<br />Critical limit: ' + str(self.critical_limit))
	self.configService.addToParameter('setup', 'definition', '<br />Minimum number of jobs for rating: ' + str(int(self.min_cmsprd_jobs)))

        dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])
        if dl_error != "":
            self.error_message+= dl_error
            return
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)
        self.error_message += xml_error

        ##############################################################################
        # if xml parsing fails, abort the test; 
	# self.status will be pre-defined -1
        if source_tree == "": return

	root = source_tree.getroot()

	for element in root:
	    if element.tag == "GlobalInfo":
		element_attrib = element.attrib
		self.db_values["starttime"] = element_attrib["qstatStart"]
		self.db_values["endtime"] = element_attrib["qstatEnd"]

	    if element.tag == "jobsummary":
		for child in element:
		    if child.tag == "all":
			child_attrib = child.attrib
			self.db_values["all_total"] = int(child_attrib["total"])
			self.db_values["all_running"] = int(child_attrib["running"])
			self.db_values["all_ratio10"] = int(child_attrib["ratio10"])
		    if child.tag == "cms":
			child_attrib = child.attrib
			self.db_values["cms_total"] = int(child_attrib["total"])
			self.db_values["cms_running"] = int(child_attrib["running"])
			self.db_values["cms_ratio10"] = int(child_attrib["ratio10"])
		    if child.tag == "cmsprd":
			child_attrib = child.attrib
			self.db_values["cmsprd_total"] = int(child_attrib["total"])
			self.db_values["cmsprd_running"] = int(child_attrib["running"])
			self.db_values["cmsprd_ratio10"] = int(child_attrib["ratio10"])

	#############################################################################
	# parse the details and store it in a special database table
	details_database = self.__module__ + "_table_details"
	self.db_values["details_database"] = details_database

	details_db_keys = {}
	details_db_values = {}

	details_db_keys["user"] = StringCol()
	details_db_keys["total"] = IntCol()
	details_db_keys["running"] = IntCol()
	details_db_keys["queue"] = IntCol()
	details_db_keys["waiting"] = IntCol()
	details_db_keys["ratio100"] = IntCol()
	details_db_keys["ratio80"] = IntCol()
	details_db_keys["ratio30"] = IntCol()
	details_db_keys["ratio10"] = IntCol()

	my_subtable_class = self.table_init( details_database, details_db_keys )

	users = {}

	for element in root:
	    if element.tag == "jobDetails":
		for child in element:

		    user = child.attrib["user"]
		    if user not in users:
			users[user] = {}

			users[user]["total"] = 0
			users[user]["running"] = 0
			users[user]["waiting"] = 0
			users[user]["queue"] = 0
			users[user]["ratio100"] = 0
			users[user]["ratio80"] = 0
			users[user]["ratio30"] = 0
			users[user]["ratio10"] = 0

		    users[user]["total"] = users[user]["total"] + 1

		    if child.attrib["job_state"] == "Q": users[user]["queue"] = users[user]["queue"] + 1
		    if child.attrib["job_state"] == "W": users[user]["waiting"] = users[user]["waiting"] + 1
		    if child.attrib["job_state"] == "R":
                        users[user]["running"] = users[user]["running"] + 1
                        try:
                            # sometimes there is no "cpuwallratio" variable for running jobs
                            if int(child.attrib["cpuwallratio"]) > 80: users[user]["ratio100"] = users[user]["ratio100"] + 1
                            if int(child.attrib["cpuwallratio"]) > 30 and int(child.attrib["cpuwallratio"]) <= 80: users[user]["ratio80"] = users[user]["ratio80"] + 1
                            if int(child.attrib["cpuwallratio"]) > 10 and int(child.attrib["cpuwallratio"]) <= 30: users[user]["ratio30"] = users[user]["ratio30"] + 1
                            if int(child.attrib["cpuwallratio"]) <= 10: users[user]["ratio10"] = users[user]["ratio10"] + 1
                        except:
                            pass

	
	for user in users.keys():
	    details_db_values["user"] = user
	    details_db_values["total"] = users[user]["total"]
	    details_db_values["running"] = users[user]["running"]
	    details_db_values["queue"] = users[user]["queue"]
	    details_db_values["waiting"] = users[user]["waiting"]
	    details_db_values["ratio100"] = users[user]["ratio100"]
	    details_db_values["ratio80"] = users[user]["ratio80"]
	    details_db_values["ratio30"] = users[user]["ratio30"]
	    details_db_values["ratio10"] = users[user]["ratio10"]

	    # write details to database
	    self.table_fill( my_subtable_class, details_db_values )
	


        ################################
        # rating algorithm
        self.status = 1.0

        # look only for "cmsprd" jobs
        if "cmsprd" in users:
            if users["cmsprd"]["running"] > 0:
                trigger_ratio = float(users["cmsprd"]["ratio10"]) / float(users["cmsprd"]["running"])
	        if users["cmsprd"]["running"] >= self.min_cmsprd_jobs:
                
                    if trigger_ratio > self.critical_limit: self.status = 0.0
                    elif trigger_ratio <= self.critical_limit and trigger_ratio > self.warning_limit: self.status = 0.5



        


        # create plots for output
	self.createEffPlots(users)

    def createEffPlots(self,users):

	################################################################
	### AT THE MOMENT: QUICK AND DIRTY
	### inspired by: http://matplotlib.sourceforge.net/examples/pylab_examples/bar_stacked.html

	### muss bei gelegenheit ueberschrieben werden
	### saubere initialisierung der "figure", "canvas", ...
	### striktere definitionen der plot-eigenschaften, verschieben der legende
	### verringerung von code durch auslagerung von funktionen

	
	N = len(users)

	### break image creation if there are no user stats about batch jobs
	if N == 0:
	    return

	user_names = []
	total = []
	
	ratio100 = []; ratio80 = []; ratio30 = []; ratio10 = []; queue = []
	rel_ratio100 = []; rel_ratio80 = []; rel_ratio30 = []; rel_ratio10 = []; rel_queue = []

	for user in users:
	    user_names.append(user)
	    total.append(float(users[user]["total"]))
	    ratio100.append(float(users[user]["ratio100"]))
	    ratio80.append(float(users[user]["ratio80"]))
	    ratio30.append(float(users[user]["ratio30"]))
	    ratio10.append(float(users[user]["ratio10"]))
	    queue.append(float(users[user]["queue"]))

	max_jobs = max(total)
        scale_value = max_jobs // 10
        if scale_value == 0: scale_value = 5


	bot_queue = queue
	bot10 = array(queue) + array(ratio10)
	bot30 = array(queue) + array(ratio10) + array(ratio30)
	bot80 =	array(queue) + array(ratio10) + array(ratio30) + array(ratio80)

	for user in users:
	    if users[user]["total"] != 0:
		rel_ratio100.append( round(float(users[user]["ratio100"]) * 100. / float(users[user]["total"]),1) )
		rel_ratio80.append( round(float(users[user]["ratio80"]) * 100. / float(users[user]["total"]),1) )
		rel_ratio30.append( round(float(users[user]["ratio30"]) * 100. / float(users[user]["total"]),1) )
		rel_ratio10.append( round(float(users[user]["ratio10"]) * 100. / float(users[user]["total"]),1) )
		rel_queue.append( round(float(users[user]["queue"]) * 100. / float(users[user]["total"]),1) )
	    else:
		rel_ratio100.append(0); rel_ratio80.append(0); rel_ratio30.append(0); rel_ratio10.append(0)

	rel_bot_queue = rel_queue
	rel_bot10 = array(rel_queue) + array(rel_ratio10)
	rel_bot30 = array(rel_queue) + array(rel_ratio10) + array(rel_ratio30)
	rel_bot80 = array(rel_queue) + array(rel_ratio10) + array(rel_ratio30) + array(rel_ratio80)



	ind = np.arange(N)    # the x locations for the groups
	width = 0.36       # the width of the bars: can also be len(x) sequence

	fig_abs = plt.figure()
	fig_rel = plt.figure()

	#canvas_abs = FigureCanvas(fig_abs)
	#canvas_rel = FigureCanvas(fig_rel)

	axis_abs = fig_abs.add_subplot(111)
	axis_rel = fig_rel.add_subplot(111)
	
        #if N > 1: axis_abs.set_yscale('log')
	
	##########################################################
	# create first plot, absolute view
	
	p0 = axis_abs.bar(ind, queue,   width, color='violet')
	p1 = axis_abs.bar(ind, ratio10,   width, color='r', bottom = bot_queue)
	p2 = axis_abs.bar(ind, ratio30, width, color='orange', bottom = bot10 )
	p3 = axis_abs.bar(ind, ratio80, width, color='y', bottom = bot30 )
	p4 = axis_abs.bar(ind, ratio100, width, color='g', bottom = bot80 )

	axis_abs.set_ylabel('Number of Jobs')
	axis_abs.set_title('Job Efficiency (absolute view)')
	axis_abs.set_xticks(ind+width/2.)
	axis_abs.set_xticklabels(user_names)
	#if N > 1: axis_abs.set_ylim(1,max_jobs)
	axis_abs.set_yticks(np.arange(0,max_jobs + 5,scale_value))
	axis_abs.legend( (p0[0], p1[0], p2[0], p3[0], p4[0]), ('queue', 'ratio < 10%', '10% < ratio < 30%', '30% < ratio < 80%', 'ratio > 80%') )

	
	fig_abs.savefig(self.archive_dir + "/qstat_eff.png",dpi=60)
	self.db_values["eff_plot"] = "qstat_eff.png"

	##########################################################
	# create second plot, relative view

	rel_p0 = axis_rel.bar(ind, rel_queue,   width, color='violet')
	rel_p1 = axis_rel.bar(ind, rel_ratio10,   width, color='r', bottom = rel_bot_queue)
	rel_p2 = axis_rel.bar(ind, rel_ratio30, width, color='orange', bottom = rel_bot10 )
	rel_p3 = axis_rel.bar(ind, rel_ratio80, width, color='y', bottom = rel_bot30 )
	rel_p4 = axis_rel.bar(ind, rel_ratio100, width, color='g', bottom = rel_bot80 )
	
	axis_rel.set_ylabel('fraction in %')
	axis_rel.set_title('Job Efficiency (relative view)')
	axis_rel.set_xticks(ind+width/2.)
	axis_rel.set_xticklabels(user_names)
	axis_rel.set_yticks(np.arange(0,101,10))

	axis_rel.legend( (rel_p0[0], rel_p1[0], rel_p2[0], rel_p3[0], rel_p4[0]), ('queue', 'ratio < 10%', '10% < ratio < 30%', '30% < ratio < 80%', 'ratio > 80%') )

	fig_rel.savefig(self.archive_dir + "/qstat_rel_eff.png",dpi=60)
	self.db_values["rel_eff_plot"] = "qstat_rel_eff.png"

    def output(self):

	begin = []
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '<td class="QstatTableFirstCol">Qstat Command Start Time</td>')
	begin.append("""<td>'.$data["starttime"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Qstat Command End Time</td>')
	begin.append("""  <td>'.$data["endtime"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br />')
	begin.append(  '<strong>ALL JOBS</strong>')
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Total Jobs</td>')
	begin.append("""  <td>'.$data["all_total"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Running Jobs</td>')
	begin.append("""  <td>'.$data["all_running"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Jobs with Walltime-Ratio under 10%</td>')
	begin.append("""  <td>'.$data["all_ratio10"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br />')
	begin.append(  '<strong>CMS JOBS</strong>')
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Total Jobs</td>')
	begin.append("""  <td>'.$data["cms_total"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Running Jobs</td>')
	begin.append("""  <td>'.$data["cms_running"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Jobs with Walltime-Ratio under 10%</td>')
	begin.append("""  <td>'.$data["cms_ratio10"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br/>')
	begin.append(  '<strong>CMSPRD JOBS</strong>')
	begin.append(  '<table class="TableData">')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Total Jobs</td>')
	begin.append("""  <td>'.$data["cmsprd_total"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Running Jobs</td>')
	begin.append("""  <td>'.$data["cmsprd_running"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  ' <tr>')
	begin.append(  '  <td class="QstatTableFirstCol">Jobs with Walltime-Ratio under 10%</td>')
	begin.append("""  <td>'.$data["cmsprd_ratio10"].'</td>""")
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br/>')
	begin.append(  '')
	begin.append(  '<table class="TableDetails">')
	begin.append(  ' <tr>')
	begin.append(  '  <td>')
	begin.append("""   <img src="' . $archive_dir . '/' . $data["eff_plot"] . '" alt=""/>""")
	begin.append(  '  </td>')
	begin.append(  '  <td>')
	begin.append("""   <img src="' . $archive_dir . '/' . $data["rel_eff_plot"] . '" alt=""/>""")
	begin.append(  '  </td>')
	begin.append(  ' </tr>')
	begin.append(  '</table>')
	begin.append(  '<br />')
	begin.append(  '')
	begin.append("""<input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__+ """_result\\\');" />""")
	begin.append(  '<div class="DetailedInfo" id="' + self.__module__+ '_result" style="display:none;">')
	begin.append(  ' <strong>JOB STATISTICS</strong>')
	begin.append(  ' <table class="TableDetails QstatTableDetails">')
	begin.append(  '  <tr class="TableHeader">')
	begin.append(  '   <td>User</td>')
	begin.append(  '   <td>Total</td>')
	begin.append(  '   <td>Running</td>')
	begin.append(  '   <td>Waiting</td>')
	begin.append(  '   <td>Queue</td>')
	begin.append(  '   <td>Eff. > 80%</td>')
	begin.append(  '   <td>80% > Eff. > 30%</td>')
	begin.append(  '   <td>30% > Eff. > 10%</td>')
	begin.append(  '   <td>Eff. &lt; 10%</td>')
	begin.append(  '  </tr>')

	details_row = []
	details_row.append(  '  <tr>')
	details_row.append("""   <td>'.$info["user"].'</td>""")
	details_row.append("""   <td>'.$info["total"].'</td>""")
	details_row.append("""   <td>'.$info["running"].'</td>""")
	details_row.append("""   <td>'.$info["waiting"].'</td>""")
	details_row.append("""   <td>'.$info["queue"].'</td>""")
	details_row.append("""   <td>'.$info["ratio100"].'</td>""")
	details_row.append("""   <td>'.$info["ratio80"].'</td>""")
	details_row.append("""   <td>'.$info["ratio30"].'</td>""")
	details_row.append("""   <td>'.$info["ratio10"].'</td>""")
	details_row.append(  '  </tr>')

	end = []
	end.append(  ' </table>')
	end.append(  '</div>')
	end.append(  '<br />')

	module_content = """<?php

	print('""" + self.PHPArrayToString(begin) + """');

	$tm = localtime($data['timestamp']);
	$year = $tm[5] + 1900; // PHP gives year since 1900
	$month = sprintf('%02d', $tm[4] + 1); // PHP uses 0-11, Python uses 1-12
	$day = sprintf('%02d', $tm[3]);
	$archive_dir = "archive/$year/$month/$day/" . $data['timestamp'];

	// Assume old format if archive_dir does not exist
	if(!file_exists($archive_dir))
		$archive_dir = '.';

	$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		print('""" + self.PHPArrayToString(details_row) + """');
	}

	print('""" + self.PHPArrayToString(end) + """');
	?>"""

	return self.PHPOutput(module_content)
