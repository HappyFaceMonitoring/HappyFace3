package mod::data::DataUSCHI;

use mod::XML::Simple;
#use Data::Dumper;

#---------------------------------------------------------------------------------

sub new {

$self = shift @_;
my %options = @_;

my $inXMLfile = $options{"sourcexml"};
my $outXMLfile = $options{"targetxml"};

$status = system("cp $inXMLfile $outXMLfile");

if (!-e $outXMLfile || -z $outXMLfile || !open(SOURCE_FILE, $outXMLfile) ) {
  print "Nonexistent or empty or can not open for read $outXMLfile, skipping\n";
  my $ref = {};
  bless $ref, $self;
  return $self;
}


# load the xml source code to the string '$source_code'
$source_code = "";
while(<SOURCE_FILE>) {
	#chop;
	$source_code = $source_code . $_;
}
close(SOURCE_FILE);

$xml = new XML::Simple;

$ref = $xml->XMLin($source_code);

$ref = {%{$ref}};

bless $ref,$self;

}

1;
