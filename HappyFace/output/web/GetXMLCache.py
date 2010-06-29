import os

class GetXMLCache(object):
	
    def __init__(self, config, timestamp):

	# Create cache directory if it does not exist already
	output_dir = config.get('setup', 'output_dir')
	cache_dir = output_dir + '/cache'

	if not os.path.exists(cache_dir):
	    os.makedirs(cache_dir)
	os.chmod(cache_dir, 0777)

        # If there is a cached file, and its timestamp is higher than the
	# timestamp of the latest update and the most recent version was
	# requested, then deliver it instead of doing a database query.
	self.output = """<?php

	if(isset($_GET['action']) && $_GET['action'] == 'getxml' && $timestamp >= """ + str(timestamp) + """)
	{
		$xml_cache_file = 'cache/HappyFace.xml';
		$stat_result = @stat($xml_cache_file);
		$xml_timestamp = """ + str(timestamp) + """;
		$xml_cache_uptodate = ($stat_result && $stat_result['mtime'] > $xml_timestamp);

		if($xml_cache_uptodate)
		{
			header('Content-Type: text/xml');
			$xml_data = file_get_contents($xml_cache_file);
			print $xml_data;
			exit;
		}
	}

	?>"""
