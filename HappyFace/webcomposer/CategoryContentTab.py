import sys, os

class CategoryContentTab(object):
    def __init__(self,cat_content,config,category,timestamp):

	# a few symbols / hyperlinks for the status bar ;-)
	valid_xhtml11 = """
	<a href="http://validator.w3.org/check?uri=referer"><img style="border:0;vertical-align: middle;" src="config/images/valid-xhtml11.png" alt="Valid XHTML 1.1" /></a>
	"""
	valid_css = """
	<a href="http://jigsaw.w3.org/css-validator/check/referer"><img style="border:0;vertical-align: middle;" src="config/images/vcss.gif" alt="Valid CSS!" /></a>
	"""
	python = """
	<a href="http://python.org"><img style="border:0;vertical-align: middle;" src="config/images/python_logo_mini.png" alt="Python" /></a>
	"""
	sqlite = """
	<a href="http://sqlite.org"><img style="border:0;vertical-align: middle;" src="config/images/sqlite_logo_mini.png" alt="SQLite" /></a>
	"""
	php = """
	<a href="http://php.net"><img style="border:0;vertical-align: middle;" src="config/images/php_logo_mini.png" alt="PHP" /></a>
	"""

	output = ""

        output += '<div id="HappyPanelsContent1" class="HappyPanelsContent">' + "\n"

        output += ' <div id="nav" class="nav">' + "\n"
	output += """
	<?php
	    if ( is_array($ModuleResultsArray) ) {
		printf('<ul>');
                printf('<li>
                        <table class="nav_entry">
                        <tr style="border-bottom:1px solid #FFF;">
                        <td style="width:200px;"><div class="topdiv">Move navigation bar</div></td>
                        <td style="width:40px;"><div class="topdiv"><a href="javascript:movenav()" onFocus="this.blur()"><img id="navarrow" alt="" border="0" width="32px" src="config/images/leftarrow.png" /></a></div></td>
                        </tr>
                        </table>
                        </li>
                ');		

	        foreach ($ModuleResultsArray as $module) {

	            if ($module["category"] == """ + category + """) {

			$nav_symbol = getModNavSymbol($module["status"], $module["mod_type"]);

		        printf('<li>
				<table class="nav_entry">
				<tr style="border-bottom:1px solid #FFF;">
				<td style="width:200px;"><a href="#' . $module["module"] . '" onFocus="this.blur()">' . $module["mod_title"] . '</a></td>
				<td style="width:40px;"><div class="imgdiv">' . $nav_symbol . '</div></td>
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

	output += ' </div>' + "\n"

        output += cat_content + "\n"

        output += ' <div>' + "\n"
        output += valid_xhtml11 + valid_css + python + sqlite + php + "\n"
        output += ' </div>' + "\n"

	output += '</div>' + "\n"

        self.output = output
