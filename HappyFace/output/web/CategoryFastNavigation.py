import sys, os

from HTMLOutput import *

class CategoryFastNavigation(HTMLOutput):
    def __init__(self,category):
    	HTMLOutput.__init__(self, 5)

	begin = []
	begin.append(       '<div id="HappyFNnav_' + category + '" class="HappyFNnav">')

	list_begin = []
	list_begin.append(  ' <ul>')
	list_begin.append(  '  <li>')
	list_begin.append(  '   <table class="HappyFNnaventry" style="border-top: solid 1px #999;">')
	list_begin.append(  '    <tr>')
	list_begin.append(  '     <td style="width:200px;" align="left">')
	list_begin.append(  '      <div class="HappyFNtopdiv">Fast Navigation Bar</div>')
	list_begin.append(  '     </td>')
	list_begin.append(  '     <td style="width:40px;" align="center">')
	list_begin.append(  '      <div class="HappyFNtopdiv">')
	list_begin.append("""       <a href="javascript:movenav(\\\'HappyFNnav_""" + category + """\\\')" onfocus="this.blur()">""")
	list_begin.append("""        <img id="HappyFNnav_""" + category + """arrow" alt="" style="width:32px;border:0px;" src="config/images/rightarrow.png" />""")
	list_begin.append(  '       </a>')
	list_begin.append(  '      </div>')
	list_begin.append(  '     </td>')
	list_begin.append(  '    </tr>')
	list_begin.append(  '   </table>')
	list_begin.append(  '  </li>')

	list_item = []
	list_item.append(   '  <li>')
	list_item.append(   '   <table class="HappyFNnaventry">')
	list_item.append(   '    <tr style="border-bottom:1px solid #FFF;">')
	list_item.append(   '     <td style="width:200px;" align="left">')
	list_item.append( """      <a href="javascript:goto(\\\'' . $module["module"] . '\\\')" onfocus="this.blur()">'. htmlentities($module["mod_title"]) . '</a>""")
	list_item.append(   '     </td>')
	list_item.append(   '     <td style="width:40px;" align="left">')
	list_item.append(   '      <div class="HappyFNnavimg">')
	list_item.append( """       <a href="javascript:goto(\\\'' . $module["module"] . '\\\')" onfocus="this.blur()">' . $nav_symbol . '</a>""")
	list_item.append(   '      </div>')
	list_item.append(   '     </td>')
	list_item.append(   '    </tr>')
	list_item.append(   '   </table>')
	list_item.append(   '  </li>')

	list_end = []
	list_end.append(    ' </ul>');

	end = []
	end.append(         '</div>')
	end.append(         '<script type="text/javascript">getFNSize("HappyFNnav_' + category + '");</script>')

	output = """<?php

	printf('""" + self.PHPArrayToString(begin) + """');

	if ( is_array($ModuleResultsArray) ) {
	    printf('""" + self.PHPArrayToString(list_begin) + """');

	    foreach ($ModuleResultsArray as $module) {

	        if ($module["category"] == """ + category + """) {

		    $nav_symbol = getModNavSymbol($module["status"], $module["mod_type"], $module["mod_title"]);

		    printf('""" + self.PHPArrayToString(list_item) + """');
	        }
	    }
	    printf('""" + self.PHPArrayToString(list_end) + """');
	}

	printf('""" + self.PHPArrayToString(end) + """');

	?>"""

        self.output = output
