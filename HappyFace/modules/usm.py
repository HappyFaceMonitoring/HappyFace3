from XMLParsing import *
from ModuleBase import *
from datetime import *

class myUser:   #class storing the user's information
    matchedDirs = 0 #total number of matched directories
    totalDirs = 0   #total number of directories
    totalSpace = 0.0    #total space usage
    sites = []  #list of used gird sites
    
    def __init__(self, dirname):
        self.places = []    #users can store their data in different locations (even on one grid site)
        self.dirname = dirname
        self.username = ""
        self.dn = ""
        self.voms = ""
        self.mail = ""      
        self.matched = False
        self.limit = 0.0    #the user's space quota
        self.lifetime = ""  #an optional lifetime for the user's non-standard quota
        myUser.totalDirs += 1
    
    def setUserInfo(self, name, dn, voms, mail):
        self.username = name
        self.dn = dn
        self.voms = voms
        self.mail = mail
        self.matched = True
        myUser.matchedDirs += 1
                        
    def setPlace(self, time, site, se, path, du):
        self.places.append({"time" : time, "site" : site, "se" : se, "path" : path, "du" : du})
        myUser.totalSpace += float(du)
        if site not in myUser.sites:
            myUser.sites.append(site)
    
    def getTotalSpace(self):    #calculate the user's total amount of data
        total_du = 0.0
        for place in self.places:
            total_du += float(place["du"])
        return total_du
        
    def getQuotaUsage(self):    #returns the relative quota usage
        if self.limit == 0.0:
            return -1.0
        else:
            return self.getTotalSpace()/pow(1024,3)/float(self.limit)
            
    def getQuotaLifetime(self): #returns the optional quota lifetime
        today = date.today()
        if self.lifetime == "":
            return 0.1
        else:
            delta = date(int(self.lifetime.split(".")[0]),int(self.lifetime.split(".")[1]),int(self.lifetime.split(".")[2])) - today
            return delta.days
                    
        

class usm(XMLParsing,ModuleBase):

   # def __init__(self,category,timestamp,storage_dir):
    def __init__(self,module_options):

        # inherits from the ModuleBase Class
        #ModuleBase.__init__(self,category,timestamp,storage_dir)
        ModuleBase.__init__(self,module_options)
        # read additional config settings
        self.xml_paths = self.configService.options('downloadservice')    #get the list of xml filenames
        self.gen_limit = self.configService.get('users','general_limit')   #get the default user quota
        self.power_users = self.configService.options('power_users')   #get the list of power user names
        self.excl_users = self.configService.get('users','excluded_users').split(",")  #get the list of excluded directory names
        self.admins = self.configService.get('users','admins').split(",")  #get the list admins
        self.allDirs = {}   #the main dictionary
        self.users_overquota = 0
        self.holdback_time=float(self.configService.get('users','holdback_time'))
        
        # definition of the database keys and pre-defined values
        # possible format: StringCol(), IntCol(), FloatCol(), ...
        self.db_keys["totaldirs"] = IntCol()
        self.db_values["totaldirs"] = 0
        self.db_keys["matcheddirs"] = IntCol()
        self.db_values["matcheddirs"] = 0
        self.db_keys["totalspace"] = StringCol()
        self.db_values["totalspace"] = ""
        self.db_keys["usersoq"] = IntCol()
        self.db_values["usersoq"] = 0
        
        #all users subtable
        self.db_keys["users"] = StringCol()
        self.db_values["users"] = self.__module__ + "_users"
        self.db_keys["site"] = StringCol()
        self.db_values["site"] = self.__module__ + "_site"
 
                                
    def run(self):
        
        site_sub_keys={}
        users_sub_keys = {}
      
        site_sub_keys["site"] = StringCol()

        users_sub_keys["username"] = StringCol()
        users_sub_keys["dirname"] = StringCol()
        users_sub_keys["dn"] = StringCol()
        users_sub_keys["voms"] = StringCol()
        users_sub_keys["email"] = StringCol()
        users_sub_keys["site"] = StringCol()
        users_sub_keys["sitedir"] = StringCol()
        users_sub_keys["du"] = FloatCol()
        users_sub_keys["total"] = FloatCol()
        users_sub_keys["red"] = BoolCol()
        users_sub_keys["matched"] = BoolCol()
        users_sub_keys["color"] = StringCol()
        users_sub_keys["status"] = StringCol()
        
        users_class = self.table_init( self.db_values["users"], users_sub_keys )
        site_class = self.table_init( self.db_values["site"], site_sub_keys )
 
        for filetag in self.xml_paths:
            dl_error,sourceFile = self.downloadService.getFile(self.downloadRequest[filetag])
            if dl_error != "":
                self.error_message+= dl_error
                return
            
            xmldata,xml_error = self.parse_xmlfile_minidom(sourceFile)
            self.error_message+=xml_error
            xmlGlobalInfo = xmldata.getElementsByTagName("GlobalInfo")[0]   #get the global info tag
            xmlMatchedDirs = xmldata.getElementsByTagName("matchedSpace")[0].getElementsByTagName("user")   #get the list of matched users
            xmlUnmatchedDirs = xmldata.getElementsByTagName("noMatching")[0].getElementsByTagName("user")   #get the list of unmatched directories
            
            for user in xmlMatchedDirs: #get user info from the xml structure and fill it in a myUser object
                if user.getAttribute("dirname") not in self.excl_users:
                    if user.getAttribute("dirname") not in self.allDirs:    #check if the user already exists
                        tmpUser = myUser(user.getAttribute("dirname"))
                        tmpUser.setUserInfo(user.getAttribute("username"), user.getAttribute("DN"), user.getAttribute("voms"), user.getAttribute("mail"))
                        if user.getAttribute("dirname") in self.power_users:    #special rules for power users
                            if len(self.configService.get('power_users',user.getAttribute("dirname")).split()) == 2:
                                tmpUser.limit = float(self.configService.get('power_users',user.getAttribute("dirname")).split()[0])
                                tmpUser.lifetime = self.configService.get('power_users',user.getAttribute("dirname")).split()[1]
                            elif len(self.configService.get('power_users',user.getAttribute("dirname")).split()) == 1:
                                tmpUser.limit = float(self.configService.get('power_users',user.getAttribute("dirname")).split()[0])                    
                        else:
                            tmpUser.limit = self.gen_limit
                            
                        self.allDirs[user.getAttribute("dirname")] = tmpUser
                    
                    self.allDirs[user.getAttribute("dirname")].setPlace(xmlGlobalInfo.getAttribute("time"), xmlGlobalInfo.getAttribute("site"), xmlGlobalInfo.getAttribute("se"), xmlGlobalInfo.getAttribute("path"), user.getAttribute("du"))
                    
            for user in xmlUnmatchedDirs:
                if user.getAttribute("dirname") not in self.excl_users:
                    if user.getAttribute("dirname") not in self.allDirs:
                        self.allDirs[user.getAttribute("dirname")] = myUser(user.getAttribute("dirname"))
                    
                    self.allDirs[user.getAttribute("dirname")].setPlace(xmlGlobalInfo.getAttribute("time"), xmlGlobalInfo.getAttribute("site"), xmlGlobalInfo.getAttribute("se"), xmlGlobalInfo.getAttribute("path"), user.getAttribute("du"))
                            
        for user in self.allDirs:   #check if user is over quota
            if self.allDirs[user].getQuotaUsage() > 1.0 or self.allDirs[user].getQuotaLifetime() < 0.0:
                self.users_overquota += 1
        
        # define module status 0.0..1.0 or -1 for error
        if myUser.totalDirs == 0:
            self.status = -1.0 # no dirs found!
        else:
            self.status = 1.0 - ( float( self.users_overquota + myUser.totalDirs - myUser.matchedDirs ) / float(myUser.totalDirs) )

        # define the output value for the database
        self.db_values["totaldirs"] = myUser.totalDirs
        self.db_values["matcheddirs"] = myUser.matchedDirs
        self.db_values["totalspace"] = "%.1f" % (myUser.totalSpace/pow(1024,4))
        self.db_values["usersoq"] = self.users_overquota 
        
        
        self.fill__users_subtable(users_class)
        self.fill__site_subtable(site_class)
        self.table_clear( users_class,[],self.holdback_time)
        self.table_clear( site_class,[],self.holdback_time)
        
                       

    def cmp_du(self, x, y): #a comparison function, sorting a list according to user's disk usage. puts unmatched users at the end of the list
        if self.allDirs[x].matched == True and self.allDirs[y].matched == False:
            return -1
        elif self.allDirs[x].matched == False and self.allDirs[y].matched == True:
            return 1
        elif self.allDirs[x].matched == True and self.allDirs[y].matched == True:                   
            if self.allDirs[x].getTotalSpace() < self.allDirs[y].getTotalSpace():
                return 1
            elif self.allDirs[x].getTotalSpace() == self.allDirs[y].getTotalSpace():
                return 0
            else:
                return -1
        else:
            if self.allDirs[x].getTotalSpace() < self.allDirs[y].getTotalSpace():
                return 1
            elif self.allDirs[x].getTotalSpace() == self.allDirs[y].getTotalSpace():
                return 0
            else:
                return -1        
    
    def fill__site_subtable(self,site_class):
        sub_values = {}
        for site in myUser.sites:
                sub_values["site"] = site
                self.table_fill( site_class, sub_values )
    
    def fill__users_subtable(self,users_class):
 
        sub_values = {}
        dir_list = self.allDirs.keys()
        dir_list.sort(self.cmp_du)  #sort the main user list
        
        for site in myUser.sites:
            for user in dir_list:
                sub_values["site"] = site
                sub_values["sitedir"] =""
                sub_values["du"]=0.0
                sub_values["dirname"] = self.allDirs[user].dirname
                sub_values["dn"] = self.allDirs[user].dn
                sub_values["voms"] = self.allDirs[user].voms
                sub_values["email"] = self.allDirs[user].mail
                sub_values["username"] = self.allDirs[user].username
                sub_values["total"] =float( "%.1f" %(float(self.allDirs[user].getTotalSpace()/pow(1024,3))))
                sub_values["red"] =False
                if self.allDirs[user].matched:
                   sub_values["matched"] =True
                   if self.allDirs[user].getQuotaUsage() <= 1.0 and self.allDirs[user].getQuotaLifetime() > 0.0:
                       if self.allDirs[user].voms == "/cms/dcms":
                            sub_values["color"] ="000000"
                       else:
                            sub_values["color"] ="0033CC"
                   else:
                       sub_values["color"] ="FF0000"
                       sub_values["red"] =True
                else:
                    sub_values["color"] ="FF9900"
                    sub_values["matched"] =False
                for place in self.allDirs[user].places:
                    if place["site"] == site:
                        sub_values["sitedir"] ="[" + place["site"] + "] " + place["se"]  + ":" + place["path"] + self.allDirs[user].dirname
                        sub_values["du"]=float("%.1f" %(float(place["du"])/pow(1024,3)))
                if self.allDirs[user].matched:
                    if self.allDirs[user].getQuotaUsage() <= 1.0:
                        if self.allDirs[user].getQuotaLifetime() > 0.0 and self.allDirs[user].getQuotaLifetime() != 0.1:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(1024,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0) + '''&thinsp;%%. The quota expires in ''' + "%d" % (self.allDirs[user].getQuotaLifetime()) + ''' day(s) on ''' + (date.today()+timedelta(self.allDirs[user].getQuotaLifetime())).strftime('%b %d %Y') 
                        elif self.allDirs[user].getQuotaLifetime() == 0.1:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(1024,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0)+ '''&thinsp;%%''' 
                        else:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(1024,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0) + '''&thinsp;%%. The quota expired ''' + "%d" % (-1.0*float(self.allDirs[user].getQuotaLifetime())) + ''' day(s) ago on ''' + (date.today()+timedelta(self.allDirs[user].getQuotaLifetime())).strftime('%b %d %Y')
                    else:
                        if self.allDirs[user].getQuotaLifetime() > 0.0 and self.allDirs[user].getQuotaLifetime() != 0.1:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(102424,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0) + '''&thinsp;%%. The quota expires in ''' + "%d" % (self.allDirs[user].getQuotaLifetime()) + ''' day(s) on ''' + (date.today()+timedelta(self.allDirs[user].getQuotaLifetime())).strftime('%b %d %Y')
                        elif self.allDirs[user].getQuotaLifetime() == 0.1:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(1024,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0)+'''&thinsp;%%'''
                        else:
                            sub_values["status"]="%.1f" % (float(self.allDirs[user].limit)/pow(1024,1)) + '''&thinsp;TiB quota used by ''' + "%.1f" % (self.allDirs[user].getQuotaUsage()*100.0) + '''&thinsp;%%. The quota expired ''' + "%d" % (-1.0*float(self.allDirs[user].getQuotaLifetime())) + ''' day(s) ago on ''' + (date.today()+timedelta(self.allDirs[user].getQuotaLifetime())).strftime('%b %d %Y')
                else:
                    sub_values["status"]=""
                self.table_fill( users_class, sub_values )

    
    
    def cmp_nn(self, x, y): #a comparison function, sorting a list according to last names. puts unmatched users at the end of the list
        if self.allDirs[x].matched == True and self.allDirs[y].matched == False:
            return -1
        elif self.allDirs[x].matched == False and self.allDirs[y].matched == True:
            return 1
        elif self.allDirs[x].matched == True and self.allDirs[y].matched == True:
            tmp_pair = [self.allDirs[x].username.split()[-1], self.allDirs[y].username.split()[-1]]
            tmp_pair.sort()
            if self.allDirs[x].username.split()[-1] != tmp_pair[0]:
                return 1
            else:
                return -1
        else:
            tmp_pair = [self.allDirs[x].dirname, self.allDirs[y].dirname]
            tmp_pair.sort()
            print tmp_pair
            if self.allDirs[x].dirname != tmp_pair[0]:
                return 1
            else:
                return -1
    def getuserSQLcontent(self):
        phpusercontent='''
<?php
        $usm=array();
        $user_sql=array();
        $sites_sql=array();
        $a_places=array();        
        $i=0;
        $plasces_sqlquery = "SELECT site FROM " . $data["site"] . " WHERE timestamp = " . $data["timestamp"];

        $users_sqlquery = "SELECT * FROM " . $data["users"] . " WHERE timestamp = " . $data["timestamp"]." group by dirname order by matched desc, total desc";
#        print_r ($users_sqlquery);
        foreach ($dbh->query($plasces_sqlquery) as $place)
        {
            $sites_sql[$place["site"]]= $i;
            
            $i++;
        }
        foreach ($dbh->query($users_sqlquery) as $user)
        {
               $user_sql["dirname"]=$user["dirname"];    
               $user_sql["username"]=$user["username"];    
               $user_sql["dn"]=$user["dn"];    
               $user_sql["voms"]=$user["voms"];    
               $user_sql["mail"]=$user["email"];    
#               $user_sql["matched"]=$user["matched"];    
               $user_sql["color"]=$user["color"];    
               $user_sql["total"]=$user["total"];    
               $user_sql["status"]=$user["status"];    

               $sites_sqlquery =  "SELECT site, sitedir,du FROM " . $data["users"] . " WHERE timestamp = " . $data["timestamp"]." and dirname = '".$user_sql["dirname"]."'";
               $a_places=array();
               $a_sites=array();        
               $i=0;              
               foreach ($dbh->query($sites_sqlquery) as $site)
                {
                    if ($site["du"]>0 )
                    {
                        $a_sites[$sites_sql[$site["site"]]]=$site["du"];
                    }else
                    {
                        $a_sites[$sites_sql[$site["site"]]]="";
                    }
                    
                    if (! empty($site["sitedir"]))
                    {
                        $a_places[$i]=$site["du"]."&thinsp;GiB @ ".$site["sitedir"];
                        $i++;
                    }                   
                    
                }
                $user_sql["sites"]=$a_sites;
                $user_sql["places"]=$a_places;
                   
                if ($user["matched"])
                {
                       $user_sql["matched"]=$user["matched"];
                       $usm[$user["username"]]=$user_sql;
                }else
                {
                       $user_sql["matched"]="";
                       $user_sql["username"]=$user["dirname"];    
                       $usm[$user["dirname"]]=$user_sql;
                }
            
        }
   
?>
        '''
        return phpusercontent

    def getAdminsString(self):
        tmpString='''
<?php
$admins= array('''
        for admin in self.admins:
           tmpString+='"'+admin+'",'
           
        tmpString+=''');
?>
'''
            
        return tmpString
                
    def output(self):
        num_sites = len(myUser.sites)
        num_cols = 2*num_sites  #calculate the needed number of columns
        if num_sites != 1:
            num_cols += 2

        dir_list = self.allDirs.keys()
        dir_list.sort(self.cmp_du)  #sort the main user list
        
        adminsString=self.getAdminsString()        

        # the module's output is completely stored in 'phpString'
        phpString = '''
    <?php
        if ( $_SERVER[SSL_CLIENT_CERT])
        {
        $cert=openssl_x509_parse($_SERVER[SSL_CLIENT_CERT]);
        }
        else
        {
        $cert[name]=$_SERVER[SSL_CLIENT_S_DN];
        }
        if ($cert[name])

    {

#            printf("DN:".$cert[name]); 
printf('
       '''

        phpString += '''
<div id="usmtablemenu">
    <div id="usmtrmenu">
        <div id="usmtd2menu" style="width:66%%">
            <div id="usmthmenu" style="border-top: none;" align="left"><strong>used disk space</strong></div>
            <div id="usmthmenu" align="left">&nbsp;&nbsp;<i>sites: '''
            
        for site in myUser.sites:
            if site != myUser.sites[-1]:
                phpString += site + ", "
            else:
                phpString += site
#        <div id="usmtd2menu" style="width:34%%; vertical-align:middle"><strong>''' + "%.1f" % (myUser.totalSpace/pow(1000,4)) + '''&thinsp;TiB</strong></div>
                
        phpString += '''</i></div>
        </div>
        <div id="usmtd2menu" style="width:34%%; vertical-align:middle"><strong>' . $data["totalspace"] . '&thinsp;TiB</strong></div>
    </div>
    <div id="usmtrmenu">
        <div id="usmtd2menu" style="width:66%%">
            <div id="usmthmenu" style="border-top: none;" align="left"><strong>users exceeding quota</strong></div>
            <div id="usmthmenu" align="left">&nbsp;&nbsp;<i>quota of ''' + "%.1f" % (float(self.gen_limit)/pow(1024,1)) + '''&thinsp;TiB per user, individual limits for power users</i></div>
        </div>
        <div id="usmtd2menu" style="width:34%%; vertical-align:middle"><strong><font color="#FF0000">''' + "%d" % (self.users_overquota) + '''</font></strong></div>
    </div>
    <div id="usmtrmenu">
        <div id="usmtd1menu" style="width:66%%; text-align:left"><strong>unmatched directories</strong></div>
        <div id="usmtd1menu" style="width:34%%; vertical-align:middle"><strong><font color="#FF9900">''' + "%d" % (myUser.totalDirs-myUser.matchedDirs) + '''</font></strong></div>
    </div>
</div><br>
');'''
        phpString += '''
        if (in_array($cert[name],$admins)){ 
            printf('
<div><button type="button" onclick="show_hide(\\\'userspacelist\\\');">show/hide details</button></div>
<div id="userspacelist" style="display:none;"><br>
'); 
        } else {
            printf('
<div id="userspacelist" style="display:block;"><br>
'); 
         }

printf('
<div id="usmtableheader">
    <div style="display:table-header-group">
        <div id="usmtr">
            <div id="usmtdheader" style="width:25%%; text-align:left">User</div>'''
        
        for site in myUser.sites:
            phpString += '''
            <div id="usmtdheader"><div style="width:150px; display:inline-block">''' + site + '''</div></div>'''
        
        if num_sites != 1:
            phpString += '''
            <div id="usmtdheader"><div style="width:150px; display:inline-block">Total Usage</div></div>'''

        phpString += '''
        </div>
    </div>
</div>'''

        phpString += '''
');
        foreach($usm as $usm_entry){
              if ( $cert[name]==$usm_entry["dn"] or in_array($cert[name],$admins)){
                printf('
<div id="usmtable">
    <div id="usmtr">
        <div id="usmtd" style="width:25%%; text-align:left"><button class ="textbutton" type="button" onfocus="this.blur()" onclick="show_hide(\\''.$usm_entry["dirname"].'\\');"><div');
        if ($usm_entry["matched"]){
            printf(' style="text-transform:capitalize"');
        }
        printf('><font color="#'.$usm_entry["color"].'">'.$usm_entry["username"].'</font></div></button></div>');
        foreach($usm_entry["sites"] as $site){
            if ($site){
             printf('
         <div id="usmtd">
           <div style="display:inline-block; width:60px; text-align:right"><font color="#'.$usm_entry["color"].'">'.$site.'</font></div>
           <div style="display:inline-block; width:40px; text-align:left" ><font color="#'.$usm_entry["color"].'">GiB</font></div>
        </div>
');
            } else{
             printf('
         <div id="usmtd">
            <div style="display:inline-block; width:60px; text-align:right"><font color="#'.$usm_entry["color"].'">&mdash;</font></div>
            <div style="display:inline-block; width:40px; text-align:left" ><font color="#'.$usm_entry["color"].'">&nbsp;</font></div>
        </div>
');
                
            }
         }
            if (isset($usm_entry["total"])){
                if ($usm_entry["total"]){
                printf('
        <div id="usmtd">
            <div style="display:inline-block; width:60px; text-align:right"><font color="#'.$usm_entry["color"].'">'.$usm_entry["total"].'</font></div>
            <div style="display:inline-block; width:40px; text-align:left" ><font color="#'.$usm_entry["color"].'">GiB</font></div>
        </div>');
                } 
                else{
                printf('
        <div id="usmtd">
            <div style="display:inline-block; width:60px; text-align:right"><font color="#'.$usm_entry["color"].'">&mdash;</font></div>
            <div style="display:inline-block; width:40px; text-align:left" ><font color="#'.$usm_entry["color"].'">&nbsp;</font></div>
        </div>');
                } 
            }
           printf('
    </div>
</div>
');
        if (in_array($cert[name],$admins)){ 
            printf('
<div id=\\''.$usm_entry["dirname"].'\\' class="usminfotable" style="display: none;">
');
        } else {
            printf('
<div id=\\''.$usm_entry["dirname"].'\\' class="usminfotable" style="display: block;">
');
	}
        printf('
                <div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><strong>Directory Name: </strong>'.$usm_entry["dirname"].'</div>
                </div>
                <div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><strong>DN: </strong>'.$usm_entry["dn"].'</div>
                </div>
                <div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><strong>email: </strong> <a href="mailto:'.$usm_entry["mail"].'">'.$usm_entry["mail"].'</a></div>
                </div>
                <div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><strong>VOMS Group: </strong>'.$usm_entry["voms"].'</div>
                </div>');
                       foreach($usm_entry["places"] as $place){
                         if ($place){
                            printf('<div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><strong>Storage Path: </strong>'.$place.'</div>
                    </div>');
                         }
                       }
                printf('<div id="usminfotr">
                    <div id="usminfotd" class="userinfo"><font color="#'.$usm_entry["color"].'"><strong>Status: </strong>'.$usm_entry["status"].'</font></div>
                </div>
</div> 
');
        }
}
        if (in_array($cert[name],$admins)){ 
printf('
'''
    
        
        phpString += '''
<div id="usmtable" style="border-bottom: none;">
    <div id="usmtr">
        <div id="usmtd" style="width:25%%; text-align:left"><strong>Total Usage:</strong></div>'''
        
        for site in myUser.sites:
            site_du = 0.0
            for user in dir_list:
                for place in self.allDirs[user].places:
                    if place["site"] == site:
                        site_du += float(place["du"])
                        
            phpString += '''
        <div id="usmtd">
            <div style="display:inline-block; width:60px; text-align:right"><strong>''' + "%.1f" % (site_du/pow(1024,4)) + '''</strong></div>
            <div style="display:inline-block; width:40px; text-align:left" ><strong>TiB</strong></div>
        </div>'''
        
        if num_sites != 1:
            phpString += '''
        <div id="usmtd">
            <div style="display:inline-block; width:60px; text-align:right"><strong>''' + "%.1f" % (myUser.totalSpace/pow(1024,4)) + '''</strong></div>
            <div style="display:inline-block; width:40px; text-align:left" ><strong>TiB</strong></div>
        </div>'''

        phpString += '''
    </div>
</div>
');
        } else {
            printf('
<div id="usmtable" style="border-bottom: none;">
    <div id="usmtrmenu">
        <div id="usmtd1menu" style="width:12%%; text-align:right"><strong><font size=0.7em;<i>DN</i> : </strong></div>
        <div id="usmtd1menu" style="width:88%%; text-align:left"><strong><font size=0.7em; color="#FF0000"><i>'.$cert[name].'</i></font></strong></div>
    </div>
</div>
'            );
        }
    
} 
printf('
</div>'''
        phpString += '''
                      ');
    ?>'''

       # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call
 
        module_content = adminsString+self.getuserSQLcontent()+phpString
    
        return self.PHPOutput(module_content)
