import sys, os

from ModuleStatusSymbolLogic import *
from CategoryStatusLogic import *
from CategoryStatusSymbolLogic import *
from TimeMachineLogic import *
from TimeMachineController import *
from SQLCallRoutines import *
from ModuleResultsArrayBuilder import *

class FinalOutput(object):
    def __init__(self,config,theme,navigation,content):

	output = ""

	#######################################################
	################## create index.php ###################

	# initiate the database
	output += '<?php' + "\n"
	output += '    /*** connect to SQLite database ***/' + "\n"
	output += '    $dbh = new PDO("sqlite:HappyFace.db");' + "\n"
	output += '?>' + "\n"

	# provides the logic for the timestamp definition
	output += TimeMachineLogic().output
	
	# SQL call routines for all active modules
	output += SQLCallRoutines(config).output

	# create an multi-array variable with all important information from the modules:
	# status, type, weight, category => used by the CategoryStatusLogic
	output += ModuleResultsArrayBuilder().output
	
	# provides a function for the category status
	output += CategoryStatusLogic().output

	# provides a function for the category status symbol
	output += CategoryStatusSymbolLogic(theme).output

	# provides a function for the module status symbol
	output += ModuleStatusSymbolLogic(theme).output
	
	#######################################################

	# start with HTML output
	output += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">' + "\n"
	output += '<html xmlns="http://www.w3.org/1999/xhtml">' + "\n"
	
	# header
	output += '<head>' + "\n"
	#output += '<meta http-equiv="refresh" content="300" charset=utf-8" />' + "\n"
	output += '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />' + "\n"
	output += '<title>HappyFace v2.0a</title>' + "\n"
	output += '<script src="config/SpryTabbedPanels.js" type="text/javascript"></script>' + "\n"
	output += '<link href="config/SpryTabbedPanels.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '<script src="config/FastNavigation.js" type="text/javascript"></script>' + "\n"
	output += '<link href="config/FastNavigation.css" rel="stylesheet" type="text/css" />' + "\n"
	output += '</head>' + "\n"
	
	# body
	output += '<body>' + "\n"

	# time bar on the top of the website, input forms for time control
	output += TimeMachineController().output

	output += '<div id="TabbedPanels1" class="TabbedPanels">' + "\n"

	# input navigation
	output += '  <ul class="TabbedPanelsTabGroup">' + "\n"
	output += navigation
	output += '  </ul>' + "\n"

	# input content
	output += '  <div class="TabbedPanelsContentGroup">' + "\n"
	output += content + "\n"
	output += '  </div>' + "\n"

	output += '</div>' + "\n"

	# some javascripts for website navigation
	output += '<script type="text/javascript">' + "\n"
	output += '<!--' + "\n"
	output += 'var TabbedPanels1 = new Spry.Widget.TabbedPanels("TabbedPanels1");' + "\n"
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
	
	self.output = output
