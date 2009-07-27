#!/usr/bin/env python

import sys, getopt

def dumpModuleCfg(name,xml):

    name_module_cfg = makeModuleName(name, ".cfg")

    file_cont = ''
    file_cont += '[setup]\n\n'
    file_cont += 'mod_title\t=\tBoomerang [Joachim Ringelnatz]\n'
    file_cont += 'mod_type\t=\trated\n'
    file_cont += 'weight\t\t=\t1.0\n'
    file_cont += 'definition\t=\tpoetry.\n'
    file_cont += 'instruction\t='
    if xml:
        file_cont += "\n\n"
        file_cont += "base_url\t=\t\n\n"
        file_cont += "file_type\t=\txml\n\n"
        file_cont += "[phpArgs]\n"

    file_module_cfg = open(name_module_cfg,"w")
    file_module_cfg.write(file_cont)
    file_module_cfg.close

    return name_module_cfg

def dumpModulePy(name):

    name_module_py = makeModuleName(name, ".py")

    ## get rid of ".py"
    name_module = name_module_py.split(".",1)
    name_nomodule = name_module[0].split("/",1)
    name_small = name_nomodule[1]

    del name_module
    del name_nomodule

    file_cont = ''
    file_cont += 'import os, sys\n\n'
    file_cont += 'from ' + name + ' import * \n\n'
    file_cont += 'class ' + name_small + '(' + name + '):\n\n'
    file_cont += '    def __init__(self,category,timestamp,archive_dir):\n\n'
    file_cont += '        ' + name + '.__init__(self,category,timestamp,archive_dir)'

    file_module = open(name_module_py,"w")

    file_module.write(file_cont)
    file_module.close()

    return name_module_py


def makeModuleName(name, string):

    name_module = ''

    ## In this loop the name will be split at its uppe cases.
    ## If the first letter is an upper case letter, than the
    ## first entry in the list is empty
    ## numbers are not accepted
    snippetList = []
    name_snippet = ''
    for char in name:
        if 'a' <= char <= 'z':
            name_snippet += char
        elif 'A' <= char <= 'Z':
            snippetList.append(name_snippet)
            name_snippet = char.lower()
    ## put the last snippet also into the list
    snippetList.append(name_snippet)

    name_module = "modules/" + snippetList[0]
    snippetList.pop(0)
    name_module +=  "_".join(snippetList) + string

    return name_module

def dumpHappycoreCss(name):

    name_css = "happycore/" + name + ".css"

    file_css = open(name_css,"w")
    
    file_css.write(str("/*CSS file for the HappyFace module: " + name + " */\n"))
    file_css.write(str("." + name + "Table,." + name + "TableDetails {\n"))
    file_css.write("        border: solid 1px #999;\n")
    file_css.write("        width: 800px;\n")
    file_css.write("}\n\n")
    file_css.write(str("." + name + "Table td {\n"))
    file_css.write("	padding: 5px;\n")
    file_css.write("	border: solid 1px #999;\n")
    file_css.write("	text-align: left;\n")
    file_css.write("}\n\n")
    file_css.write(str("." + name + "TableDetails td {\n"))
    file_css.write("	padding: 5px;\n")
    file_css.write("	border: solid 1px #999;\n")
    file_css.write("	text-align: left;\n")
    file_css.write("}\n\n")
    file_css.write(str("." + name + "DetailedInfo { \n"))
    file_css.write("	font-family: monospace;\n")
    file_css.write("	line-height: 14px;\n")
    file_css.write("}\n\n\n")
    file_css.write("tr.success {\n")
    file_css.write("	background-color:  \#AAFFAA;\n")
    file_css.write("}\n")
    file_css.write("tr.warning {\n")
    file_css.write("	background-color:  \#FFAA46;\n")
    file_css.write("}\n")
    file_css.write("tr.critical {\n")
    file_css.write("	background-color:  \#FF6464;\n")
    file_css.write("}\n")
    file_css.write("tr.undef {\n")
    file_css.write("	background-color:  \#C0C0C0;\n")
    file_css.write("}\n")
        
    file_css.close()
    return name_css
    

def dumpHappycoreCfg(name):

    name_cfg = "happycore/" + name + ".cfg"

    file_cfg = open(name_cfg,"w")
    file_cfg.write("[setup]")
    file_cfg.close()

    return name_cfg


def dumpHappycorePy(name,xml):

    name_py = "happycore/" + name + ".py"

    intro = "from ModuleBase import *\n"
    intro += "from XMLParsing import *\n\n" 

    init = 'class '+name+'(ModuleBase):\n\n'
    init += '\tdef __init__(self,category,timestamp,storage_dir):\n\n'
    init += '\t\t# inherits from the ModuleBase Class\n'
    init += '\t\tModuleBase.__init__(self,category,timestamp,storage_dir)\n\n'
    init += "\t\tconfig = self.readConfigFile('./happycore/"+name+"')\n"
    init += "\t\tself.addCssFile(config,'./happycore/"+name+"')\n\n"
    if xml:
        init += "\t\t## get the url\n"
        init += "\t\tself.base_url = self.mod_config.get('setup','base_url')\n"
        init += "\t\tself.phpArgs = {}\n\n"
        init += "\t\t# read in the php arguments\n"
        init += "\t\tself.getPhpArgs(self.mod_config)\n\n"
    init += '\t\t# definition of the database table keys and pre-defined values\n'
    init += '\t\tself.db_keys["details_database"] = StringCol()\n'
    init += '\t\tself.db_values["details_database"] = ""\n\n'
    if xml:
        init += "\t\tself.dsTag = '"+name+"_xml_source'\n"
        init += "\t\tself.fileType = self.mod_config.get('setup','file_type')\n\n"
        init += "\t\tself.makeUrl()\n\n"
        init += "\tdef getPhpArgs(self, config):\n"
        init += "\t\t\tfor i in config.items('phpArgs'):\n"
        init += "\t\t\t\tself.phpArgs[i[0]] = i[1]\n\n"
        init += "\tdef makeUrl(self):\n"
        init += "\t\t\tif len(self.phpArgs) == 0:\n"
        init += "\t\t\t\tprint \"Php Error: makeUrl called without phpArgs\"\n"
        init += "\t\t\t\tsys.exit()\n"
        init += "\t\t\tif self.base_url == \"\":\n"
        init += "\t\t\t\tprint \"Php Error: makeUrl called without base_url\"\n"
        init += "\t\t\t\tsys.exit()\n\n"
        init += "\t\t\t## if last char of url is \"/\", remove it\n"
        init += "\t\t\tif self.base_url[-1] == \"/\":\n"
        init += "\t\t\t\tself.base_url = self.base_url[:-1]\n\n"
        init += "\t\t\targList = []\n"
        init += "\t\t\tfor i in self.phpArgs:\n"
        init += "\t\t\t\tfor j in self.phpArgs[i].split(\",\"):\n"
        init += "\t\t\t\t\targList.append(i+'='+j)\n\n"
        init += "\t\t\tself.downloadRequest[self.dsTag] = 'wget:'+self.fileType+':'+self.base_url+'/'+self.instance+'/agents'+\"?\"+\"&\".join(argList)\n\n"

    run = '\tdef run(self):\n'
    run += '\t\t# run the test\n\n'
    if xml:
        run += '\t\tif not self.dsTag in self.downloadRequest:\n'
        run += '\t\t\terr = \'Error: Could not find required tag: \'+self.dsTag+\'\\n\'\n'
        run += '\t\t\tsys.stdout.write(err)\n'
        run += '\t\t\tself.error_message +=err\n'
        run += '\t\t\treturn -1\n\n'
        run += '\t\tsuccess,sourceFile = self.downloadService.getFile(self.downloadRequest[self.dsTag])\n'
        run += '\t\tsource_tree = XMLParsing().parse_xmlfile_lxml(sourceFile)\n\n'
        run += '\t\t##############################################################################\n'
        run += '\t\t# if xml parsing fails, abort the test;\n'
        run += '\t\t# self.status will be pre-defined -1\n'
        run += '\t\tif source_tree == "": return\n\n'       
    run += '\t\t# parse the details and store it in a special database table\n'
    run += '\t\tdetails_database = self.__module__ + "_table_details"\n\n'
    run += '\t\tself.db_values["details_database"] = details_database\n\n'
    run += '\t\tdetails_db_keys = {}\n'
    run += '\t\tdetails_db_values = {}\n\n'
    run += '\t\t## write global after which the query will work\n'
    run += '\t\tdetails_db_keys["timestamp"] = IntCol()\n'
    run += '\t\tdetails_db_values["timestamp"] = self.timestamp\n\n'
    run += '\t\t## create index for timestamp\n'
    run += '\t\tdetails_db_keys["index"] = DatabaseIndex(\'timestamp\')\n\n'
    run += '\t\t## lock object enables exclusive access to the database\n'
    run += '\t\tself.lock.acquire()\n\n'
    run += '\t\tDetails_DB_Class = type(details_database, (SQLObject,), details_db_keys )\n\n'
    run += '\t\tDetails_DB_Class.sqlmeta.cacheValues = False\n'
    run += '\t\tDetails_DB_Class.sqlmeta.fromDatabase = True\n\n'
    run += '\t\t## if table is not existing, create it\n'
    run += '\t\tDetails_DB_Class.createTable(ifNotExists=True)\n\n'
    if not xml:
        run += '\t\t### now do something\n\n'
    else:
        run += '\t\t## now start parsing the xml tree\n'
        run += '\t\troot = source_tree.getroot()\n\n'
        run += '\t\t### now do something\n\n'
    run += '\t\t# unlock the database access\n'
    run += '\t\tself.lock.release()\n\n'
    run += '\t\t# always happy for the moment\n'
    run += '\t\tself.status = 1.\n\n'

    output = '\tdef output(self):\n\n'
    output += '\t\tmodule_content = """\n'
    output += '\t\t<?php\n'
    output += "\t\tprintf('War einmal ein Boomerang,<br>');\n"
    output += "\t\tprintf('War um ein Weniges zu lang.<br>');\n"
    output += "\t\tprintf('Boomerang flog ein Stueck<br>');\n"
    output += "\t\tprintf('Und kehrte nie mehr zurueck.<br>');\n"
    output += "\t\tprintf('Publikum noch stundenlang<br>');\n"
    output += "\t\tprintf('Wartete auf Boomerang.<br>');\n"
    output += '\t\t?>\n'
    output += '\t\t"""\n\n'
    output += '\t\treturn self.PHPOutput(module_content)\n'

    file_py = open(name_py,"w")
    file_py.write(intro)
    file_py.write(init)
    file_py.write(run)
    file_py.write(output)
    file_py.close()

    return name_py

    

def dumpFiles(name,xml):
    name_py = dumpHappycorePy(name,xml)
    name_cfg = dumpHappycoreCfg(name)
    name_css = dumpHappycoreCss(name)
    name_mod_py = dumpModulePy(name)
    name_mod_cfg = dumpModuleCfg(name,xml)
    return name_py,name_cfg,name_css,name_mod_py,name_mod_cfg

def printExitMessage(name_py,name_cfg,name_css,name_mod_py,name_mod_cfg):
    print "wrote the files " + name_py + ", " + name_cfg + ", " + name_css + ", " + name_mod_py + ",and " + name_mod_cfg +"."

def usage():
    print "usage: dumpSceleton [option]"
    print "options are"
    print
    print "-h,--help:\t\t\tprint this message and exit"
    print "-x,--xml:\t\t\tif switched on, the sceleton for xml parsing will be added."
    print "\t\t\t\tdefault is False."
    print "-n ARG, --name=ARG:\t\tdefine the name of the new test."


def main(argv):

    ## the name of the test
    name = "RingelnatzPoetry"

    ## should parsing an xml file be added?
    xml = False

    
    try:
        options,arguments = getopt.getopt(argv,"h,x,n:",["help","xml","name"])

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in options:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif opt in ("-x","--xml"):
            xml = True
        elif opt in ("-n", "--name"):
            name = arg

    return name, xml


if __name__ == "__main__":

    ## get the command lines
    name, xml = main(sys.argv[1:])

    name_py,name_cfg,name_css,name_mod_py,name_mod_cfg = dumpFiles(name,xml)

    printExitMessage(name_py,name_cfg,name_css,name_mod_py,name_mod_cfg)
