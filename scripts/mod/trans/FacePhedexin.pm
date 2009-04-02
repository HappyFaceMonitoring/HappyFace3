package mod::trans::FacePhedexin;

use strict;

use Data::Dumper;

use mod::DataFactory;

#---------------------------------------------------------------------------------

sub result {
	my $self = shift @_;

	my $dataPhedexin = $self->{DATA};

	print "FacePhedexin for ",$self->{'test'}," ", Dumper $dataPhedexin, "\n";

	my $facevalue = -1;
	my $unixtime = time;


	#business logic - we check if number of target errors is more than allowed.
	#let's hardcode the threshold by now
	my $allowed_dest_errors = $self->{'allowed_dest_errors'};
	my $allowed_client_errors = $self->{'allowed_client_errors'};

#	my $ePerSite = $dataPhedexin;
	
	my %ePerOrigin = %{$self->{EORIGIN}};

	if ($ePerOrigin{'all'} &&  $ePerOrigin{'dest'}/$ePerOrigin{'all'} > $allowed_dest_errors) {
	    $facevalue = 2;
	}
	if ($ePerOrigin{'all'} &&  $ePerOrigin{'client'}/$ePerOrigin{'all'} > $allowed_dest_errors) {
	    $facevalue = 1;
	}
	else {
	    $facevalue = 0;
	}

	open(PHEDEXIN_RESULTS, ">../results/phedexin_results.txt");
	print PHEDEXIN_RESULTS "facevalue\t=\t",$facevalue,"\n";
	print PHEDEXIN_RESULTS "unixtime\t=\t",$unixtime,"\n";
	close(PHEDEXIN_RESULTS);
	
	$self->{'facevalue'} = $facevalue;
	
	return $facevalue;
}

#---------------------------------------------------------------------------------

sub createHTMLFragment {
    my $self = shift @_;

    my $dataPhedexin = $self->{DATA};
    my $metadata = $self->{METADATA};
    my $transfersumm =  $self->{TRANSFERSUMM};

    print "Got METADATA ", Dumper $metadata;


    my %data = ();

    my $htmlfragfile = $self->{'htmlfragfile'};

    print "Creating html fragment $htmlfragfile for ".$self->{'test'}."\n";

    my $htmltitle = $self->{'htmltitle'};

    open(PHEDEXIN_RESULTS, "../results/phedexin_results.txt");

    while(<PHEDEXIN_RESULTS>) {
	chomp;
	next unless length;
	my ($var, $value) = split(/\s*=\s*/, $_, 2);
	$data{$var} = $value;
    }
    close(PHEDEXIN_RESULTS);
	

    open(HTML, ">$htmlfragfile");

    my $facevalue = $self->{'facevalue'};

    if ($facevalue == -1) {
	close HTML;
	return;
    }

    print HTML '	<table border="0">',"\n";
    print HTML '		<tr>',"\n";
    print HTML '			<td>',"\n";
    
    
    
    if ($facevalue == 0)    { print HTML '<img src="images/4_small.png" />',"\n"; }
    elsif ($facevalue == 1) { print HTML '<img src="images/3_small.png" />',"\n"; }
    elsif ($facevalue == 2) { print HTML '<img src="images/1_small.png" />',"\n"; }
    
    print HTML '			</td>',"\n";
    
    print HTML "			<td><h3>".$htmltitle."</h3></td>","\n";
    
    print HTML '		</tr>',"\n";
    print HTML '	</table>',"\n";


    my %ePerOrigin = %{$self->{EORIGIN}};

    my $fraction_dest_errors = 0;
    my $fraction_client_errors = 0;

    if ($ePerOrigin{'all'}) { 
	$fraction_dest_errors =  $ePerOrigin{'dest'}/$ePerOrigin{'all'} ;
	$fraction_client_errors =  $ePerOrigin{'client'}/$ePerOrigin{'all'} ;
    }


    #New summary table here.
    #Color scheme for summary table
    #red is numbers that are below specified metrix.
    my $dest_error_color = "";
    $dest_error_color = 'color="red"' if ($fraction_dest_errors >= $self->{'allowed_dest_errors'} ); #FF0000

    print "COLOR fraction_dest_errors $fraction_dest_errors allowed_dest_errors ",$self->{'allowed_dest_errors'},"\n";

    my $client_error_color = "";
    $client_error_color = 'color="red"' if ($fraction_client_errors >= $self->{'allowed_client_errors'} );


    print HTML '	<table width="860" border="1">',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td colspan="2"><strong><center>Transfer summary</center></strong></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td><strong>All transfers</strong></td>',"\n";
    print HTML '		<td><div align="center"><strong>',$transfersumm->{'ALL'},'</strong></div></td>',"\n";
    print HTML '	</tr>',"\n";
    print HTML '		<tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td>Successful transfers</td>',"\n";
    print HTML '		<td><div align="center">',$transfersumm->{'OK'},'</div></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '		<tr>',"\n";
    print HTML '	<td>Failed transfers</td>',"\n";
    print HTML '		<td><div align="center"><font>',$ePerOrigin{'all'} || 0,'</font></div></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td colspan="2"><strong><center>Failed transfers details</center></strong></td>',"\n";
    print HTML '	</tr>',"\n";


    print HTML '	<tr>',"\n";
    print HTML '        	<td>Failed transfers due to client</td>',"\n";
    print HTML '		<td><div align="center"><font '.$client_error_color.'>',$ePerOrigin{'client'} || 0,'</font></div></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td>Failed transfers due to destination</td>',"\n";
    print HTML '		<td><div align="center"><font '.$dest_error_color.'>',$ePerOrigin{'dest'} || 0,'</font></div></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td>Failed transfers due to source</td>',"\n";
    print HTML '		<td><div align="center"><font>',$ePerOrigin{'source'} || 0,'</font></div></td>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td>Failed transfers with unknown source of error</td>',"\n";
    print HTML '		<td><div align="center"><font>',$ePerOrigin{'unknown'} || 0,'</font></div></td>',"\n";
    print HTML '	</tr>',"\n";
    
    print HTML '	<tr>',"\n";
    print HTML '		<td><strong>Client error fraction</strong></td>',"\n";
    print HTML '		<th rowspan="2"><div align="center"><strong><font '.$client_error_color.'>',sprintf('%.1d%',$fraction_client_errors*100),'</font></strong></div></th>',"\n";
    print HTML '	</tr>',"\n";

    print HTML '	<tr>',"\n";
    print HTML '		<td><i>warning status if the fraction of client errors is over ',sprintf('%.1d%',$self->{'allowed_client_errors'}*100),'</i></td>',"\n";
    print HTML '	</tr>',"\n";
    
    print HTML '	<tr>',"\n";
    print HTML '		<td><strong>Dest error fraction</strong></td>',"\n";
    print HTML '		<th rowspan="2"><div align="center"><strong><font '.$dest_error_color.'>',sprintf('%.1d%',$fraction_dest_errors*100),'</font></strong></div></th>',"\n";
    print HTML '	</tr>',"\n";
    print HTML '	<tr>',"\n";
    print HTML '		<td><i>critical status if the fraction of destination errors is over ',sprintf('%.1d%',$self->{'allowed_dest_errors'}*100),'</i></td>',"\n";
    print HTML '	</tr>',"\n";
    
    print HTML '	<tr>',"\n";
    print HTML '		<td>start</td>',"\n";
# VMB 2008-10-14  print HTML '		<td><div align="center">',$metadata->{'startlocaltime'},'</div></td>',"\n";
    print HTML '		<td><div align="center">',$metadata->{'givenstarttime'},'</div></td>',"\n";
    print HTML '	</tr>',"\n";
    print HTML '	<tr>',"\n";
    print HTML '		<td>end</td>',"\n";
# VMB 2008-10-14   print HTML '		<td><div align="center">',$metadata->{'endlocaltime'},'</div></td>',"\n";
    print HTML '		<td><div align="center">',$metadata->{'givenendtime'},'</div></td>',"\n";
    print HTML '	</tr>',"\n";
    
    print HTML '	</table>',"\n";

    # end of visible summary table

    # a button to show/hide results
    print HTML '	<br>',"\n";

    print HTML "	<form><input type=button value=\"show/hide results\" onClick=\"show_hide(\'".$self->{'test'}."\');\"></form>","\n";
    print HTML '	<div id="'.$self->{'test'}.'" style="display:none;">',"\n";

#    print HTML '	<table width="1024" border="1">',"\n";
#    print HTML '		<tr>',"\n";
#    print HTML '		<td><br><div align="center"><img src="plots/phedexin_days.png" /></div><br></td>',"\n";
#    print HTML '		<td><br><div align="center"><img src="plots/phedexin_months.png" /></div><br></td>',"\n";
#    print HTML '		</tr>',"\n";
#    print HTML '	</table>',"\n";
    
    print HTML '	<br>',"\n";


    #invisible table with failed nodes and reasons
    #it gets visible by clicking show/hide button from above

    print HTML '	<table width="1024" border="1">',"\n";
    print HTML '		<tr>',"\n";
    print HTML '		<td><div align="center"><strong>node</strong></div></td>',"\n";
#    print HTML '		<td><div align="center"><strong>category</strong><div></td>',"\n";
    print HTML '		<td><div align="center"><strong>origin</strong><div></td>',"\n";
    print HTML '		<td><div align="center"><strong>failed transfers</strong><div></td>',"\n";
    print HTML '		<td><div align="center"><strong>error content</strong><div></td>',"\n";
    print HTML '		</tr>',"\n";
    
    my $ePerSite = $self->{ESITE};

    foreach my $site (keys %$ePerSite) {
	foreach my $reasonname (keys %{$ePerSite->{$site}}) {
	    my $reason = $ePerSite->{$site}->{$reasonname};
	    print HTML '<tr>',"\n";
	    print HTML '  <td><div align="center">',$site,'</div></td>',"\n";
#	    print HTML '  <td><div align="center">',$reason->{'cat'},'</div></td>',"\n";
	    print HTML '  <td><div align="center">',$reason->{'origin'},'</div></td>',"\n";
	    print HTML '  <td><div align="center">',$reason->{'n'},' of ',$ePerOrigin{'all'},'</div></td>',"\n";
	    print HTML '  <td><div align="center">',$reasonname,'</div></td>',"\n";
	    print HTML '</tr>',"\n";
	}

    }


    print HTML '	</table>',"\n";
    print HTML '	</div>',"\n";

    print HTML '	<br>',"\n";
    print HTML '	<hr>',"\n";	

    close(HTML);
}

#---------------------------------------------------------------------------------

sub new {
    
    my $self = shift @_;
    my %options = @_;

    use Data::Dumper;
    print "Got options from FaceTransfer:\n", Dumper %options,"\n";
    
    my $face = {%options};
    
    #we use generic PhedexIn data class, file name is passes as an option
    my $dataPhedexin = mod::DataFactory->new("Phedexin",%options);
    
    use Data::Dumper;
    print "Got XML data for Debug:\n"; print Dumper $dataPhedexin; print "\n";
    
    $face->{DATA} = $dataPhedexin->{DATA};
    $face->{METADATA} = $dataPhedexin->{METADATA};
    $face->{TRANSFERSUMM} = $dataPhedexin->{TRANSFERSUMM};
    $face->{EORIGIN} = $dataPhedexin->{EORIGIN};
    $face->{ESITE} = $dataPhedexin->{ESITE};

    $face->{'htmlfragfile'} = '../HTMLFragments/'.$face->{'test'}.'_HTML';
    
    bless $face, $self;
    return $face;

}

1;
