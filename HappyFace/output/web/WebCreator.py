import sys, os

from CategoryNavigationTab import *
from CategoryContentTab import *
from ModuleStatusSymbolLogic import *
from CategoryStatusLogic import *
from CategoryStatusSymbolLogic import *
from TimeMachineLogic import *
from TimeMachineController import *
from SQLCallRoutines import *
from ModuleResultsArrayBuilder import *

class WebCreator(object):
    def __init__(self,config,modObj_list,timestamp):

        self.config      = config
	self.modObj_list = modObj_list
	self.timestamp   = timestamp
        self.cssList     = []

	self.theme	 = config.get('setup','theme')

    def setCss(self,cssList):
        self.cssList     = cssList

    def getOutput(self):

   	navigation       = ""
        content 	 = ""
	category_id	 = 0

	web_title	 = self.config.get('setup','web_title')
	logo_image	 = self.config.get('setup','logo_image')
	histo_step	 = self.config.get('setup','histo_step')

        for category in self.config.get('setup','categories').split(","):

             cat_title   = self.config.get(category,'cat_title')
             cat_type    = self.config.get(category,'cat_type')
             cat_algo    = self.config.get(category,'cat_algo')
             cat_content = ""

             for module in self.config.get(category,'modules').split(","):

                  if module == "": continue
                  cat_content += self.modObj_list[module].output()

	     # collect all navigation and content tabs
             navigation  += CategoryNavigationTab(category,cat_title,cat_type,cat_algo).output
             content     += CategoryContentTab(cat_content,self.config,category,category_id,self.timestamp).output

	     category_id += 1

	output = ""

	#######################################################
	################## create index.php ###################

	# initiate the database
	output += '<?php' + "\n"
	output += '    /*** connect to SQLite database ***/' + "\n"
	output += '    $dbh = new PDO("sqlite:HappyFace.db");' + "\n"
	output += '?>' + "\n"

	# provides the logic for the timestamp definition
	output += TimeMachineLogic(histo_step).output
	
	# SQL call routines for all active modules
	output += SQLCallRoutines(self.config).output

	# create an multi-array variable with all important information from the modules:
	# status, type, weight, category => used by the CategoryStatusLogic
	output += ModuleResultsArrayBuilder().output
	
	# provides a function for the category status
	output += CategoryStatusLogic().output

	# provides a function for the category status symbol
	output += CategoryStatusSymbolLogic(self.theme).output

	# provides a function for the module status symbol
	output += ModuleStatusSymbolLogic(self.theme).output
	
	#######################################################

	# start with HTML output
	output += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">' + "\n"
	output += '<html xmlns="http://www.w3.org/1999/xhtml">' + "\n"
	
	# header
	output += '<head>' + "\n"
	output += '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />' + "\n"
	output += '<title>The HappyFace Project - ' + web_title + ' </title>' + "\n"
	output += '<script src="config/TabNavigation.js" type="text/javascript"></script>' + "\n"
	output += '<link href="config/TabNavigation.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '<script src="config/FastNavigation.js" type="text/javascript"></script>' + "\n"
	output += '<link href="config/FastNavigation.css" rel="stylesheet" type="text/css" />' + "\n"
        for css in self.cssList:
            output += '<link href="'+css+'" rel="stylesheet" type="text/css" />' + "\n"
        
	output += '</head>' + "\n"
	
	# body
	output += '<body onload="javascript:HappyReload(300)">' + "\n"

	# logic to memorize selected tab on auto reload part 1
	output += """
		<?php
			if ($_GET["t"] != "") { $selectedTab = $_GET["t"]; }
			else { $selectedTab = "0"; }
			printf('
				<script type="text/javascript">
				<!-- 
				var selectedTab='.$selectedTab.'; 
				//-->
				</script>
			');
			if ($_GET["m"] != "") { $selectedMod = $_GET["m"]; }
		?>
		"""
	output += '<form id="ReloadForm" action="<?php echo $PHP_SELF; ?>" method="get"><div>' + "\n"
	output += ' <input type="hidden" id="ReloadTab" name="t" value="<?php echo $selectedTab; ?>" />' + "\n"
	output += ' <input type="hidden" id="ReloadMod" name="m" value="<?php echo $selectedMod; ?>" />' + "\n"
	output += '</div></form>' + "\n"

	# time bar on the top of the website, input forms for time control
	output += TimeMachineController(logo_image).output

	output += '<div id="HappyPanels1" class="HappyPanels">' + "\n"

	# input navigation
	output += '  <ul class="HappyPanelsTabGroup">' + "\n"
	output += navigation
	output += '  </ul>' + "\n"

	# input content
	output += '  <div class="HappyPanelsContentGroup">' + "\n"

	output += content + "\n"
	output += '  </div>' + "\n"

	output += '</div>' + "\n"

	# include layer to hide content when scrolling
	output += '<div class="HappySolidLayer"></div>' + "\n"

	# logic to memorize selected tab on auto reload part 2
	output += """
		<?php
			if ($selectedMod != "") {
				printf('
					<script type="text/javascript">
					<!-- 
					goto("'.$selectedMod.'"); 
					//-->
					</script>	
				');
			}
			if ($historyview) {
				printf('
					<script type="text/javascript">
					<!-- 
					AutoReload=false; 
					//-->
					</script>	
				');
			}
		?>
		"""

	# some javascripts for website navigation
	output += '<script type="text/javascript">' + "\n"
	output += '<!--' + "\n"
	output += 'var HappyPanels1 = new HappyTab.Widget.HappyPanels("HappyPanels1",selectedTab);' + "\n"
	output += '//-->' + "\n"
	output += '</script>' + "\n"
	
	output += '<script type="text/javascript">' + "\n"
	output += '<!--' + "\n"
	output += 'function show_hide(me) {' + "\n"
	output += '	if (document.getElementById(me).style.display=="none") {' + "\n"
	output += '		document.getElementById(me).style.display="block";' + "\n"
	output += '	} else {' + "\n"
	output += '		document.getElementById(me).style.display="none";' + "\n"
	output += '	}' + "\n"
	output += '}' + "\n"
	output += '//-->' + "\n"
	output += '</script>' + "\n"

	# end of html output
	output += '</body>' + "\n"
	output += '</html>' + "\n"
	
	# close the database
	output += '<?php' + "\n"
	output += '    /*** close the database connection ***/' + "\n"
	output += '    $dbh = null;' + "\n"
	output += '?>' + "\n"
	
	#######################################################
	
	return output
