import sys, os

class ModuleStatusSymbolLogic(object):
	
    def __init__(self,theme):

	self.output = """
	<?php
	function getModStatusSymbol($status,$mod_type)
	{
	    if ($mod_type == "plots") {
		if ($status == 1) { return '<img alt="" src="config/themes/""" + theme + """/mod_avail_plot.png" />'; }
		else if ($status == -1) { return '<img alt="" src="config/themes/""" + theme + """/mod_unavail_plot.png" />'; }
	    }
	    else if ($mod_type == "rated") {
		if ($status > 0.66 && $status <= 1.0) { return '<img alt="" src="config/themes/""" + theme + """/mod_happy.png" />'; }
		else if ($status > 0.33 && $status <= 0.66) { return '<img alt="" src="config/themes/""" + theme + """/mod_neutral.png" />'; }
		else if ($status >= 0.0 && $status <= 0.33) { return '<img alt="" src="config/themes/""" + theme + """/mod_unhappy.png" />'; }
		else if ($status == -1) { return '<img alt="" src="config/themes/""" + theme + """/mod_noinfo.png" />'; }
	    }
	}

	function getModNavSymbol($status,$mod_type)
	{
	    if ($mod_type == "plots") {
		if ($status == 1) { return '<img alt="" src="config/themes/""" + theme + """/nav_avail_plot.png" border="0" />'; }
		else if ($status == -1) { return '<img alt="" src="config/themes/""" + theme + """/nav_unavail_plot.png" border="0" />'; }
	    }
	    else if ($mod_type == "rated") {
		if ($status > 0.66 && $status <= 1.0) { return '<img alt="" src="config/themes/""" + theme + """/nav_happy.png" border="0" />'; }
		else if ($status > 0.33 && $status <= 0.66) { return '<img alt="" src="config/themes/""" + theme + """/nav_neutral.png" border="0" />'; }
		else if ($status >= 0.0 && $status <= 0.33) { return '<img alt="" src="config/themes/""" + theme + """/nav_unhappy.png" border="0" />'; }
		else if ($status == -1) { return '<img alt="" src="config/themes/""" + theme + """/nav_noinfo.png" border="0" />'; }
	    }
	}

	?>
	"""
