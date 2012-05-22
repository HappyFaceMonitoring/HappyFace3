<?php
debug("plot_common.php");
// Parse $_GET parameters into $timestamp0 and $timestamp1
// Also sets $timestamp_now and $timestamp_timerange to specify how the
// timerange was provided.

// First get end date
debug("First get end date");
if(isset($_GET['date1']) && isset($_GET['time1']) && $_GET['date1'] != '' && $_GET['time1'] != '')
{
	// End date given
	debug("date_parse");
	$ta1 = date_parse($_GET['date1'] . ' ' . $_GET['time1']);
	debug("mktime");
	$timestamp1 = mktime($ta1['hour'], $ta1['minute'], 0, $ta1['month'], $ta1['day'], $ta1['year']);
	$timestamp_now = false;
}

if(!isset($timestamp1))
{
	// If end date is not given use current time
	$timestamp1 = time();
	$timestamp_now = true;
}

// Get start date. There are two ways it can be provided; either explicitely
// via date0 and time0 or by a timerange.
debug("Get start date");
if(isset($_GET['date0']) && isset($_GET['time0']) && $_GET['date0'] != '' && $_GET['time0'] != '')
{
	debug("case 1");
	$ta0 = date_parse($_GET['date0'] . ' ' . $_GET['time0']);
	debug("case 1, mktime");
	$timestamp0 = mktime($ta0['hour'], $ta0['minute'], 0, $ta0['month'], $ta0['day'], $ta0['year']);
	$timestamp_timerange = false;
}
else if(isset($_GET['timerange']))
{
	debug("case 2");
	$str = $_GET['timerange'];
	debug("loop over string for int-check");
	for($i = 0; $i < strlen($str); ++$i)
		if(!ctype_digit($str[$i]))
			break;
	debug("strange numeric conversion");
	$num = intval(substr($str, 0, $i));
	debug("case-statement");
	switch($str[$i])
	{
	case 'm': $secs = $num *           60; break;
	case 'h': $secs = $num *        60*60; break;
	case 'd': $secs = $num *     24*60*60; break;
	case 'w': $secs = $num *   7*24*60*60; break;
	case 'y': $secs = $num * 365*24*60*60; break; // TODO: take into account leap years
	}

	if(isset($secs)) $timestamp0 = $timestamp1 - $secs;
	$timestamp_timerange = true;
}

if(!isset($timestamp0))
{
	// 48h timerange if nothing given
	$timestamp0 = $timestamp1 - 48*60*60;
	$timestamp_timerange = true;
}
debug("end: plot_common.php");
?>
