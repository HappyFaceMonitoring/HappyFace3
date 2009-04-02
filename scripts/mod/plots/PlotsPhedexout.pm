package mod::plots::PlotsPhedexout;

use mod::DataFactory;

sub update {

	open(PHEDEXOUT_RESULTS, "../results/phedexout_results.txt");
	while(<PHEDEXOUT_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(PHEDEXOUT_RESULTS);


	if ($data{'facevalue'} != -1) {
		$transfer_quality = $data{'transfer_quality'}*100;

		my $tm = time;
		if (($tm - $data{'unixtime'}) < 1800) {

		  system("rrdtool update ../plots/phedexout.rrd $tm:$transfer_quality");

		  system('rrdtool graph -s -192h ../plots/phedexout_days.png  --vertical-label % DEF:phedexout=../plots/phedexout.rrd:phedexout:AVERAGE LINE2:phedexout#00FF00:"Transfer Quality" HRULE:66#FF0000:"limit for failed status"');
		  system('rrdtool graph -s -120d ../plots/phedexout_months.png  --vertical-label % DEF:phedexout=../plots/phedexout.rrd:phedexout:AVERAGE LINE2:phedexout#00FF00:"Transfer Quality" HRULE:66#FF0000:"limit for failed status"');
		}
	}
	
}

1;
