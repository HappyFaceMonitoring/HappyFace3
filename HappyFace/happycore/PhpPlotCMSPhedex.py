from Plot import *
from PhpDownload import *


class PhpPlotCMSPhedex(Plot,PhpDownload):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
        PhpDownload.__init__(self)
        

        globalVars = {}
	globalVars['localsitename'] = self.configService.get('setup','localsitename')
        
        globalVars['plot_type'] = self.configService.get('setup','plot_type')
        globalVars['instance'] = self.configService.get('setup','instance')



        for phparg in self.phpArgs:
            for glob in globalVars:
                self.phpArgs[phparg] = self.phpArgs[phparg].replace('__'+glob+'__',globalVars[glob])
                

            

        # Create URL from base_url and phpArgs
        self.base_url = self.base_url+"/"+globalVars['plot_type']
        self.downloadRequest['plot'] = 'wget|'+self.makeUrl()

        mod_title = self.configService.get('setup', 'mod_title')

        
        if mod_title == 'auto':
            title = ""
            title += 'CMS PhEDEx summary: '

            if globalVars['plot_type'] == 'quality_all':
                title += 'Quality'
            elif globalVars['plot_type']  == 'quantity_rates':
                title += 'Rate'
            else:
                title += "-not defined("+globalVars['plot_type']+")-"

            
            title +=' of transfers from '
            if self.phpArgs['from_node'] == '.%2A':
                title +='All'
            else:
                title += self.phpArgs['from_node']

            title +=' to '
            if self.phpArgs['to_node'] == '.%2A':
                title +='All'
            else:
                title +=self.phpArgs['to_node']

            title +=' ('

            if globalVars['instance'] == 'Prod':
                title += 'Production'
            elif globalVars['instance'] == 'Debug':
                title += 'Debug'
            else:
                title +='not defined - '+globalVars['instance']
            title +=')'

            self.configService.set('setup', 'mod_title',title)
            
