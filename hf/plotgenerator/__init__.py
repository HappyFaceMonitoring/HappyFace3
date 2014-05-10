import hf
import logging
from dispatcher import Dispatcher
from timeseries import timeseriesPlot, getTimeseriesUrl, getTimeseriesPlotConfig

logger = logging.getLogger(__name__)


def init():
    """ Configure matplotlib backends by hf-configuration. Call before any plot-commands """
    try:
        import matplotlib
        matplotlib.use(hf.config.get('plotgenerator', 'backend'))
    except Exception, e:
        logger.error("Cannot initialize matplotlib %s" % str(e))
