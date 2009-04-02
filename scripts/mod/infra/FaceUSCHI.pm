package mod::infra::FaceUSCHI;

#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;



	my $dataUSCHI = mod::DataFactory->new("USCHI", %{$self});


if ($dataUSCHI->{'summary'}) {
	$ok_tests	= $dataUSCHI->{'summary'}{'ok'};
	$err_tests	= $dataUSCHI->{'summary'}{'err'};

	open(USCHI_RESULTS, ">../results/uschi_results.txt");
	open(USCHI_TESTS, ">../results/uschi_tests.txt");

	print USCHI_RESULTS "ok\t=\t",$ok_tests,"\n";
	print USCHI_RESULTS "err\t=\t",$err_tests,"\n";
	print USCHI_RESULTS "time\t=\t",$dataUSCHI->{'time'},"\n";


	foreach my $key (sort keys %{$dataUSCHI->{'tests'}{'test'}} ) {
		print USCHI_TESTS $key,"\t=\t",$dataUSCHI->{'tests'}{'test'}{$key}{'result'},"\n";

		if ($dataUSCHI->{'tests'}{'test'}{$key}{'result'} > $facevalue && $dataUSCHI->{'tests'}{'test'}{$key}{'result'} <= 2) { $facevalue = $dataUSCHI->{'tests'}{'test'}{$key}{'result'}; }

		open(USCHI_LOG,">../results/". $key . '_log.txt');
		print USCHI_LOG $dataUSCHI->{'tests'}{'test'}{$key}{'log'};
		close(USCHI_LOG);

		open(USCHI_ABOUT,">../results/". $key . '_about.txt');
		print USCHI_ABOUT $dataUSCHI->{'tests'}{'test'}{$key}{'about'};
		close(USCHI_ABOUT);
	}

	print USCHI_RESULTS "facevalue\t=\t",$facevalue,"\n";

	close(USCHI_TESTS);
	close(USCHI_RESULTS);

} else {
	open(USCHI_RESULTS, ">../results/uschi_results.txt");
	print USCHI_RESULTS "facevalue\t=\t",$facevalue,"\n";
	close(USCHI_RESULTS);
}
	

	$self->{'facevalue'} = $facevalue;

	return $facevalue;
}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	open(USCHI_RESULTS, "../results/uschi_results.txt");
	while(<USCHI_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$results{$var} = $value;
	}
	close(USCHI_RESULTS);

	open(USCHI_TESTS, "../results/uschi_tests.txt");
	while(<USCHI_TESTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$tests{$var} = $value;
	}
	close(USCHI_TESTS);

	my $facevalue	= $results{'facevalue'};
	my $time	= $results{'time'};

	open(USCHI_HTML, ">../HTMLFragments/USCHI_HTML");

if ($facevalue != -1) {

	print USCHI_HTML '	<table border="0">',"\n";
	print USCHI_HTML '		<tr>',"\n";
	print USCHI_HTML '			<td>',"\n";

	if ($facevalue == 0) 	{ print USCHI_HTML '<img src="images/4_small.png" />',"\n"; }
	elsif ($facevalue == 1) { print USCHI_HTML '<img src="images/3_small.png" />',"\n"; }
	elsif ($facevalue == 2) { print USCHI_HTML '<img src="images/1_small.png" />',"\n"; }

	print USCHI_HTML '			</td>',"\n";
	print USCHI_HTML '			<td><h3>USCHI results</h3></td>',"\n";
	print USCHI_HTML '		</tr>',"\n";
	print USCHI_HTML '	</table>',"\n";

	print USCHI_HTML '	<h4>time: ',$time,'</h4>',"\n";


	foreach my $key (sort keys %tests ) {

		print USCHI_HTML '	<table width="860" border="1">',"\n";
		print USCHI_HTML '		<tr>',"\n";
		print USCHI_HTML '			<td><div align="center"><strong>',$key,'</strong></div></td>',"\n";

		print USCHI_HTML '			<th width="140" rowspan="2"><div align="center">';
		if ($tests{$key} == 0) {print USCHI_HTML '<font color="#00FF00">successful</fount>';}
		elsif ($tests{$key} == -1) {print USCHI_HTML 'no information';}
		elsif ($tests{$key} == 1) {print USCHI_HTML '<font color="#FF0000">warning</fount>';}
		elsif ($tests{$key} == 2) {print USCHI_HTML '<font color="#FF0000">critical error</fount>';}
		else { print USCHI_HTML '<font color="#FF0000">',$tests{$key},'</fount>'; }
		print USCHI_HTML '</div></th>',"\n";


		$about = "";
		open(USCHI_ABOUT, "../results/". $key . '_about.txt');
		while(<USCHI_ABOUT>) {
			$about = $about . $_;
		}
		close(USCHI_ABOUT);
	
	
		print USCHI_HTML '		</tr>',"\n";
		print USCHI_HTML '		<tr>',"\n";
		print USCHI_HTML '			<td><div align="center"><i>',$about,'</i></div></td>',"\n";
		print USCHI_HTML '		</tr>',"\n";
		print USCHI_HTML '	</table>',"\n";
	
	
		print USCHI_HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'uschi_".$key."\');\"></form>","\n";
		print USCHI_HTML '	<div id="uschi_',$key,'" style="display:none;">',"\n";
	
		open(USCHI_LOG, "../results/" . $key . '_log.txt');
		while(<USCHI_LOG>) {
			chomp;
			print USCHI_HTML "<p>",$_,"<\p>\n";
		}
		close(USCHI_LOG);

		print USCHI_HTML '	</div>',"\n";
	
		print USCHI_HTML '	<br>',"\n";
	
	}
}
	close(USCHI_HTML);
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
