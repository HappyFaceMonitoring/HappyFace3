package mod::trans::FaceTransfer;

use strict 'vars';

use mod::trans::FacePhedexin;
use mod::trans::FacePhedexout;

use Data::Dumper;

#---------------------------------------------------------------------------------

sub collectResults {
    my $self = shift @_;
    my $facevalue = -1;
    
    my @tests;
    
    foreach my $test (sort keys %{$self}) {
	my $result_value	= $self->{$test}->result();
	if ($result_value > $facevalue) { $facevalue = $result_value; }
    }
    
    return $facevalue;
    
}

sub sortTransfer {
    return 1 if ($a =~ /ProdCern/);
    return -1 if ($b =~ /ProdCern/);
    return 1 if ($a =~ /Prod/);
    return -1 if ($b =~ /Prod/);
    return 1 if ($a =~ /out/);
    return -1 if ($b =~ /out/);

    return 0;
}



#---------------------------------------------------------------------------------

sub createHTMLFragment {
    my $self = shift @_;
    my @tests;
    
    open(TRANSFER_HTML, ">../HTMLFragments/TRANSFER_HTML");
    
    foreach my $test (sort keys %{$self}) {
	$self->{$test}->createHTMLFragment();
	my $file_handle; my $file;
	open($file_handle = $test, $file = "../HTMLFragments/".$test."_HTML");
	while (<$file_handle>) {
	    chomp;
	    print TRANSFER_HTML "$_\n";
	}
	close($file_handle);
    }
    
    close(TRANSFER_HTML);
    
}

#---------------------------------------------------------------------------------

sub new {
    my $self = shift @_;
    my %options = @_;
    
    my %face = ();
    
    my $i = 0;
    foreach my $test (keys %options) {
	if ($test =~ /Phedexin/) {
	    $face{$test} = mod::trans::FacePhedexin->new(%{$options{$test}});
	}
	elsif ($test =~ /Phedexout/) {
#	    $face{$test} = mod::trans::FacePhedexout->new(%{$options{$test}});
	    $face{$test} = mod::trans::FacePhedexin->new(%{$options{$test}});
	}
	else {
	    print "No constructor for test $test in FaceTransfer\n";
	}
    }
    
    my $face = {%face};
    bless $face, $self;
    return $face;
}

1;
