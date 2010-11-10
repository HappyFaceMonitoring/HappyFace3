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
from GetXML import *
from GetXMLCache import *

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

	first_cat	 = ""

        for category in self.config.get('setup','categories').split(","):

             cat_title   = self.config.get(category,'cat_title')
             cat_type    = self.config.get(category,'cat_type')
             cat_algo    = self.config.get(category,'cat_algo')
             cat_content = ""

	     if first_cat == "":
		  first_cat = category

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

	# this should be used to get validated PHP hrefs (only cosmetics ;-) )
	output += '<?php ini_set("arg_separator.output","&amp;"); ?>'

	output += '<?php' + "\n"
	output += '    include("plot_timerange_select.php");' + "\n"
	output += '?>'

	# provides the logic for the timestamp definition
	output += TimeMachineLogic(histo_step).output
	
	# Deliver XML from cache if possible
	output += GetXMLCache(self.config, self.timestamp).output

	#######################################################

	# start with HTML output
	output += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">' + "\n"
	output += '<html xmlns="http://www.w3.org/1999/xhtml">' + "\n"
	
	# header
	output += ' <head>' + "\n"
	output += '  <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />' + "\n"
	output += '  <title>' + web_title + ' - The HappyFace Project</title>' + "\n"
	output += '  <script src="config/TabNavigation.js" type="text/javascript"></script>' + "\n"
	output += '  <link href="config/TabNavigation.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '  <script src="config/FastNavigation.js" type="text/javascript"></script>' + "\n"
	output += '  <link href="config/FastNavigation.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '  <script src="config/Sort.js" type="text/javascript"></script>' + "\n"
	output += '  <link href="config/Sort.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '  <link rel="shortcut icon" type="image/vnd.microsoft.icon" href="favicon.ico" />' + "\n"
        for css in self.cssList:
            output += '  <link href="'+css+'" rel="stylesheet" type="text/css" />' + "\n"
        
	output += ' </head>' + "\n"
	
	# body
	output += ' <body onload="javascript:HappyReload(300)">' + "\n"

	# logic to memorize selected tab on auto reload part 1
	output += """<?php
			$selectedTab = $selectedMod = "";
			$initialScroll = -1;

			if (isset($_GET["t"]) && $_GET["t"] != "") { $selectedTab = $_GET["t"]; } else { $selectedTab = '""" + first_cat + """'; }
			if (isset($_GET["m"]) && $_GET["m"] != "") { $selectedMod = $_GET["m"]; }
			if (isset($_GET["scroll"]) && $_GET["scroll"] != "") { $initialScroll = intval($_GET["scroll"]); }

			print('  <script type="text/javascript">\n');
			print('  <!--\n');
			print('  var selectedTab="'.$selectedTab.'";\n');
			print('  var selectedMod="'.$selectedMod.'";\n');
			print('  var initialScroll='.$initialScroll.';\n');
			print('  //-->\n');
			print('  </script>\n');
		?>"""
	output += '  <form id="ReloadForm" action="<?php echo $_SERVER["PHP_SELF"]; ?>" method="get">' + "\n"
	output += '   <div>' + "\n"
	output += '    <input type="hidden" id="ReloadTab" name="t" value="<?php echo htmlentities($selectedTab); ?>" />' + "\n"
	output += '    <input type="hidden" id="ReloadMod" name="m" value="<?php echo htmlentities($selectedMod); ?>" />' + "\n"
	output += '    <input type="hidden" id="ReloadExpand" name="expand" value="" />' + "\n"
	output += '    <input type="hidden" id="ReloadScroll" name="scroll" value="" />' + "\n"
	output += '    <input type="hidden" id="ReloadManualRefresh" name="refresh" value="" />' + "\n"
	output += '   </div>' + "\n"
	output += '  </form>' + "\n"

	# Great try/catch block to catch errors during database access
	output += '<?php try { ?>'

	# initiate the database
	output += '<?php' + "\n"
	output += '    /*** connect to SQLite database ***/' + "\n"
	output += '    $dbh = new PDO("sqlite:HappyFace.db");' + "\n"
	output += '?>'

	# SQL call routines for all active modules
	output += SQLCallRoutines(self.config).output

	# create an multi-array variable with all important information from the modules:
	# status, type, weight, category => used by the CategoryStatusLogic
	output += ModuleResultsArrayBuilder(self.config).output
	
	# provides general XML output (this is used for 
	output += GetXML(self.config).output

	# provides a function for the category status
	output += CategoryStatusLogic().output

	# provides a function for the category status symbol
	output += CategoryStatusSymbolLogic(self.theme).output

	# provides a function for the module status symbol
	output += ModuleStatusSymbolLogic(self.theme).output

	# time bar on the top of the website, input forms for time control
	output += TimeMachineController(logo_image).output

	# Catch any exception during installation and treat them as fatal
	# (for example database connection failure).
	output += '<?php } catch(Exception $e) {'
	output += '  print($e->getMessage() . "\n"); ?>'
	output += ' </body>' + "\n"
	output += '</html>' + "\n"
	output += '<?php exit(1); } ?>'

	# Disable Auto Reload on history view (only if there was no error,
	# always auto-reload on error so that we retry in).
	output += '<?php if(isset($historyview) && $historyview != "") { ?>'
	output += '  <script type="text/javascript">' + "\n"
	output += '  <!--' + "\n"
	output += '  AutoReload=false;' + "\n"
	output += '  //-->' + "\n"
	output += '  </script>' + "\n"
	output += '<?php } ?>'

	output += '  <div id="HappyPanels1" class="HappyPanels">' + "\n"

	# input navigation
	output += '   <ul class="HappyPanelsTabGroup">' + "\n"
	output += navigation
	output += '   </ul>' + "\n"

	# input content
	output += '   <div class="HappyPanelsContentGroup" id="HappyPanelsContentGroup">' + "\n"

	output += content
	output += '   </div>' + "\n"

	output += '  </div>' + "\n"

	# include layer to hide content when scrolling
	output += '  <div class="HappySolidLayer">' + "\n"
	output += '  </div>' + "\n"

	# some javascripts for website navigation
	output += '  <script type="text/javascript">' + "\n"
	output += '  <!--' + "\n"

	output += '  var reload_expands = new Array();' + "\n"
	output += '  function show_hide(me) {' + "\n"
	output += '    if (document.getElementById(me).style.display=="none") {' + "\n"
	output += '      reload_expands.push(me);' + "\n"
	output += '      document.getElementById(me).style.display="block";' + "\n"
	output += '    } else {' + "\n"
	output += '      for(var i = 0; i < reload_expands.length; ++i)' + "\n"
	output += '        if(reload_expands[i] == me)' + "\n"
	output += '          { reload_expands.splice(i,1); break; }' + "\n"
	output += '      document.getElementById(me).style.display="none";' + "\n"
	output += '    }' + "\n"
	output += '    ' + "\n"
	output += '    var joined = reload_expands.join(" ");' + "\n"
	output += '    document.getElementById("ReloadExpand").value = joined;' + "\n"
	output += '    document.getElementById("HistoReloadExpand1").value = joined;' + "\n"
	output += '    document.getElementById("HistoReloadExpand2").value = joined;' + "\n"
	output += '  }' + "\n"

	output += '  function show_hide_info(me, link) {' + "\n"
	output += '    show_hide(me);' + "\n"
	output += '    if(document.getElementById(me).style.display=="none")' + "\n"
	output += '      document.getElementById(link).innerHTML = "Show module information";' + "\n"
	output += '    else' + "\n"
	output += '      document.getElementById(link).innerHTML = "Hide module information";' + "\n"
	output += '  }' + "\n"

	# re-expand details infos on reload (do this before we do initial
	# scrolling, so that scrolling takes into account potentially
	# expanded regions).
	output += '  var expand = "<?php if(isset($_GET["expand"])) echo $_GET["expand"]; ?>";' + "\n"
	output += '  var expand_modules = expand.split(" ");' + "\n"
	output += '  for(var j = 0; j < expand_modules.length; ++j) {' + "\n"
	output += '    if(expand_modules[j].length > 0) {' + "\n"
	output += '      if(document.getElementById(expand_modules[j] + "_link"))' + "\n"
	output += '        show_hide_info(expand_modules[j], expand_modules[j] + "_link");' + "\n"
	output += '      else' + "\n"
	output += '        show_hide(expand_modules[j]);' + "\n"
	output += '    }' + "\n";
	output += '  }' + "\n";

	output += '  if(document.getElementById("ReloadManualRefresh").value == "")' + "\n"
	output += '    document.getElementById("ReloadManualRefresh").value = "1";' + "\n"
	output += '  else' + "\n"
	output += '    initialScroll = -1;' + "\n" # user refreshed manually: let the browser do a proper rescroll
	output += '  var HappyPanels1 = new HappyTab.Widget.HappyPanels("HappyPanels1",selectedTab,selectedMod,initialScroll);' + "\n"

	# Function to always open a form in a new tab or window (depending on the browser's settings)
	output += '  var plotCounter = 0;' + "\n"
	output += '  function submitFormToWindow(myForm) {' + "\n"
	output += "    window.open('about:blank','PlotWindow_' + plotCounter);" + "\n"
	output += "    myForm.target = 'PlotWindow_' + plotCounter;" + "\n"
	output += '    ++plotCounter;' + "\n"
	output += '    return true;' + "\n"
	output += '  }' + "\n"

	output += '  //-->' + "\n"
	output += '  </script>' + "\n"

	# end of html output
	output += ' </body>' + "\n"
	output += '</html>' + "\n"
	
	# close the database
	output += '<?php' + "\n"
	output += '    /*** close the database connection ***/' + "\n"
	output += '    $dbh = null;' + "\n"
	output += '?>'
	
	#######################################################
	
	return output
