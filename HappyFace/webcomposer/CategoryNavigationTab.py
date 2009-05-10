import sys, os

class CategoryNavigationTab(object):
    def __init__(self, category, cat_title, cat_type, cat_algo):

	# build navigation tab for the navigation bar
	output = ""
	
	output += '    <li class="HappyPanelsTab">' + "\n" # tabindex="0" onfocus="this.blur()"
	output += '      <table>' + "\n"
	output += '        <tr>' + "\n"
	output += '          <td><div style="text-align:center;">' + "\n"
	output += '           <?php printf(getCatStatusSymbol("' + category + '","' + cat_type + '","' + cat_algo + '", $ModuleResultsArray)); ?>' + "\n"
	output += '          </div></td>' + "\n"
	output += '        </tr>' + "\n"
	output += '        <tr>' + "\n"
	output += '          <td><div style="text-align:center;">' + "\n"
	output += cat_title
	output += '          </div></td>' + "\n"
	output += '        </tr>' + "\n"
	output += '      </table>' + "\n"
	output += '    </li>' + "\n"
	
	self.output = output
