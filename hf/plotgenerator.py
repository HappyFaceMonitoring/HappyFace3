
import hf
import cherrypy as cp
import json, StringIO, traceback, logging, datetime, time
import numpy as np
import timeit
from sqlalchemy.sql import select, func

def init():
    """ Configure matplotlib backends by hf-configuration. Call before any plot-commands """
    import matplotlib
    matplotlib.use(hf.config.get('plotgenerator', 'backend'))
    
@hf.url.absoluteUrl
def getTimeseriesUrl():
    return "/plot/time/img"

def timeseriesPlot(**kwargs):
    """
    Supported arguments:
     curve_XXX: colon-separated curve info: (module_instance,[subtable],column,title)
     filter: include only rows where specified column in result set matches value, can be specified more than once: col,value
     filter_XXX: include only rows where specified column in result set matches value for curve XXX, can be specified more than once: col,value
     exclude: include only rows where specified column in result set matches value, can be specified more than once: col,value
     exclude_XXX: include only rows where specified column in result set matches value for curve XXX, can be specified more than once: col,value
     legend: Show legend in image
     title: (string) Display a title above plot
     ylabel: self-explanatory
     start_date: Start date (Y-m-d)
     end_date: End date (Y-m-d)
     start_time: Start time (H:M)
     end_date: End time (H:M)
     renormalize: (true, false / 1, 0) Scales all curves to a [0,1] interval
    """
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.dates import AutoDateFormatter, AutoDateLocator, date2num
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__+".timeseriesPlot")
    
    # generate plot
    fig = plt.figure()
    ax = Axes(fig, [.12, .15, .84, 0.78])
    fig.add_axes(ax)
    
    # extract constraints from kwargs dictionary
    constraint = {'filter': {None: []}, 'exclude':{None: []}}
    for t in constraint.iterkeys():
        for key, value in kwargs.iteritems():
            if key.startswith(t):
                if len(key) <= len(t)+1:
                    curve = None
                else:
                    curve = key[len(t)+1:]
                if type(value) is not list:
                    value = [value,]
                print value
                for constr in value:
                    if curve not in constraint[t]:
                        constraint[t][curve] = []
                    constraint[t][curve].append(constr.split(','))

    errors = []
    try:
        curve_list = []
        title = ""
        legend = False
        ylabel = ""
        timerange = None
        renormalize = False
        
        # extract timeranges
        now = datetime.datetime.now()
        end_date = kwargs['end_date'] if 'end_date' in kwargs else now.strftime('%Y-%m-%d')
        start_date = kwargs['start_date'] if 'start_date' in kwargs else end_date
        start_time = kwargs['start_time'] if 'start_time' in kwargs else "00:00"
        end_time = kwargs['end_time'] if 'end_time' in kwargs else now.strftime('%H:%M')
        start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start_date+'_'+start_time, "%Y-%m-%d_%H:%M")))
        end = datetime.datetime.fromtimestamp(time.mktime(time.strptime(end_date+'_'+end_time, "%Y-%m-%d_%H:%M"))+60)
        timerange = [start, end]
        
        if 'renormalize' in kwargs:
            if kwargs['renormalize'].lower() in ['true', '1']:
                renormalize = True
        
        # download data for curves        
        for key, value in kwargs.iteritems():
            if key.lower().startswith(u"curve_"):
                try:
                    curve_name = key[6:]
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
                    
                    # A helper method to create queries with all
                    # neccessary constraints applied.
                    def queryDatabase(query_columns):
                        if len(table_name) == 0:
                            # query from module table
                            query = select(query_columns, \
                                table.c.instance == module) \
                                .where(table.c.run_id == hf_runs.c.id)
                        else:
                            # query from subtable
                            mod_table = module_class.module_table
                            query_columns[1] = mod_table.c.id
                            query = select(query_columns, \
                                mod_table.c.instance == module) \
                                .where(table.c.parent_id == mod_table.c.id) \
                                .where(mod_table.c.run_id == hf_runs.c.id)
                        
                        # apply constraints
                        for include in constraint['filter'][None]:
                            query = query.where(getattr(table.c, include[0]) == include[1])
                        for exclude in constraint['exclude'][None]:
                            query = query.where(getattr(table.c, exclude[0]) != exclude[1])
                        # apply named constraints
                        if curve_name in constraint['filter']:
                            for include in constraint['filter'][curve_name]:
                                query = query.where(getattr(table.c, include[0]) == include[1])
                        if curve_name in constraint['exclude']:
                            for exclude in constraint['exclude'][curve_name]:
                                query = query.where(getattr(table.c, exclude[0]) != exclude[1])
                        
                        # apply timerange selection
                        if timerange is not None:
                            query = query.where(hf_runs.c.time >= timerange[0]).where(hf_runs.c.time < timerange[1])
                        return query
                    
                    query = queryDatabase([hf_runs.c.time, 0, col])
                    # query data from database and convert datetime object to ordinal
                    if renormalize:
                        limits = queryDatabase([func.min(col), 0, func.max(col)]).execute().fetchone()
                        print limits
                        fac = limits[2]-limits[0]
                        data = [(date2num(p[0]), float(p[2] - limits[0])/fac) for p in query.execute().fetchall()]
                    else:
                        data = [((p[0]), p[2]) for p in query.execute().fetchall()]
                    
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
        try:
            if renormalize:
                ax.set_ylim(0.0, 1.0)
            else:
                ax.set_ymargin(0.01)
            ax.set_autoscalex_on(True)
        except Exception:
            # these might not be supported by
            # old matplotlib versions
            pass
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
            if len(curve[1]) == 0:
                continue
            options = {
                'fmt': plot_format_list[num%len(plot_format_list)],
                'label': curve[0],
                'markersize': 4.0,
            }
            ax.plot_date(*zip(*curve[1]), **options)
        # custom date formats
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