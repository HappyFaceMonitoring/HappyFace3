package mod::plots::PlotsDashboard;

use mod::DataFactory;

sub update {

	# readout the values from the file 'results/dashboard_results.txt'
	open(DASHBOARD_RESULTS, "../results/dashboard_results.txt");
	while(<DASHBOARD_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(DASHBOARD_RESULTS);

	if ($data{'facevalue'} != -1) {
	  $succeeded	= $data{"app_succeeded"};
	  $failed		= $data{"app_failed"};
	  $unknown	= $data{"app_unknown"};
	
	  my $tm = time;
	  if (($tm - $data{'unixtime'}) < 1800) {

	    $status = system("rrdtool update ../plots/dashboard.rrd $tm:$succeeded:$failed:$unknown");

	    $status = system('rrdtool graph -s -192h ../plots/dashboard_days.png	DEF:succeeded=../plots/dashboard.rrd:succeeded:AVERAGE LINE2:succeeded#00FF00:"succeeded jobs" DEF:failed=../plots/dashboard.rrd:failed:AVERAGE LINE2:failed#FF0000:"failed jobs" DEF:unknown=../plots/dashboard.rrd:unknown:AVERAGE LINE2:unknown#0000FF:"unknown jobs"');
	    $status = system('rrdtool graph -s -120d ../plots/dashboard_months.png 	DEF:succeeded=../plots/dashboard.rrd:succeeded:AVERAGE LINE2:succeeded#00FF00:"succeeded jobs" DEF:failed=../plots/dashboard.rrd:failed:AVERAGE LINE2:failed#FF0000:"failed jobs" DEF:unknown=../plots/dashboard.rrd:unknown:AVERAGE LINE2:unknown#0000FF:"unknown jobs"');
	  }
	}

}

1;
