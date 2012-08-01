
import hf
import cherrypy as cp
import json, StringIO, traceback, logging, datetime, time
import numpy as np
import timeit
from sqlalchemy.sql import select

def init():
    """ Configure matplotlib backends by hf-configuration. Call before any plot-commands """
    import matplotlib
    matplotlib.use(hf.config.get('plotgenerator', 'backend'))

def timeseriesPlot(**kwargs):
    """
    Supported arguments:
     curve_XXX: colon-separated curve info: (module_instance,[subtable],column,title)
     legend: (true, false / 1, 0) Show legend in image
     title: (string) Display a title above plot
     ylabel: self-explanatory
     timerange: Start date and end date: (Y-m-d_H:M,Y-m-d_H:M)
    """
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.dates import AutoDateFormatter, AutoDateLocator, date2num
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__+".timeseriesPlot")
    
    # generate plot
    fig = plt.figure()
    ax = Axes(fig, [.08, .15, .88, 0.78])
    fig.add_axes(ax)

    errors = []
    try:
        curve_list = []
        title = ""
        legend = False
        ylabel = ""
        timerange = None
        
        # extract timerange
        if 'timerange' in kwargs:
            timestamps = kwargs['timerange'].split(',')
            start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestamps[0], "%Y-%m-%d_%H:%M")))
            end = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestamps[1], "%Y-%m-%d_%H:%M"))+60)
            timerange = [start, end]
        
        # download data for curves        
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
                        table = module_class.module_table if len(table_name) == 0 else module_class.subtables[table_name]
                    except IndexError, e:
                        raise Exception("No such subtable")
                    col = getattr(table.c, col_name)
                    
                    hf_runs = hf.module.database.hf_runs
                    if len(table_name) == 0:
                        # query from module table
                        query = select([hf_runs.c.time, col], table.c.run_id==hf_runs.c.id)
                        if timerange is not None:
                            query = query.where(hf_runs.c.time >= timerange[0]).where(hf_runs.c.time < timerange[1])
                        data = [(date2num(p[0]),p[1]) for p in query.execute().fetchall()]
                    else:
                        # query from subtable
                        mod_table = module_class.module_table
                        query = select([hf_runs.c.time, mod_table.c.id, col], \
                            table.c.parent_id==mod_table.c.id and mod_table.c.run_id==hf_runs.c.id)
                        if timerange is not None:
                            query = query.where(hf_runs.c.time >= timerange[0]).where(hf_runs.c.time < timerange[1])
                        data = [(date2num(p[0]),p[2]) for p in query.execute().fetchall()]
                    
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
                
        # generate plot
        
        ax.set_ymargin(0.01)
        ax.set_autoscalex_on(True)
        
        plot_format_list = [
            'bo-', 'go-', 'ro-', 'co-', 'mo-', 'yo-', 'ko-', 'wo-', 
            'bo--', 'go--', 'ro--', 'co--', 'mo--', 'yo--', 'ko--', 'wo--', 
        ]
        
        '''locator = AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        formatter = AutoDateFormatter(AutoDateLocator())
        
        ax.xaxis.set_major_formatter(formatter)
        '''''''''
        fig.autofmt_xdate()
        
        for num,curve in enumerate(curve_list):
            options = {
                'fmt': plot_format_list[num%len(plot_format_list)],
                'label': curve[0],
            }
            ax.plot_date(*zip(*curve[1]), **options)
        ax.xaxis.get_major_formatter().scaled = {
            365.0  : '%Y',
            30.    : '%Y-%m',
            1.0    : '%Y-%m-%d',
            1./24. : '%H:%M %y-%m-%d',
        }
        if title in kwargs:
            ax.set_title(kwargs['title'])
        if 'legend' in kwargs:
            if kwargs['legend'].lower() in ('true', '1'):
                ax.legend(numpoints=1)
        ax.set_ylabel(ylabel)
    except Exception, e:
        logger.error("Plotting Failed: %s" % str(e))
        logger.debug(traceback.format_exc())
        errors.append("Plotting Failed: %s" % str(e))
    
    img_data = StringIO.StringIO()
    try:
        fig.savefig(img_data)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()