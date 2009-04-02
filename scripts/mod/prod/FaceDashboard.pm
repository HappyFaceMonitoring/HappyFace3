package mod::prod::FaceDashboard;

#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;

	$site = $self->{'site'};
	$activity = $self->{'activity'};

	$dataDashboard = mod::DataFactory->new("Dashboard");
	$plot_url = mod::DataFactory->new("DashboardPlot");

	# check if data is available
	if ($dataDashboard->{'summaries'}{'item'}{$activity}) {

		my $date1		= $dataDashboard->{'meta'}{'date1'}{'item'};
		my $date2		= $dataDashboard->{'meta'}{'date2'}{'item'};
		$date1			=~ s/\ /%20/; # change the format for the url
		$date2			=~ s/\ /%20/; # change the format for the url

		my $terminated		= $dataDashboard->{'summaries'}{'item'}{$activity}{'terminated'};
		my $app_succeeded	= $dataDashboard->{'summaries'}{'item'}{$activity}{'app-succeeded'};
		my $app_failed		= $dataDashboard->{'summaries'}{'item'}{$activity}{'app-failed'};
		my $app_unknown		= $dataDashboard->{'summaries'}{'item'}{$activity}{'app-unknown'};

		if ($app_failed < $app_succeeded) { $facevalue = 0; }
		else { $facevalue = 1; }

		# if there are failed jobs, try to make stats of exitcodes
		if ($app_failed != 0) {
			my $count = 1 + $app_failed;

			$url = "http://lxarda09.cern.ch/dashboard/request.py/jobstatus?&date1=$date1&date2=$date2&sortby=activity&site=FZK-LCG2%20(Karlsruhe,%20Germany)&nbars=20&activity=$activity&status=failed&count=$app_failed&len=$count";
			$filename = "cms_dashboard_failed_status.xml";

			my $dataFailedStatus = mod::DataFactory->new("XMLParser", %options	= (
											"url"		=> $url,
											"filename"	=> $filename,
											));

			my %stats;
			my $exitcode;

			if ($dataFailedStatus->{'jobs'}{'item'} =~ /^ARRAY/) {
				$failedjobs_number = scalar(@{$dataFailedStatus->{'jobs'}{'item'}});
				
				for (my $i = 0; $i < $failedjobs_number; $i++) {
					$exitcode = $dataFailedStatus->{'jobs'}{'item'}[$i]{'JobExecExitCode'};
					if (!($stats{$exitcode}))	{ $stats{$exitcode} = 1; }
					else				{ $stats{$exitcode} = $stats{$exitcode} + 1; }
				}
			} else {
					$exitcode = $dataFailedStatus->{'jobs'}{'item'}{'JobExecExitCode'};
					$stats{$exitcode} = 1;
			}

			open(DASHBOARD_FAILED_JOBS, ">../results/dashboard_failed_jobs.txt");
			foreach my $key (keys %stats) { 
				print DASHBOARD_FAILED_JOBS $key,"\t",$stats{$key},"\n";
			}
			close(DASHBOARD_FAILED_JOBS);
		} else {
			open(DASHBOARD_FAILED_JOBS, ">../results/dashboard_failed_jobs.txt");			
			close(DASHBOARD_FAILED_JOBS);
		}


		my $unixtime = time;

		open(DASHBOARD_RESULTS, ">../results/dashboard_results.txt");

		print DASHBOARD_RESULTS "plot_url\t=\t",$plot_url,"\n";
		print DASHBOARD_RESULTS "date1\t=\t",$dataDashboard->{'meta'}{'date1'}{'item'},"\n";
		print DASHBOARD_RESULTS "date2\t=\t",$dataDashboard->{'meta'}{'date2'}{'item'},"\n";
		print DASHBOARD_RESULTS "activity\t=\t",$self->{'activity'},"\n";
		print DASHBOARD_RESULTS "facevalue\t=\t",$facevalue,"\n";
		print DASHBOARD_RESULTS "terminated\t=\t",$terminated,"\n";
		print DASHBOARD_RESULTS "app_succeeded\t=\t",$app_succeeded,"\n";
		print DASHBOARD_RESULTS "app_failed\t=\t",$app_failed,"\n";
		print DASHBOARD_RESULTS "app_unknown\t=\t",$app_unknown,"\n";
		print DASHBOARD_RESULTS "failed_jobs_url\t=\t",$url,"\n";
		print DASHBOARD_RESULTS "unixtime\t=\t",$unixtime,"\n";

		close(DASHBOARD_RESULTS);
	} else {
		open(DASHBOARD_RESULTS, ">../results/dashboard_results.txt");
		print DASHBOARD_RESULTS "facevalue\t=\t",$facevalue,"\n";
		print DASHBOARD_RESULTS "unixtime\t=\t",$unixtime,"\n";
		close(DASHBOARD_RESULTS);		
	}

	$self->{'facevalue'} = $facevalue;
	return $facevalue;
	
}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	# readout the values from the file 'results/dashboard_results.txt'
	open(DASHBOARD_RESULTS, "../results/dashboard_results.txt");
	while(<DASHBOARD_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(DASHBOARD_RESULTS);

	open(DASHBOARD_HTML, ">../HTMLFragments/Dashboard_HTML");

if ($data{'facevalue'} != -1) {

	print DASHBOARD_HTML '	<table border="0">',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td>',"\n";

	my $facevalue = $data{'facevalue'};
	
	if ($facevalue == 0) 	{ print DASHBOARD_HTML '<img src="images/4_small.png" />',"\n"; }
	elsif ($facevalue == 1) { print DASHBOARD_HTML '<img src="images/3_small.png" />',"\n"; }
	elsif ($facevalue == 2) { print DASHBOARD_HTML '<img src="images/1_small.png" />',"\n"; }

	print DASHBOARD_HTML '			</td>',"\n";
	print DASHBOARD_HTML '			<td><h3>CMS dashboard values (FZK-LCG2) for the activity: ',$data{"activity"},'</h3></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '	</table>',"\n";

	print DASHBOARD_HTML '	<h4><a href="http://lxarda09.cern.ch/dashboard/request.py/jobsummary?user=&site=FZK-LCG2+%28Karlsruhe%2C+Germany%29&ce=&submissiontool=&dataset=&application=&rb=&activity=&grid=&sortby=activity&nbars=">CMS Dashboard (FZK-LCG2) - last 24 hours</a></h4>',"\n";
	print DASHBOARD_HTML '	<table width="860" border="1">',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td><br><div align="center"><img src="',$data{'plot_url'},'" /></div><br></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '	</table>',"\n";

	print DASHBOARD_HTML '	<table width="860" border="1">',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td><strong>succeeded jobs (application)</strong></td>',"\n";
	print DASHBOARD_HTML '			<td><div align="center"><strong>',$data{"app_succeeded"},'</strong></div></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td><strong>unknown jobs (application)</strong></td>',"\n";
	print DASHBOARD_HTML '			<td><div align="center"><strong>',$data{"app_unknown"},'</strong></div></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td><strong>failed jobs (application)</strong></td>',"\n";
	print DASHBOARD_HTML '			<td><div align="center"><strong><font color="#FF0000">',$data{"app_failed"},'</font></strong></div></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td>start</td>',"\n";
	print DASHBOARD_HTML '			<td><div align="center">',$data{"date1"},'</div></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td>end</td>',"\n";
	print DASHBOARD_HTML '			<td><div align="center">',$data{"date2"},'</div></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '	</table>',"\n";
	print DASHBOARD_HTML '	<br>',"\n";

	print DASHBOARD_HTML '	<table width="860" border="0">',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td>If the number of failed jobs is bigger than the number of succeeded jobs -> status: WARNING</td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '	</table>',"\n";
	print DASHBOARD_HTML '	<br>',"\n";

	print DASHBOARD_HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'dashboard\');\"></form>","\n";
	print DASHBOARD_HTML '	<div id="dashboard" style="display:none;">',"\n";
	print DASHBOARD_HTML '	<table width="1024" border="1">',"\n";
	print DASHBOARD_HTML '		<tr>',"\n";
	print DASHBOARD_HTML '			<td><br><div align="center"><img src="plots/dashboard_days.png" /></div><br></td>',"\n";
	print DASHBOARD_HTML '			<td><br><div align="center"><img src="plots/dashboard_months.png" /></div><br></td>',"\n";
	print DASHBOARD_HTML '		</tr>',"\n";
	print DASHBOARD_HTML '	</table>',"\n";
	print DASHBOARD_HTML '	<br>',"\n";

	if ($data{"app_failed"} != 0) {
		print DASHBOARD_HTML '	<h4><a href="',$data{'failed_jobs_url'},'">job detailed view</a>, <a href="https://twiki.cern.ch/twiki/bin/view/CMS/JobExitCodes">meaning of exitcodes</a></h4>',"\n";
		print DASHBOARD_HTML '	<table width="1024" border="1">',"\n";

		print DASHBOARD_HTML '		<tr>',"\n";
		print DASHBOARD_HTML '			<td><div align="center"><strong>exitcode</strong></div></td>',"\n";
		print DASHBOARD_HTML '			<td><div align="center"><strong>number of jobs</strong><div></td>',"\n";
		print DASHBOARD_HTML '		</tr>',"\n";

		open(DASHBOARD_FAILED_JOBS, "../results/dashboard_failed_jobs.txt");
		while(<DASHBOARD_FAILED_JOBS>) {
			chomp;
			my ($exitcode, $jobs) = split(/\t/);
			print DASHBOARD_HTML '		<tr>',"\n";
			print DASHBOARD_HTML '			<td><div align="center">',$exitcode,'</div></td>',"\n";
			print DASHBOARD_HTML '			<td><div align="center">',$jobs,'</div></td>',"\n";
			print DASHBOARD_HTML '		</tr>',"\n";
	
		}
		close(DASHBOARD_FAILED_JOBS);
	
		print DASHBOARD_HTML '	</table>',"\n";
	}
	print DASHBOARD_HTML '	</div>',"\n";

	print DASHBOARD_HTML '	<br>',"\n";
	print DASHBOARD_HTML '	<hr>',"\n";
}

	close(DASHBOARD_HTML);
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
