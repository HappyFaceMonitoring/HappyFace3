import sys, os

class CategoryStatusSymbolLogic(object):
	
    def __init__(self,theme):

	self.output = """
	<?php
	function getCatStatusSymbol($category,$cat_type,$cat_algo,$ModuleResultsArray)
	{
	    $cat_status = getCatStatus($category,$cat_algo,$ModuleResultsArray);
	
	    if ($cat_type == "plots") { 
	        if ($cat_status >= 0) { return '<img alt="" src="config/themes/""" + theme + """/cat_avail_plot.png" />'; }
		else if ($cat_status == -1) { return '<img alt="" src="config/themes/""" + theme + """/cat_unavail_plot.png" />'; }
	    }
	    else if ($cat_type == "rated") {
		if ($cat_status > 0.66 && $cat_status <= 1.0) { return '<img alt="" src="config/themes/""" + theme + """/cat_happy.png" />'; }
		else if ($cat_status > 0.33 && $cat_status <= 0.66) { return '<img alt="" src="config/themes/""" + theme + """/cat_neutral.png" />'; }
		else if ($cat_status >= 0.0 && $cat_status <= 0.33) { return '<img alt="" src="config/themes/""" + theme + """/cat_unhappy.png" />'; }
		else if ($cat_status == -1) { return '<img alt="" src="config/themes/""" + theme + """/cat_noinfo.png" />'; }
	    }
	}
	?>
	"""

