package mod::DataFactory;

use mod::data::DataGridkajobs;
use mod::data::DataSam;
use mod::data::DataDashboard;
use mod::data::DataFairshare;
use mod::data::DataUSCHI;
use mod::data::DataCMSDiskOnly;
use mod::data::DataCMSWriteTape;
use mod::data::DataXMLParser;
use mod::data::DataPhedexIn;
use mod::data::DataPhedexout;
use mod::data::DataQstat;
use mod::data::DataDashboardPlot;

#---------------------------------------------------------------------------------

sub new {
	my $self = shift @_;
	my $type = shift @_;

	my %options = @_;

	my $data;	

	if ($type eq "Gridkajobs") {
		$data = mod::data::DataGridkajobs->new(%options);
	} elsif ($type eq "SAM") {
		$data = mod::data::DataSam->new(%options);
	} elsif ($type eq "Dashboard") {
		$data = mod::data::DataDashboard->new(%options);
	} elsif ($type eq "Fairshare") {
		$data = mod::data::DataFairshare->new(%options);
	} elsif ($type eq "Phedexin") {
		$data = mod::data::DataPhedexIn->new(%options);
	} elsif ($type eq "Phedexout") {
		$data = mod::data::DataPhedexout->new(%options);
	} elsif ($type eq "USCHI") {
		$data = mod::data::DataUSCHI->new(%options);
	} elsif ($type eq "XMLParser") {
		$data = mod::data::DataXMLParser->new(%options);
	} elsif ($type eq "CMSDiskOnly") {
		$data = mod::data::DataCMSDiskOnly->new(%options);
	} elsif ($type eq "CMSWriteTape") {
		$data = mod::data::DataCMSWriteTape->new(%options);
	} elsif ($type eq "Qstat") {
		$data = mod::data::DataQstat->new(%options);
	} elsif ($type eq "DashboardPlot") {
		$data = mod::data::DataDashboardPlot->new(%options);
	}

	return $data;
}



1;
