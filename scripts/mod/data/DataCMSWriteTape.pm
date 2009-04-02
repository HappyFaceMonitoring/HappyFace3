package mod::data::DataCMSWriteTape;

#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------


sub new {

$self = shift;

system("wget --output-document=\"../data/cms_write_tape_original.html\" \"http://adm-dcache.gridka.de:2289/pools/list/PoolManager/cms-write-tape-pools/spaces/\"");

$source_code = "";
open(ORIGINAL, "../data/cms_write_tape_original.html");
while (<ORIGINAL>) {
	chop;
	$source_code = $source_code . $_;
}
close(ORIGINAL);


$source_code =~ /pools<\/emph><\/h3>(.+?)<\/div><div\ id\=\"footer\">/ix;

$content = $1;


open(NEW_OUTPUT,">../data/cms_write_tape.html");

print NEW_OUTPUT '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">',"\n";
print NEW_OUTPUT '<html><head>',"\n";
print NEW_OUTPUT '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">',"\n";
print NEW_OUTPUT '<link type="text/css" rel="stylesheet" href="styles/common.css">',"\n";
print NEW_OUTPUT '<link type="text/css" rel="stylesheet" href="styles/poolinfo.css">',"\n";
print NEW_OUTPUT '<title>Pool Property Tables</title>',"\n";
print NEW_OUTPUT '</head><body>',"\n";

print NEW_OUTPUT $content,"\n";

print NEW_OUTPUT '</body></html>',"\n";
close(NEW_OUTPUT);


}

1;
