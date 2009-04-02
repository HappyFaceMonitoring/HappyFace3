#!/usr/bin/perl

# this script will be excecute every 10 minutes

use mod::plots::PlotsFairshare;
use mod::plots::PlotsDashboard;
use mod::plots::PlotsPhedexinDebug;
use mod::plots::PlotsPhedexout;

#=====================================================================

$unixtime		= time();
$humantime		= localtime($unixtime);
@ht_array		= split(/ +/,$humantime);
@time			= split(/:/,$ht_array[3]);

# $time[0] = hours, $time[1] = minutes
$hours		= $time[0];
$minutes	= $time[1];

#=====================================================================

# every time when script runs
mod::plots::PlotsFairshare->update();


# every hour: xx:10
if ($minutes == 10) {
	mod::plots::PlotsDashboard->update();
	mod::plots::PlotsPhedexinDebug->update();
	mod::plots::PlotsPhedexout->update();
}
