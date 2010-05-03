from Plot import *
import time

# Note we cannot derive from SinglePlot since it checks the download tag
# existence in its constructor already.
class PhpPlotDashboardJobSummary(Plot):

    def __init__(self,module_options):

        Plot.__init__(self,module_options)

	base_url = self.configService.get('setup', 'base_url')
	time_range = float(self.configService.get('setup', 'time_range'))
	site = self.configService.get('setup', 'site')
        sort_by = self.configService.getDefault( 'setup','sort_by','activity' )

        # Get current UTC time, query plot for last time_range hours up to now
	date1 = time.gmtime(time.time()-round(time_range*3600))
	date2 = time.gmtime(time.time())
	date1str = time.strftime('%Y-%m-%d %H:%M:%S', date1)
	date2str = time.strftime('%Y-%m-%d %H:%M:%S', date2)

	get_params = 'user=&site=' + site + '&ce=&submissiontool=&dataset=&application=&rb=&activity=&grid=&date1=' + date1str + '&date2=' + date2str + '&sortby=' + sort_by + '&nbars=&jobtype=&tier=&check=submitted'
	source_url = self.EscapeHTMLEntities(base_url + '/jobsummary#' + get_params)
	self.configService.addToParameter('setup', 'source', 'Generated from: <a href="' + source_url + '">' + source_url + '</a><br />')

	self.downloadRequest['plot'] = 'wget|html|--header="Accept: application/image-map"|' + base_url + '/jobsummary-plot-or-table?' + get_params + '|wget|png||<img\\s*src=\"(?P<url>\\S*)\" (\\s*\\S*=\"\\S*\"\\s*)*/>'

    def process(self):
        # Catch if the regex did not match: This happens if there is no
        # Dashboard data available.
        try:
            self.downloadService.checkDownload(self.downloadRequest['plot'])
        except DownloadTag.MatchFailedError, ex:
            raise Exception('No Dashboard Data available')

        return Plot.process(self)
