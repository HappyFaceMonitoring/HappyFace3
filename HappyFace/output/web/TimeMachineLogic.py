import sys, os

class TimeMachineLogic(object):
	
    def __init__(self,histo_step):

	self.output = """<?php

	# check if stepping is set, otherwise use default
	if (isset($_GET["s"]) && $_GET["s"] != "") { $histo_step = $_GET["s"];}
	else { $histo_step = '""" + histo_step + """';}

	# function to reset the date/time input variables from previous views
	# used by the TimeMachineControler part
	function reset_time () {
	    $_GET["date"] = "";
	    $_GET["time"] = "";
	}

	# define current date / time from server time
	$server_time = $_SERVER['REQUEST_TIME'];

	# define empty error message string for wrong date / time input
	$time_error_message = "";

	# read $_GET["..."] variables (from previous views)
	if (isset($_GET["date"]) && isset($_GET["time"]) && $_GET["date"] != "" && $_GET["time"] != "") {

	    # variable to disable the auto reload on history view
	    $historyview = "true";
	
	    # build timestamp array
	    $ta = strtotime($_GET["date"] . " " . $_GET["time"]);

	    # check if date / time input has the right format
	    # if the input is ok, define new $timestamp variable for the SQL queries
	    if ($ta !== false && $ta !== -1) {
		$date_string = $_GET["date"];
		$time_string = $_GET["time"];
		$timestamp = $ta;

		# for future inputs, print error message and go back to current server time
		if ($timestamp - $server_time > 0) {
		    $time_error_message = '<td><span style="color:red;">I am not an oracle!!</span></td>';
		    $date_string = date("Y-m-d",$server_time);
		    $time_string = date("H:i",$server_time);
		    $timestamp = $server_time;
		}

		# if the input has a wrong format, take current servertime, define $error_message string for output
	    } else {
		$time_error_message = '<td><span style="color:red;">Wrong Date/Time Format!!</span></td>';
	    	$date_string = date("Y-m-d",$server_time);
		$time_string = date("H:i",$server_time);
		$timestamp = $server_time;
	    }
	}

	# if $_GET["..."] variables are empty (first call of the website)
	# take the current servertime as $timestamp variable for the SQL queries
	else {
	    $date_string = date("Y-m-d",$server_time);
	    $time_string = date("H:i",$server_time);
	    $timestamp = $server_time;
	}

	# if the chosen timestamp is "older" then a half hour (1800 seconds)
	# define a RED colored time string for the time bar output
	if ($server_time - $timestamp < 1800) {
	    $date_message = '<span>' . date("D, d. M Y", $timestamp) . '</span>';
	    $date_message_short = '<span>' . date("d. M Y", $timestamp) . '</span>';
	    $time_message = '<span>' . date("H:i", $timestamp) . '</span>';
	}
	else {
	    $date_message = '<span style="color:red;">' . date("D, d. M Y", $timestamp) . '</span>';
	    $date_message_short = '<span style="color:red;">' . date("d. M Y", $timestamp) . '</span>';
	    $time_message = '<span style="color:red;">' . date("H:i", $timestamp) . '</span>';
	}

	?>"""
