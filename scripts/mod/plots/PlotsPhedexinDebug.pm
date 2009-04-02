package mod::plots::PlotsPhedexinDebug;

use mod::DataFactory;

sub update {

	open(PHEDEXIN_RESULTS, "../results/phedexin_results.txt");
	while(<PHEDEXIN_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(PHEDEXIN_RESULTS);

	if ($data{'facevalue'} != -1) {
		$transfer_quality = $data{'transfer_quality'}*100;

		my $tm = time;
		if (($tm - $data{'unixtime'}) < 1800) {
		  system("rrdtool update ../plots/phedexin.rrd $tm:$transfer_quality");

		  system('rrdtool graph -s -192h ../plots/phedexin_days.png  --vertical-label % DEF:phedexin=../plots/phedexin.rrd:phedexin:AVERAGE LINE2:phedexin#00FF00:"fraction of succeeded transfers"');
		  system('rrdtool graph -s -120d ../plots/phedexin_months.png  --vertical-label % DEF:phedexin=../plots/phedexin.rrd:phedexin:AVERAGE LINE2:phedexin#00FF00:"fraction of succeeded transfers"');
		}
	}
	
}

1;
