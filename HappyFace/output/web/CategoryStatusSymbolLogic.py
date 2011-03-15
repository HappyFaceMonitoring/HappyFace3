import sys, os

class CategoryStatusSymbolLogic(object):
	
    def __init__(self,theme):

	self.output = """<?php

	function getCatStatusSymbol($cat_type,$cat_status,$cssclass)
	{
	    if($cssclass != '')
	        $cssclass = 'class="' . $cssclass . '"';

	    if ($cat_type == "plots") { 
	        if ($cat_status >= 0) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_avail_plot.png" />'; }
		else if ($cat_status == -1) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_unavail_plot.png" />'; }
		else if ($cat_status == -2) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_noinfo.png" />'; }
	    }
	    else if ($cat_type == "rated") {
		if ($cat_status > 0.66 && $cat_status <= 1.0) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_happy.png" />'; }
		else if ($cat_status > 0.33 && $cat_status <= 0.66) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_neutral.png" />'; }
		else if ($cat_status >= 0.0 && $cat_status <= 0.33) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_unhappy.png" />'; }
		else if ($cat_status == -1) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_noinfo.png" />'; }
		else if ($cat_status == -2) { return '<img alt="" ' . $cssclass . ' src="config/themes/""" + theme + """/cat_noinfo.png" />'; }
	    }
	}

	function getCatStatusSymbolForCategory($category,$cat_type,$cat_algo,$ModuleResultsArray)
	{
	    $cat_status = getCatStatus($category,$cat_algo,$ModuleResultsArray);
	    return getCatStatusSymbol($cat_type, $cat_status, 'HappyNavTab');
	}

        function getCatIndexSymbolForCategory($category,$ModuleResultsArray)
        {
            $cssclass = 'class="HappyNavTabIndex"';

            $indexstatus = 'ok';

	    foreach ($ModuleResultsArray as $module) {
		if ($module["category"] == $category) {
		    $mod_status = $module["status"];
		    if ($mod_status == -1) {
			$indexstatus = 'warn';
		    } 
		}
	    }
            return '<img alt="" ' . $cssclass . ' src="config/images/index_' . $indexstatus . '.png" />';
        }

	# funktion for small lock icon besides category icon
	function getCatLockSymbolForCategory($category,$ModuleResultsArray) {
            $lock_icon = false;

            foreach ($ModuleResultsArray as $module) {
                if ($module["category"] == $category) {
                    $mod_status = $module["status"];
                    if ($mod_status == -2) $lock_icon=true;
                }
            }
            $cssclass = 'class="HappyNavLockTabIndex"';
	    global $hideIcons;
            if ($lock_icon == true && $hideIcons != true) return '<img alt="" ' . $cssclass . ' src="config/images/index_lock.png" />';
            else return '';
	}

	?>"""

