from Plot import *

#############################################
# class to donwload plots (via WGET command)
#############################################
class CMSPhedexPlot(Plot):

    def __init__(self, category, timestamp, archive_dir):

        Plot.__init__(self, category, timestamp, archive_dir)
	
        # read class config file
	config = self.readConfigFile('./happycore/CMSPhedexPlot')
	self.site = config.get('setup','site')

	graph		= self.mod_config.get('setup','graph')
	direction	= self.mod_config.get('setup','direction')
	instance	= self.mod_config.get('setup','instance')

	url	= ""
	
	url 	+= 'http://cmsweb.cern.ch/phedex/graphs/' + graph + '?link=link&no_mss=true'

	if direction == "to":
	    url += '&to_node=' + self.site + '&from_node=.%2A'
	elif direction == "from":
	    url += '&to_node=.%2A&from_node=' + self.site

        url += '&conn=' + instance + '%2FWebSite&span=3600'
	
	self.url = url

        # create module title (if setting is 'auto')
        if self.mod_title == 'auto':
            
            title = ""
            title += 'CMS PhEDEx '

            if instance == 'Prod':
                title += 'Production '
            elif instance == 'Debug':
                title += 'Debug '

            if graph == 'quality_all':
                title += 'Transfer Quality '
            elif graph == 'quantity_rates':
                title += 'Transfer Rate '

            title += direction + ' '
            
            if self.site == '.%2A':
                title += 'all sites'
            else:
                title += self.site

            title += ' - 72 hours'

            self.mod_title = title
