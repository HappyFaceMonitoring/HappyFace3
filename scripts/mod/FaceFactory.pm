package mod::FaceFactory;

use mod::prod::FaceProduction;
use mod::trans::FaceTransfer;
use mod::infra::FaceInfrastructure;

#---------------------------------------------------------------------------------

sub new {
	my $self = shift @_;
	my $type = shift @_;

	my %options = @_;


	my $face;

	if ($type eq "prod") {
		$face = mod::prod::FaceProduction->new(%options);
	}
	elsif($type eq "transfer") {
		$face = mod::trans::FaceTransfer->new(%options);
	}
	elsif ($type eq "infra") {
		$face = mod::infra::FaceInfrastructure->new(%options);
	}

	return $face;
}

1;
