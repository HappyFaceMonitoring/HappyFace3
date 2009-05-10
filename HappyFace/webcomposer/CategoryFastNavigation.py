import sys, os

class CategoryFastNavigation(object):
    def __init__(self,category):

	output = ""

        output += '<div id="HappyFNnav_'+category+'" class="HappyFNnav">' + "\n"
	output += """
	<?php
	    if ( is_array($ModuleResultsArray) ) {
		printf('<ul>');
                printf('<li>
                        <table class="HappyFNnaventry">
                        <tr style="border-bottom:1px solid #FFF;">
                        <td style="width:200px;"><div class="HappyFNtopdiv">Fast Navigation Bar</div></td>
                        <td style="width:40px;"><div class="HappyFNtopdiv"><a href="javascript:movenav(\\\'HappyFNnav_""" + category + """\\\')" onFocus="this.blur()"><img id="HappyFNnav_""" + category + """arrow" alt="" border="0" width="32px" src="config/images/rightarrow.png" /></a></div></td>
                        </tr>
                        </table>
                        </li>
                ');		

	        foreach ($ModuleResultsArray as $module) {

	            if ($module["category"] == """ + category + """) {

			$nav_symbol = getModNavSymbol($module["status"], $module["mod_type"]);

		        printf('<li>
				<table class="HappyFNnaventry">
				<tr style="border-bottom:1px solid #FFF;">
				<td style="width:200px;"><a href="javascript:goto(\\\'HappyPanelsContent\\\',\\\'' . $module["module"] . '\\\')" onFocus="this.blur()">'. $module["mod_title"] . '</a></td>
				<td style="width:40px;"><div class="HappyFNnavimg"><a href="javascript:goto(\\\'' . $module["module"] . '\\\')" onFocus="this.blur()">' . $nav_symbol . '</a></div></td>
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

        self.output = output
