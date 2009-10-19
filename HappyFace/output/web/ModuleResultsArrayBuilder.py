import sys, os

class ModuleResultsArrayBuilder(object):
	
    def __init__(self):

	self.output = """
	<?php
	# $sql_command_strings[] are available from the SQLCallRoutines
	foreach ($sql_command_strings as $module=>$sql_command) {
	    $sql_queries[$module] = $dbh->query($sql_command);
	}

	# create a multi-array $ModuleResultsArray with the results of the modules
	# will be used by the CategoryStatusLogic (called by CategoryNavigationTab)
	foreach ($sql_queries as $module=>$query) {
	    foreach ($query as $data) {
		$ModuleResultsArray[$module]["module"]		= $data["module"];
		$ModuleResultsArray[$module]["mod_title"]	= $data["mod_title"];
		$ModuleResultsArray[$module]["status"]		= $data["status"];
		$ModuleResultsArray[$module]["mod_type"]	= $data["mod_type"];
		$ModuleResultsArray[$module]["weight"]		= $data["weight"];
		$ModuleResultsArray[$module]["category"]	= $data["category"];
                $ModuleResultsArray[$module]["timestamp"]	= $data["timestamp"];
	    }
	}
	?>
	"""
