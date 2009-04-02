package mod::data::DataPhedexIn;

use strict;

use mod::XML::Simple;

use XML::LibXML;

use Data::Dumper;

#----------------------------------------------------------------------------

sub new {

    my $self = shift @_;
    my %options = @_;

    my $ref = {%options};

    print "Got options in DataPhedexIn for ".
	$options{'sourcexml'}.": ", Dumper \%options; print "\n";

    my $sourcexml = $options{'sourcexml'};
    my $targetxml = $options{'targetxml'};

    #arrayref of patterns to match against sites
    my $sitepats = $options{sites}; 

    system("cp $sourcexml $targetxml");
    
    if (!-e $sourcexml || -z $sourcexml || !open(SOURCE_FILE, $sourcexml) ) {
	print "Nonexistent or empty or can not open for read file \"$sourcexml\", skipping\n";
	my $ref = {};
	bless $ref, $self;
	return $ref;
    }
    close SOURCE_FILE;
    

    my ($data, $metadata, $transfersumm) = &parseXML($ref, $sourcexml);

    $ref->{DATA} = $data || {};
    $ref->{METADATA} = $metadata || {};
    $ref->{TRANSFERSUMM} = $transfersumm || {};




    print "Got Parsed data from xml file for ".$options{test}.":\n", Dumper $data; print "\n";


    #error per origin
    #we collect them all, since we know we have
    #either TO our site, or FROM our site
    #and never have to analyse any other link combination
    my %ePerOrigin = ();

    foreach my $fromsite (keys %$data) {
	foreach my $tosite (keys %{$data->{$fromsite}} ) {
	    foreach my $reasonname (keys %{$data->{$fromsite}->{$tosite}} ) {

		my $reason = $data->{$fromsite}->{$tosite}->{$reasonname};

		$ePerOrigin{$reason->{'origin'}} += $reason->{'n'};
		$ePerOrigin{'all'} += $reason->{'n'};
	    }
	}
    }

    $ref->{EORIGIN} = \%ePerOrigin;    
    print "Got ePerOrigin from xml file for ".$options{test}.":\n", Dumper $ref->{EORIGIN}; print "\n";

    #now we group error per site. 
    #Here we must chose whether to group based on FROM or TO our site.
    #we have to take a hint from the config
    my %ePerSite = ();

    foreach my $fromsite (keys %$data) {
	foreach my $tosite (keys %{$data->{$fromsite}} ) {

	    my $keysite = $fromsite;
	    $keysite = $tosite if ($options{'groupsites'} eq 'to');

	    foreach my $reasonname (keys %{$data->{$fromsite}->{$tosite}} ) {
		my $reason = $data->{$fromsite}->{$tosite}->{$reasonname};

		$ePerSite{$keysite}{$reasonname} = $reason;
#		$ePerSite{$keysite}{'all'} += $reason->{'n'};
	    }
	}
    }
    
    $ref->{ESITE} = \%ePerSite;
    print "Got ePerSite from xml file for ".$options{test}.":\n", Dumper $ref->{ESITE}; print "\n";

    bless $ref,$self;
    
    return $ref;
}

sub parseXML {
    my $self = shift;
    my $file = shift;

    my $data = {};

    my $metadata = {};

    my $transfersumm = {};

    my $sitepats = $self->{'sites'} || undef;

    my $parser = XML::LibXML->new();

#We parse file into a DOM object
#DOM is a document object model
    my $doc = $parser->parse_file( $file ); #print $doc->toString();

    $transfersumm->{"OK"}      = 0;
    $transfersumm->{"FAILED"}  = 0;
    $transfersumm->{"ALL"}     = 0;
    my $sitestats = $doc->getElementsByTagName("/ErrorPerSite/SiteStat/fromsite");
    my $isActive = "yes";
    if(@$sitestats == 1) {
	if( @$sitestats[0]->getAttribute('name') eq "noinfo") {
	    $isActive = "no"; 
	}
    }
    if($isActive eq "no") {
      $transfersumm->{"OK"}      = "not available";
      $transfersumm->{"FAILED"}  = "not available";
      $transfersumm->{"ALL"}     = "not available";
    } else {
      foreach my $sitestat (@$sitestats) {
	my $fromsitename = $sitestat->getAttribute('name');
	next if ($sitepats && ! &siteMatch($fromsitename, $sitepats));
	foreach my $summaryTag (keys %$transfersumm) {
	  my $val = $sitestat->getAttribute($summaryTag);
	  $transfersumm->{$summaryTag} += $val if($val);
	}
      }
      $transfersumm->{"ALL"} = $transfersumm->{"OK"} +  $transfersumm->{"FAILED"};
    }
  
#get times etc - "metadata"
    my $rootelement = $doc->getElementsByTagName("/ErrorPerSite"); #pr
    foreach my $at ($rootelement->[0]->attributes) {
	$metadata->{$at->name} = $at->value;
    }

#get number of successful transfers as well?
#they are not yet supplied in xml files

#This is how we can look up data in the DOM object
#we can search elements by tag, return a plain perl list
    my $fromsites = $doc->getElementsByTagName("/ErrorPerSite/fromsite"); #print Dumper $errors;
    foreach my $fromsite (@$fromsites) {
	#This is how we get attributes
	my $fromsitename = $fromsite->getAttribute('name');

	print "Parsing: got fromsite $fromsitename\n";

	next if ($sitepats && ! &siteMatch($fromsitename, $sitepats));

	my $tosites = $fromsite->getElementsByTagName("tosite");
	foreach my $tosite (@$tosites) {
	    #This is how we get attributes
	    my $tositename = $tosite->getAttribute('name');   

	    my $reasons = $tosite->getElementsByTagName("reason");
	
	    foreach my $reason (@$reasons) {
		#this is how we get text data (content) of elements
		my $reasonname = $reason->firstChild->nodeValue;
		
		#since we get all of it, with formatting of original file
		#we need to remove this leading and trailing non-char data
		$reasonname =~ s/^\W+//; $reasonname =~ s/\W+$//;
		
		#next is illustrations on working with a list of attributes
		#and attribute objects
		foreach my $at ($reason->attributes) {
		    $data->{$fromsitename}->{$tositename}->{$reasonname}->{$at->name} = $at->value;
		}
	    }	
	}
    }

    return $data, $metadata, $transfersumm;
}


sub siteMatch {
    my $site = shift;
    my $sitepats = shift;

    my $sitematch = 0;

    foreach my $sitepat (@$sitepats){
#	print "Checking sitepat $sitepat agains site $site\n";
	if ($site =~ m/$sitepat/) { $sitematch = 1; last }
    }

    return $sitematch;
}

1;
