package mod::cache::CacheStandard;

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	open(CACHESTANDARD_HTML, ">../HTMLFragments/CACHESTANDARD_HTML.txt");

	print CACHESTANDARD_HTML '		<br>',"\n";

	print CACHESTANDARD_HTML '	<a href="http://grid.fzk.de/monitoring/main.html">GridKa Monitoring</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="http://lxarda16.cern.ch/dashboard/request.py/latestresultssmry?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all">SAM (T1_DE_FZK)</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="http://lxarda09.cern.ch/dashboard/request.py/jobsummary?user=&site=FZK-LCG2+%28Karlsruhe%2C+Germany%29&ce=&submissiontool=&dataset=&application=&rb=&activity=&grid=&sortby=activity&nbars=">CMS Dashboard (FZK-LCG2)</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="https://twiki.cern.ch/twiki/bin/view/CMS/GridKaPhedexMonitor">GridKa PhEDEx Monitor</a>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";



# create HTML part with the plots, titles, descriptions from the config_file "./data/CacheStandard_config_file"
for ($i = 0; $i <= ($self->{'plot_number'}); $i++) {
	$status = system('wget --output-document="../images/CacheStandard_plot_'.$i.'.png" "'.$self->{'link'}[$i].'"');

	print CACHESTANDARD_HTML '		<br>',"\n";

	print CACHESTANDARD_HTML '		<table width="100%">',"\n";
	print CACHESTANDARD_HTML '			<tr><td><strong>',$self->{'title'}[$i],'</strong></td></tr>',"\n";	
	print CACHESTANDARD_HTML '			<tr><td><a href="',$self->{'link'}[$i],'"><img src="images/CacheStandard_plot_',$i,'.png" style="border: 0px solid;"></a></td></tr>',"\n";
	print CACHESTANDARD_HTML '                        <tr><td>',$self->{'description'}[$i],'</td></tr>',"\n";
	print CACHESTANDARD_HTML '		</table>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";

}


#CMS SAM test

        print CACHESTANDARD_HTML '         <iframe src="http://lxarda16.cern.ch/dashboard/request.py/latestresultssmrytable?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all" width="100%" height="300" frameborder="0" name="SELFHTML_in_a_box">',"\n";
        print CACHESTANDARD_HTML '         </iframe>',"\n";

	#description of the SAM table
        print CACHESTANDARD_HTML '         <table width="860">',"\n";
        print CACHESTANDARD_HTML '                 <tr align="center"><td>Here is SAM test results. Yuo should clearly separate two failure cases - tests that fail entirely due to GridKa and test thqat may fail due to CMS. Several CEs here are for redundancy, thus you should only report if all CEs show an error for a particular test. Jobs submission test fail due to GridKa (js, jsprod). Also frontier and squod tests. If you see that these tests fail for <b>all</b> CEs - send GridKa a GGUS ticket. In the ticket, say that all CE fail specific CMS test and list the log of one test (click on the "error"cell to get the log - you certificate in the browser is necessary).<p> MC test may be due to CMS failure (e.g. when disk-noly buffer fill up). Report MC test failure to CMS expert. If SE tests are failing, contact CMS expert as well</td></tr>',"\n";
        print CACHESTANDARD_HTML '         </table>',"\n";

        print CACHESTANDARD_HTML '         <br>',"\n";
        print CACHESTANDARD_HTML '         <hr>',"\n";



	close(CACHESTANDARD_HTML);
}

#---------------------------------------------------------------------------------

sub new {

$self = shift @_;

# open the config file 
open (PLOTS_FILE, "../data/CacheStandard_config_file");

$i = 0;

# load the data from the config file
while(<PLOTS_FILE>) {
	chomp;
	my ($link, $title, $description) = split(/\t/);
	$plots{"link"}[$i] = $link;
	$plots{"title"}[$i] = $title;
	$plots{"description"}[$i] = $description;
	$i++;
}
$plot_number = $i-1;

close(PLOTS_FILE);

# max service name number
$plots{"plot_number"} = $plot_number;

$plots = {%plots};
bless $plots, $self;
return $plots;


}

1;
