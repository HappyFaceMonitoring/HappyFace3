package mod::prod::FaceQstat;

#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;

	#load to plots from the gridka monitoring site
	system('wget --output-document="../images/cms_efficiency1.png" "http://grid.fzk.de/monitoring/rrd/png/cpuratio_cms_day.png"');
	system('wget --output-document="../images/cms_efficiency2.png" "http://grid.fzk.de/monitoring/incoming_results/cpu-wall/paw-cms.png"');

	my $dataQstat = mod::DataFactory->new("Qstat", %{$self});
	# $dataGridKa
	my %summary;

	# check if data is available
	if ($dataQstat->{'jobsummary'}) {

		$facevalue = 0;

		my $all_ratio10	= $dataQstat->{'jobsummary'}{'all'}{'ratio10'};
		my $all_run	= $dataQstat->{'jobsummary'}{'all'}{'running'};
		my $all_total	= $dataQstat->{'jobsummary'}{'all'}{'total'};

#		my $cms_ratio10	= $dataQstat->{'jobsummary'}{'cms'}{'ratio10'};
#		my $cms_run	= $dataQstat->{'jobsummary'}{'cms'}{'running'};
#		my $cms_total	= $dataQstat->{'jobsummary'}{'cms'}{'total'};

#		my $cmsprd_ratio10	= $dataQstat->{'jobsummary'}{'cmsprd'}{'ratio10'};
#		my $cmsprd_run		= $dataQstat->{'jobsummary'}{'cmsprd'}{'running'};
#		my $cmsprd_total	= $dataQstat->{'jobsummary'}{'cmsprd'}{'total'};

		my $cms_ratio10 = 0;
		my $cms_run = 0;
		my $cms_total = 0;
		my $cms_queue = 0;
		my $cms_waiting = 0;

		foreach my $jobid ( keys %{$dataQstat->{'jobDetails'}{'job'}} ) {
			$user = $dataQstat->{'jobDetails'}{'job'}{$jobid}{'user'};
#			$cpuwalltimeratio = $dataQstat->{'jobDetails'}{'job'}{$jobid}{'cpupercent'};
			$cpuwalltimeratio = $dataQstat->{'jobDetails'}{'job'}{$jobid}{'cpuwallratio'};
			$job_state = $dataQstat->{'jobDetails'}{'job'}{$jobid}{'job_state'};

			if (!($summary->{$user})) {
				$summary->{$user}{'total'} = 0;
				$summary->{$user}{'waiting'} = 0;
				$summary->{$user}{'queue'} = 0;
				$summary->{$user}{'ratio10'} = 0;
				$summary->{$user}{'ratio30'} = 0;
				$summary->{$user}{'ratio80'} = 0;
				$summary->{$user}{'ratio100'} = 0;
			}

			$summary->{$user}{'total'}++;
			$cms_total++;

			if ($job_state eq "Q") { $summary->{$user}{'queue'}++; $cms_queue++; }
			elsif ($job_state eq "W") { $summary->{$user}{'waiting'}++; $cms_waiting++; }
			elsif ($job_state eq "R") {
				if ($cpuwalltimeratio <= 10) { $summary->{$user}{'ratio10'}++; $cms_ratio10++; }
				if ($cpuwalltimeratio > 10 && $cpuwalltimeratio <= 30) { $summary->{$user}{'ratio30'}++; }
				if ($cpuwalltimeratio > 30 && $cpuwalltimeratio <= 80) { $summary->{$user}{'ratio80'}++; }
				if ($cpuwalltimeratio > 80 ) { $summary->{$user}{'ratio100'}++; }
				$cms_run++;
			}
		}


		if ($summary->{'cmsprd'}) {
			$cmsprd_ratio10	= $summary->{'cmsprd'}{'ratio10'};
			$cmsprd_total	= $summary->{'cmsprd'}{'total'};
			$cmsprd_run	= $summary->{'cmsprd'}{'ratio100'} + $summary->{'cmsprd'}{'ratio80'} + $summary->{'cmsprd'}{'ratio30'} + $summary->{'cmsprd'}{'ratio10'};
			$cmsprd_queue	= $summary->{'cmsprd'}{'queue'};
			$cmsprd_waiting	= $summary->{'cmsprd'}{'waiting'};
		} else {
			$cmsprd_ratio10	= 0;
			$cmsprd_run	= 0;
			$cmsprd_total	= 0;
			$cmsprd_queue	= 0;
			$cmsprd_waiting	= 0;
		}


		open (QSTAT_JOBS, ">../results/qstat_jobs.txt");
		foreach my $key ( keys %{$summary} ) {
			print QSTAT_JOBS $key,"\t",$summary->{$key}{'total'},"\t",$summary->{$key}{'queue'},"\t",$summary->{$key}{'waiting'},"\t",$summary->{$key}{'ratio10'},"\t",$summary->{$key}{'ratio30'},"\t",$summary->{$key}{'ratio80'},"\t",$summary->{$key}{'ratio100'},"\n";
		}
		close (QSTAT_JOBS);
		# run the python script FaceQstatPlot.py to create the Plot
		system("./mod/prod/FaceQstatPlot.py");

		# Berechnung des Laufzeit des qstat befehls
		my $qstat_start = $dataQstat->{'GlobalInfo'}{'qstatStart'};
		my $qstat_end = $dataQstat->{'GlobalInfo'}{'qstatEnd'};

		my @qstat_start_array = split(/ /,$qstat_start);
		my @qstat_end_array = split(/ /,$qstat_end);

		my ($start_hours, $start_min, $start_sec) = split(/:/,$qstat_start_array[4]);
		my ($end_hours, $end_min, $end_sec) = split(/:/,$qstat_end_array[4]);

		if ($start_hours <= $end_hours) {
			$qstat_run = ($end_hours * 3600 + $end_min * 60 + $end_sec) - ($start_hours * 3600 + $start_min*60 + $start_sec);
		} else {
			$qstat_run = 24*3600 - ($start_hours * 3600 + $start_min*60 + $start_sec) + ($end_hours * 3600 + $end_min * 60 + $end_sec);
		}

		my $unixtime = time;

		open(QSTAT_RESULTS, ">../results/qstat_results.txt");

		print QSTAT_RESULTS "cms_ratio10\t=\t",$cms_ratio10,"\n";
		print QSTAT_RESULTS "cms_run\t=\t",$cms_run,"\n";
		print QSTAT_RESULTS "cms_total\t=\t",$cms_total,"\n";
		print QSTAT_RESULTS "cms_queue\t=\t",$cms_queue,"\n";
		print QSTAT_RESULTS "cms_waiting\t=\t",$cms_waiting,"\n";
		

		print QSTAT_RESULTS "cmsprd_ratio10\t=\t",$cmsprd_ratio10,"\n";
		print QSTAT_RESULTS "cmsprd_run\t=\t",$cmsprd_run,"\n";
		print QSTAT_RESULTS "cmsprd_total\t=\t",$cmsprd_total,"\n";
		print QSTAT_RESULTS "cmsprd_queue\t=\t",$cmsprd_queue,"\n";
		print QSTAT_RESULTS "cmsprd_waiting\t=\t",$cmsprd_waiting,"\n";

		print QSTAT_RESULTS "all_ratio10\t=\t",$all_ratio10,"\n";
		print QSTAT_RESULTS "all_run\t=\t",$all_run,"\n";
		print QSTAT_RESULTS "all_total\t=\t",$all_total,"\n";

		print QSTAT_RESULTS "qstat_start\t=\t",$qstat_start,"\n";
		print QSTAT_RESULTS "qstat_end\t=\t",$qstat_end,"\n";
		print QSTAT_RESULTS "qstat_run\t=\t",$qstat_run,"\n";

		print QSTAT_RESULTS "facevalue\t=\t",$facevalue,"\n";
		print QSTAT_RESULTS "unixtime\t=\t",$unixtime,"\n";


		close(QSTAT_RESULTS);
		
	} else {
		
		my $unixtime = time;

		open(QSTAT_RESULTS, ">../results/qstat_results.txt");
		print QSTAT_RESULTS "facevalue\t=\t",$facevalue,"\n";
		print QSTAT_RESULTS "unixtime\t=\t",$unixtime,"\n";
		close(QSTAT_RESULTS);		
	}

	$self->{'facevalue'} = $facevalue;
	return $facevalue;
	
}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	# readout the values from the file 'results/dashboard_results.txt'
	open(QSTAT_RESULTS, "../results/qstat_results.txt");
	while(<QSTAT_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(QSTAT_RESULTS);

	open(QSTAT_HTML, ">../HTMLFragments/Qstat_HTML");

if ($data{'facevalue'} != -1) {

	print QSTAT_HTML '	<table border="0">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td>',"\n";

	my $facevalue = $data{'facevalue'};
	
	if ($facevalue == 0) 	{ print QSTAT_HTML '<img src="images/4_small.png" />',"\n"; }
	elsif ($facevalue == 1) { print QSTAT_HTML '<img src="images/3_small.png" />',"\n"; }
	elsif ($facevalue == 2) { print QSTAT_HTML '<img src="images/1_small.png" />',"\n"; }

	print QSTAT_HTML '			</td>',"\n";
	print QSTAT_HTML '			<td><h3>Qstat Test</h3></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";




	print QSTAT_HTML '	<table width="860" border="0">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>all jobs</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";

	print QSTAT_HTML '	<table width="860" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>total</strong></td>',"\n";
	print QSTAT_HTML '			<td width="200"><div align="center"><strong>',$data{"all_total"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>running</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"all_run"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>efficiency under 10 %</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong><font color="#FF0000">',$data{"all_ratio10"},'</font></strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";


	print QSTAT_HTML '	<table width="860" border="0">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>cms jobs</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";

	print QSTAT_HTML '	<table width="860" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>total</strong></td>',"\n";
	print QSTAT_HTML '			<td width="200"><div align="center"><strong>',$data{"cms_total"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>running</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cms_run"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>queue</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cms_queue"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>waiting</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cms_waiting"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>efficiency under 10 %</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong><font color="#FF0000">',$data{"cms_ratio10"},'</font></strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";

	print QSTAT_HTML '	<table width="860" border="0">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>cmsprd jobs</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";


	print QSTAT_HTML '	<table width="860" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>total</strong></td>',"\n";
	print QSTAT_HTML '			<td width="200"><div align="center"><strong>',$data{"cmsprd_total"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>running</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cmsprd_run"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>queue</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cmsprd_queue"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>waiting</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>',$data{"cmsprd_waiting"},'</strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><strong>cmsprd jobs efficiency under 10 %</strong></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong><font color="#FF0000">',$data{"cmsprd_ratio10"},'</font></strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";
	
	print QSTAT_HTML '	<br>',"\n";


	print QSTAT_HTML '	<table width="860" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td>Qstat Start Time</td>',"\n";
	print QSTAT_HTML '			<td width="200"><div align="center">',$data{"qstat_start"},'</div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td>Qstat Running Time (sec)</td>',"\n";
	print QSTAT_HTML '			<td><div align="center">',$data{"qstat_run"},'</div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";

	print QSTAT_HTML '	<br>',"\n";


	print QSTAT_HTML '	<table width="860" height="250" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><img src="images/cms_efficiency1.png" /></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><img src="images/cms_efficiency2.png" /></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";


	print QSTAT_HTML '	<table width="860" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><img src="plots/qstat_jobs.png" /></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";
	print QSTAT_HTML '	</table>',"\n";
	print QSTAT_HTML '	<br>',"\n";


	# qstat job statistics
	print QSTAT_HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'qstat\');\"></form>","\n";
	print QSTAT_HTML '	<div id="qstat" style="display:none;">',"\n";

	print QSTAT_HTML '	<table width="1000" border="1">',"\n";
	print QSTAT_HTML '		<tr>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>user</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>total jobs</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>queue</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>waiting</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>eff. > 80%</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>30% < eff. < 80%</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong>10% < eff. < 30%</strong></div></td>',"\n";
	print QSTAT_HTML '			<td><div align="center"><strong><font color="#FF0000">critical eff. < 10% </font></strong></div></td>',"\n";
	print QSTAT_HTML '		</tr>',"\n";


	open(QSTAT_JOBS, "../results/qstat_jobs.txt");
	while(<QSTAT_JOBS>) {
		my ($user, $total, $queue, $waiting, $ratio10, $ratio30, $ratio80, $ratio100) = split(/\t/);
		print QSTAT_HTML '	<tr>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$user,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$total,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$queue,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$waiting,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$ratio100,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$ratio80,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center">',$ratio30,'</div></td>',"\n";
		print QSTAT_HTML '		<td><div align="center"><font color="#FF0000">',$ratio10,'</font></div></td>',"\n";
		print QSTAT_HTML '	</tr>',"\n";
	}
	close(QSTAT_JOBS);

	print QSTAT_HTML '	</table>',"\n";

	print QSTAT_HTML '	</div>',"\n";
	print QSTAT_HTML '	<br>',"\n";



	print QSTAT_HTML '	<br>',"\n";
	print QSTAT_HTML '	<hr>',"\n";
}

	close(QSTAT_HTML);
}

#---------------------------------------------------------------------------------

sub new {

	$self = shift;
	my %options = %{shift @_};
	my $face = {%options};

	bless $face, $self;
	return $face;

}

1;
