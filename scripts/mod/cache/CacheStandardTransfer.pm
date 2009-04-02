package mod::cache::CacheStandardTransfer;

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	open(CACHESTANDARD_HTML, ">../HTMLFragments/CACHESTANDARDTRANSFER_HTML.txt");

	print CACHESTANDARD_HTML '		<br>',"\n";

	print CACHESTANDARD_HTML '	<a href="http://grid.fzk.de/monitoring/main.html">GridKa Monitoring</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="http://lxarda16.cern.ch/dashboard/request.py/latestresultssmry?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all">SAM (T1_DE_FZK)</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="http://lxarda09.cern.ch/dashboard/request.py/jobsummary?user=&site=FZK-LCG2+%28Karlsruhe%2C+Germany%29&ce=&submissiontool=&dataset=&application=&rb=&activity=&grid=&sortby=activity&nbars=">CMS Dashboard (FZK-LCG2)</a> |',"\n";
	print CACHESTANDARD_HTML '	<a href="https://twiki.cern.ch/twiki/bin/view/CMS/GridKaPhedexMonitor">GridKa PhEDEx Monitor</a>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";

	# insert the PhEDEx CMS Data Transfers table (to DE)
	# 2008-08-20, Volker Buege: Change in Phedex url
	#                           cmsdoc.cern.ch/cms/aprom/phedex/ --> cmsweb.cern.ch/phedex/
	print CACHESTANDARD_HTML '		<iframe src="http://cmsweb.cern.ch/phedex/prod/Activity::Rate?span=d&tofilter=FZK&andor=or&fromfilter=" width="100%" height="600" frameborder="0" name="SELFHTML_in_a_box">',"\n";
	print CACHESTANDARD_HTML '		</iframe>',"\n";

	print CACHESTANDARD_HTML '		<table width="860">',"\n";
	print CACHESTANDARD_HTML '                 <tr align="center"><td></td></tr>',"\n";
	print CACHESTANDARD_HTML '		</table>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";


	# insert the PhEDEx CMS Data Transfers table (from DE)
	# 2008-08-20, Volker Buege: Change in Phedex url
	#                           cmsdoc.cern.ch/cms/aprom/phedex/ --> cmsweb.cern.ch/phedex/
	print CACHESTANDARD_HTML '		<iframe src="http://cmsweb.cern.ch/phedex/prod/Activity::Rate?span=d&tofilter=&andor=or&fromfilter=FZK" width="100%" height="600" frameborder="0" name="SELFHTML_in_a_box">',"\n";
	print CACHESTANDARD_HTML '		</iframe>',"\n";

	print CACHESTANDARD_HTML '		<table width="860">',"\n";
	print CACHESTANDARD_HTML '                 <tr align="center"><td></td></tr>',"\n";
	print CACHESTANDARD_HTML '		</table>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";




# create HTML part with the plots, titles, descriptions from the config_file "./data/CacheStandard_config_file"
for ($i = 0; $i <= ($self->{'plot_number'}); $i++) {
	$status = system('wget --output-document="../images/CacheStandardTransfer_plot_'.$i.'.png" "'.$self->{'link'}[$i].'"');

	print CACHESTANDARD_HTML '		<br>',"\n";

	print CACHESTANDARD_HTML '		<table width="100%">',"\n";
	print CACHESTANDARD_HTML '			<tr><td><strong>',$self->{'title'}[$i],'</strong></td></tr>',"\n";	
	print CACHESTANDARD_HTML '			<tr><td><a href="',$self->{'link'}[$i],'"><img src="images/CacheStandardTransfer_plot_',$i,'.png" style="border: 0px solid;"></a></td></tr>',"\n";
	print CACHESTANDARD_HTML '                        <tr><td>',$self->{'description'}[$i],'</td></tr>',"\n";
	print CACHESTANDARD_HTML '		</table>',"\n";

	print CACHESTANDARD_HTML '		<br>',"\n";
	print CACHESTANDARD_HTML '		<hr>',"\n";

}


#dcache plots

        print CACHESTANDARD_HTML '         <iframe src="http://ekpganglia.physik.uni-karlsruhe.de/~happyface/HappyFace/data/cms_disk_only.html" width="100%" height="500" frameborder="0" name="SELFHTML_in_a_box">',"\n";
        print CACHESTANDARD_HTML '         </iframe>',"\n";

	# description of the CMS-DISK-ONLY pools
        print CACHESTANDARD_HTML '         <table width="860">',"\n";
        print CACHESTANDARD_HTML '                 <tr align="center"><td>Listed in the table are dCache pools - think about them as file systems, or disks, where data is put and stored. If they fill up, you cant transfer to it anymore. Disk-only pools above are used for intermediate result of production. After these intermediate results are merged, the data should be deleted by production team. Also this disk-only pool is used to by Phedex Debug transfers. Disk can get full for a number of reasons, but the all are due to CMS - we are responsible for cleaning it up, not GridKa. <p>If you see Disk only pools close to fill up (to little yellow space), notify CMS expert on call.</td></tr>',"\n";
        print CACHESTANDARD_HTML '         </table>',"\n";

        print CACHESTANDARD_HTML '         <br>',"\n";
        print CACHESTANDARD_HTML '         <hr>',"\n";

        print CACHESTANDARD_HTML '         <iframe src="http://ekpganglia.physik.uni-karlsruhe.de/~happyface/HappyFace/data/cms_write_tape.html" width="100%" height="500" frameborder="0" name="SELFHTML_in_a_box">',"\n";
        print CACHESTANDARD_HTML '         </iframe>',"\n";

	# description of the CMS-WRITE_TAPE pools
        print CACHESTANDARD_HTML '         <table width="860">',"\n";
        print CACHESTANDARD_HTML '                 <tr align="center"><td>Listed in the table are dCache pools - think about them as file systems, or disks, where data is put and stored. If they fill up, you cant transfer to it anymore. Tape-write buffers are used as an intermediate buffer where files are transferred from outside and stored until they are written to tape (this is called migration). If tape migration doesnt work for any reason, then tape-write dCache buffers can fill up and thus transfer will also stop. Migration to tape is managed by GridKa. Thus if you see tape write only pools close to fill up (to much red space), notify GridKa. To assist you in judging when is too much, look at Infrastructure face - there is a test under this tab that automatically calculates occupied space and checks against threshold. Please also report if individual pools are filled up, not only the overal status. In your GGUS ticket state that tape-migration buffers are so many % full - take the number from that infrastructure test. Also cross check with tape migration rate plot on this page. Its most likely that its low or 0 as well. </td></tr>',"\n";
        print CACHESTANDARD_HTML '         </table>',"\n";

        print CACHESTANDARD_HTML '         <br>',"\n";
        print CACHESTANDARD_HTML '         <hr>',"\n";


	close(CACHESTANDARD_HTML);
}

#---------------------------------------------------------------------------------

sub new {

$self = shift @_;

# open the config file 
open (PLOTS_FILE, "../data/CacheTransfer_config_file");

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
