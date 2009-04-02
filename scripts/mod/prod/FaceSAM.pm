
package mod::prod::FaceSAM;

#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;

	my $happy_CEs = 0;
	my $warning_CEs = 0;
	my $critical_CEs = 0;

	my $warning_SEs = 0;


	$dataSam = mod::DataFactory->new("SAM", %options = ("site"	=> $self->{'site'}) );


	if (! $dataSam->{'data'}) {
	  	open(PHEDEXIN_RESULTS, ">../results/phedexin_prod_results.txt");
		print PHEDEXIN_RESULTS "facevalue\t=\t",$facevalue,"\n";
		print PHEDEXIN_RESULTS "unixtime\t=\t",$unixtime,"\n";
		close(PHEDEXIN_RESULTS);
	
		$self->{'facevalue'} = $facevalue;
	
		return $facevalue;
	}

	open(SAM_FAILED_TESTS, ">../results/sam_failed_tests.txt");

	my $st = $dataSam->{'data'}{'item'}{'Services'}{'item'};

	# hash or array
	if($st =~ /^HASH/) { undef($services_type); $services_type->[0] = $st; }
	else { undef($services_type); $services_type = $st; }

	for (my $i=0; $i < scalar@{$services_type}; $i++ ) {

		my $sn = $services_type->[$i]{'ServiceNames'}{'item'};

		# hash or array
		if($sn =~ /^HASH/) { undef($services_name); $services_name->[0] = $sn; }
		else { undef($services_name); $services_name = $sn; }

		for ($j=0; $j < scalar@{$services_name}; $j++) {
		# print "\n",$services_type->[$i]{'ServiceType'},"  ",$services_name->[$j]{'ServiceName'},"\n"; 

##############################################################
######################## Analye Code #########################


if ($services_name->[$j]{'ServiceStatus'} == -1) {
	$critical_flag = 0;	

	# loop over all tests
	my $tests_type = $services_name->[$j]{'Tests'}{'item'};
	my $numberOF_tests_type = scalar@{$tests_type};
	for ($k=0; $k < $numberOF_tests_type; $k++) {


		# print the failed tests to a file
		my $ServiceType	= $services_type->[$i]{'ServiceType'};
		my $ServiceName	= $services_name->[$j]{'ServiceName'};
		my $Status 	= $tests_type->[$k]{'Status'};
		my $Type 	= $tests_type->[$k]{'Type'};
		my $Time 	= $tests_type->[$k]{'Time'};
		my $Url		= $tests_type->[$k]{'Url'};
		
		if ($Status =~ /^HASH/) {}
		elsif (!($Status eq "ok")) { print SAM_FAILED_TESTS $ServiceType,"\t",$ServiceName,"\t",$Type,"\t",$Time,"\t",$Status,"\t",$Url,"\n"; }

		# check if CEs are "critical" or only "warning"
		if	($Type eq "CE-cms-prod" && $Status eq "error") { $critical_flag = 1; }
		elsif	($Type eq "CE-cms-frontier" && $Status eq "error") { $$critical_flag = 1; }
		elsif	($Type eq "CE-cms-squid" && $Status eq "error") { $critical_flag = 1; }
		elsif	($Type eq "CE-sft-job" && $Status eq "error") { $critical_flag = 1; }
	}

	# count critical and warning CEs
	if ($services_type->[$i]{"ServiceType"} eq "CE") {
		if ($critical_flag == 1) { $critical_CEs++; }
		elsif ($critical_flag == 0) { $warning_CEs++; }
	}

	# count warning SEs
	if ($services_type->[$i]{"ServiceType"} eq "SRM" || $services_type->[$i]{"ServiceType"} eq "SRM2") { $warning_SEs++; }
}

if ($services_name->[$j]{'ServiceStatus'} == 1) {
	# count happy CEs
	if ($services_type->[$i]{"ServiceType"} eq "CE") {
		$happy_CEs++;
	}
}



##############################################################
##############################################################


		}
	}

	close(SAM_FAILED_TESTS);

	$facevalue = 0;

	if ($warning_SEs > 0) { $facevalue = 1; }
	if ($happy_CEs == 0) {
		if ($warning_CEs > 0) { $facevalue = 1; }
		elsif ($critical_CEs > 0) { $facevalue = 2; }
	}

	open(SAM_RESULTS, ">../results/sam_results.txt");
	print SAM_RESULTS "facevalue\t=\t",$facevalue,"\n";
	print SAM_RESULTS "site\t=\t",$self->{"site"},"\n";
	close(SAM_RESULTS);

	$self->{'facevalue'} = $facevalue;
	return $facevalue;


}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	open(SAM_RESULTS, "../results/sam_results.txt");
	while(<SAM_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(SAM_RESULTS);

	open(SAM_HTML, ">../HTMLFragments/SAM_HTML");

if ($data{'facevalue'} != -1) {

	print SAM_HTML '	<table border="0">',"\n";
	print SAM_HTML '		<tr>',"\n";
	print SAM_HTML '			<td>',"\n";

	my $facevalue = $data{'facevalue'};
	
	if ($facevalue == 0) 	{ print SAM_HTML '<img src="images/4_small.png" />',"\n"; }

	elsif ($facevalue == 1) { print SAM_HTML '<img src="images/3_small.png" />',"\n"; }

	elsif ($facevalue == 2) { print SAM_HTML '<img src="images/1_small.png" />',"\n"; }

	print SAM_HTML '			</td>',"\n";
	print SAM_HTML '			<td><h3>SAM results for: ',$data{"site"},'</h3></td>',"\n";
	print SAM_HTML '		</tr>',"\n";
	print SAM_HTML '	</table>',"\n";

	print SAM_HTML '	<h4><a href="http://lxarda16.cern.ch/dashboard/request.py/latestresultssmry?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all">SAM (',$data{"site"},')</a></h4>',"\n";
	print SAM_HTML '	<table width="960" border="1">',"\n";

	print SAM_HTML '	<tr>',"\n";
	print SAM_HTML '		<td><div align="center"><strong>Status</strong></div></td>',"\n";
	print SAM_HTML '		<td><div align="center"><strong>Service Type</strong></div></td>',"\n";
	print SAM_HTML '		<td><div align="center"><strong>Service Name</strong></div></td>',"\n";
	print SAM_HTML '		<td><div align="center"><strong>Test</strong></div></td>',"\n";
	print SAM_HTML '		<td><div align="center"><strong>Time</strong></div></td>',"\n";
	print SAM_HTML '	</tr>',"\n";

	open(SAM_FAILED_TESTS, "../results/sam_failed_tests.txt");
	while(<SAM_FAILED_TESTS>) {
		chomp;

		my ($service_type, $service_name, $test, $time, $status, $url) = split(/\t/);
		print SAM_HTML '	<tr>',"\n";
		print SAM_HTML '		<td><div align="center"><strong><a href="https://lcg-sam.cern.ch:8443/sam/sam.py?funct=TestResult',$url,'">',$status,'</a></strong></div></td>',"\n";
		print SAM_HTML '		<td><div align="center">',$service_type,'</div></td>',"\n";
		print SAM_HTML '		<td><div align="center">',$service_name,'</div></td>',"\n";
		print SAM_HTML '		<td><div align="center">',$test,'</div></td>',"\n";
		print SAM_HTML '		<td><div align="center">',$time,'</div></td>',"\n";
		print SAM_HTML '	</tr>',"\n";
	}
	close(SAM_FAILED_TESTS);	

	print SAM_HTML '	</table>',"\n";

	print SAM_HTML '	<br>',"\n";

	print SAM_HTML '	<table width="960" border="0">',"\n";
	print SAM_HTML '		<tr>',"\n";
	print SAM_HTML '		<td>When critical condition for CEs is raised, please report to GridKa (during off hours, please forward this ticket also by mail to GridKa cg-admins list). In your report state what tests are failing, and that all CEs are failing this (or these) tests. Please include a sample log from one of CEs. When warning conditions exists for CEs or SEs, please send your report to CMS expert on call. Please do not forget to update list of current issues is the problem persists beyond your shift!</td>',"\n";
	print SAM_HTML '		</tr>',"\n";
	print SAM_HTML '	</table>',"\n";
	

	print SAM_HTML '	<br>',"\n";
	print SAM_HTML '	<hr>',"\n";
}
	close(SAM_HTML);
}

#---------------------------------------------------------------------------------

sub new {

	$self = shift @_;
	my %options = %{shift @_};
	my $face = {%options};

	bless $face, $self;
	return $face;

}

1;
