from PhpPlotDashboard import *

class phpplotdashboard_jobs_pend_run(PhpPlotDashboard):

    def __init__(self,module_options):

        PhpPlotDashboard.__init__(self,module_options)

        # Also load and show the pie chart
        self.downloadRequest['plot2'] = 'wget|'+self.makeUrl({'type': 'r'})

