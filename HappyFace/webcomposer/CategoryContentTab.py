import sys, os

class CategoryContentTab(object):
    def __init__(self,cat_content,config,category,timestamp):

	# a few symbols / hyperlinks for the status bar ;-)
	valid_xhtml11 = """
	<a href="http://validator.w3.org/check?uri=referer"><img style="border:0;vertical-align: middle;" src="config/valid-xhtml11.png" alt="Valid XHTML 1.1" /></a>
	"""
	valid_css = """
	<a href="http://jigsaw.w3.org/css-validator/check/referer"><img style="border:0;vertical-align: middle;" src="config/vcss.gif" alt="Valid CSS!" /></a>
	"""
	python = """
	<a href="http://python.org"><img style="border:0;vertical-align: middle;" src="config/python_logo_mini.png" alt="Python" /></a>
	"""
	sqlite = """
	<a href="http://sqlite.org"><img style="border:0;vertical-align: middle;" src="config/sqlite_logo_mini.png" alt="SQLite" /></a>
	"""
	php = """
	<a href="http://php.net"><img style="border:0;vertical-align: middle;" src="config/php_logo_mini.png" alt="PHP" /></a>
	"""

	output = ""

        output += '<div class="TabbedPanelsContent">' + "\n"


	output += '<table style="width:1250px">' + "\n"
	output += '  <tr>' + "\n"
	
	output += '    <td style="width:250px;">' + "\n"
        output += '<div class="nav">' + "\n"
	output += """
	<?php
	    if ( is_array($ModuleResultsArray) ) {
		printf('<ul>');
	        foreach ($ModuleResultsArray as $module) {

	            if ($module["category"] == """ + category + """) {

			$nav_symbol = getModNavSymbol($module["status"], $module["mod_type"]);

		        printf('<li>
				<table class="nav_entry">
				<tr style="border-bottom:1px solid #FFF;">
				<td style="width:40px;"><div class="imgdiv">' . $nav_symbol . '</div></td>
				<td style="width:200px;"><a href="#' . $module["module"] . '">' . $module["mod_title"] . '</a></td>
				</tr>
				</table>
				</li>
			');
	            }
	        }
		printf('</ul>');
	    }
	?>
	"""
	output += '</div>' + "\n"
	output += '    </td>' + "\n"

	output += '    <td>' + "\n"
        output += cat_content + "\n"
        output += valid_xhtml11 + valid_css + python + sqlite + php + "\n"
	output += '    </td>' + "\n"
	
	output += '  </tr>' + "\n"
	output += '</table>' + "\n"



	output += '</div>' + "\n"

        self.output = output




	#<div id="imgdiv"><img src="config/themes/armin_box_arrows/nav_neutral.png" /></div>
	#for category in config.get('setup','categories').split(","):
	#    for module in config.get(category,'modules').split(","):
	#	if module == "": continue
	#	output += '<li><a href="#' + module + '">' + module + '</a></li>' + "\n"
        #output += '<li><a href="#top">top </a></li>' + "\n"