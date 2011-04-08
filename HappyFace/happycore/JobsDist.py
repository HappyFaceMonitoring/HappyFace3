##############################################
# Jobs distribution plot
# at the moment experimental
# the plot creating part has to be rewritten!!!
##############################################

from ModuleBase import *
from XMLParsing import *

from numpy import array
import numpy as np
import matplotlib
# The warn=False statement hides the matplotlib warning displayed during
# a HF run if more than one module are configured using the same base class.
# Problem description: a warning is displayed if matplotlib.use() is called
# after matplotlib.pyplot was imported. However this is always the case if
# more than one modules inheriting from this base class are instanciated.
matplotlib.use("cairo.png", warn=False)
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure


class JobsDist(ModuleBase):

    def __init__(self,module_options):

        ModuleBase.__init__(self,module_options)

	self.old_result_warning_limit = float(self.configService.getDefault('setup', 'old_result_warning_limit', '1.0'))
	self.old_result_critical_limit = float(self.configService.getDefault('setup', 'old_result_critical_limit', '4.0'))
        self.variable = self.configService.get("setup", "variable")

        group = self.configService.getDefault("setup", "group", "").strip()

	self.groups = []
	if group != '': self.groups = group.split(',')

	self.db_keys["groupname"] = StringCol()
	self.db_keys["filename"] = StringCol()

	self.db_keys["result_timestamp"] = IntCol()
	self.db_keys["old_result_warning_limit"] = FloatCol()
	self.db_keys["old_result_critical_limit"] = FloatCol()

	self.db_values["groupname"] = ""
	self.db_values["filename"] = ""

	self.db_values["result_timestamp"] = 0
	self.db_values["old_result_warning_limit"] = self.old_result_warning_limit
	self.db_values["old_result_critical_limit"] = self.old_result_critical_limit

        self.dsTag = 'xml_source'

	# Split up cputime and walltime into seconds, minutes and hours
	self.splitnum = 1
	if self.variable == 'cputime' or self.variable == 'walltime':
	    self.splitnum = 3

    def getGroupHierarchy(self, root):
        hierarchy = {}
        for element in root:
	    if element.tag == "summaries":
	        for child in element:
		    if child.tag == 'summary':
		        group = 'all'
		        if 'group' in child.attrib:
			    group = child.attrib['group']

	                if 'parent' in child.attrib:
	                    hierarchy[group] = child.attrib['parent']
		        else:
		            hierarchy[group] = None
	return hierarchy

    def checkGroup(self, group_chk, group, hierarchy):
        try:
            while group_chk != group:
	        if hierarchy[group_chk] == None:
	            return False
	        group_chk = hierarchy[group_chk]
	    return True
	except:
	    return False

    def checkGroups(self, group_chk, groups, hierarchy):
        if len(groups) == 0: return True

        for group in groups:
	    if self.checkGroup(group_chk, group, hierarchy):
	        return True
	return False

    def process(self):

	self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(self.dsTag)))
	self.configService.addToParameter('setup', 'definition', '<br />Old result warning limit: ' + str(self.old_result_warning_limit) + ' hours')
	self.configService.addToParameter('setup', 'definition', '<br />Old result critical limit: ' + str(self.old_result_critical_limit) + ' hours')

        dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)

	root = source_tree.getroot()

	values = []
	variable = self.variable
	nbins = 20

	hierarchy = self.getGroupHierarchy(root)

	# Check input file timestamp
	date = 0
	for element in root:
	    if element.tag == "header":
	        for child in element:
		    if child.tag == "date" and child.text is not None:
		        date = int(float(child.text.strip()))

	self.db_values["result_timestamp"] = date
	self.status = 1.0
#	if self.timestamp - date > self.old_result_critical_limit*3600:
#	    self.status = 0.0
#	elif self.timestamp - date > self.old_result_warning_limit*3600:
#	    self.status = 0.5

	for element in root:
	    if element.tag == "jobs":
		for child in element:
                    group = job_state = variable_str = ''
		    # Only count running jobs
		    for subchild in child:
		        if subchild.tag == 'group' and subchild.text is not None:
			    group = subchild.text.strip()
			if subchild.tag == 'state' and subchild.text is not None:
			    job_state = subchild.text.strip()
			if subchild.tag == variable and subchild.text is not None:
			    variable_str = subchild.text.strip()

		    # Check user
		    if not self.checkGroups(group, self.groups, hierarchy) or job_state != 'running' or variable_str == '':
		    	continue

		    values.append(float(variable_str))

	if len(self.groups) == 0:
	    self.db_values["groupname"] = ''
	else:
	    self.db_values["groupname"] = ', '.join(self.groups)

	# create plots for output
	self.createDistPlot(variable,values,nbins)

    def createDistPlot(self,variable,values,nbins):

	################################################################
	### AT THE MOMENT: QUICK AND DIRTY
	### inspired by: http://matplotlib.sourceforge.net/examples/pylab_examples/bar_stacked.html

	### muss bei gelegenheit ueberschrieben werden
	### saubere initialisierung der "figure", "canvas", ...
	### striktere definitionen der plot-eigenschaften, verschieben der legende
	### verringerung von code durch auslagerung von funktionen

	### break image creation if there are no jobs
	if len(values) == 0:
	    return

	min_var = min(values)
	max_var = max(values)
	diff_var = max_var - min_var

	# Show only one bin in case there is only one value or all values are
	# equivalent
	if diff_var == 0:
	    nbins = 1

	content = [0]*nbins
	for value in values:
	    if diff_var > 0:
	        bin = int(round((value - min_var) * nbins / diff_var))
	    else:
	        bin = nbins;

	    if bin == nbins:
	        bin = nbins - 1
	    content[bin] += 1

	xlabels = [0]*nbins
	for x in range(0,nbins):
	    num = min_var + (x + 0.5)/nbins * diff_var
	    int_num = int(num + 0.5)

	    xlabelvalues = []
	    for y in range(0, self.splitnum):
	        c = int_num / (60**y)
		cstr = ''
		if y < self.splitnum-1:
		    cstr = "%02d" % (c % 60)
		else:
		    cstr = str(c)
	        xlabelvalues.append(cstr)

            xlabelvalues.reverse()
	    xlabels[x] = ':'.join(xlabelvalues)

	max_bin_height = max(content);
	scale_value = max_bin_height // 10
	if scale_value == 0: scale_value = 5

	ind = np.arange(nbins)    # the x locations for the groups
	width = 1.00       # the width of the bars: can also be len(x) sequence

	fig = plt.figure()

	axis = fig.add_subplot(111)

	p0 = axis.bar(ind, content, width, color='orange')

	axis.set_position([0.10,0.2,0.85,0.75])
	axis.set_xlabel(variable);
	axis.set_ylabel('Number of Jobs')
	axis.set_title(variable + ' distribution')
	axis.set_xticks(ind + width / 2.0)
	axis.set_xticklabels(xlabels, rotation='vertical')
	axis.set_yticks(np.arange(0,max_bin_height + 5,scale_value))

	
	fig.savefig(self.archive_dir + "/" + self.__module__ + "_jobs_dist_" + variable + ".png",dpi=60)
	self.db_values["filename"] = self.__module__ + "_jobs_dist_" + variable + ".png"
        self.archive_columns.append('filename')

    def output(self):

        old_result_warning_message = []
	old_result_warning_message.append("<p style=\"font-size: large; color: red;\">Input XML was generated more than ' . $data['old_result_warning_limit'] . ' hours in the past</p>")
        old_result_critical_message = []
	old_result_critical_message.append("<p style=\"font-size: large; color: red;\">Input XML was generated more than ' . $data['old_result_critical_limit'] . ' hours in the past</p>")

	plot = []
	plot.append("""<img src="' . $archive_dir . '/' . $data["filename"] . '" alt=""/>""")
	noplot = []
	noplot.append("<h4>There are no ' . (($data['groupname'] == '') ? '' : ('&quot;' . $data['groupname'] . '&quot; ')) . 'jobs running</h4>")

	module_content = """<?php

	if(isset($data['old_result_critical_limit']) && isset($data['old_result_warning_limit']))
	{
		if($data['timestamp'] - $data['result_timestamp'] > $data['old_result_critical_limit']*3600)
			print('""" + self.PHPArrayToString(old_result_critical_message) + """');
		if($data['timestamp'] - $data['result_timestamp'] > $data['old_result_warning_limit']*3600)
			print('""" + self.PHPArrayToString(old_result_warning_message) + """');
	}

	$tm = localtime($data['timestamp']);
	$year = $tm[5] + 1900; // PHP gives year since 1900
	$month = sprintf('%02d', $tm[4] + 1); // PHP uses 0-11, Python uses 1-12
	$day = sprintf('%02d', $tm[3]);
	$archive_dir = "archive/$year/$month/$day/" . $data['timestamp'];

	// Assume old format if archive_dir does not exist
	if(!file_exists($archive_dir))
		$archive_dir = '.';

	if($data['filename'] != '')
		print('""" + self.PHPArrayToString(plot) + """');
	else
		print('""" + self.PHPArrayToString(noplot) + """');

	?>"""

	return self.PHPOutput(module_content)
