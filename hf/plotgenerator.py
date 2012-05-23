
import hf
import cherrypy as cp
import json, StringIO, traceback, logging
import numpy as np
import timeit
from sqlalchemy.sql import select

def init():
    """ Configure matplotlib backends by hf-configuration. Call before any plot-commands """
    import matplotlib
    matplotlib.use("cairo.png")
    import matplotlib.pyplot as plt
    plt.hold(False)

def timeseriesPlot(**kwargs):
    """
    Supported arguments:
     curve_XXX: colon-separated curve info: (module_instance,[subtable],column,title)
     legend: (true, false / 1, 0) Show legend in image
     title: (string) Display a title above plot
     ylabel: self-explanatory
     timerange: 
    """
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__+".timeseriesPlot")

    errors = []
    try:
        curve_list = []
        title = ""
        legend = False
        ylabel = ""
        timerange = []
        for key, value in kwargs.iteritems():
            if key.lower().startswith(u"curve_"):
                try:
                    curve_info = value.split(",")
                    if len(curve_info) < 4:
                        raise Exception("Insufficient number of arguments for plot curve")
                    module,table_name,col_name = curve_info[:3]
                    title = ",".join(curve_info[3:])
                    if len(title) == 0:
                        title = module + " " + col_name
                    
                    if not hf.module.config.has_section(module):
                        raise Exception("No such module")
                    module_class = hf.module.getModuleClass(hf.module.config.get(module, "module"))
                    try:
                        table = module_class.module_table if len(table_name) == 0 else module_cass.subtables[table_name]
                    except IndexError, e:
                        raise Exception("No such subtable")
                    col = getattr(table.c, col_name)
                    data = [p[0] for p in select([col]).execute().fetchall()]
                    curve_list.append((title, data))
                except Exception, e:
                    logger.warning("Generating plot image:\n"+traceback.format_exc())
                    errors.append("Data '%s': %s" % (key, str(e)))
            elif key.lower() == u"legend":
                legend = (value.lower() == "true" or value == "1")
            elif key.lower() == u"ylabel":
                ylabel = value
            elif key.lower() == u"title":
                title = value
        
        for curve in curve_list:
            plt.plot(curve[1])
        plt.xlabel("Time")
        plt.title(title)
        plt.ylabel(ylabel)
    except Exception, e:
        logger.error("Plotting Failed: %s" % str(e))
        logger.debug(traceback.format_exc())
        errors.append("Plotting Failed: %s" % str(e))
    
    img_data = StringIO.StringIO()
    try:
        plt.savefig(img_data)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()