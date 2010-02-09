#!/usr/bin/perl

# written by Philip Sauerland (sauerland@physik.rwth-aachen.de)
# last modification: 2010.01.26

#REQUIREMENTS: You need to run this script on a machine with access to your storage system, to the grid-mapfile, and to a grid user interface with a valid (host) certificate. This tool is designed to work with dCache. Therefor you may need to download the dCache Toolkit -> http://datagrid.ucsd.edu/toolkit/ .

#USAGE:   ./usm.pl            <cert_path>                    <key_path>               <site_name>             <se_name>                           <storage_path_a>                                <storage_path_b>                  ...
#EXAMPLE: ./usm.pl '/etc/grid-security/hostcert.pem' '/etc/grid-security/hostkey.pem' 'T2_DE_RWTH' 'grid-srm.physik.rwth-aachen.de' '/pnfs/physik.rwth-aachen.de/cms/store/user/' '/pnfs/physik.rwth-aachen.de/cms/store/mc/CSA08/' ...
#RESULT:  usm_pnfs_physik.rwth-aachen.de_cms_store_mc_CSA08_.xml, usm_pnfs_physik.rwth-aachen.de_cms_store_user_.xml

#ATTENTION: The first part of this script matches DNs to hypernews logins. A large grid-mapfile leads to many wget requests which may hammer the siteDB server. Use this script at most a few times a day. 

use strict;
use warnings;

if (@ARGV < 5) {
    print 'usage: ./usm.pl <cert_path> <key_path> <site_name> <se_name> <storage_path_a> <storage_path_b> ...'."\n";
    exit(1);
}
my $cert_path = $ARGV[0]; #get host certificate path
shift(@ARGV);
my $key_path = $ARGV[0]; #get host key path
shift(@ARGV);
my $site_name = $ARGV[0]; #get site name
shift(@ARGV);
my $se_name = $ARGV[0]; #get storage element name
shift(@ARGV);
my @storage_paths;
foreach(@ARGV) {
    push(@storage_paths, $_) #get storage paths
}

my $unixtime = time; #get unix timestamp
my $hnkey;

my %hn; #main hash

print "starting query...\n";

# my $cmdString1 = 'wget -q --no-check-certificate -O - "https://cmsweb.cern.ch/sitedb/people/showAllEntries?initial=&site=&all=True" | grep "<td><p>"';
# my @output1 = qx($cmdString1);
# foreach (@output1) {
#     chomp;
#     print "$_\n";
# }

print "...init grid proxy...\n";
my $cmdString4 = "voms-proxy-init -cert $cert_path -key $key_path -hours 1"; #generate a grid proxy for one hour
my @output4 = qx($cmdString4);

print "...contacting voms-server for /cms/dcms...\n";
# my $cmdString5 = 'voms-admin --host voms.cern.ch --vo cms list-members /cms/dcms'; #get all /cms/dcms members by DN
my $cmdString5 = 'python /opt/glite/bin/voms-admin --host voms.cern.ch --vo cms list-members /cms/dcms'; #get all /cms/dcms members by DN
my @output5 = qx($cmdString5);
my %dcms_users;
foreach (@output5) {
    chomp;
    my ($dn, $ca) = split(/,\s+/, $_, 2);
    $dcms_users{$dn} = '/cms/dcms';
#    print "DEBUG: $_\n"; #### activate for debugging msgs ####
}

print "...contacting voms-server for /cms...\n";
# my $cmdString6 = 'voms-admin --host voms.cern.ch --vo cms list-members /cms'; #get all /cms members by DN
my $cmdString6 = 'python /opt/glite/bin/voms-admin --host voms.cern.ch --vo cms list-members /cms'; #get all /cms members by DN
my @output6 = qx($cmdString6);
my %cms_users;
foreach (@output6) {
    chomp;
    my ($dn, $ca) = split(/,\s+/, $_, 2);
    $cms_users{$dn} = '/cms';
#    print "DEBUG: $_\n"; #### activate for debugging msgs ####
}

print "...deleting grid proxy...\n";
my $cmdString7 = 'voms-proxy-destroy'; #delete grid proxy
my @output7 = qx($cmdString7);

print "...getting siteDB information...\n";
#my $cmdString2 = 'grep -e "\.cms" -e "\.dcm" /etc/grid-security/grid-mapfile | awk -F \" \'{print $2}\' | while read a ; do wget -q --no-check-certificate -O - "https://cmsweb.cern.ch/sitedb/json/index/dnUserName?dn=$a"; echo ; done'; #"here the matching between hypernews name and DN is done
my $cmdString2 = 'grep -v -e "\.aug" -e "\.ice" /etc/grid-security/grid-mapfile | awk -F \" \'{print $2}\' | while read a ; do wget -q --no-check-certificate -O - "https://cmsweb.cern.ch/sitedb/json/index/dnUserName?dn=$a"; echo ; done'; #"here the matching between hypernews name and DN is done

my @output2 = qx($cmdString2);
foreach (@output2) {
    chomp;
    if($_ =~ /\{'dn':/){ #check if the matching was successful
        my %userdata;
        # print "DEBUG: $_\n"; #### activate for debugging msgs ####
        $_ =~ /\{'dn':\s'(.+?)'/; #get the DN string
        $userdata{dn} = $1;
        if (exists($dcms_users{$userdata{dn}})) { #get the users membership in a voms group
            $userdata{voms} = $dcms_users{$userdata{dn}};
        } elsif (exists($cms_users{$userdata{dn}})) {
            $userdata{voms} = $cms_users{$userdata{dn}};
        } else {
            $userdata{voms} = '';
        }
        $_ =~ /\/CN=([^\/]+?)\s?[0-9]*?'/g; #get the real user name, excluding multiple CNs and cryptic numbers at the end of the last CN -> Perl RegEx at its best *g* 
        $userdata{name} = $1;
        $_ =~ /'user':\s'(.+?)'/; #get the hypernews name string
        $hn{$1} = \%userdata;
    }
}

# while ($hnkey = each(%hn)) print "DEBUG: $hnkey is $hn{$hnkey}{name} ($hn{$hnkey}{dn})\n"; #### activate for debugging msgs ####

foreach(@storage_paths) {
    my %data;
    print "...getting dCache storage usage for $_...\n";
    my $cmdString3 = 'source /opt/d-cache/toolkit/setup.sh; osg_dc_get_html_dump_of_fs_usage_of_pnfs_dir '.$_.'* -s'; #works like du -sm
    my @output3 = qx($cmdString3);
    foreach (@output3) {
        chomp;
        my ($value, $var) = split(/\s+/, $_, 2);
        $data{$var} = $value;
        # print "DEBUG: $_\n"; #### activate for debugging msgs ####
    }
    
    print "...filling data to xml structure...\n";
    my $pathname = $_;
    $pathname =~ s/\//_/g; 
    open(XML_OUT, ">usm$pathname.xml");
    
    print XML_OUT '<?xml version="1.0"?>'."\n";
    print XML_OUT '<userSpaceInfo>'."\n";
    print XML_OUT '  <GlobalInfo time="'.$unixtime.'" site="'.$site_name.'" se="'.$se_name.'" path="'.$_.'"/>'."\n";
    print XML_OUT '  <matchedSpace>'."\n";
    
    while(my ($var, $value) = each(%data)) {
        my $user = $var;
        my $mail = ''; #use blank mail address till email user matching is working
        $user =~ s/^.*\///; #cut out user name only
        if (exists($hn{$user})) { #search for directories with hypernews names
            
            # print "DEBUG: $hn{$user}{name} uses $value bytes ($user with $hn{$user}{dn})\n"; #### activate for debugging msgs ####
            # print XML_OUT '    <user dirname="'.$user.'" username="'.$hn{$user}{name}.'" mail="'.$mail.'" DN="'.$hn{$user}{dn}.'" du="'.$value.'"/>'."\n";
            print XML_OUT '    <user dirname="'.$user.'" username="'.$hn{$user}{name}.'" DN="'.$hn{$user}{dn}.'" voms="'.$hn{$user}{voms}.'" mail="'.$mail.'" du="'.$value.'"/>'."\n";
        }
    }
    
    print XML_OUT '  </matchedSpace>'."\n";
    print XML_OUT '  <noMatching>'."\n";
    
    while(my ($var, $value) = each(%data)) {
        my $user = $var;
        $user =~ s/^.*\///; #cut out user name only
        if (!exists($hn{$user})) { #search for directories without hypernews names
            # print "DEBUG: $user uses $value bytes\n"; #### activate for debugging msgs ####
            print XML_OUT '    <user dirname="'.$user.'" du="'.$value.'"/>'."\n";	    
        }
    }
    
    print XML_OUT '  </noMatching>'."\n";
    print XML_OUT '</userSpaceInfo>'."\n";
    
    close(XML_OUT);
}
print "...done!\n";

