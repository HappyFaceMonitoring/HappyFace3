import sys, os

from HTMLOutput import *

class CategoryNavigationTab(HTMLOutput):
    def __init__(self, category, cat_title, cat_type, cat_algo):
    	HTMLOutput.__init__(self, 4)

	output = []
	output.append('<li class="HappyPanelsTab" id="' + category + '_tab">')
	output.append(' <table width="100%">')
	output.append('  <tr>')
	output.append('   <td>')
	output.append('    <div style="text-align:center;">')
	output.append("     ' . getCatStatusSymbolForCategory('" + category + "','" + cat_type + "','" + cat_algo + "', $ModuleResultsArray) . '")
	output.append("     ' . getCatIndexSymbolForCategory('" + category + "', $ModuleResultsArray) . '")
	output.append("     ' . getCatLockSymbolForCategory('" + category + "', $ModuleResultsArray) . '")
	output.append('    </div>')
	output.append('   </td>')
	output.append('  </tr>')
	output.append('  <tr>')
	output.append('   <td>')
	output.append('    <div style="text-align:center;">')
	output.append('     ' + cat_title)
	output.append('    </div>')
	output.append('   </td>')
	output.append('  </tr>')
	output.append(' </table>')
	output.append('</li>')

	out = """<?php 
		global $hideIcons;
		if (getCatStatus("""+category+""","""+cat_algo+""",$ModuleResultsArray) == -2 && $hideIcons==true) {
			print('<li style="width:0px;height:0px;"></li>');
                }
		else {
			print('""" + self.PHPArrayToString(output) + """');
		}
	      ?>"""

	self.output = out
