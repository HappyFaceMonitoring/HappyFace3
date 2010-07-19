#!/usr/bin/env python

import os
import sys, getopt


def dumpInstanceCfg(name,xml):
    """ dumps a skeleton of instance config file """

    name_module_cfg = makeInstanceName(name, ".cfg")

    file_cont = ''
    file_cont += '[setup]\n\n'
    file_cont += 'mod_title\t=\tBoomerang [Joachim Ringelnatz]\n'
    file_cont += 'mod_type\t=\trated\n'
    file_cont += 'weight\t\t=\t1.0\n'
    file_cont += 'definition\t=\tpoetry.\n'
    file_cont += 'instruction\t='
    if xml:
        file_cont += "\n\n"
        file_cont += "base_url\t=\thttps://eine.url.de\n\n"
        file_cont += "fileextension\t=\txml\n\n"
        file_cont += "[phpArgs]\n"
        file_cont += "\ng\t=\ta\n"
        file_cont += "x\t=\ty\n"

    file_module_cfg = open(name_module_cfg,"w")
    file_module_cfg.write(file_cont)
    file_module_cfg.close

    return name_module_cfg

def dumpInstancePy(name):
    """dumps a skeleton of the instance python file"""

    name_module_py = makeInstanceName(name, ".py")

    ## get rid of ".py"
    (name_base, name_ext) = os.path.splitext(name_module_py)
    name_small = os.path.basename(name_base)

    del name_base
    del name_ext

    file_cont = ''
    file_cont += 'import os, sys\n\n'
    file_cont += 'from ' + name + ' import * \n\n'
    file_cont += 'class ' + name_small + '(' + name + '):\n\n'
    file_cont += '    def __init__(self,module_options):\n\n'
    file_cont += '        ' + name + '.__init__(self,module_options)'

    file_module = open(name_module_py,"w")

    file_module.write(file_cont)
    file_module.close()

    return name_module_py


def makeInstanceName(name, string):
    """
    Composes instance name out of capital letter
    name from the initial name. Has problems with
    names with neighboring capital letters.
    """

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

    name_module = "../HappyFace/modules/" + snippetList[0]
    snippetList.pop(0)
    name_module +=  "_".join(snippetList) + string

    return name_module

#def dumpHappycoreCss(name):
#    """dumps a skeleton for the core module css file"""
#
#    name_css = "../HappyFace/happycore/" + name + ".css"
#
#    file_css = open(name_css,"w")
#    
#    file_css.write(str("/*CSS file for the HappyFace module: " + name + " */\n"))
#
#    file_css.close()
#    return name_css
    

def dumpHappycoreCfg(name,xml):
    """dumps a skeleton for the core module config file"""

    name_cfg = "../HappyFace/happycore/" + name + ".cfg"

    file_cfg = open(name_cfg,"w")
    file_cfg.write("[setup]")
    if xml:
        file_cfg.write("\n\nfileextension\t=\txml\n")
        file_cfg.write("base_url\t=\thttps://eine.url.de\n")
    file_cfg.close()

    return name_cfg


def dumpHappycorePy(name,xml):
    """
    dumps a skeleton of the main python file of the core
    module.
    """

    name_py = "../HappyFace/happycore/" + name + ".py"

    intro = "from ModuleBase import *\n"
    intro += "from XMLParsing import *\n"
    
    if xml:
        intro += "from PhpDownload import *\n\n"
        init = 'class '+name+'(ModuleBase,PhpDownload):\n\n'
        init += '\tdef __init__(self,module_options):\n\n'
        #init += '\t\t# inherits from the ModuleBase Class\n'
        init += '\t\tModuleBase.__init__(self,module_options)\n'
        init += '\t\tPhpDownload.__init__(self)\n\n'

    else:
        init = '\nclass '+name+'(ModuleBase):\n\n'
        init += '\tdef __init__(self,module_options):\n\n'
        init += '\t\t# inherits from the ModuleBase Class\n'
        init += '\t\tModuleBase.__init__(self,module_options)\n\n'
        
    if xml:
        init += "\t\t## get the url\n"
        init += "\t\tself.base_url = self.configService.get('setup','base_url')\n\n"
    init += '\t\t# definition of the database table keys and pre-defined values\n'
    init += '\t\tself.db_keys["details_database"] = StringCol()\n'
    init += '\t\tself.db_values["details_database"] = ""\n\n'
    if xml:
        init += "\t\tself.dsTag = '"+name+"_xml_source'\n"
        init += "\t\tself.downloadRequest[self.dsTag] = 'wget|'+self.makeUrl()\n\n"

    run = '\tdef process(self):\n'
    run += '\t\t"""\n\t\tCollects the data from the web source. Stores it then into the\n'
    run += '\t\tsqlite data base. The overall status has to be determined here.\n\t\t"""\n'
    run += '\t\t# run the test\n\n'
    if xml:
        run += '\t\tsuccess,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))\n'
        run += '\t\tsource_tree, error_message = XMLParsing().parse_xmlfile_lxml(sourceFile)\n\n'
    run += '\t\t# parse the details and store it in a special database table\n'
    run += '\t\tdetails_database = self.__module__ + "_table_details"\n\n'
    run += '\t\tself.db_values["details_database"] = details_database\n\n'
    run += '\t\tdetails_db_keys = {}\n'
    run += '\t\tdetails_db_values = {}\n\n'
    run += '\t\t## define details_deb_keys here\n\n\n'
    run += '\t\tmy_subtable_class = self.table_init( details_database, details_db_keys )\n\n'
    if not xml:
        run += '\t\t### now do something\n\n'
    else:
        run += '\t\t## now start parsing the xml tree\n'
        run += '\t\troot = source_tree.getroot()\n\n'
        run += '\t\t### now do something\n\n'
    run += '\t\t# always happy for the moment\n'
    run += '\t\tself.status = 1.\n\n'

    output = '\tdef output(self):\n\n'
    output += '\t\t"""\n\t\tAccess data from the sqlite database from here and decide how\n'
    output += '\t\tto present it'
    output += '\n\t\t"""\n'
    #output += '\t\tmodule_content = """\n'
    #output += '\t\t<?php\n'
    #output += "\t\tprintf('War einmal ein Boomerang,<br />');\n"
    #output += "\t\tprintf('War um ein Weniges zu lang.<br />');\n"
    #output += "\t\tprintf('Boomerang flog ein Stueck<br />');\n"
    #output += "\t\tprintf('Und kehrte nie mehr zurueck.<br />');\n"
    #output += "\t\tprintf('Publikum noch stundenlang<br />');\n"
    #output += "\t\tprintf('Wartete auf Boomerang.<br />');\n"
    #output += '\t\t?>\n'
    #output += '\t\t"""\n\n'

    output += '\t\tbegin = []\n'
    output += '\t\tbegin.append(\'<table class="TableData">\')\n'
    output += '\t\tbegin.append(\' <tr class="TableHeader">\')\n'
    output += '\t\tbegin.append(\'  <td>Boomerang</td>\')\n'
    output += '\t\tbegin.append(\' </tr>\')\n\n'

    output += '\t\tinfo_row = []\n'
    output += '\t\tinfo_row.append(""" <tr class="ok">""")\n'
    output += '\t\t#info_row.append("""  <td>\' . $info["key"] . \'</td>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>War einmal ein Boomerang,</td></tr>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>War um ein Weniges zu lang.,</td></tr>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>Boomerang flog ein Stueck,</td></tr>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>Und kehrte nie mehr zurueck.</td></tr>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>Publikum noch stundenlang,</td></tr>""")\n'
    output += '\t\tinfo_row.append("""  <tr class="ok"><td>Wartete auf Boomerang</td>""")\n'
    output += '\t\tinfo_row.append(  \' </tr>\')\n\n'

    output += '\t\tmid = []\n'
    output += '\t\tmid.append(  \'</table>\')\n'
    output += '\t\tmid.append(  \'<br />\');\n'
    output += '\t\tmid.append("""<input type="button" value="details" onfocus="this.blur()" onclick="show_hide(\\\\\'""" + self.__module__+ "_failed_result" + """\\\\\');" />""")\n'
    output += '\t\tmid.append(  \'<div class="DetailedInfo" id="\' + self.__module__+ \'_failed_result" style="display:none;">\')\n'
    output += '\t\tmid.append(  \' <table class="TableDetails">\')\n'
    output += '\t\tmid.append(  \'  <tr class="TableHeader">\')\n'
    output += '\t\tmid.append(  \'   <td>details</td>\')\n'
    output += '\t\tmid.append(  \'  </tr>\')\n\n'

    output += '\t\tdetailed_row = []\n'
    output += '\t\tdetailed_row.append("""  <tr class="ok">""")\n'
    output += '\t\t#detailed_row.append("""   <td>\' . $info["key"]   . \'</td>""")\n'
    output += '\t\tdetailed_row.append("""   <td>Gedicht.</td>""")\n'
    output += '\t\tdetailed_row.append(  \'  </tr>\');\n\n'

    output += '\t\tend = []\n'
    output += '\t\tend.append(\' </table>\')\n'
    output += '\t\tend.append(\'</div>\')\n\n'

    output += '\t\tmodule_content = self.PHPArrayToString(begin) + """<?php\n\n'
    output += '\t\t#$details_db_sqlquery = "SELECT * FROM " . $data["details_database"] . " WHERE timestamp = " . $data["timestamp"];\n\n'
    output += '\t\t#foreach ($dbh->query($details_db_sqlquery) as $info)\n'
    output += '\t\t#{\n'
    output += '\t\tprint(\'""" + self.PHPArrayToString(info_row) + """\');\n'
    output += '\t\t#}\n\n'
    output += '\t\tprint(\'""" + self.PHPArrayToString(mid) + """\');\n'
    
    output += '\t\t#foreach ($dbh->query($details_db_sqlquery) as $info)\n'
    output += '\t\t#{\n'
    output += '\t\tprint(\'""" + self.PHPArrayToString(detailed_row) + """\');\n'
    output += '\t\t#}\n\n'

    output += '\t\tprint(\'""" + self.PHPArrayToString(end) + """\');\n'
    output += '\t\t?>"""\n\n'

    output += '\t\treturn self.PHPOutput(module_content)\n\n'

    file_py = open(name_py,"w")
    file_py.write(intro)
    file_py.write(init)
    file_py.write(run)
    file_py.write(output)
    file_py.close()

    return name_py

    

def dumpFiles(name,xml):
    """executes all the dump functions"""
    name_py = dumpHappycorePy(name,xml)
    name_cfg = dumpHappycoreCfg(name,xml)
    #name_css = dumpHappycoreCss(name)
    name_inst_py = dumpInstancePy(name)
    name_inst_cfg = dumpInstanceCfg(name,xml)
    return name_py,name_cfg,name_inst_py,name_inst_cfg

def printExitMessage(name_py,name_cfg,name_inst_py,name_inst_cfg):
    """prints the names of the files created"""
    print "wrote the files " + name_py + ", " + name_cfg + ", " + name_inst_py + ",and " + name_inst_cfg +"."

def usage():
    """usage of this script"""
    print "usage: hf-dump-skeleton [option]"
    print "be careful! No testing of this script yet!"
    print "options are"
    print
    print "-h,--help:\t\t\tprint this message and exit"
    print "-x,--xml:\t\t\tif switched on, the skeleton for xml parsing will be added."
    print "\t\t\t\tdefault is False."
    print "-n ARG, --name=ARG:\t\tdefine the name of the new test."


def main(argv):
    """ reads in options"""

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

    name_py,name_cfg,name_mod_py,name_mod_cfg = dumpFiles(name,xml)

    printExitMessage(name_py,name_cfg,name_mod_py,name_mod_cfg)
