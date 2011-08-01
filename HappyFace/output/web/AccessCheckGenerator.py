from ConfigService import *

class AccessCheckGenerator(object):

    # reads out the access.cfg file
    def __init__(self):

        config_file='access'

        config = ConfigParser.ConfigParser()
        config.optionxform = str # needed to enable capital letters

        try:
            config.readfp(open(config_file + '.cfg'))
        except IOError:
            sys.stdout.write('Could not find configuration file ' + config_file + '.cfg, aborting ...\n')
            sys.exit(-1)
        try:
            config.readfp(open('./local/cfg/' + config_file + '.local'))
        except IOError:
            pass

        self.hideIcons = False
        if (config.get("icons", "hide_icons")  == "true"):
            self.hideIcons = True

        allModulesSection = config.sections()

        self.accessesMods = []
        self.accessesSects = []

        largeSplitter = config.get("separators", "split_a")
        smallSplitter = config.get("separators", "split_b")

        for actSecNr in range(len(allModulesSection)):

                if (allModulesSection[actSecNr]) == 'separators':
                     continue

                splitModules = allModulesSection[actSecNr].split(',')

                allAccessItem = config.items(allModulesSection[actSecNr]) # item ueber required certs holen

                splitAccess  = allAccessItem[0][1].split(largeSplitter) # 0 erster eintrag in section, 0 key, 1 value

                if (allAccessItem[0][0]!='required_crts'):
                    continue

                tmpListUserCA = []
                for userCAGrantNr in range(len(splitAccess)):
                    splitUserCA = splitAccess[userCAGrantNr].split(smallSplitter)
                    tmpListUserCA.append(splitUserCA)

                for moduleOrSect in splitModules:
                    info = moduleOrSect.split(':')
                    if info[0]=='module':
                       self.accessesMods.append([info[1],tmpListUserCA])
                    elif info[0]=='section':
                       self.accessesSects.append([info[1],tmpListUserCA])
                    else:
                       sys.stdout.write('Error in access.cfg - invalid section. '+info[1]+' should be either module or section - skipping entry\n')

    def getOutputCertificatArray(self):
        output = ""
        # generates the php code which fills on page load $accessMod[modName] with the certificates required for 'modName'
        phpstring = '<?php $accessCerts=array();'
        for moduleInfo in self.accessesMods:
              for uc in moduleInfo[1]:
                  phpstring += '$accessCerts[] = array("'+uc[0]+'","'+uc[1]+'");'
              phpstring += '$accessMod["'+moduleInfo[0]+'"]=$accessCerts;'
              phpstring += 'unset($accessCerts);'
        phpstring += ' ?>'
        output += phpstring

        # generates the php code which fills on page load $accessSect[sectName] with the certificates required for 'sectName'
        phpstring = '<?php $accessSect=array(); ?>'
        phpstring += '<?php $accessCerts=array();'
        for sectInfo in self.accessesSects:
              for uc in sectInfo[1]:
                  phpstring += '$accessCerts[] = array("'+uc[0]+'","'+uc[1]+'");'
              phpstring += '$accessSect["'+sectInfo[0]+'"]=$accessCerts;'
              phpstring += 'unset($accessCerts);'
        phpstring += ' ?>'
        output += phpstring
        return output

    # basic php funktion for accessing
    def getOutputPhpCheckFunctions(self):
        # php function that checks if module is accessible
        phpFuncCheckAccess = '<?php '
        phpFuncCheckAccess+= 'function isModuleAccessible($moduleName, $categoryName = "")'
        phpFuncCheckAccess+= '{   global $accessMod; global $ModuleResultsArray;'
        phpFuncCheckAccess+= '    if($categoryName == "")'
        phpFuncCheckAccess+= '    foreach ((array) $ModuleResultsArray as $module)'
        phpFuncCheckAccess+= '    {'
        phpFuncCheckAccess+= '       if ($module["module"]==$moduleName)'
        phpFuncCheckAccess+= '       {'
        phpFuncCheckAccess+= '           if (isCategoryAccessible($module["category"]) == false) { return false; }'
        phpFuncCheckAccess+= '       }'
        phpFuncCheckAccess+= '    }'
        phpFuncCheckAccess+= '    else'
        phpFuncCheckAccess+= '    {'
        phpFuncCheckAccess+= '       if (isCategoryAccessible($categoryName) == false) return false;'
        phpFuncCheckAccess+= '    }'
	phpFuncCheckAccess+= "    if (is_null($accessMod)) { return true; }"
	phpFuncCheckAccess+= "    if (!array_key_exists($moduleName, $accessMod)) { return true; }"
        phpFuncCheckAccess+= "    if (in_array(array('*', '*'), $accessMod[$moduleName])) { return true; }"
        phpFuncCheckAccess+= "    if (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] == 'on') {"
        phpFuncCheckAccess+= "    if (in_array(array($_SERVER['SSL_CLIENT_S_DN'], $_SERVER['SSL_CLIENT_I_DN']), $accessMod[$moduleName])) return true;"
        phpFuncCheckAccess+= "    if (in_array(array('*', $_SERVER['SSL_CLIENT_I_DN']), $accessMod[$moduleName])) return true;"
        phpFuncCheckAccess+= "    if (in_array(array($_SERVER['SSL_CLIENT_S_DN'], '*'), $accessMod[$moduleName])) return true;"
        phpFuncCheckAccess+= '    }'
        phpFuncCheckAccess+= '    return false;'
        phpFuncCheckAccess+= '}'
        # php function that checks if a category is accessible
        phpFuncCheckAccess+= 'function isCategoryAccessible($categoryName)'
        phpFuncCheckAccess+= '{'
        phpFuncCheckAccess+= '    global $accessSect;'
	phpFuncCheckAccess+= "    if (!array_key_exists($categoryName, $accessSect)) { return true; }"
        phpFuncCheckAccess+= "    if (in_array(array('*', '*'), $accessSect[$categoryName])) { return true; }"
        phpFuncCheckAccess+= "    if (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] == 'on') {"
        phpFuncCheckAccess+= "    if (in_array(array($_SERVER['SSL_CLIENT_S_DN'], $_SERVER['SSL_CLIENT_I_DN']), $accessSect[$categoryName])) return true;"
        phpFuncCheckAccess+= "    if (in_array(array('*', $_SERVER['SSL_CLIENT_I_DN']), $accessSect[$categoryName])) return true;"
        phpFuncCheckAccess+= "    if (in_array(array($_SERVER['SSL_CLIENT_S_DN'], '*'), $accessSect[$categoryName])) return true;"
        phpFuncCheckAccess+= '    }'
        phpFuncCheckAccess+= '    return false;'
        phpFuncCheckAccess+= '}'
        phpFuncCheckAccess+= ' ?>'

        return phpFuncCheckAccess

    # sets php variable if locked category icons are displayed
    def getOutputIconVar(self):
        if (self.hideIcons == True):
              return "<?php $hideIcons=true; ?>"
        else:
              return "<?php $hideIcons=false; ?>"

    # asked for
    def get_AccessMods(self):
        return self.accessesMods
    def get_AccessSects(self):
        return self.accessesSects
