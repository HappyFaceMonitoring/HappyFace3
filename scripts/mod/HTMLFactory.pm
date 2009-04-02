package mod::HTMLFactory;

sub createHTMLFile {
	$self = shift @_;
	my %options = @_;
	my @facevalue;
	my @faceimage;

# ==================================================================================================

	$unixtime		= time();
	$humantime		= localtime($unixtime);
	@ht_array		= split(/ +/,$humantime);
	@time			= split(/:/,$ht_array[3]);
	$timestring		= "$ht_array[0], $ht_array[2]. $ht_array[1] $ht_array[4], $time[0]:$time[1]";

# ==================================================================================================

	open(FINAL_HTML, ">../HTMLFragments/FINAL_HTML",);

	$faceimage[1] = '<img src="images/fernglas.gif" />';

	$facevalue[2]	= $options{'infrastructure_face'};
	$facevalue[3]	= $options{'transfer_face'};
	$facevalue[4]	= $options{'production_face'};

	for ($i = 2; $i <= 4; $i++) {
		if ($facevalue[$i] == -1) { $faceimage[$i] = '<img src="images/vault.png" />'; }
		elsif ($facevalue[$i] == 0) { $faceimage[$i] = '<img src="images/4.png" />'; }
		elsif ($facevalue[$i] == 1) { $faceimage[$i] = '<img src="images/3.png" />'; }
		elsif ($facevalue[$i] == 2) { $faceimage[$i] = '<img src="images/1.png" />'; }
	}

	$faceimage[5] = '<img src="images/plots3.gif" />';
	$faceimage[6] = '<img src="images/plots3.gif" />';


# ==================================================================================================
# ==================================================================================================

	print FINAL_HTML '	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',"\n";
	print FINAL_HTML '	<html xmlns="http://www.w3.org/1999/xhtml">',"\n";
	print FINAL_HTML '	<head>',"\n";
	print FINAL_HTML '	<meta http-equiv="refresh" content="300" charset=utf-8" />',"\n";
	print FINAL_HTML '	<title>Monitoring Center</title>',"\n";
	print FINAL_HTML '	<script src="SpryAssets/SpryTabbedPanels.js" type="text/javascript"></script>',"\n";
	print FINAL_HTML '	<link href="SpryAssets/SpryTabbedPanels.css" rel="stylesheet" type="text/css" />',"\n";
	print FINAL_HTML '	</head>',"\n";

	print FINAL_HTML '	<body>',"\n";


# ==================================================================================================

	print FINAL_HTML '	<div id="TabbedPanels1" class="TabbedPanels">',"\n";
	print FINAL_HTML '	  <ul class="TabbedPanelsTabGroup">',"\n";

for ($i = 1; $i <= 6; $i++) {
	print FINAL_HTML '	    <li class="TabbedPanelsTab" tabindex="0" onFocus="this.blur()">',"\n";
	print FINAL_HTML '	      <table border="0">',"\n";
	print FINAL_HTML '	        <tr>',"\n";
	print FINAL_HTML '	          <td>';

	print FINAL_HTML $faceimage[$i],"\n";

	print FINAL_HTML '		  </td>',"\n";
	print FINAL_HTML '	        </tr>',"\n";

# ==================================================================================================

	print FINAL_HTML '	        <tr>',"\n";
	print FINAL_HTML '	          <td><div align="center">';

	if ($i == 1) {print FINAL_HTML 'Cached Plots for Shifters';}
	elsif ($i == 2)	{print FINAL_HTML 'Infrastracture Status';}
	elsif ($i == 3) {print FINAL_HTML 'Transfer Status';}
	elsif ($i == 4) {print FINAL_HTML 'Production Status';}
	elsif ($i == 5) {print FINAL_HTML 'Standard Cached Plots';}
	elsif ($i == 6) {print FINAL_HTML 'Transfer Cached Plots';}

	print FINAL_HTML '		  </div></td>',"\n";
	print FINAL_HTML '	        </tr>',"\n";
	print FINAL_HTML '	      </table>',"\n";
	print FINAL_HTML '	    </li>',"\n";
}
 	print FINAL_HTML '	 </ul>',"\n";


# ==================================================================================================
# ==================================================================================================

 	print FINAL_HTML '	  <div class="TabbedPanelsContentGroup">',"\n";

# ==================================================================================================

 	print FINAL_HTML '	    <div class="TabbedPanelsContent">',"\n";
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";

if ($options{'cached_plots_shift'} == 1) {
	$cacheShift = mod::CacheFactory->new('Shift');
	$cacheShift->createHTMLFragment();

	open (CACHESHIFT_HTML, "../HTMLFragments/CACHESHIFT_HTML.txt");
		while (<CACHESHIFT_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
	close(CACHESHIFT_HTML);
}

	print FINAL_HTML '	    </div>',"\n";

# ==================================================================================================



 	print FINAL_HTML '	    <div class="TabbedPanelsContent">';
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";
	if ($options{'infrastructre_face'} != -1) {
		open(INFRA_HTML, "../HTMLFragments/INFRA_HTML");
		while (<INFRA_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
		close (INFRA_HTML);
	}
	print FINAL_HTML '	    </div>',"\n";

# ==================================================================================================

 	print FINAL_HTML '	    <div class="TabbedPanelsContent">',"\n";
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";
	if ($options{'transfer_face'} != -1) {
		open(TRANSFER_HTML, "../HTMLFragments/TRANSFER_HTML");
		while (<TRANSFER_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
		close (TRANSFER_HTML);
	}
	print FINAL_HTML '	    </div>',"\n";

# ==================================================================================================

 	print FINAL_HTML '	    <div class="TabbedPanelsContent">',"\n";
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";
	if ($options{'production_face'} != -1) {
		open(PROD_HTML, "../HTMLFragments/PROD_HTML");
		while (<PROD_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
		close (PROD_HTML);
	}
	print FINAL_HTML '	    </div>',"\n";

# ==================================================================================================


 	print FINAL_HTML '	    <div class="TabbedPanelsContent">',"\n";
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";

if ($options{'cached_plots_standard'} == 1) {
	$cacheStandard = mod::CacheFactory->new('Standard');
	$cacheStandard->createHTMLFragment();

	open (CACHESTANDARD_HTML, "../HTMLFragments/CACHESTANDARD_HTML.txt");
		while (<CACHESTANDARD_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
	close(CACHESTANDARD_HTML);
}
	print FINAL_HTML '	    </div>',"\n";


# ==================================================================================================


 	print FINAL_HTML '	    <div class="TabbedPanelsContent">',"\n";
	print FINAL_HTML '		<h4>Last Update: ',$timestring,'</h4>',"\n";
	print FINAL_HTML '		<hr>',"\n";

if ($options{'cached_plots_standardtransfer'} == 1) {
	$cacheStandard = mod::CacheFactory->new('Transfer');
	$cacheStandard->createHTMLFragment();

	open (CACHESTANDARD_HTML, "../HTMLFragments/CACHESTANDARDTRANSFER_HTML.txt");
		while (<CACHESTANDARD_HTML>) {
			chomp;
			print FINAL_HTML "$_\n";
		}
	close(CACHESTANDARD_HTML);
}
	print FINAL_HTML '	    </div>',"\n";


# ==================================================================================================
# ==================================================================================================

 	print FINAL_HTML '	  </div>',"\n";
 	print FINAL_HTML '	</div>',"\n";

 	print FINAL_HTML '	<script type="text/javascript">',"\n";
 	print FINAL_HTML '	<!--',"\n";
 	print FINAL_HTML '	var TabbedPanels1 = new Spry.Widget.TabbedPanels("TabbedPanels1");',"\n";
 	print FINAL_HTML '	//-->',"\n";
 	print FINAL_HTML '	</script>',"\n";

 	print FINAL_HTML '	<script type="text/javascript">',"\n";
 	print FINAL_HTML '	<!--',"\n";
 	print FINAL_HTML '	function show_hide(me) {',"\n";
 	print FINAL_HTML '		if (document.getElementById(me).style.display=="none") {',"\n";
 	print FINAL_HTML '			document.getElementById(me).style.display="block";',"\n";
 	print FINAL_HTML '		} else {',"\n";
 	print FINAL_HTML '			document.getElementById(me).style.display="none";',"\n";
 	print FINAL_HTML '		}',"\n";
 	print FINAL_HTML '	}',"\n";
 	print FINAL_HTML '	//-->',"\n";
 	print FINAL_HTML '	</script>',"\n";

 	print FINAL_HTML '	</body>',"\n";
 	print FINAL_HTML '	</html>',"\n";


	close(FINAL_HTML);

	# replace the old output
	system("rm ../index.html");
	system("cp ../HTMLFragments/FINAL_HTML ../index.html");

# ==================================================================================================
# ==================================================================================================
	
}

1;
