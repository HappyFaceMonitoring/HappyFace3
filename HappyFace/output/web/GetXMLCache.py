import os

class GetXMLCache(object):
	
    def __init__(self, config, timestamp):

	# Create cache directory if it does not exist already
	output_dir = config.get('setup', 'output_dir')
	cache_dir = output_dir + '/cache'

	if not os.path.exists(cache_dir):
	    os.makedirs(cache_dir)
            os.chmod(cache_dir, 0777)

	# Generate a custom ID which represents the state of which modules
	# are accessible for the current user. This is used to access the
	# cache file for this configuration of accessible modules.
	self.output = """<?php

	$custom_id = 'c';
	"""
	for category in config.get('setup', 'categories').split(","):
	    for module in config.get(category, 'modules').split(","):
		if module == "": continue

		self.output += """
	if(isModuleAccessible('""" + module + """', '""" + category + """'))
		$custom_id .= '1';
	else
		$custom_id .= '0';"""

        # If there is a cached file, and its timestamp is higher than the
	# timestamp of the latest update and the most recent version was
	# requested, then deliver it instead of doing a database query.
	self.output += """
	$xml_output = isset($_GET['action']) && $_GET['action'] == 'getxml';
	$xml_cache_file = "cache/HappyFace_$custom_id.xml";
	if($xml_output && $timestamp >= """ + str(timestamp) + """)
	{
		// Deliver file from cache
		$xml_file_handle = fopen($xml_cache_file, 'r');
		if($xml_file_handle && flock($xml_file_handle, LOCK_SH))
		{
			$stat_result = fstat($xml_file_handle);
			$xml_timestamp = """ + str(timestamp) + """;
			$xml_cache_uptodate = ($stat_result && $stat_result['mtime'] > $xml_timestamp);

			if($xml_cache_uptodate)
			{
				header('Content-Type: text/xml');
//				$xml_data = stream_get_contents($xml_file_handle);
//				print $xml_data;
				fpassthru($xml_file_handle);
			}

			flock($xml_file_handle, LOCK_UN);
			fclose($xml_file_handle);

			if($xml_cache_uptodate)
				exit;
		}
		else
		{
			$xml_cache_uptodate = false;
		}
	}

	?>"""
