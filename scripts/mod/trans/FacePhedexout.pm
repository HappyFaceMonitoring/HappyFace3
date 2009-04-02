package mod::trans::FacePhedexout;


#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;
	my $facevalue = -1;
	my $node_fraction;
	my $transfer_quality;

	my $dataPhedexout = mod::DataFactory->new("Phedexout", %options = (
								"time_range"	=> $self->{'time_range'},
								"from_node"	=> $self->{'from_node'},
								));

if ($dataPhedexout->{'query'}) {
	my $node_number = @{$dataPhedexout->{'query'}{'data'}{'pivot'}};
	my $value_number;
	my $all_success = 0;
	my $all_fail = 0;

	my $failed_nodes = 0;

	open(FAILED_NODES, ">../results/phedexout_failed_nodes.txt");

	for ($i = 0; $i < $node_number; $i++) {
		if ($dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'}) {

			my $success = 0;
			my $fail = 0;
			my $name_node = $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'name'};

			if ($dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'} =~ /^ARRAY/) {		
				$value_number = @{ $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'} };
				for ($j = 0; $j < $value_number; $j++) {
					$success = $success + $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'}[$j]{'d'}[0];
					$fail = $fail + $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'}[$j]{'d'}[1];
				}

			} else {
				$success = $success + $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'}{'d'}[0];
				$fail = $fail + $dataPhedexout->{'query'}{'data'}{'pivot'}[$i]{'group'}{'d'}[1];
			}

			$all_success	+= $success;
			$all_fail	+= $fail;

			if (($succes + $fail) != 0) {
				$node_fraction = sprintf("%.2f",$success / ($success + $fail));
				if ($node_fraction < $self->{'node_limit'}) {
					$failed_nodes++;
					print FAILED_NODES $name_node,"\t",$fail,"\t",$fail+$success,"\n";
				}
			} else {
				$node_fraction = "no information";
			}
		}
	}

	close(FAILED_NODES);

	# correction of the node_number
	if ($dataPhedexout->{'query'}{'data'}{'pivot'}[0] eq "Link") { $node_number--; }
	
	if ($node_number != 0) {
		$transfer_quality = sprintf("%.2f",1 - $failed_nodes / $node_number);
		if ($transfer_quality < $self->{'global_limit'}) { $facevalue = 1; }
		else { $facevalue = 0; }

	} else {
		$transfer_quality = "no information";
		$facevalue = -1;
	}





	my $unixtime = time;

	open(PHEDEXOUT_RESULTS, ">../results/phedexout_results.txt");

	print PHEDEXOUT_RESULTS "global_limit\t=\t",$self->{'global_limit'},"\n";
	print PHEDEXOUT_RESULTS "node_limit\t=\t",$self->{'node_limit'},"\n";
	print PHEDEXOUT_RESULTS "transfer_quality\t=\t",$transfer_quality,"\n";
	print PHEDEXOUT_RESULTS "time_range\t=\t",$self->{'time_range'},"\n";
	print PHEDEXOUT_RESULTS "from_node\t=\t",$self->{'from_node'},"\n";
	print PHEDEXOUT_RESULTS "node_number\t=\t",$node_number,"\n";
	print PHEDEXOUT_RESULTS "failed_nodes\t=\t",$failed_nodes,"\n";
	print PHEDEXOUT_RESULTS "facevalue\t=\t",$facevalue,"\n";
	print PHEDEXOUT_RESULTS "unixtime\t=\t",$unixtime,"\n";
	print PHEDEXOUT_RESULTS "all_success\t=\t",$all_success,"\n";
	print PHEDEXOUT_RESULTS "all_fail\t=\t",$all_fail,"\n";

	close(PHEDEXOUT_RESULTS);
} else {
        my $unixtime = time;
	

	open(PHEDEXOUT_RESULTS, ">../results/phedexout_results.txt");
	print PHEDEXOUT_RESULTS "facevalue\t=\t",$facevalue,"\n";
	print PHEDEXOUT_RESULTS "unixtime\t=\t",$unixtime,"\n";
	close(PHEDEXOUT_RESULTS);
}
	$self->{'facevalue'} = $facevalue;

	return $facevalue;
}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	open(PHEDEXOUT_RESULTS, "../results/phedexout_results.txt");
	while(<PHEDEXOUT_RESULTS>) {
		chomp;
		next unless length;
		my ($var, $value) = split(/\s*=\s*/, $_, 2);
		$data{$var} = $value;
	}
	close(PHEDEXOUT_RESULTS);
	

	open(PHEDEXOUT_HTML, ">../HTMLFragments/Phedexout_HTML");

if ($data{'facevalue'} != -1) {

	print PHEDEXOUT_HTML '	<table border="0">',"\n";
	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td>',"\n";

	my $facevalue = $data{'facevalue'};
	
	if ($facevalue == 0) 	{ print PHEDEXOUT_HTML '<img src="images/4_small.png" />',"\n"; }
	elsif ($facevalue == 1) { print PHEDEXOUT_HTML '<img src="images/3_small.png" />',"\n"; }
	elsif ($facevalue == 2) { print PHEDEXOUT_HTML '<img src="images/1_small.png" />',"\n"; }

	print PHEDEXOUT_HTML '			</td>',"\n";
	print PHEDEXOUT_HTML '			<td><h3>PhEDEx Test for Outgoing Transfers</h3></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";
	print PHEDEXOUT_HTML '	</table>',"\n";



	print PHEDEXOUT_HTML '  <h4><a href="http://t2.unl.edu/phedex/xml/quality_all?span=3600&show_expired=False&link=link&starttime=',time-3600 * $self->{'time_range'},'&no_mss=True&endtime=',time,'&to_node=.*&from_node=',$self->{'from_node'},'">CMS PhEDEx - Transfer Quality</a></h4>',"\n";
	print PHEDEXOUT_HTML '	<table width="860" border="1">',"\n";

	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td><strong>general transfer quality</strong></td>',"\n";
	print PHEDEXOUT_HTML '			<th rowspan="2"><div align="center"><strong>',$data{'transfer_quality'}*100,' %</strong></div></th>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";
	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td><i>fraction of successfull target nodes, should be higher than ',$data{'global_limit'}*100,' %</i></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";

	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td><strong>number of target nodes</strong></td>',"\n";
	print PHEDEXOUT_HTML '			<td><div align="center"><strong>',$data{'node_number'},'</strong></strong></div></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";

	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td><strong>failed target nodes</strong></td>',"\n";
	print PHEDEXOUT_HTML '			<th rowspan="2"><div align="center"><font color="#FF0000">',$data{'failed_nodes'},'</font></div></th>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";
	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td><i>definition: transfer quality under ',$data{'node_limit'}*100,' %</i></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";

	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td>all successful transfers</td>',"\n";
	print PHEDEXOUT_HTML '			<td><div align="center">',$data{'all_success'},'</strong></div></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";
	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td>all failed transfers</td>',"\n";
	print PHEDEXOUT_HTML '			<td><div align="center">',$data{'all_fail'},'</strong></div></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";

	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td>from node</td>',"\n";
	print PHEDEXOUT_HTML '			<td><div align="center">',$data{'from_node'},'</strong></div></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";
	print PHEDEXOUT_HTML '		<tr>',"\n";
	print PHEDEXOUT_HTML '			<td>time range</td>',"\n";
	print PHEDEXOUT_HTML '			<td><div align="center">',$data{'time_range'},' hours</strong></div></td>',"\n";
	print PHEDEXOUT_HTML '		</tr>',"\n";


	print PHEDEXOUT_HTML '	</table>',"\n";
	print PHEDEXOUT_HTML '	<br>',"\n";

	print PHEDEXOUT_HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'phedexout\');\"></form>","\n";

	print PHEDEXOUT_HTML '	<div id="phedexout" style="display:none;">',"\n";
#	print PHEDEXOUT_HTML '	<table width="1024" border="1">',"\n";
#	print PHEDEXOUT_HTML '		<tr>',"\n";
#	print PHEDEXOUT_HTML '			<td><br><div align="center"><img src="plots/phedexout_days.png" /></div><br></td>',"\n";
#	print PHEDEXOUT_HTML '			<td><br><div align="center"><img src="plots/phedexout_months.png" /></div><br></td>',"\n";
#	print PHEDEXOUT_HTML '		</tr>',"\n";
#	print PHEDEXOUT_HTML '	</table>',"\n";
	print PHEDEXOUT_HTML '	<table width="1024" border="1">',"\n";
		print PHEDEXOUT_HTML '		<tr>',"\n";
		print PHEDEXOUT_HTML '			<td><div align="center"><strong>failed nodes</strong></div></td>',"\n";
		print PHEDEXOUT_HTML '			<td><div align="center"><strong>failed transfers</strong><div></td>',"\n";
		print PHEDEXOUT_HTML '		</tr>',"\n";
	open(RESULTS, "../results/phedexout_failed_nodes.txt");
	while(<RESULTS>) {
		chomp;
		my ($node, $failed_transfers, $total_transfers) = split(/\t/);
		print PHEDEXOUT_HTML '		<tr>',"\n";
		print PHEDEXOUT_HTML '			<td><div align="center">',$node,'</div></td>',"\n";
		print PHEDEXOUT_HTML '			<td><div align="center">',$failed_transfers,' of ',$total_transfers,'</div></td>',"\n";
		print PHEDEXOUT_HTML '		</tr>',"\n";
	}
	close(RESULTS);
	print PHEDEXOUT_HTML '	</table>',"\n";
	print PHEDEXOUT_HTML '	</div>',"\n";


	print PHEDEXOUT_HTML '	<br>',"\n";
	print PHEDEXOUT_HTML '	<hr>',"\n";	
}
	close(PHEDEXOUT_HTML);

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
