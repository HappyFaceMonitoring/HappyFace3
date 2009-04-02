package mod::CacheFactory;

use mod::cache::CacheStandard;
use mod::cache::CacheStandardTransfer;
use mod::cache::CacheShift;

#---------------------------------------------------------------------------------

sub new {
	my $self = shift @_;
	my $type = shift @_;

	my %options = @_;


	my $cache;

	if ($type eq "Standard") {
		$cache = mod::cache::CacheStandard->new(%options);
	}
	elsif($type eq "Shift") {
		$cache = mod::cache::CacheShift->new(%options);
	}
	elsif($type eq "Transfer") {
		$cache = mod::cache::CacheStandardTransfer->new(%options);
	}

	return $cache;
}

1;
