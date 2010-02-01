import sys, os

class GetText4Firefox(object):
	
    def __init__(self):

	self.output = """<?php

	function getModStatusText($status,$mod_type)
	{
	    if ($mod_type == "plots") {
	        if ($status == 1) { return "available" ; }
	        else if ($status == -1) { return "unavailable" ; }
	    }
	    else if ($mod_type == "rated" || $mod_type == "unrated") {
	        if ($status > 0.66 && $status <= 1.0) { return "happy"; }
	        else if ($status > 0.33 && $status <= 0.66) { return "neutral"; }
	        else if ($status >= 0.0 && $status <= 0.33) { return "unhappy"; }
	        else if ($status == -1) { return "noinfo"; }
	    }
	}

	function getCatStatusText($myModuleResultsArray)
	{
            # Get different categories with their type from the result Matrix
	    $mycategory = array ();
	    foreach ($myModuleResultsArray as $module=>$data) {
	        if(array_key_exists($data["category"],$mycategory)){ #append sucategory
	            $mycategory[$data["category"]]=$mycategory[$data["category"]].";".$module.",".date("Y-m-d",$data["timestamp"])." ".date("H:i",$data["timestamp"]).",".getModStatusText($data["status"],$data["mod_type"]);
	            if($data["status"]<$mystatus[$data["category"]]) {
	                $mystatus[$data["category"]]=$data["status"];
	            }
	            if($data["mod_type"] == "rated" && $mytype[$data["category"]] != "rated" ) {
	                $mytype[$data["category"]]= "rated";
	            }
	        }
	        else { #new category
	            $mycategory[$data["category"]]=$module.",".date("Y-m-d",$data["timestamp"])." ".date("H:i",$data["timestamp"]).",".getModStatusText($data["status"],$data["mod_type"]);
	            $mytype[$data["category"]]=$data["mod_type"];
	            $mystatus[$data["category"]]=$data["status"];
	        }
	    }
	    # Loop over categories to get the status their status
	    foreach ($mycategory as $categoryname=>$categoryvalue) {
	        echo getModStatusText($mystatus[$categoryname],$mytype[$categoryname]).";".$categoryvalue."\n";
	    }
	    exit;
	}

	if ($_REQUEST['action']=="gettext") getCatStatusText($ModuleResultsArray);

	?>"""
