package mod::data::DataXMLParser;

use mod::XML::Simple;
#use Data::Dumper;

#---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------

sub new {

	$self = shift @_;

	%options = @_;

	$url = $options{'url'};
	$fname = $options{'filename'};

	$command_string = "curl -H \'Accept: text/xml\' \'$url\' | xmllint --format -> ../data/$fname";

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
