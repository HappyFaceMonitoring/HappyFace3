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
                        <td style="width:200px;" align="left"><div class="HappyFNtopdiv">Fast Navigation Bar</div></td>
                        <td style="width:40px;" align="center"><div class="HappyFNtopdiv"><a href="javascript:movenav(\\\'HappyFNnav_""" + category + """\\\')" onfocus="this.blur()"><img id="HappyFNnav_""" + category + """arrow" alt="" style="width:32px;border:0px;" src="config/images/rightarrow.png" /></a></div></td>
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
				<td style="width:200px;" align="left"><a href="javascript:goto(\\\'' . $module["module"] . '\\\')" onfocus="this.blur()">'. $module["mod_title"] . '</a></td>
				<td style="width:40px;" align="left"><div class="HappyFNnavimg"><a href="javascript:goto(\\\'' . $module["module"] . '\\\')" onfocus="this.blur()">' . $nav_symbol . '</a></div></td>
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
