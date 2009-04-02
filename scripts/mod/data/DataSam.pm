package mod::data::DataSam;

use mod::XML::Simple;
#use Data::Dumper;

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------

sub new {

	$self = shift @_;
	%options = @_;
	$site = $options{"site"};

	$fname = "../data/db_sam_summary.xml";

	$command_string = "curl -H \'Accept: text/xml\' \'http://lxarda16.cern.ch/dashboard/request.py/latestresultssmry?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all\' | xmllint --format -> $fname";

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
	
	$ref = $xml->XMLin($source_code);
	
	$ref = {%{$ref}};
	
	bless $ref, $self;
	
}

1;
