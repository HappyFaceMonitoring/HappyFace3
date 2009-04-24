from PhpPlot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class PhpPlotCMSPhedex(PhpPlot):

    def __init__(self, category, timestamp, archive_dir):

        PhpPlot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/PhpPlotCMSPhedex')
	self.base_url = config.get('setup','base_url')
        self.getPhpArgs(config)


        globalVars = {}
	globalVars['localsitename'] = config.get('setup','localsitename')
        


        globalVars['plot_type'] = self.mod_config.get('setup','plot_type')
        globalVars['instance'] = self.mod_config.get('setup','instance')


        # read module specific phpArgs from modul config file
        self.getPhpArgs(self.mod_config)

        for phparg in self.phpArgs:
            for glob in globalVars:
                self.phpArgs[phparg] = self.phpArgs[phparg].replace('__'+glob+'__',globalVars[glob])
                

            

        # Create URL from base_url and phpArgs
        self.base_url = self.base_url+"/"+globalVars['plot_type']
        self.makeUrl()

        if self.mod_title == 'auto':
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

            self.mod_title = title
