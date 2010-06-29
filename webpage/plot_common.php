<?php

// Parse $_GET parameters into $timestamp0 and $timestamp1

// First get end date
if(isset($_GET['date1']) && isset($_GET['time1']) && $_GET['date1'] != '' && $_GET['time1'] != '')
{
	// End date given
	$ta1 = date_parse($_GET['date1'] . ' ' . $_GET['time1']);
	$timestamp1 = mktime($ta1['hour'], $ta1['minute'], 0, $ta1['month'], $ta1['day'], $ta1['year']);
}

if(!isset($timestamp1))
{
	// If end date is not given use current time
	$timestamp1 = time();
}

// Get start date. There are two ways it can be provided; either explicitely
// via date0 and time0 or by a timerange.
if(isset($_GET['date0']) && isset($_GET['time0']) && $_GET['date0'] != '' && $_GET['time0'] != '')
{
	$ta0 = date_parse($_GET['date0'] . ' ' . $_GET['time0']);
	$timestamp0 = mktime($ta0['hour'], $ta0['minute'], 0, $ta0['month'], $ta0['day'], $ta0['year']);
}
else if(isset($_GET['timerange']))
{
	$str = $_GET['timerange'];
	for($i = 0; $i < strlen($str); ++$i)
		if(!ctype_digit($str[$i]))
			break;

	$num = intval(substr($str, 0, $i));
	switch($str[$i])
	{
	case 'm': $secs = $num *           60; break;
	case 'h': $secs = $num *        60*60; break;
	case 'd': $secs = $num *     24*60*60; break;
	case 'w': $secs = $num *   7*24*60*60; break;
	case 'y': $secs = $num * 365*24*60*60; break; // TODO: take into account leap years
	}

	if(isset($secs)) $timestamp0 = $timestamp1 - $secs;
}

if(!isset($timestamp0))
{
	// 48h timerange if nothing given
	$timestamp0 = $timestamp1 - 48*60*60;
}

?>
