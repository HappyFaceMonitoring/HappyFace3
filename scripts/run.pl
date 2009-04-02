#!/usr/bin/perl

use mod::DataFactory;
use mod::FaceFactory;
use mod::HTMLFactory;
use mod::CacheFactory;

system("./getLogFiles.sh");

# --------------------------------------------------------------
# options for the SAM Test
%sam_options = (
 	"site" 				=> "T1_DE_FZK",
);

# --------------------------------------------------------------
# options for the Qstat Test
%qstat_options = (
		  sourcexml		=>	"../inputFiles/qstat.xml",
		  targetxml		=>	"../data/qstat.xml",
);


# -------------------------------------------------------------
# options for the Fairshare Test
# needed information: experiment, the lower limit of the nominal fairshare fraction,
# the lower limit of the fraction run/(run+queued)
%fairshare_options = (
	"experiment"			=> "cms",
	"nom_fairshare_limit_frac"	=> 0.66,
	"run_queued_limit_frac"	=> 0.8,
);

# -------------------------------------------------------------
# options for the Dashboard Test
# needed information: activity name, upper limit of the unknown_grid value
# lower limit of the success_app value
%dashboard_options = (
	"activity"			=> "production",
);

# =============================================================
# =============================================================
# create the production face object
my $prodFace = mod::FaceFactory->new("prod", 
				     %prodOptions = 
				     (
				      "SAM"		=> \%sam_options,
				      "Fairshare"	=> \%fairshare_options,
				      "Dashboard"	=> \%dashboard_options,
				      "Qstat"		=> \%qstat_options,
				      ));

my %phedex_transfer_checks = 
    (
     allowed_dest_errors=>.5,
     allowed_client_errors=>.1,
     relevant_frac=> 0.8,
     warn_limit	  => 0.66,
     critical_limit=> 0.1,			      
     );

# -------------------------------------------------------------
# options for phedex incoming transfer test (debug)
%phedexin_debug_options = 
    (%phedex_transfer_checks,
     test=>'xDebugPhedexin',
     sourcexml=>"../inputFiles/logx",
     targetxml=>"../data/phedex_fzk_incoming_transfers.xml",
     groupsites=>'from', #to present in summary table of error origins
     htmltitle=>'PhEDEx Test for Incoming Transfers (Debug)'
     );


# options for phedex incoming CERN transfer test (debug)
#value of sites is array of patterns to match agains site names
%phedexin_debug_cern_options = 
    (%phedex_transfer_checks,
     test=>'xDebugPhedexinCern',
     sourcexml=>"../inputFiles/logx",
     targetxml=>"../data/phedex_fzk_incoming_transfers.xml",
     sites=>['CERN'],
     groupsites=>'from', #to present in summary table of error origins
     htmltitle=>'PhEDEx Test for Incoming Transfers from CERN (Debug)'
     );

# options for phedex incoming transfer test (production)
%phedexin_prod_options = 
    (%phedex_transfer_checks,
     test=>'aProdPhedexin',
     sourcexml=>"../inputFiles/logxprod",
     targetxml=>"../data/phedex_prod_fzk_incoming_transfers.xml",
     groupsites=>'from', #to present in summary table of error origins
     htmltitle=>'PhEDEx Test for Incoming Transfers (Prod)'
     );


# options for phedex incoming CERN transfer test (production)
%phedexin_prod_cern_options = 
    ( %phedex_transfer_checks,
      test=>'aProdPhedexinCern',
      sourcexml=>"../inputFiles/logxprod",
      targetxml=>"../data/phedex_prod_fzk_incoming_transfers.xml",
      sites=>['CERN'],
      groupsites=>'from', #to present in summary table of error origins
      htmltitle=>'PhEDEx Test for Incoming Transfers from CERN (Prod)'
      );


# -------------------------------------------------------------
# options for phedex outgoing transfer test - Prod
%phedexoutProd_options = 
    ( %phedex_transfer_checks,
      test=>'aProdPhedexout',
      sourcexml=>"../inputFiles/logxfromfzk",
      targetxml=>"../data/phedex_fzk_outgoing_transfers.xml",
      groupsites=>'to', #to present in summary table of error origins
      htmltitle=>'PhEDEx Test for Outgoing Transfers from FZK (Prod)',
      "node_limit"		=> 0.33,
      "global_limit"		=> 0.66,
      "time_range"		=> 1, # in hours
      "from_node"		=> "FZK",
);

# -------------------------------------------------------------
# options for phedex outgoing transfer test - Debug
%phedexoutDebug_options = 
    ( %phedex_transfer_checks,
      test=>'xDebugPhedexout',
      sourcexml=>"../inputFiles/logxfromfzkDebug",
      targetxml=>"../data/phedex_fzk_outgoing_transfers-debug.xml",
      groupsites=>'to', #to present in summary table of error origins
      htmltitle=>'PhEDEx Test for Outgoing Transfers from FZK (Debug)',
      "node_limit"		=> 0.33,
      "global_limit"		=> 0.66,
      "time_range"		=> 1, # in hours
      "from_node"		=> "FZK",
);





# =============================================================
# =============================================================
# create the transfer face object
my $transferFace = mod::FaceFactory->
    new("transfer", 
	%transferOptions = (
			    "aProdPhedexout"	=> \%phedexoutProd_options,
			    "aProdPhedexin"  => \%phedexin_prod_options,
			    "aProdPhedexinCern" => \%phedexin_prod_cern_options,
			    "xDebugPhedexin"	=> \%phedexin_debug_options,
			    "xDebugPhedexinCern"	=> \%phedexin_debug_cern_options,
			    "xDebugPhedexout"	=> \%phedexoutDebug_options,
			    )
	);



# -------------------------------------------------------------
# options for phedex outgoing transfer test
%uschi_options = (
		  sourcexml=>"../inputFiles/monjobs_happyface_summary.xml",
		  targetxml=>"../data/monjobs_happyface_summary.xml",
);


# =============================================================
# =============================================================
# create the infrastructure face object
my $infraFace = mod::FaceFactory->new("infra", %infraOptions = (
								"USCHI"		=> \%uschi_options
							));




# -------------------------------------------------------------
# options for the HTML File Creater
%html_options = (
	"production_face"	=> $prodFace->collectResults(),
	"transfer_face"		=> $transferFace->collectResults(),
	"infrastructure_face"	=> $infraFace->collectResults(),
	"cached_plots_standard"	=> 1,
	"cached_plots_shift"	=> 1,
	"cached_plots_standardtransfer"	=> 1,
#	"cached_plots_tapemon"	=> 1,
);

# =============================================================
# =============================================================

$prodFace->createHTMLFragment();
$transferFace->createHTMLFragment();
$infraFace->createHTMLFragment();

mod::HTMLFactory->createHTMLFile(%html_options);

