from ModuleBase import *
from InputService import *
import os
import sys
import re
import subprocess
import time

class LogMessages(ModuleBase):

    def __init__(self,module_options):
        # inherits from the ModuleBase Class
        ModuleBase.__init__(self, module_options)

        # create an InputService
        self.inputService = InputService(self)
        self.inputService.prepareInput('logfile', 'log')
        
        
        # read rule list
        self.rules = []
        rulecount = 1
        cont = True

        self.setDEFAULTconfig()

        while cont:
            # go on reading until rule does not exist
            try:
                rule = self.configService.getDefault('logrules', 'rule%i' % rulecount, '')

                if rule == '':
                    # the rule before was the last rule
                    cont = False
                else:
                    # a rule consists of two parts separated by a ';'
                    # the first part indicates a string that has to appear in
                    # the error message, the second gives the related error class
                    rule = rule.split(';')

                    if len(rule) == 2:
                        rule[0] = rule[0].strip()
                        rule[1] = rule[1].strip()
                        if rule[1] in ('critical', 'warning', 'ignore', 'hide', 'delete'):
                            self.rules.append(rule)
                        else:
                            err = 'Error while reading rule %i: Expecting class critical, warning, ignore, hide or delete.\n' % rulecount
                            sys.stdout.write(err)
                            self.error_message += err
                    else:
                        err = 'Error while reading rule %i: Expecting the character ";" exactly one time.\n' % rulecount
                        sys.stdout.write(err)
                        self.error_message += err
                    rulecount += 1

            except:
                cont = False

        # read column delimiter setting
        self.columndelimiter = self.configService.getDefault('logdisplay','columndelimiter', 'space')
        # some special values allowed
        if self.columndelimiter == 'space':
            self.columndelimiter = ' '
        elif self.columndelimiter == 'tab':
            self.columndelimiter = '\t'


        # read column list
        self.column = []
        columncount = 1
        self.maxsourcecolumn = 0
        cont = True

        while cont:
            # go on reading until column does not exist
            column = self.configService.getDefault('logdisplay', 'column%i' % columncount, '')

            if column == '':
                cont = False
            else:
                # a column consists of two parts separated by a ';'
                # the first part indicates a title string for the column
                # the second part indicates the group, which is described
                # in the function isvalidgroup
                # example: Time;^(.{10});1     this extracts the first 10 chars

                column = column.split(';', 1)
                if len(column) == 2:

                    # verify that the second part is a valid group
                    if self.isvalidgroup(column[1]):
                        self.column.append(column)
                    else:
                        err = 'Error while reading column %i: Expecting a valid group after first ";".\n' % columncount
                        sys.stdout.write(err)
                        self.error_message += err

                else:
                    err = 'Error while reading column %i: Expecting the character ";" at least one time.\n' % columncount
                    sys.stdout.write(err)
                    self.error_message += err
                columncount += 1

        # read setting sort (comma separated list of source columns)
        self.sort = self.configService.getDefault('logdisplay', 'sort', '^(.*)$;1')
        if not self.isvalidgroup(self.sort):
            err = 'Error while reading setting sort: Expecting a valid group.\n'
            sys.stdout.write(err)
            self.error_message += err
            # default
            self.sort = '^(.*)$;1'

        # read setting unique (empty or comma seperated list of source columns)
        self.unique = self.configService.getDefault('logdisplay', 'unique', '')
        self.unique = self.unique.strip()
        if self.unique != '' and not self.isvalidgroup(self.unique):
            err = 'Error while reading setting unique: Expecting empty setting or a valid group.\n' 
            sys.stdout.write(err)
            self.error_message += err
            # default -> empty means no uniqueness required
            self.unique = ''

        # read setting sortorder (must be ascending or descending)
        self.sortorder = self.configService.getDefault('logdisplay', 'sortorder', 'ascending')
        if self.sortorder not in ('ascending', 'descending'):
            err = 'Error while reading setting sortorder: Expecting "ascending" or "descending".\n'
            sys.stdout.write(err)
            self.error_message += err
            # default
            self.sortorder = 'ascending'

        # the contents of the logfile (after some filtering and sorting) is
        # stored into the database
        self.db_keys['logmessages'] = StringCol()
        self.db_values['logmessages'] = ''
       

    def run(self):
        # set initial values
        self.status = 1.0
        
        lines = self.inputService.fetchInput('logfile', 'log')
        if len(lines) < 1:
            self.status = -1.
            self.inputService.printError('No input data.')


        # process info
        if self.status != -1:
            # if info available -> it is in the array lines
            messagelist = {}
            messagecount = 0

            # start preprocessing of all lines in python
            for line in lines:
                line = line.strip()

                # strip empty lines
                if line == '':
                    continue

                # What we experience here seems to be an inherent concept
                # failure in HappyFace: The status of the module has to be
                # determined by python, although (by the original idea) a
                # change of rules should affect the output of the module
                # correctly, so the status of the lines in the output has
                # to be determined by php. Thus, we have to go through the
                # error lines twice, once in python and once in php.
                # Nevertheless, a change of the rules cannot alter the
                # status of the older data points, since this is impossible
                # by construction. -.-

                skipline = False
                for rule in self.rules:
                    # check if a rule applies
                    # "*"s in the rules are interpreted as .* in regexp
                    # "?"s in the rules are interpreted as . in regexp
                    if re.search(re.escape(rule[0]).replace('\\*','(.*)').replace('\\?','(.)'), line):
                        # ... and if this is the case, set status accordingly
                        if rule[1] == 'warning':
                            self.status = min(self.status, 0.5)
                        elif rule[1] == 'critical':
                            self.status = min(self.status, 0.0)
                        elif rule[1] == 'delete':
                            # lines that match this rule will not be stored in db
                            skipline = True
                        break

                # also, the lines have to be sorted and made unique according
                # to the given parameters
                if skipline == False:
                    # build string for sorting
                    sortstr = self.getlinegroup(line, self.sort)
                    # last sort criterion is the message number
                    sortstr += ' '+str(messagecount)

                    # if uniquement is enforced
                    uniquestr = ''
                    if self.unique != '':
                        # build string for uniqueness check
                        uniquestr = self.getlinegroup(line, self.unique)
                
                if skipline == False:
                    # finally, add relevant messages into array (with uniqueinfo)
                    messagelist[sortstr] = [line, uniquestr]
                    messagecount += 1

            # save the retrieved list (sorted!) into db
            k = messagelist.keys()
            k = sorted(k, key=str.lower)
            if self.sortorder == 'descending':
                k.reverse()


            # keep track of unique strings
            uniques = []
            for msg in k:
                # check for uniqueness
                if messagelist[msg][1] in uniques:
                    continue
                # append unique strings that are already added
                # why check for uniqueness so late? because sorting has to be
                # done beforehands!
                if self.unique != '':
                    uniques.append(messagelist[msg][1])
                
                self.db_values['logmessages'] += messagelist[msg][0] + '\n'
            # that's it. formatting is done in python.

    def isvalidgroup(self, group):
        # return True if the given string is a valid group
        # a group is a rule how to extract information from a message line
        # a valid group has the following syntax:
        # [regexp;]source column;source column;...

        # split by ";"
        # NOTICE: up until now, the regular expressions may not contain any ";"s
        # because these will be interpreted as delimiters
        group = group.strip().split(';')
        reg = None

        for i in range(0, len(group)):
            # a valid element is a number or a regexp
            # check if element is a number
            try:
                # sc is the source column
                sc = int(group[i])

                # sc must be positive
                if sc < 1:
                    return False

                # also, remember the maximal source column
                # this is done to expand the last source column to the rest of
                # the line
                if (reg == None) and (sc > self.maxsourcecolumn):
                    self.maxsourcecolumn = sc
                
            except:
                # first element may also be a valid regexp
                if i == 0:
                    # check if element is a valid regexp
                    try:
                        reg = re.compile(group[i])
                    except:
                        return False
                else:
                    return False

        return True

    def getlinegroup(self, line, group):
        # this function applies a group to a given line and retrieves the info
        # a valid group has the following syntax:
        # [regexp;]source column;source column;...

        # split by ";"
        # NOTICE: up until now, the regular expressions may not contain any ";"s
        # because these will be interpreted as delimiters
        group = group.strip().split(';')

        # split line the given column delimiter into source columns
        # thereby, expand the highest mentioned column to the rest of the line
        linearray = line.split(self.columndelimiter, self.maxsourcecolumn-1)

        # return value will contain the extracted info
        ret = ''

        for i in range(0, len(group)):
            # a valid element is a number or a regexp
            # check if element is a number
            try:
                # sc is the source column number
                sc = int(group[i])

                # separate with spaces
                if ret != '':
                    ret += ' '
                
                if sc < 1:
                    ret += ''
                elif sc <= len(linearray):
                    # add the requested source column to the result
                    ret += linearray[sc-1]
                else:
                    ret += ''
                    
            except:

                # first element may also be a valid regexp
                if i == 0:
                    # check if element is a valid regexp
                    try:
                        reg = re.compile(group[i])
                        match = reg.match(line)
                        if not match:
                            return ''
                        else:
                            # matched groups replace linearray
                            linearray = match.groups()
                            
                    except:
                        return ''
                else:
                    return ''

        return ret


    def tophpstr(self, phpstr):
        # helper function which quotes a given string, so it can be used in
        # php output
        return "'" + phpstr.replace('\\', '\\\\').replace('\'', '\\\'') + "'"

    def output(self):

        # php handles the classification of the lines and converts them
        # into an html table (and an extra table for hidden elements)
        module_content = """<?php

        $ar = explode("\\n", $data['logmessages']);
        $errorcount = 0;
        $errorrows = "    <tr>"""

        # add all column titles
        for col in self.column:
            module_content += '<th>".htmlspecialchars(' + self.tophpstr(col[0]) + ')."</th>'

        module_content += """</tr>\\n";
        $hiddencount = 0;
        $hiddenrows = $errorrows;
        
        foreach($ar as $line)
        {
            $tr = '';
            $cl = 'ignore';
            
            if($line == '')
                continue;
            """

        # apply the rules and thus determine the class
        # "*"s in the rules are interpreted as .* in regexp
        # "?"s in the rules are interpreted as . in regexp
        for rule in self.rules:
            # python needs "/"-delimiters for regexp
            regexp = '/'+re.escape(rule[0]).replace('\\*','(.*)').replace('\\?','(.)')+'/'
            module_content += """
            elseif(preg_match(""" + self.tophpstr(regexp) + """, $line) > 0)
                $cl = """ + self.tophpstr(rule[1])+  """;
            """

        # from the class, choose the correct form of output
        module_content += """
            if($cl == 'hide')
                $trclass = '';
            elseif($cl == 'ignore')
                $trclass = '';
            elseif($cl == 'warning')
                $trclass = 'warning';
            elseif($cl == 'critical')
                $trclass = 'critical';

            """

        # now, determine the contents of the columns
        # split line into source columns with column delimiters
        # also, expand last column to the rest of the line
        module_content += """
            $linearray = explode(""" + self.tophpstr(self.columndelimiter)+  """, $line, """ + str(self.maxsourcecolumn) + """);
            """

        # string which contains the php string of the columns
        colout = ''
        cnum = 0

        # build the string by going through all columns
        for col in self.column:
            # count the columns
            cnum += 1
            colout += '<td>'

            # read the group and split by ";"
            group = col[1].strip().split(';')
            # there are two possibilities, either first entry of the group is a
            # number or a regexp, with this try, we will find out
            try:
                testdummy = group[0]
                # if no exception thrown here, then we have a list of source
                # columns -- easy going
                for sc in group:
                    # just output the relevant source column
                    # keep in mind, that the expected index might not exist
                    colout += """'.htmlspecialchars((array_key_exists("""+str(int(sc)-1)+""", $linearray))?$linearray["""+str(int(sc)-1)+"""]:'').' """
            
            except:
                # in this case, our first entry is a regexp
                # thus, we first run the regexp on the current line and call
                # the result $matches_#cnum#
                module_content += """
            if(!preg_match(""" + self.tophpstr('/'+group[0]+'/') + """, $line, $matches_"""+str(cnum)+"""))
                $matches_"""+str(cnum)+""" = 0;
                
                """

                # now we can just gather the relevant entries
                for sc in group[1:]:
                    # keep in mind that the expected variable may not exist
                    # or the index may not exist
                    colout += """'.htmlspecialchars((($matches_"""+str(cnum)+"""!=0)&&(array_key_exists("""+str(int(sc)-1)+""",$matches_"""+str(cnum)+""")))?$matches_"""+str(cnum)+"""["""+str(int(sc)-1)+"""]:'').' """

            # close the td
            colout += '</td>'

        # now, all data for the current line is gathered and can be stored in $tr
        # from there, it will be filled into the relevant table
        module_content += """

            $tr = '    <tr class="'.$trclass.'">""" + colout + """</tr>';

            if($cl == 'hide')
            {
                $hiddenrows .= $tr."\\n";
                $hiddencount += 1;
            }
            else
            {
                $errorrows .= $tr."\\n";
                $errorcount += 1;
            }

        }

        if($errorcount == 0)
            print('<h3><img src="config/images/symbol_ok.png">&nbsp;No errors/warnings detected.</h3>');
        else
            print("<table class=\\"TableData\\">\\n".$errorrows.'</table>');

        if($hiddencount != 0)
            print('<p><input type="submit" value="Show '.$hiddencount.' hidden messages" onclick="javascript:document.getElementById(\\'div_hidden_""" + self.__module__ + """\\').style.display=((document.getElementById(\\'div_hidden_""" + self.__module__ + """\\').style.display==\\'none\\')?\\'block\\':\\'none\\')"><div id="div_hidden_""" + self.__module__ + """" style="display: none;"><table class="TableData">\n'.$hiddenrows.'</table></div>')

        ?>"""
        # the above code creates a button which shows/hides a div containing
        # a hidden table

        return self.PHPOutput(module_content)

    def setDEFAULTconfig(self):
        # add current date to config file
        localtime = time.localtime(time.time())
        self.configService.set('DEFAULT','_DAY',localtime[2])
        self.configService.set('DEFAULT','_YEAR',localtime[0])
        self.configService.set('DEFAULT','_MONTH',localtime[1])
        month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        self.configService.set('DEFAULT','_MONTHalpha',month[localtime[1]-1])
