package mod::cache::CacheShift;

#---------------------------------------------------------------------------------

sub createHTMLFragment {
	$self = shift @_;

	$cms_disk_only = mod::DataFactory->new("CMSDiskOnly");
	$cms_write_tape = mod::DataFactory->new("CMSWriteTape");

	open(CACHESHIFT_HTML, ">../HTMLFragments/CACHESHIFT_HTML.txt");

	print CACHESHIFT_HTML '		<br>',"\n";

	print CACHESHIFT_HTML '	<strong><a href="https://twiki.cern.ch/twiki/bin/view/CMS/T1GridKaShifterPage">Shifter Page</a> |</strong>',"\n";
	print CACHESHIFT_HTML '	<strong><a href="https://twiki.cern.ch/twiki/bin/view/CMS/T1GridKaCSA08Blog">GridKa Blog</a></strong>',"\n";

	print CACHESHIFT_HTML '		<br>',"\n";
	print CACHESHIFT_HTML '		<hr>',"\n";

for ($i = 0; $i <= ($self->{'plot_number'}); $i++) {
	$status = system('wget --output-document="../images/CacheShift_plot_'.$i.'.png" "'.$self->{'link'}[$i].'"');

	print CACHESHIFT_HTML '		<br>',"\n";

	print CACHESHIFT_HTML '		<table width="860">',"\n";
	print CACHESHIFT_HTML '			<tr align="center"><td><strong>',$self->{'title'}[$i],'</strong></td></tr>',"\n";	
	print CACHESHIFT_HTML '			<tr align="center"><td><a href="',$self->{'link'}[$i],'"><img src="images/CacheShift_plot_',$i,'.png" style="border: 0px solid;"></a></td></tr>',"\n";
	print CACHESHIFT_HTML '                 <tr align="center"><td>',$self->{'description'}[$i],'</td></tr>',"\n";
	print CACHESHIFT_HTML '		</table>',"\n";

	print CACHESHIFT_HTML '		<br>',"\n";
	print CACHESHIFT_HTML '		<hr>',"\n";
}

#These are now moved to Standard
#
#	print CACHESHIFT_HTML '		<iframe src="http://www-ekp.physik.uni-karlsruhe.de/~happyface/HappyFace/data/cms_disk_only.html" width="1200" height="500" frameborder="0" name="SELFHTML_in_a_box">',"\n";
#	print CACHESHIFT_HTML '		</iframe>',"\n";
#
#	print CACHESHIFT_HTML '		<table width="860">',"\n";
#	print CACHESHIFT_HTML '                 <tr align="center"><td>Listed in the table are dCache pools - think about them as file systems, or disks, where data is put and stored. If they fill up, you cant transfer to it anymore. Disk-only pools above are used for intermediate result of production. After these intermediate results are merged, the data should be deleted by production team. Also this disk-only pool is used to by Phedex Debug transfers. Disk can get full for a number of reasons, but the all are due to CMS - we are responsible for cleaning it up, not GridKa. <p>If you see Disk only pools close to fill up (to little yellow space), notify CMS expert on call.</td></tr>',"\n";
#	print CACHESHIFT_HTML '		</table>',"\n";

#	print CACHESHIFT_HTML '		<br>',"\n";
#	print CACHESHIFT_HTML '		<hr>',"\n";

#	print CACHESHIFT_HTML '		<iframe src="http://www-ekp.physik.uni-karlsruhe.de/~happyface/HappyFace/data/cms_write_tape.html" width="1200" height="500" frameborder="0" name="SELFHTML_in_a_box">',"\n";
#	print CACHESHIFT_HTML '		</iframe>',"\n";

#	print CACHESHIFT_HTML '		<table width="860">',"\n";
#	print CACHESHIFT_HTML '                 <tr align="center"><td>Listed in the table are dCache pools - think about them as file systems, or disks, where data is put and stored. If they fill up, you cant transfer to it anymore. Tape-write buffers are used as an intermediate buffer where files are transferred from outside and stored until they are written to tape (this is called migration). If tape migration doesnt work for any reason, then tape-write dCache buffers can fill up and thus transfer will also stop. Migration to tape is managed by GridKa. Thus if you see tape write only pools close to fill up (to much red space), notify GridKa. To assist you in judging when is too much, look at Infrastructure face - there is a test under this tab that automatically calculates occupied space and checks against threshold. Please also report if individual pools are filled up, not only the overal status. In your GGUS ticket state that tape-migration buffers are so many % full - take the number from that infrastructure test. Also cross check with tape migration rate plot on this page. Its most likely that its low or 0 as well. </td></tr>',"\n";
#	print CACHESHIFT_HTML '		</table>',"\n";

#	print CACHESHIFT_HTML '		<br>',"\n";
#	print CACHESHIFT_HTML '		<hr>',"\n";

#	print CACHESHIFT_HTML '		<iframe src="http://lxarda16.cern.ch/dashboard/request.py/latestresultssmrytable?siteSelect3=T1T0&serviceTypeSelect3=vo&sites=T1_DE_FZK&services=CE&services=SE&services=SRM&services=SRMv2&tests=1301&tests=133&tests=111&tests=6&tests=1261&tests=76&tests=64&tests=20&tests=142&tests=13&tests=177&tests=33&tests=50&tests=882&exitStatus=all" width="1050" height="300" scrolling="no" frameborder="0" name="SELFHTML_in_a_box">',"\n";
#	print CACHESHIFT_HTML '		</iframe>',"\n";

#	print CACHESHIFT_HTML '		<table width="860">',"\n";
#	print CACHESHIFT_HTML '                 <tr align="center"><td>Here is SAM test results. Yuo should clearly separate two failure cases - tests that fail entirely due to GridKa and test thqat may fail due to CMS. Several CEs here are for redundancy, thus you should only report if all CEs show an error for a particular test. Jobs submission test fail due to GridKa (js, jsprod). Also frontier and squod tests. If you see that these tests fail for <b>all</b> CEs - send GridKa a GGUS ticket. In the ticket, say that all CE fail specific CMS test and list the log of one test (click on the "error"cell to get the log - you certificate in the browser is necessary).<p> MC test may be due to CMS failure (e.g. when disk-noly buffer fill up). Report MC test failure to CMS expert. If SE tests are failing, contact CMS expert as well</td></tr>',"\n";
#	print CACHESHIFT_HTML '		</table>',"\n";

#	print CACHESHIFT_HTML '		<br>',"\n";
#	print CACHESHIFT_HTML '		<hr>',"\n";

	close(CACHESHIFT_HTML);

}

#---------------------------------------------------------------------------------

sub new {

$self = shift @_;

# open the config file 
open (PLOTS_FILE, "../data/CacheShift_config_file");

$i = 0;

while(<PLOTS_FILE>) {
        next if /^\#/;
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
