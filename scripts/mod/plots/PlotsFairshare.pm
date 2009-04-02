package mod::plots::PlotsFairshare;

use mod::DataFactory;

sub update {

	open(FAIRSHARE_RESULTS, "../results/fairshare_results.txt");
	while(<FAIRSHARE_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(FAIRSHARE_RESULTS);

	if ($data{'facevalue'} != -1) {
	  $nominal_fairshare = $data{'nominal_fairshare'};

	  # has to be load here, because the change period is 10 min, main script 15 min
	  $dataGridkajobs = mod::DataFactory->new("Gridkajobs");

	  my $run_total_frac = sprintf("%.2f", $dataGridkajobs->{"cms"}{"running"} / $dataGridkajobs->{"sum"}{"running"} * 100);
	  my $run_queued_frac = sprintf("%.2f", $dataGridkajobs->{"cms"}{"running"} / $dataGridkajobs->{"cms"}{"all"} * 100);

	  my $tm = time;
	  if (($tm - $data{'unixtime'}) < 1800) {
	
	    $status = system("rrdtool update ../plots/fairshare.rrd $tm:$run_queued_frac:$run_total_frac");

	    $status = system('rrdtool graph -s -192h ../plots/fairshare_days.png  	--vertical-label % DEF:run_queued=../plots/fairshare.rrd:run_queued:AVERAGE LINE2:run_queued#00FF00:"run_queued_fraction" DEF:run_total=../plots/fairshare.rrd:run_total:AVERAGE LINE2:run_total#0000FF:"run_total_fraction" HRULE:'.$nominal_fairshare.'#FF0000:"nominal fairshare"');
	    $status = system('rrdtool graph -s -120d ../plots/fairshare_months.png  	--vertical-label % DEF:run_queued=../plots/fairshare.rrd:run_queued:AVERAGE LINE2:run_queued#00FF00:"run_queued_fraction" DEF:run_total=../plots/fairshare.rrd:run_total:AVERAGE LINE2:run_total#0000FF:"run_total_fraction" HRULE:'.$nominal_fairshare.'#FF0000:"nominal fairshare"');
	  }
	}
}

1;
