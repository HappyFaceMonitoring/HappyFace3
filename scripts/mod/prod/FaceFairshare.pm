package mod::prod::FaceFairshare;


#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;

	my $dataGridkajobs	= mod::DataFactory->new("Gridkajobs");
	my $dataFairshare	= mod::DataFactory->new("Fairshare");

	my $run_total_frac = sprintf("%.2f", $dataGridkajobs->{$self->{'experiment'}}{"running"} / $dataGridkajobs->{"sum"}{"running"} * 100);
	my $run_queued_frac = sprintf("%.2f", $dataGridkajobs->{$self->{'experiment'}}{"running"} / $dataGridkajobs->{$self->{'experiment'}}{"all"} * 100);

	my $nominal_fairshare = $dataFairshare->{$self->{'experiment'}}{"nominal"};
	my $used_fairshare = $dataFairshare->{$self->{'experiment'}}{"used_walltime_180d"};


	if (($run_total_frac > $self->{'nom_fairshare_limit_frac'} * $nominal_fairshare) || ($run_queued_frac >= $self->{'run_queued_limit_frac'}*100)) {
		$facevalue = 0;
	} else {
		$facevalue = 1;
	}

	my $unixtime = time;

	open(FAIRSHARE_RESULTS, ">../results/fairshare_results.txt");
	
	print FAIRSHARE_RESULTS "fairshare_experiment\t=\t",$self->{'experiment'},"\n";
	print FAIRSHARE_RESULTS "facevalue\t=\t",$facevalue,"\n";
	print FAIRSHARE_RESULTS "run_total_frac\t=\t",$run_total_frac,"\n";
	print FAIRSHARE_RESULTS "run_queued_frac\t=\t",$run_queued_frac,"\n";
	print FAIRSHARE_RESULTS "nominal_fairshare\t=\t",$nominal_fairshare,"\n";
	print FAIRSHARE_RESULTS "used_fairshare\t=\t",$used_fairshare,"\n";
	print FAIRSHARE_RESULTS "unixtime\t=\t",$unixtime,"\n";
	print FAIRSHARE_RESULTS "number_exp_running_jobs\t=\t",$dataGridkajobs->{$self->{'experiment'}}{"running"},"\n";
	print FAIRSHARE_RESULTS "number_exp_queued_jobs\t=\t",$dataGridkajobs->{$self->{'experiment'}}{"queued"},"\n";
	print FAIRSHARE_RESULTS "number_all_running_jobs\t=\t",$dataGridkajobs->{"sum"}{"running"},"\n";
	print FAIRSHARE_RESULTS "number_all_queued_jobs\t=\t",$dataGridkajobs->{"sum"}{"queued"},"\n";

	close(FAIRSHARE_RESULTS);

	$self->{'facevalue'} = $facevalue;
	return $facevalue;

}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	my $self = shift @_;

	# readout the values from the file 'results/fairshare_results.txt'
	open(FAIRSHARE_RESULTS, "../results/fairshare_results.txt");
	$data_key = "";
	while(<FAIRSHARE_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(FAIRSHARE_RESULTS);

	open(FAIRSHARE_HTML, ">../HTMLFragments/Fairshare_HTML");

if ($data{"facevalue"} != -1) {

	print FAIRSHARE_HTML '	<table border="0">',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>',"\n";

	my $facevalue = $data{'facevalue'};
	
	if ($facevalue == 0) 	{ print FAIRSHARE_HTML '<img src="images/4_small.png" />',"\n"; }
	elsif ($facevalue == 1) { print FAIRSHARE_HTML '<img src="images/3_small.png" />',"\n"; }
	elsif ($facevalue == 2) { print FAIRSHARE_HTML '<img src="images/1_small.png" />',"\n"; }

	print FAIRSHARE_HTML '			</td>',"\n";
	print FAIRSHARE_HTML '			<td><h3>fairshare values for the experiment: ',$data{"fairshare_experiment"},'</h3></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '	</table>',"\n";
	print FAIRSHARE_HTML '	<h4><a href="http://grid.fzk.de/monitoring/main.html">GridKa Monitoring</a></h4>',"\n";

	print FAIRSHARE_HTML '	<table width="860" border="1">',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td><strong>',$data{"fairshare_experiment"},' running jobs / ',$data{"fairshare_experiment"},' running & queued jobs</strong></td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center"><strong>',$data{"run_queued_frac"},' %</strong></div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td><strong>',$data{"fairshare_experiment"},' running jobs / all running jobs</strong></td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center"><strong>',$data{"run_total_frac"},' %</strong></div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>nominal fairshare value</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"nominal_fairshare"},' %</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>used fairshare value (180 days)</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"used_fairshare"},' %</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";

	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>all runing jobs</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"number_all_running_jobs"},'</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>all queued jobs</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"number_all_queued_jobs"},'</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>',$data{"fairshare_experiment"},' running jobs</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"number_exp_running_jobs"},'</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>',$data{"fairshare_experiment"},' queued jobs</td>',"\n";
	print FAIRSHARE_HTML '			<td><div align="center">',$data{"number_exp_queued_jobs"},'</div></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '	</table>',"\n";
	print FAIRSHARE_HTML '	<br>',"\n";

	print FAIRSHARE_HTML '	<table width="860" border="0">',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td>If the fraction of ',$data{"fairshare_experiment"},' running jobs / ',$data{"fairshare_experiment"},' running & queued jobs is under ',$self->{'run_queued_limit_frac'}*100,'% and the fraction of ',$data{"fairshare_experiment"},' running jobs / all running jobs is under ',$self->{'nom_fairshare_limit_frac'}*100,'% of the nominal fairshare -> status: WARNING.</td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '	</table>',"\n";
	print FAIRSHARE_HTML '	<br>',"\n";

	print FAIRSHARE_HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'fairshare\');\"></form>","\n";
	print FAIRSHARE_HTML '	<div id="fairshare" style="display:none;">',"\n";

	print FAIRSHARE_HTML '	<table width="1024" border="1">',"\n";
	print FAIRSHARE_HTML '		<tr>',"\n";
	print FAIRSHARE_HTML '			<td><br><div align="center"><img src="plots/fairshare_days.png" /></div><br></td>',"\n";
	print FAIRSHARE_HTML '			<td><br><div align="center"><img src="plots/fairshare_months.png" /></div><br></td>',"\n";
	print FAIRSHARE_HTML '		</tr>',"\n";
	print FAIRSHARE_HTML '	</table>',"\n";
	print FAIRSHARE_HTML '	</div>',"\n";

	print FAIRSHARE_HTML '	<br>',"\n";
	print FAIRSHARE_HTML '	<hr>',"\n";
}

	close(FAIRSHARE_HTML);

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
