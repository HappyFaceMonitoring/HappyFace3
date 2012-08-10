
import hf
from dispatcher import Dispatcher
from timeseries import timeseriesPlot, getTimeseriesUrl

def init():
    """ Configure matplotlib backends by hf-configuration. Call before any plot-commands """
    import matplotlib
    matplotlib.use(hf.config.get('plotgenerator', 'backend'))
    