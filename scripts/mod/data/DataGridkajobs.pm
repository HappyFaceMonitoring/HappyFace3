package mod::data::DataGridkajobs;

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------


sub new {

	$self = shift;
	%gridkajobs;

	$fname1 = "../data/gridka_pbs_jobs_all_queued";
	$fname2 = "../data/gridka_pbs_jobs_all_running";


	system("wget --output-document=\"$fname1\" \"http://grid.fzk.de/monitoring/export/pbs_jobs_all_queued\"");
	system("wget --output-document=\"$fname2\" \"http://grid.fzk.de/monitoring/export/pbs_jobs_all_running\"");

	if (!-e $fname1 || -z $fname1 || !open(ALL_QUEUED, $fname1)){
	    print "Nonexistent or empty or can not open for read $fname, skipping\n";
	    my $ref = {};
	    bless $ref, $self;
	    return $self;
	}
	if (!-e $fname2 || -z $fname2 || !open(ALL_RUNNING, $fname2)){
	    print "Nonexistent or empty or can not open for read $fname, skipping\n";
	    my $ref = {};
	    bless $ref, $self;
	    return $self;
	}

	while(<ALL_RUNNING>) {
		chomp;
		my ($experiment, $running) = split(/\ /);
		$gridkajobs{$experiment}{"running"} = $running;
	}
	while(<ALL_QUEUED>) {
		chomp;
		my ($experiment, $queued) = split(/\ /);
		$gridkajobs{$experiment}{"queued"} = $queued;
	}

	my $sum_running = 0;
	my $sum_queued = 0;	

	foreach my $key (keys %gridkajobs) {
		$gridkajobs{$key}{"all"} = $gridkajobs{$key}{"running"} + $gridkajobs{$key}{"queued"};

		$sum_running	+= $gridkajobs{$key}{"running"};
		$sum_queued	+= $gridkajobs{$key}{"queued"};
	}

	$gridkajobs{"sum"}{"running"}	= $sum_running;
	$gridkajobs{"sum"}{"queued"}	= $sum_queued;
	$gridkajobs{"sum"}{"all"}	= $sum_running + $sum_queued;

	close(ALL_RUNNING);
	close(ALL_QUEUED);

	$gridkajobs = {%gridkajobs};

	bless $gridkajobs, $self;
	return $gridkajobs;

}

1;
