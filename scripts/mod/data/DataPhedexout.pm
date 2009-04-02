package mod::data::DataPhedexout;

use mod::XML::Simple;
#use Data::Dumper;

sub new {

	$self = shift @_;
	%options = @_;

	$endtime = time; # unixtime (in seconds)
	$starttime = time - 3600 * $options{'time_range'};
	$from_node = $options{'from_node'};

	my $fname = "../data/phedex_fzk_outgoing_transfers.xml";
	$command_string = "wget \"http://t2.unl.edu/phedex/xml/quality_all?span=3600&show_expired=False&link=link&starttime=$starttime&no_mss=True&endtime=$endtime&to_node=.*&from_node=$from_node\" -O $fname";

	system($command_string);

	# open the xml source code
	if (!-e $fname || -z $fname || !open(SOURCE_FILE, $fname)){
	    print "Nonexistent or empty or can not open for read $fname, skipping\n";
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
	
	$xml = new XML::Simple;
	
	eval { $ref = $xml->XMLin($source_code); };
	if($@) {
	  $ref = {};
	  bless $ref, $self;
	} else {
	  $ref = {%{$ref}};
	  bless $ref,$self;
	}

}

1;
