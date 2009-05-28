from dCacheInfo import *

class dCacheInfoPool(dCacheInfo):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        dCacheInfo.__init__(self,category,timestamp,storage_dir)

	config = self.readConfigFile('./happycore/dCacheInfoPool')
        self.readDownloadRequests(config)
	self.addCssFile(config,'./happycore/dCacheInfoPool')


        self.poolType = 'cms-write-tape-pools'

        self.poolAttribs = []
        self.poolAttribs.append({'id':'total' , 'name':'Total Space [GB]'})
        self.poolAttribs.append({'id':'free' , 'name':'Free Space [GB]'})
        self.poolAttribs.append({'id':'used' , 'name':'Used Space [GB]'})
        self.poolAttribs.append({'id':'precious' , 'name':'Precious Space [GB]'})
        self.poolAttribs.append({'id':'removable' , 'name':'Removable Space [GB]'})


        self.db_keys['poolnumber'] = IntCol()
        self.db_values['poolnumber'] = None
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.sumInfo = {}

        for att in self.poolAttribs:
            self.db_keys[ att['id'] ] = IntCol()
            self.db_values[ att['id'] ] = None
            self.sumInfo[ att['id'] ] = 0

        self.fromBytetToGb = 1024*1024*1024


    def run(self):
        thePoolInfo = self.getPoolInfo(self.poolType)
        self.db_values['poolnumber'] = len(thePoolInfo)



        details_database = self.__module__ + "_details_" + str(self.timestamp) + "_table"
        self.db_values["details_database"] = details_database

        
	details_db_keys = {}
	details_db_values = {}
        
        details_db_keys["poolname"] = StringCol()
        for att in self.poolAttribs:
            details_db_keys[ att['id'] ] = IntCol()

        # lock object enables exclusive access to the database
	self.lock.acquire()

	Details_DB_Class = type(details_database, (SQLObject,), details_db_keys )

	Details_DB_Class.sqlmeta.cacheValues = False
	Details_DB_Class.sqlmeta.fromDatabase = True
		
	# if table is not existing, create it
        Details_DB_Class.createTable(ifNotExists=True)

        
        for pool in thePoolInfo.keys():
            details_db_values["poolname"] = pool
            for att in self.poolAttribs:
                theId = att['id']
                theVal =int( int(thePoolInfo[pool][theId]) /self.fromBytetToGb)
                self.sumInfo[theId] += theVal
                details_db_values[theId] = theVal

            # store the values to the database
            Details_DB_Class(**details_db_values)

	# unlock the database access
	self.lock.release()

        for att in self.poolAttribs:
            self.db_values[ att['id'] ] = self.sumInfo[ att['id'] ]




    def output(self):

        # create output sting, will be executed by a printf('') PHP command
        # all data stored in DB is available via a $data[key] call

        mc = []
        mc.append("<?php")
        # Define sub_table for this module
        mc.append('$details_db_sqlquery = "SELECT * FROM " . $data["details_database"];')
      
        #Start with module output
        mc.append("printf('")
        mc.append(' <table class="dCacheInfoPoolTable">')

        #Summary table
        mc.append("  <tr>")
        mc.append("    <td>Number of pools</td>")
        mc.append("""    <td>'.$data["poolnumber"].'</td>""")
        mc.append("   </tr>")

        for att in self.poolAttribs:
            mc.append("  <tr>")
            mc.append("    <td>"+att['name']+"</td>")
            mc.append("""    <td>'.$data["""+'"'+ att['id'] +'"'+ """].'</td>""")
            mc.append("   </tr>")
            
        mc.append("  </table>")
        mc.append(" <br/>")


        # Show/Hide details table
        mc.append(""" <input type="button" value="show/hide results" onfocus="this.blur()" onclick="show_hide(""" + "\\\'" + self.__module__+ "_result\\\'" + """);" />""")
        mc.append(""" <div class="dCacheInfoPoolDetailedInfo" id=""" + "\\\'" + self.__module__+ "_result\\\'" + """ style="display:none;">""")

        mc.append(' <table class="dCacheInfoPoolTableDetails">')
        mc.append("  <tr>")
        mc.append('   <td class="dCacheInfoPoolTableDetails1RowHead">Poolname</td>')
        for att in self.poolAttribs:
            mc.append('   <td class="dCacheInfoPoolTableDetailsRestRowHead">'+att["name"]+'</td>')
        mc.append("  </tr>")
     

        mc.append("');") 
        mc.append("foreach ($dbh->query($details_db_sqlquery) as $sub_data)")
        mc.append(" {")
        mc.append("  printf('")
        mc.append("   </tr>")
        mc.append("""    <td class="dCacheInfoPoolTableDetails1Row">'.$sub_data["poolname"].'</td>""")
        for att in self.poolAttribs:
            mc.append("""    <td class="dCacheInfoPoolTableDetailsRestRow">'.$sub_data["""+'"'+ att['id'] +'"'+ """].'</td>""")
        mc.append("   </tr>")
        mc.append("  ');")
        mc.append(" }")

        mc.append("printf('")
        mc.append(" </table>")
        mc.append(" </div>")
        mc.append("');")
        mc.append("?>")


        
        # export content string
        module_content = ""
        for i in mc:
            module_content +=i+"\n"

        return self.PHPOutput(module_content)
