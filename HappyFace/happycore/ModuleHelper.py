import os
import subprocess
import re
from threading import Thread
from HTMLParser import HTMLParser

# a class that provides some simple methods which are required by many modules
class ModuleHelper(object):
    def __init__(self):
        self.error_message = ''
        self.name = ''
        
    def __init__(self, name = ''):
        self.name = name
        self.error_message = ''

    def getName(self):
        if hasattr(self, 'name') and (self.name != ''):
            return self.name
        else:
            return self.__class__.__name__

    def printMessage(self, message):
        # print a message to stdout
        print self.getName() + ': ' + message.replace('\n', '\n\t')

    def printError(self, message):
        # print an error message to std out and to the web site
        self.printMessage(message)
        self.error_message += message
        
    def printInputError(self, section, prefix, message):
        self.printError('Error while reading settings "' + prefix + '..." in section "' + section + '":\n' + message)

    def htmlMessage(self, message, type = 'information'):

        if type == 'information':
            #return '<h3><img src="config/images/symbol_failed.png">&nbsp;' + message + '</h3>'
            return '<h3><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAAZiS0dEAAAAAAAA+UO7fwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAzBJREFUOMuVlE9oXGUUxc+57zWxTFKSScoQSEOaSW0CMbpIEdsmVStN4A2IIhp0IQgu3bqdN5u6EEFciUsX7oSi78WAtYkWpmAWFlNNYoLpIlgX+QMNyUxm3vuOC6NEnaTmLj84v+/eew6XAKBSaRjAcwJ+h/SDheEvOGapVOoTMEkXhq+R/Ex7e0bfBzwPAJ5ksfjj/wSNA/hEUhvIVqpUmnfr60PJygpgBi+fl9fZWZVzL1sYTh8KCsNBkDcAPA4JIkEga5I+ttOnYdksSCJdXqZ78OAxmn3pSqWLjWAuDEMBP6taPadaDSB/IzDOYnGLAOBKpY8IvKNqVcnCAlWrwXI5+L29kPSmheGn++P5AmZpdim9fx9eTw8A3GCx+NJfn/HACF0gPwTwqtvaQrqyAnZ0yM/nUzj3lszu0vO+ULXamy4tycvliNbWW3b9+tWD3bPBbgZATilJzibz87JsFtbdTVYqSOfmlMzOounaNcLsc5uefuXfeh7h3tcCXkimp6HFRYAE6nWcuHwZ9LxVRlHfcaMFNzm56UZHVQFUAeSuXJELgrmjNA07VBD4INeUJLl6uSxtb5OnTsHr7ZV35kxNUr/F8VojrTUEAt+pWs3Vbt6Ue/iQ/siImsbGwJYWpmtrzSQXXaHgPxLogiCnQmEZu7vP1G7fhpKEfl+fvK6uVM49a9nsXba1QdvbGZLfHAl0QdBE8p7b3OyvzcxAe3vwBwbkDw0Rzr1ocfytpIvW0rIFM6BeH3OFwleHAmm27jY2OuvlsgTAy+Xk9/dTafo6o2gKACyKKpJ6mMksKUlAcsIFwdv/MMUFQQfJn9zGRq52586fLjU3o3liAkjTdxlF7/9nx4VCO5zbVKUCZjL3BDxtUbQLAEZyxu3s5Or7MAE4ceEClCSLkD5oGI0o2pLZVWYyCYAhAlMHR37Cra5q3134+bysvb0OYIRx7A7Lm0XRLQBnASQAOv9+l1Tyh4fhnT8Pnjwpf3CQcu4Ni+OdRwWfUbQm6T0A51wQyAVBO/eD3AdyAc41yaxsUXTpWNe6UPgewFOS2g0AGMe/ShqFWQxpHMev5yV1Wxzv/AEP8YwFMPd9VwAAAABJRU5ErkJggg==">&nbsp;' + message + '</h3>'

        if type == 'error':
            #return '<h3><img src="config/images/symbol_failed.png">&nbsp;' + message + '</h3>'
            return '<h3><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAAZiS0dEAAAAAAAA+UO7fwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAzBJREFUOMuVlE9oXGUUxc+57zWxTFKSScoQSEOaSW0CMbpIEdsmVStN4A2IIhp0IQgu3bqdN5u6EEFciUsX7oSi78WAtYkWpmAWFlNNYoLpIlgX+QMNyUxm3vuOC6NEnaTmLj84v+/eew6XAKBSaRjAcwJ+h/SDheEvOGapVOoTMEkXhq+R/Ex7e0bfBzwPAJ5ksfjj/wSNA/hEUhvIVqpUmnfr60PJygpgBi+fl9fZWZVzL1sYTh8KCsNBkDcAPA4JIkEga5I+ttOnYdksSCJdXqZ78OAxmn3pSqWLjWAuDEMBP6taPadaDSB/IzDOYnGLAOBKpY8IvKNqVcnCAlWrwXI5+L29kPSmheGn++P5AmZpdim9fx9eTw8A3GCx+NJfn/HACF0gPwTwqtvaQrqyAnZ0yM/nUzj3lszu0vO+ULXamy4tycvliNbWW3b9+tWD3bPBbgZATilJzibz87JsFtbdTVYqSOfmlMzOounaNcLsc5uefuXfeh7h3tcCXkimp6HFRYAE6nWcuHwZ9LxVRlHfcaMFNzm56UZHVQFUAeSuXJELgrmjNA07VBD4INeUJLl6uSxtb5OnTsHr7ZV35kxNUr/F8VojrTUEAt+pWs3Vbt6Ue/iQ/siImsbGwJYWpmtrzSQXXaHgPxLogiCnQmEZu7vP1G7fhpKEfl+fvK6uVM49a9nsXba1QdvbGZLfHAl0QdBE8p7b3OyvzcxAe3vwBwbkDw0Rzr1ocfytpIvW0rIFM6BeH3OFwleHAmm27jY2OuvlsgTAy+Xk9/dTafo6o2gKACyKKpJ6mMksKUlAcsIFwdv/MMUFQQfJn9zGRq52586fLjU3o3liAkjTdxlF7/9nx4VCO5zbVKUCZjL3BDxtUbQLAEZyxu3s5Or7MAE4ceEClCSLkD5oGI0o2pLZVWYyCYAhAlMHR37Cra5q3134+bysvb0OYIRx7A7Lm0XRLQBnASQAOv9+l1Tyh4fhnT8Pnjwpf3CQcu4Ni+OdRwWfUbQm6T0A51wQyAVBO/eD3AdyAc41yaxsUXTpWNe6UPgewFOS2g0AGMe/ShqFWQxpHMev5yV1Wxzv/AEP8YwFMPd9VwAAAABJRU5ErkJggg==">&nbsp;' + message + '</h3>'

        if type == 'warning':
            #return '<h3><img src="config/images/symbol_failed.png">&nbsp;' + message + '</h3>'
            return '<h3><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAAZiS0dEAAAAAAAA+UO7fwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAzBJREFUOMuVlE9oXGUUxc+57zWxTFKSScoQSEOaSW0CMbpIEdsmVStN4A2IIhp0IQgu3bqdN5u6EEFciUsX7oSi78WAtYkWpmAWFlNNYoLpIlgX+QMNyUxm3vuOC6NEnaTmLj84v+/eew6XAKBSaRjAcwJ+h/SDheEvOGapVOoTMEkXhq+R/Ex7e0bfBzwPAJ5ksfjj/wSNA/hEUhvIVqpUmnfr60PJygpgBi+fl9fZWZVzL1sYTh8KCsNBkDcAPA4JIkEga5I+ttOnYdksSCJdXqZ78OAxmn3pSqWLjWAuDEMBP6taPadaDSB/IzDOYnGLAOBKpY8IvKNqVcnCAlWrwXI5+L29kPSmheGn++P5AmZpdim9fx9eTw8A3GCx+NJfn/HACF0gPwTwqtvaQrqyAnZ0yM/nUzj3lszu0vO+ULXamy4tycvliNbWW3b9+tWD3bPBbgZATilJzibz87JsFtbdTVYqSOfmlMzOounaNcLsc5uefuXfeh7h3tcCXkimp6HFRYAE6nWcuHwZ9LxVRlHfcaMFNzm56UZHVQFUAeSuXJELgrmjNA07VBD4INeUJLl6uSxtb5OnTsHr7ZV35kxNUr/F8VojrTUEAt+pWs3Vbt6Ue/iQ/siImsbGwJYWpmtrzSQXXaHgPxLogiCnQmEZu7vP1G7fhpKEfl+fvK6uVM49a9nsXba1QdvbGZLfHAl0QdBE8p7b3OyvzcxAe3vwBwbkDw0Rzr1ocfytpIvW0rIFM6BeH3OFwleHAmm27jY2OuvlsgTAy+Xk9/dTafo6o2gKACyKKpJ6mMksKUlAcsIFwdv/MMUFQQfJn9zGRq52586fLjU3o3liAkjTdxlF7/9nx4VCO5zbVKUCZjL3BDxtUbQLAEZyxu3s5Or7MAE4ceEClCSLkD5oGI0o2pLZVWYyCYAhAlMHR37Cra5q3134+bysvb0OYIRx7A7Lm0XRLQBnASQAOv9+l1Tyh4fhnT8Pnjwpf3CQcu4Ni+OdRwWfUbQm6T0A51wQyAVBO/eD3AdyAc41yaxsUXTpWNe6UPgewFOS2g0AGMe/ShqFWQxpHMev5yV1Wxzv/AEP8YwFMPd9VwAAAABJRU5ErkJggg==">&nbsp;' + message + '</h3>'

        if type == 'ok':
            #return '<h3><img src="config/images/symbol_ok.png">&nbsp;' + message + '</h3>'
            return '<h3><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAAZiS0dEAAAAAAAA+UO7fwAAAAlwSFlzAAALEwAACxMBAJqcGAAAA7JJREFUOMutlGtMXEUYht85Z88eFqx0WaBQKazGS9RAwECLIJfWoDEkBpX+wFJTL7VAg4SC0hajP9BAjS7RLgUCCQtF0Ai1tUYSbdBaWBZqiZE0aGlgWRZx265blr1y5pzxBwajYFNb59/MZJ55JvN9L3Cb4+y1ARgm316dE/xP41Nb+x2MMJG7HUjnTBMA4Li1+TGP5Pk8IAVqb8nw5Hw3LjjHUJf0EUzTxhrKpDrGmEAIoauG3dbm1QMfz7beEFhwVzHSdBlq08zRfklZbgAgcISf0/CaTA4AuqzHUKwvRb/dJPba2qN3JexDr619DajPblp5qtUY4wxe/dKzvPSszCg4wo+LvJizS18yxgHAC/oy9NjaEtxB9ycB6vsQANwB599gx63NKIzbgxPznbGM4eSVwG95MmSoOXFSw4c8V6wvmQGAPw2bsoPU/62XegsUpuR3zzRn77u/ZtXo8Gg1dutLwRjjloKe7+fctm3X/W4QRbUUHhKeW5TwqnXl0mMgXTNNr0iK1Da7ZMXoFTN7PO4JEh2y6UR2Qu7Oe/hE5flvCtGT14dDlqowyqQRh8+ROLX4C1Ijty4zRlKNOa0Tn9k7sDPuRQAAp0DJ8khLmHRdBAHBj1cvgDKaN3B5YAcA9OT1oWr4NY2kSB0OnyNx/Np5JOseoaJKLDXmtE68bq5YhQEA6bW1hQVooH/eO/fkiGOIUUVGlLCZbNHc/YVP8hWKoVpJCXrfdAV/rzu7MIis2FymE3WdPFR7j2Q00n9+HFcUv9er4viquLAt0w+EP0jG5scx8qsFzoDzaYET0mjAnR6g/jqz4xxSdKnYKGy0awRN+ZGMRlry3Z41lcB1WZuwW192UUXUb4Uo4b74UD1Z8C0wu3cOMuQWWZH7Ly3+jA3CnYgJjYGKUz1Tl/ae56ClEi25pjVAAgAuNgUtuQ8V50rekRmt/WruNPNTPzJisojCZEw4f2LZm7cTrVp7+INMY321uRzvZxxdt+h5AOCeEjDUPoLRjh8GM19+NCFKE5UytXgJ0+7LZNZjZUkRKSR+Q/wZgRcqXNvt9FT+mX/tIg4A6tMNeGOkYmWBkKrIkCjztuh0QhllEWIkeUj78HUwvNuQ3ugvuLfohm25bjgcGN6fxnOq04PzX29KikhmWlFnMmQaX7qZ4Fg3vgyZTeclZbk2J3aHHK7WunhwDQBQY6n879F0yHLgL9Oh/YbK4bIWAMg/lYNbMqxPN6DaXL6yyXEHBU5dDQDJMVtvCvgHbhmVjRcx0X0AAAAASUVORK5CYII=">&nbsp;' + message + '</h3>'

        return '<h3>' + message + '</h3>'

    def configGetInt(self, section, valuename, default):
        # read a setting from config service and make sure its an int
        try:
            ret = int(self.configService.getDefault(section, valuename, str(default)))
        except:
            ret = default
            self.printError('Error while reading setting ' + valuename + ' from section ' + section + ':\nExpecting integer.\n')
        return ret

    def configGetBool(self, section, valuename, default):
        # read a setting from config service and make sure its a bool
        setting = self.configService.getDefault(section, valuename, default)
        if (setting == '1') or (setting.lower() == 'true'):
            return True
        elif (setting == '0') or (setting.lower() == 'false'):
            return False
        else:
            self.printError('Error while reading setting ' + valuename + ' from section ' + section + ':\nExpecting "True", "1", "False" or "0".\n')
            # default
            return default

    def prepareInput(self, section, prefix):
        # prepares the retrieval of some input as defined in the config file
        # in the given section with the given prefix:
        # expected settings in the section:
        # prefixuse = file | download | command | none
        # prefixfile = /path/to/file
        # prefixdownload = wget|html||http://server/file.html
        # prefixcommand = ['command', 'parameters']

        # check if initialized
        if not hasattr(self, 'inputRequests'):
            self.inputRequests = {}

        # read additional config settings
        req = {}
        req['file'] = self.configService.getDefault(section, prefix + 'file', '')
        req['download'] = self.configService.getDefault(section, prefix + 'download', '')
        req['command'] = self.configService.getDefault(section, prefix + 'command', '')
        req['use'] = self.configService.getDefault(section, prefix + 'use', 'file')
        req['prefix'] = prefix
        req['section'] = section
        
        if req['use'] not in ('download', 'file', 'command', 'none'):
            req['use'] = 'none'
            self.printInputError(section, prefix, '"' + prefix + 'use" must be "file", "download", "command" or "none".\nUsing default value "none".')
        
        # if download required, pass it to download service
        if req['use'] == 'download':
            # therefore, we create a unique download_tag
            req['download_tag'] = self.getName() + '_' + section + '_' + prefix
            self.downloadRequest[req['download_tag']] = req['download']
            
        #  ... add request to request list
        self.inputRequests[section + '/' + prefix] = req


    def fetchInput(self, section, prefix, registerSource = True):
        # fetches some input prepared with prepareinput
        # fetching can only be done in run() when it has been prepared in __init__()
        # result is a line array or an empty array in case of an error
        # if registerSource is True, a reference to the source will be added
        # to the source parameter of the module

        if (section + '/' + prefix) in self.inputRequests.keys():
            req = self.inputRequests[section + '/' + prefix]
        else:
            self.printInputError(section, prefix, 'fetchInput was called for input that was not prepared.')
            return []

       
        if req['use'] == 'none':
             # "none" is the easiest type
             return ['']
        
        elif req['use'] == 'file':
            # get input from file
            if registerSource:
                self.configService.addToParameter('setup', 'source', req['file'])

            # check if specified file exists
            if os.path.exists(req['file']):
                try:
                    # open logfile and read lines
                    file = open(req['file'], 'r')
                    lines = (''.join(file.readlines())).split('\n')
                    file.close()
                    # return line array
                    return lines

                except Exception as e:
                    self.printInputError(section, prefix, 'Unable to read from file "%s":\n%s\n' % (req['file'], e.__str__()))
                    return []
            else:
                # show error
                self.printInputError(section, prefix, 'The specified file "%s" does not exist.\n' % req['file'])
                return []

        elif req['use'] == 'download':
            # get input from url / download
            if registerSource:
                try:
                    self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(req['download_tag'])))
                except:
                    pass
                
            try:
                dl_error, sourceFile = self.downloadService.getFile(self.getDownloadRequest(req['download_tag']))
            except Exception as e:
                dl_error = e.__str__()
                sourceFile = ''

            # check if downloaded file exists
            if (sourceFile != '') and os.path.exists(sourceFile):
                try:
                    # open logfile and read lines
                    file = open(sourceFile, 'r')
                    lines = (''.join(file.readlines())).split('\n')
                    file.close()
                    # return line array
                    return lines

                except Exception as e:
                    self.printInputError(section, prefix, 'Unable to read from downloaded logfile "%s":\n%s\n' % (sourceFile, e.__str__()))
                    return []

            else:
                # show error
                self.printInputError(section, prefix, 'Download of "%s" was not successful.\n%s' % (req['download'], dl_error))
                return []

        elif req['use'] == 'command':
            # get input from command output
            
            try:
                # interprete the given logcommand as python array
                req['command'] = eval(req['command'])

                if registerSource:
                    self.configService.addToParameter('setup', 'source', ' '.join(req['command']))

                # execute given command
                outp = subprocess.Popen(req['command'], stdout=subprocess.PIPE).stdout.read()

                # split at line end
                lines = outp.split('\n')
                return lines

            except:
                self.printInputError(section, prefix, 'The given command is not avalid python array.\n')
                return []

    def fetchDownload(self, download_tag, registerSource = False):
        # get input from url / download
        if registerSource:
            self.configService.addToParameter('setup', 'source', self.downloadService.getUrlAsLink(self.getDownloadRequest(download_tag)))

        try:
            dl_error, sourceFile = self.downloadService.getFile(self.getDownloadRequest(download_tag))
        except Exception as e:
            dl_error = e.__str__()
            sourceFile = ''

        # check if downloaded file exists
        if (sourceFile != '') and os.path.exists(sourceFile):
            try:
                # open logfile and read lines
                file = open(sourceFile, 'r')
                lines = (''.join(file.readlines())).split('\n')
                file.close()
                # return line array
                return lines

            except Exception as e:
                self.printError('Unable to read from downloaded file "%s":\n%s\n' % (sourceFile, e.__str__()))
                return []

        else:
            # show error
            self.printError('Download of "%s" was not successful.\n%s' % (self.downloadService.getUrl(self.getDownloadRequest(download_tag)), dl_error))
            return []
    
    def readTableConfig(self, section):
        # read list of columns in the given config section
        # also, read more display
        columns = []
        columncount = 0
        
        while True:
            # go on reading until column does not exist
            column = self.configService.getDefault(section, 'column%i' % (columncount+1), '')

            # last column? -> exit loop
            if column == '':
                break

            columncount += 1
            
            # a column consists of four parts separated by a ';'
            # title;display text;hover text;link url
            # several tokens such as %ip% can be used

            column = column.split(';', 3)
            if len(column) <= 4:

                if len(column) < 4:
                    column.extend(['']*(4-len(column)))

                # strip tabs/spaces
                for i in range(0, len(column)):
                    column[i] = column[i].strip()

                # column title may contain %nowrap% which sets a flag
                if column[0].find('%nowrap%') >= 0:
                    # remove %nowrap%
                    column[0] = column[0].replace('%nowrap%', '')
                    # set nowrap flag
                    column.append(1)
                else:
                    # unset nowrap flag
                    column.append(0)

                columns.append(column)

            else:
                self.printError('Error while reading display configuration in section "' + section + '":\nExpecting the character ";" in column %i at least four times. This column will be ignored.\n' % columncount)
            

        if columncount == 0:
            self.printError('Error while reading display configuration in section "' + section + '":\nNo column definitions found.')
        
        # read sort order (including tokens)
        sorting = self.configService.getDefault('display', 'sort', '')

        return (columns, sorting)

    def sortTablePHP(self, display, phpvar_table):
        # return PHP code for sorting a table with the layout given in display
        # the phpvar_table variable will be sorted

        # display is a return value from readTable config:
        sorting = display[1]
        sorting = sorting.split(';')
        
        function_code = ""
        for entry in sorting:
            asc = 1
            if entry.lower().endswith('(asc)'):
                entry = entry[0:-5]
            if entry.lower().endswith('(desc)'):
                entry = entry[0:-6]
                asc = -1

            function_code += """
            if(array_key_exists("""+self.toPHPStr(entry)+""", $a))
            {
                $c = strnatcasecmp($a["""+self.toPHPStr(entry)+"""], $b["""+self.toPHPStr(entry)+"""]);
                if($c!=0) return ($c*""" + str(asc) + """);
            }
            """

        function_code += """
            return 0;
        """

        ret = """
        uasort(""" + phpvar_table + """, create_function('$a, $b', """ + self.toPHPStr(function_code) + """));
        """
        return ret

    def beginTablePHP(self, display, phpvar_to):
        # return PHP code for beginning a table with the layout given in display
        # write the table to the PHP variable phpvar_to

        # display is a return value from readTable config:
        columns = display[0]
        
        ret = """
        """ + phpvar_to + """ = '
<table class="TableData">
    <tr>
        """

        # collect all table column headers
        for col in columns:
            ret +=  '<th>' + col[0] + '</th>'

        # go through all hosts and open a row for each
        ret += """
    </tr>
';
"""
        return ret

    def addRowPHP(self, display, phpvar_class, phpvar_from, phpvar_to):
        # return PHP code for adding a tablerow with the layout given in display
        # write the table to the PHP variable phpvar_to
        # phpvar_from contains a PHP var which contains info to be displayed
        # in the row (associative array), phpvar_class specifies the row class

        # display is a return value from readTable config:
        columns = display[0]
        
        # add row beginning
        ret = """
        """ + phpvar_to + """ .= '    <tr class=\"'.""" + phpvar_class + """.'\">';

        """
        
        # add all <td>s for the current row
        for col in columns:
            ret += """

        // start with config definition
        $_stxt = """ + self.toPHPStr(col[1]) + """;
        $_stit = """ + self.toPHPStr(col[2]) + """;
        $_surl = """ + self.toPHPStr(col[3]) + """;
        
        // get info for current <td>
        foreach (""" + phpvar_from + """ as $_t => $_value)
        {
            // if a used field is empty, empty whole string
            if($_value == '')
            {
                if(strpos($_stxt, '%'.$_t.'%') != FALSE)
                    $_stxt = '';
                if(strpos($_stit, '%'.$_t.'%') != FALSE)
                    $_stit = '';
                if(strpos($_surl, '%'.$_t.'%') != FALSE)
                    $_surl = '';
            }
            else
            {
                // fill in found information
                $_stxt = str_replace('%'.$_t.'%', $_value, $_stxt);
                $_stit = str_replace('%'.$_t.'%', $_value, $_stit);
                $_surl = str_replace('%'.$_t.'%', $_value, $_surl);
            }

        }
        $_stxt = trim($_stxt);
        $_stit = trim($_stit);
        $_surl = trim($_surl);

        // replace unwanted characters (")
        if($_stit != '')
            $_stit = ' title="'.str_replace('"', "'", $_stit).'"';

        if($_surl != '')
            $_surl = ' href="'.str_replace('"', "'", $_surl).'"';

        // ... and add <td> to row
        // depending on row setting, set nowrap flag
        """ + phpvar_to + """ .= '<td""" + (' nowrap="1"' if col[4]==1 else '') + """><a'.$_stit.$_surl.'>'.$_stxt.'</a></td>';
"""
        # close current row
        ret += """

        """ + phpvar_to + """ .= '</tr>
';"""
        return ret
    

    def endTablePHP(self, display, phpvar_to):
        # return PHP code for ending a table with the layout given in display
        # write the table to the PHP variable phpvar_to
        # display is a return value from readTable config (not required yet)
        
        ret = """
        """ + phpvar_to + """ .= '
</table>
';"""
        return ret


    def toPHPStr(self, phpstr):
        # helper function which quotes a given string, so it can be used in
        # PHP output
        return "'" + phpstr.replace('\\', '\\\\').replace('\'', '\\\'') + "'"

    def packArray(self, array):
        # pack an associative array of associative string arrays into a single
        # string, so that it can be easily stored in the db and unpacked by PHP
        
        # sort the hosts according to self.sortorder (tokenized)
        #self.sortedhosts = sorted(self.allhosts, key= (lambda h: (self.replacetokens(self.sortorder, self.allhosts[h]))) )
        
        packed = ''
        keys = []
        
        for e in array.keys():
            entry = array[e]
            
            # if first entry
            if len(keys) == 0:
                # fill field names that are saved
                for key in entry:
                    if isinstance(entry[key], str):
                        keys.append(key)
                        packed += key + '\n'
                # field name list is terminated with double \n
                packed += '\n'

            for key in keys:
                packed += entry[key].replace('\\','\\\\').replace('\n','\\n') + '\n'

        return packed

    def unpackArrayPHP(self, phpvar_from, phpvar_to, phpvar_keys = '$_keys'):
        # return the php code to unpack an array of associative arrays
        # previously packed by packArray.
        # the string in the PHP variable phpvar_from is unpacked to phpvar_to
        # the keys are stored in phpvar_keys

        return """
        list($_keystring, $_entrystring) = explode('

', """ + phpvar_from + """, 2);
        """ + phpvar_keys + """ = explode('
', $_keystring);
        $_entryvalues = explode('
', $_entrystring);

        """ + phpvar_to + """ = array();
        $_keycounter = 0;
        $_currententry = array();

        foreach ($_entryvalues as $_value)
        {
            $_currententry[""" + phpvar_keys + """[$_keycounter]] = $_value;

            $_keycounter += 1;
            if($_keycounter >= count(""" + phpvar_keys + """))
            {
                $_keycounter = 0;
                """ + phpvar_to + """[] = $_currententry;
            }
        }
        """

    def showDivDropDownPHP(self, divs):
        # returns the php code for a dropdown menu that allows the user to
        # switch between different divs
        # divs has to be an array of 3tuples (name, phpvar_description, phpvar_content)

        ret = """
        print('
Show <select onchange="javascript: """

        for div in divs:
            ret += "document.getElementById(\\\''." + self.toPHPStr(div[0]) + ".'\\\').style.display=\\\'none\\\'; "

        ret += """document.getElementById(this.value).style.display=\\\'block\\\';">"""

        for div in divs:
            ret += """
    <option value=\"'.""" + self.toPHPStr(div[0]) + """.'\">'.""" + div[1] + """.'</option>"""

        ret += """
</select><p>
');"""

        first = True
        for div in divs:
            ret += """
            print('<div id=\"'.""" + self.toPHPStr(div[0]) + """.'\" style="display: """ + ('block' if first else 'none') + """\">
'.(""" + div[2] + """).'
</div>
');"""
            first = False

        return ret

    def rawDataPHP(self, phpvar_from, phpvar_to, phpvar_keys = '$_keys', name_key = 'name_short'):

        return """
        """ + phpvar_to + """ = '
<pre>
';
        
        foreach (""" + phpvar_from + """ as $_entry)
        {
            """ + phpvar_to + """ .= '
<b>'.$_entry['""" + name_key + """'].'</b>
';
            foreach ($_entry as $_key => $_value)
            {
                """ + phpvar_to + """ .= $_key.':'.str_repeat(' ',24-strlen($_key)).$_value.'
';
            }
        }
        """ + phpvar_to + """ .= '</pre>
';      """


class SearchElement(HTMLParser):
    def __init__(self, s, ttag, tclass, tid):
        # parse given string s , searching for html tag ttag with class
        # tclass and id tid. If any of the arguments are empty, these criteria
        # will be skipped.
        # the content of all found elements will be stored in the array results

        HTMLParser.__init__(self)
        self.tstart = 0
        self.tend = 0
        self.ttag = ttag
        self.tclass = tclass
        self.tid = tid
        self.foundTag = ''
        self.tagDepth = 0
        self.tstring = s

        # results will be stored here
        self.results = []

        self.feed(s)
        self.close()

    def handle_starttag(self, tag, attributes):

        # if already found beginning of this tag
        if (self.foundTag != '') and (tag == self.foundTag):
            if(tag == 'p'):
                # p-tags are often not closed. next p tag closes the one before
                self.handle_endtag(tag)
            else:
                # .. remember depth
                self.tagDepth += 1

        if self.foundTag != '':
            return

        # search for correct tag
        if (tag != self.ttag) and (self.ttag != ''):
            return
        
        # search for correct class
        if self.tclass != '':
            for name, value in attributes:
                if name == 'class' and value == self.tclass:
                    break
            else:
                return

        # search for correct id
        if self.tid != '':
            for name, value in attributes:
                if name == 'id' and value == self.tid:
                    break
            else:
                return

        self.tstart = self.getpos()[1] + len(self.get_starttag_text())
        self.foundTag = tag
        self.tagDepth = 0

    def handle_endtag(self, tag):
        # if already found beginning of this tag
        if (self.foundTag != '') and (tag == self.foundTag):
            # look if we already have correct depth
            if self.tagDepth != 0:
                self.tagDepth -= 1
            else:
                # correct depth
                self.tend = self.getpos()[1]
                # add result and reset
                self.results.append(self.tstring[self.tstart:self.tend])
                self.foundTag = ''
                self.tagDepth = 0
            


class TableParser(HTMLParser):

    def __init__(self, s, tclass):
        # parse given string s, seaching for first table with class tclass
        # all rows and within these all columns will be saved into the array
        # table. This will be done recursively with all subtables.
        # if a table only contains one row, indexing for rows will be skipped
        # if a row only contains one column, indexing for columns will be skipped
        # if no table is found, the full input is returned

        # if no tclass is given, the first table found will be used

        HTMLParser.__init__(self)
        self.tstart = 0
        self.tend = 0
        self.foundTable = False
        self.TableDepth = 0

        self.tclass = tclass
        self.tstring = s
        self.table = []
        self.trow = []
        self.tdstart = 0
        self.tdend = 0

        self.feed(s)

        # check if given html string is complete
        self.incomplete = False
        try:
            self.close()
        except:
            self.incomplete = True
        
        if len(self.table) == 0:
            if self.foundTable:
                # empty table found
                self.table = ''
            else:
                # if no table found, then return full input string
                self.table = self.tstring

        elif len(self.table) == 1:
            # if only one row, then skip indexing rows
            self.table = self.table[0]


    def handle_starttag(self, tag, attributes):

        if tag == 'table':

            if self.foundTable:
                if self.TableDepth >= 0:
                    self.TableDepth += 1
                else:
                    self.TableDepth = -1

            else:
                # we search for table of class tclass
                if self.tclass != '':
                    for name, value in attributes:
                        if name == 'class' and value == self.tclass:
                            self.foundTable = True
                            self.tstart = self.getpos()[1] + len(self.get_starttag_text())
                else:
                    self.foundTable = True

        elif tag == 'tr':
            if self.foundTable == True and self.TableDepth == 0:
                self.trow = []

        elif tag == 'td':
            if self.foundTable == True and self.TableDepth == 0:
                self.tdstart = self.getpos()[1] + len(self.get_starttag_text())


    def handle_endtag(self, tag):

        if tag == 'table':

            if self.foundTable:
                if self.TableDepth >= 0:
                    self.TableDepth -= 1

                    if self.TableDepth == -1:
                        self.tend = self.getpos()[1]
                        self.tstring[self.tstart:self.tend]

                else:
                    self.TableDepth = -1


        elif tag == 'tr':
            if self.foundTable == True and self.TableDepth == 0:
                # it tr did not contain any td, it will not be added
                if len(self.trow) == 1:
                    # if tr does only contain one td, skip indexing tds
                    self.table.append(self.trow[0])
                elif len(self.trow) > 1:
                    self.table.append(self.trow)

        elif tag == 'td':
            if self.foundTable == True and self.TableDepth == 0:
                self.tdend = self.getpos()[1]
                td = self.tstring[self.tdstart:self.tdend]
                td = TableParser(td, '').table
                self.trow.append(td)



class ContentParser(HTMLParser):

    def __init__(self, s):
        # parse given string s, adding all content into self.content, adding all
        # hrefs to self.url and adding all img.srcs to self.img and all alts to
        # self.alt

        HTMLParser.__init__(self)
        self.cstring = s

        self.content = ''
        self.url = []
        self.img = []
        self.alt = []

        self.feed(s)
        self.close()

    def handle_starttag(self, tag, attributes):

        for name, value in attributes:
            if name == 'href':
                self.url.append(value)
            elif tag == 'img' and name == 'src':
                self.img.append(value)
            elif tag == 'alt':
                self.alt.append(value)

    def handle_data(self, data):
        self.content += data


# a helper class for downloading with elinks
# this has the advantage that elinks is capable of HTTP 1.1, whereas wget only
# supports HTTP 1.0 which is not sufficient for some purposes (ilo, ...)
# BUT THIS REQUIRES ELINKS TO BE INSTALLED!
class elinksDownload(Thread):
    def __init__ (self, url, parameters = []):
        Thread.__init__(self)

        # save our parameters and url
        self.url = url
        self.parameters = parameters
        self.status_short = 'fail'
        self.status_long = 'download not started'
        self.content = ''
        # and start the asynchronous request
        self.start()

    def run(self):

        # start the elinks request
        try:
            # reset output values before
            self.status_short = 'fail'
            self.status_long = 'download not finished'
            self.content = ''

            # issue double ping
            proc = subprocess.Popen(['elinks', '-source', '1'] + self.parameters + [self.url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        except Exception as e:
            self.status_long = 'elinks: ' + e.__str__()
            return

        # fetch output of process
        proc_out = proc.stdout.read().strip()
        proc_err = proc.stderr.read().strip()

        if proc_err.strip() == '':
            self.content = proc_out
            self.status_short = 'ok'
            self.status_long = 'ok'
        else:
            self.content = proc_out
            self.status_short = 'fail'
            self.status_long = 'elinks: ' + proc_err
