import os
import subprocess
from HTMLParser import HTMLParser


# a class that provides some simple methods for input gathering
class InputService(object):

    def __init__(self, parent):
        # single parameter is the containing module object
        # most importantly it has to have an instance of configService accessable
        self.parent = parent
        self.parentname = self.parent.__class__.__name__

        self.inputRequests = {}

    def printMessage(self, message):
        # print a message to stdout
        print self.parentname + ': ' + message.replace('\n', '\n\t')

    def printError(self, message):
        # print an error message to std out and to the web site
        self.printMessage(message)
        self.parent.error_message += message

    def printInputError(self, section, prefix, message):
        self.printError('Error while reading settings "' + prefix + '..." in section "' + section + '":\n' + message)

    def prepareInput(self, section, prefix):
        # prepares the retrieval of some input as defined in the config file
        # in the given section with the given prefix:
        # expected settings in the section:
        # prefixuse = file|download|command|none
        # prefixfile = /path/to/file
        # prefixdownload = wget|html||http://server/file.html
        # prefixcommand = ['command', 'parameters']

        # read additional config settings
        req = {}
        req['file'] = self.parent.configService.getDefault(section, prefix + 'file', '')
        req['download'] = self.parent.configService.getDefault(section, prefix + 'download', '')
        req['command'] = self.parent.configService.getDefault(section, prefix + 'command', '')
        req['use'] = self.parent.configService.getDefault(section, prefix + 'use', 'file')
        req['prefix'] = prefix
        req['section'] = section
        
        if req['use'] not in ('download', 'file', 'command', 'none'):
            req['use'] = 'none'
            self.printInputError(section, prefix, '"' + prefix + 'use" must be "file", "download", "command" or "none".\nUsing default value "none".')
        
        # if download required, pass it to download service
        if req['use'] == 'download':
            req['download_tag'] = self.parent.__class__.__name__ + '_' + section + '_' + prefix
            self.parent.downloadRequest[req['download_tag']] = req['download']

        # add request to request list
        self.inputRequests[section + '/' + prefix] = req


    def fetchInput(self, section, prefix, registerSource = True):
        # fetches some input prepared with prepareinput
        # fetching can only be done in run() when it has been prepared in __init__()
        # result is a line array or an empty array in case of an error

        if (section + '/' + prefix) in self.inputRequests.keys():
            req = self.inputRequests[section + '/' + prefix]
        else:
            self.printInputError(section, prefix, 'fetchInput was called for input that was not prepared')
            return []

       
        if req['use'] == 'none':
             # "none" is the easiest type
             return ['']
        
        elif req['use'] == 'file':
            # get input from file
            if registerSource:
                self.parent.configService.addToParameter('setup', 'source', req['file'])

            # check if specified file exists
            if os.path.exists(req['file']):
                try:
                    # open logfile and read lines
                    file = open(req['file'], 'r')
                    lines = file.readlines()
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
                    self.parent.configService.addToParameter('setup', 'source', self.parent.downloadService.getUrlAsLink(self.parent.getDownloadRequest(req['download_tag'])))
                except:
                    dummy = 1
                
            try:
                dl_error, sourceFile = self.parent.downloadService.getFile(self.parent.getDownloadRequest(req['download_tag']))
            except Exception as e:
                dl_error = e.__str__()
                sourceFile = ''

            # check if downloaded file exists
            if os.path.exists(sourceFile):
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
                    self.parent.configService.addToParameter('setup', 'source', ' '.join(req['command']))

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
            self.parent.configService.addToParameter('setup', 'source', self.parent.downloadService.getUrlAsLink(self.parent.getDownloadRequest(download_tag)))

        try:
            dl_error, sourceFile = self.parent.downloadService.getFile(self.parent.getDownloadRequest(download_tag))
        except Exception as e:
            dl_error = e.__str__()
            sourceFile = ''

        # check if downloaded file exists
        if os.path.exists(sourceFile):
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
            self.printError('Download of "%s" was not successful.\n%s' % (self.parent.downloadService.getUrl(self.parent.getDownloadRequest(download_tag)), dl_error))
            return []


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
