package mod::data::DataFairshare;

#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------


sub new {

$self = shift;
%fairshare;


my $fname = "../data/fairshare.txt";
system("wget --output-document=\"$fname\" \"http://grid.fzk.de/monitoring/export/fairshare.txt\"");


if (!-e $fname || -z $fname || !open(FAIRSHARE_FILE, $fname)){
    print "Nonexistent or empty or can not open for read $fname, skipping\n";
    my $ref = {};
    bless $ref, $self;
    return $self;
}


$i = 0;
while (<FAIRSHARE_FILE>) {
	chomp;
	if ($i != 0) {
		my ($experiment, $nominal, $used_walltime_180d, $TAB, $Korridor, $norm_Korridor, $used_walltime_1d, $usage_Korridor) = split;

		$fairshare{$experiment}{"nominal"} = $nominal;
		$fairshare{$experiment}{"used_walltime_180d"} = $used_walltime_180d;
		$fairshare{$experiment}{"TAB"} = $TAB;
		$fairshare{$experiment}{"Korridor"} = $Korridor;
		$fairshare{$experiment}{"norm_Korridor"} = $norm_Korridor;
		$fairshare{$experiment}{"used_walltime_1d"} = $nused_walltime_1d;
		$fairshare{$experiment}{"usage_Korridor"} = $usage_Korridor;		
	
	}
	$i = 1;
}

close(FAIRSHARE_FILE);

$fairshare = {%fairshare};
bless $fairshare, $self;
return $fairshare;


}

1;
