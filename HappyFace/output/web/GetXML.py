import sys, os

class GetXML(object):
	
    def __init__(self, config):

	declare_cat_titles = '$cat_titles = array(';
	declare_cat_types = '$cat_types = array(';
	declare_cat_ids = '$cat_ids = array(';

	cat_id = 0
	first_iteration = True
        for category in config.get('setup','categories').split(","):
	    cat_title = config.get(category,'cat_title')
	    cat_type  = config.get(category,'cat_type')

	    if not first_iteration:
	        declare_cat_titles += ", ";
	        declare_cat_types += ", ";
	        declare_cat_ids += ", ";
	    else:
	        first_iteration = False

	    declare_cat_titles += "'" + category + "' => '" + cat_title + "'"
	    declare_cat_types  += "'" + category + "' => '" + cat_type  + "'"
	    declare_cat_ids    += "'" + category + "' => '" + str(cat_id) + "'"
	    cat_id += 1

	declare_cat_titles += ');'
	declare_cat_types += ');'
	declare_cat_ids += ');'

	self.output = """<?php

	function curPageURL()
	{
	    $pageURL = 'http';
	    if ($_SERVER["HTTPS"] == "on") {$pageURL .= "s";}
	        $pageURL .= "://";
	    if ($_SERVER["SERVER_PORT"] != "80") {
	        $pageURL .= $_SERVER["SERVER_NAME"].":".$_SERVER["SERVER_PORT"].$_SERVER["REQUEST_URI"];
	    } else {
	        $pageURL .= $_SERVER["SERVER_NAME"].$_SERVER["SCRIPT_NAME"];
	    }

	    return $pageURL;
	}

	function getCatStatusXML($myModuleResultsArray)
	{
	    $pageURL = curPageURL();

	    """ + declare_cat_titles + "\n" + declare_cat_types + "\n" + declare_cat_ids + """

            # Get different categories with their type from the result Matrix
	    $cat_modules = array();
	    $cat_info = array();
	    foreach ($myModuleResultsArray as $module=>$data) {
	        $date = date('Y-m-d', $data['timestamp']);
		$time = date('H:i', $data['timestamp']);
		$cat_id = $cat_ids[$data['category']];

	        if(!array_key_exists($data['category'], $cat_info)) {
	            $cat_modules[$data['category']] = '';
	            $cat_info[$data['category']]['name'] = $data['category'];
	            $cat_info[$data['category']]['title'] = $cat_titles[$data['category']];
		    $cat_info[$data['category']]['status'] = $data['status'];
		    $cat_info[$data['category']]['type'] = $cat_types[$data['category']];
		    $cat_info[$data['category']]['link'] = "$pageURL?date=$date&amp;time=$time&amp;t=$cat_id";
		}

		$cat_modules[$data['category']] .= "  <module>\n";
		$cat_modules[$data['category']] .= "   <name>$module</name>\n";
		$cat_modules[$data['category']] .= "   <title>" . htmlentities($data['mod_title']) . "</title>\n";
		$cat_modules[$data['category']] .= "   <type>" . $data['mod_type'] . "</type>\n";
		$cat_modules[$data['category']] .= "   <status>" . $data['status'] . "</status>\n";
		$cat_modules[$data['category']] .= "   <time>$date $time</time>\n";
		$cat_modules[$data['category']] .= "   <link>$pageURL?date=$date&amp;time=$time&amp;t=$cat_id&amp;m=$module</link>\n";
		$cat_modules[$data['category']] .= "  </module>\n";

	        if($data['status'] < $cat_info[$data['category']]['status'])
	            $cat_info[$data['category']]['status'] = $data['status'];

	        if($data['mode_type'] == 'rated' && $cat_info[$data['category']]['type'] != 'rated')
	            $cat_info[$data['category']]['type'] = 'rated';
	    }

            echo '<happyface>' . "\n";
	    foreach ($cat_info as $category=>$info) {
	        $status = '';
		if($info['type'] == 'rated')
		    $status = 'status="' . $info['status'] . '" ';

	        echo ' <category name="' . $category . '" title="' . htmlentities($info['title']) . '" ' . $status . 'type="' . $info['type'] . '" link="' . $info['link'] . '">' . "\n";
	        echo $cat_modules[$category];
		echo ' </category>' . "\n";
	    }

	    echo '</happyface>';
	    exit;
	}

	if ($_REQUEST['action']=="getxml")
		getCatStatusXML($ModuleResultsArray);

	?>"""
