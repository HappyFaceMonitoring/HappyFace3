package mod::data::DataDashboardPlot;

use mod::XML::Simple;
#use Data::Dumper;

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------

sub new {

	$self = shift @_;

	%options = @_;

	$site = $options{'site'};


	my $fname1 = "../data/cms_dashboard.html";
	$command_string1 =  "wget --output-document=\"$fname1\" \"http://lxarda09.cern.ch/dashboard/request.py/jobsummary?user=&site=FZK-LCG2+%28Karlsruhe%2C+Germany%29&ce=&submissiontool=&dataset=&application=&rb=&activity=&grid=&sortby=activity&nbars=\"";

	system($command_string1);

	# open the html source code
	if (!-e $fname1 || -z $fname || !open(SOURCE_FILE, $fname1)){
	    print "Nonexistent or empty or can not open for read $fname1, skipping\n";
	    my $ref = {};
	    bless $ref, $self;
	    return $self;
	}


	# load the xml source code to the string '$source_code'
	$source_code = "";
	while(<SOURCE_FILE>) {
		chop;
		$source_code = $source_code . $_;
	}
	close(SOURCE_FILE);



	while ($source_code =~ m{src=\"([^<]+).png\"\ border}gx) {
		$plot_url_fragment = $1;
	}


	my $url = 'http://lxarda09.cern.ch' . $plot_url_fragment . '.png';

	$fname2 = "../images/cms_dashboard.png";

	$command_string2 = "wget --output-document=\"$fname2\" \"$url\"";
	system($command_string2);

	# for index.html
	$fname2 = "images/cms_dashboard.png";

	return $fname2;

}

1;
