from dCacheInfo import *

class dCacheInfoPool(dCacheInfo):

    def __init__(self,category,timestamp,storage_dir):

        # inherits from the ModuleBase Class
        dCacheInfo.__init__(self,category,timestamp,storage_dir)

	config = self.readConfigFile('./happycore/dCacheInfoPool')
        self.readDownloadRequests(config)
	self.addCssFile(config,'./happycore/dCacheInfoPool')


        self.poolType = self.mod_config.get('setup','pooltype')

        self.poolAttribs = []
        self.poolAttribs.append({'id':'total' , 'name':'Total Space [GB]'})
        self.poolAttribs.append({'id':'free' , 'name':'Free Space [GB]'})
        self.poolAttribs.append({'id':'used' , 'name':'Used Space [GB]'})
        self.poolAttribs.append({'id':'precious' , 'name':'Precious Space [GB]'})
        self.poolAttribs.append({'id':'removable' , 'name':'Removable Space [GB]'})


        
	self.db_keys["details_database"] = StringCol()
        self.db_values["details_database"] = ""

        self.sumInfo = {}
        for att in self.poolAttribs:
            self.db_keys[ att['id'] ] = IntCol()
            self.db_values[ att['id'] ] = None
            self.sumInfo[ att['id'] ] = 0

        for val in ['poolnumber','poolcritical','poolwarning']:
            self.db_keys[val] = IntCol()
            self.db_values[val] = None
            self.sumInfo[val] = 0
            


        self.fromBytetToGb = 1024*1024*1024



        self.thresholds = {}
        self.thresholds['limit_global_critical'] = {}
        self.thresholds['limit_local_critical'] = {}
        self.thresholds['limit_global_warning'] = {}
        self.thresholds['limit_local_warning'] = {}



        self.getThresholds(config)
        self.getThresholds(self.mod_config)




    def getThresholds(self,config):
        for sec in self.thresholds.keys():
            if  config.has_section(sec):
                for i in config.items(sec):
                    self.thresholds[sec][i[0]] = i[1]



    def limitExceeded(self,thePoolInfo,cat):
        exceeded = False
        theThresholds = self.thresholds[cat]
        for check in theThresholds.keys():
            checkList = check.split("/")

            for val in checkList:
                if not val in thePoolInfo:
                    print "Warning: No such variable "+val
                    continue

            theRelVal = 0.
            if len(checkList) == 1:
                theRelVal = float(thePoolInfo[checkList[0]])
            elif len(checkList) == 2:
                theRelVal = float(thePoolInfo[checkList[0]])/float(thePoolInfo[checkList[1]])


            theCond = str(theThresholds[check])[:1]
            theRef = float(str(theThresholds[check])[1:])


            if theCond == ">":
                if theRelVal > theRef:
                    exceeded = True
            elif theCond == "<":
                if theRelVal < theRef:
                    exceeded = True
            else:
                print "Warning: No such condition "+check+" "+theThresholds[check]

#            print checkList
#            print str(theRelVal)+theCond+str(theRef)+" --> "+str(exceeded)


        return exceeded



    def run(self):

        thePoolInfo = self.getPoolInfo(self.poolType)
        
        
        # make poolAttrib as GB
        for pool in thePoolInfo.keys():
            for att in self.poolAttribs:
                theId = att['id']
                if theId in thePoolInfo[pool]:
                    thePoolInfo[pool][theId] = float(thePoolInfo[pool][theId]) / self.fromBytetToGb




        details_database = self.__module__ + "_details_" + str(self.timestamp) + "_table"
        self.db_values["details_database"] = details_database

        
	details_db_keys = {}
	details_db_values = {}
        
        details_db_keys["poolname"] = StringCol()
        details_db_keys["poolstatus"] = FloatCol()
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
            self.sumInfo['poolnumber'] +=1
            details_db_values["poolname"] = pool

            if self.limitExceeded(thePoolInfo[pool],'limit_local_critical') == False:
                # Set 1.0 for Pool is OK
                details_db_values["poolstatus"] = 1.
            elif self.limitExceeded(thePoolInfo[pool],'limit_local_warning') == False:
                # Set 0.5 for Pool for Warning
                details_db_values["poolstatus"] = 0.5
            else:
                # Set 0.0 for Pool is Critical
                details_db_values["poolstatus"] = 0.


            for att in self.poolAttribs:
                theId = att['id']
                if theId in thePoolInfo[pool]:
                    theVal = thePoolInfo[pool][theId]
                    self.sumInfo[theId] += theVal
                    details_db_values[theId] = int(round(theVal))
                else:
                    details_db_values[theId] = -1
                    details_db_values["poolstatus"] = 0.

            if details_db_values["poolstatus"] == 0.5:
                self.sumInfo['poolwarning'] +=1
            elif details_db_values["poolstatus"] == 0.:
                self.sumInfo['poolcritical'] +=1





            # store the values to the database
            Details_DB_Class(**details_db_values)

	# unlock the database access
	self.lock.release()


        for att in self.sumInfo.keys():
            self.db_values[ att ] = int(round(self.sumInfo[att]))

 
        if self.limitExceeded(self.sumInfo,'limit_global_critical') == True:
            self.status = 0.0
        elif self.limitExceeded(self.sumInfo,'limit_global_warning') == True:
            self.status = 0.5
        else:
            self.status = 1.0
            
        self.definition+= "Poolgroup: "+self.poolType+"<br/>"
        self.definition+= self.formatLimits()


    def formatLimits(self):
        theLines = []
        for i in ['limit_global_critical','limit_local_critical','limit_global_warning','limit_local_warning']:
            theLines.append(i+": "+self.getLimitVals(i))


        var = ""
        for line in theLines:
            var+=line+"<br/>"
        return var

    def getLimitVals(self,val):
        limVec = []
        for entry in self.thresholds[val].keys():
            limVec.append(entry+self.thresholds[val][entry])
        return ", ".join(limVec)
        

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
        mc.append("  <tr>")
        mc.append("    <td>Number of pools with status warning </td>")
        mc.append("""    <td>'.$data["poolwarning"].'</td>""")
        mc.append("   </tr>")
        mc.append("    <td>Number of pools with status critical</td>")
        mc.append("""    <td>'.$data["poolcritical"].'</td>""")
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
        mc.append('   <td class="dCacheInfoPoolTableDetails1RowHead">Poolstatus</td>')
        mc.append("  </tr>")
     

        mc.append("');") 
        mc.append("foreach ($dbh->query($details_db_sqlquery) as $sub_data)")
        mc.append(" {")
        mc.append("  printf('")
        mc.append("   </tr>")
        mc.append("""    <td class="dCacheInfoPoolTableDetails1Row">'.$sub_data["poolname"].'</td>""")
        for att in self.poolAttribs:
            mc.append("""    <td class="dCacheInfoPoolTableDetailsRestRow">'.$sub_data["""+'"'+ att['id'] +'"'+ """].'</td>""")
        mc.append("""    <td class="dCacheInfoPoolTableDetails1Row">'.$sub_data["poolstatus"].'</td>""")
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
