import sys, os

class SQLCallRoutines(object):
	
    def __init__(self,config):

	self.output = ""
	
	self.output += '<?php' + "\n"

	for category in config.get('setup','categories').split(","):

	    for module in config.get(category,'modules').split(","):

		# insert all Module SQL Command Strings in one array $sql_command_strings
		self.output += '  $sql_command_strings["' + module + '"] = "SELECT * FROM ' + module + "_table" + ' WHERE timestamp <= $timestamp ORDER BY timestamp DESC LIMIT 1";' + "\n"
		
	self.output += '?>'
