# -*- coding: utf-8 -*-
#
# Copyright 2012 Institut für Experimentelle Kernphysik - Karlsruher Institut für Technologie
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import hf
import re
import cherrypy as cp
import json
import StringIO
import traceback
import logging
import datetime
import time
import numpy as np
import timeit
from sqlalchemy.sql import select, func, or_
from sqlalchemy import Integer, Float, Numeric
from hf.module.database import hf_runs


@hf.url.absoluteUrl
def getTimeseriesUrl():
    return "/plot/time/"


def __plotableColumns(table):
    blacklist = ['id', 'run_id', 'instance', 'description', 'instruction',
                 'error_string', 'source_url']
    types = [Integer, Float, Numeric]

    def isnumeric(cls):
        for t in types:
            if isinstance(cls,t):
                return True
        return False
    numerical_cols = filter(lambda x: isnumeric(x.type), table.columns)
    return [col for col in numerical_cols if col.name not in blacklist]


def getTimeseriesPlotConfig(**kwargs):
    """
    Extract the plot configuration from the URL arguments.

    Possible arguments are a subset from the ones of :meth:`timeseriesPlot() <hf.plotgenerator.timeseries.timeseriesPlot>`, see there for details.

    :param curve_XXX: colon-separated curve info: (module_instance,[subtable],expr,title)
    :param legend: Show legend in image
    :param title: (string) Display a title above plot
    :param ylabel: self-explanatory
    :param start_date: Start date (Y-m-d)
    :param end_date: End date (Y-m-d)
    :param start_time: Start time (H:M)
    :param end_date: End time (H:M)
    :param renormalize: (true, false / 1, 0) Scales all curves to a [0,1] interval

    :return: A dictionary with the configuration. The entries are

        *curve_dict*
            A dictionary encoding the curves to plot. Only curves are given where the user is authorized. to access.
            The key is the curve name, the value is a tuple of the following format: *(title, table, module_instance, col_expr, subtable)*

            *title*
                Title of the curve. Same as given in the URL.

            *table*
                sqlalchemy Table instance.

            *module_instance*
                Name of the module instance to plot data from. Same as given in the URL.

            *col_expr*
                The expression to plot. See :ref:`column_expressions` for syntax.

            *subtable*
                Subtable to plot from, empty string if plot from module table is requested. Same as given in the URL.

        *title*
            Title of the plot

        *legend*
            True or false, 0 or 1, flag to indicate if legend should be displayed.

        *ylabel*
            Label of the y-axis

        *timerange*
            Tuple of datetime objects, *(start, end)*

        *renormalize*
            If *True*, each curve is scaled into a [0,1] interval.

        *auth_required*
            Flag if authorization is required for any curve.

        *errors*
            A list of error messages that occured during the function call
    """
    logger = logging.getLogger(__name__+".getTimeseriesPlotConfig")

    logger.debug(kwargs)

    curve_dict = {}
    data_sources = set()
    title = ""
    legend = False
    ylabel = ""
    timerange = None
    renormalize = False
    errors = []

    # Set to true if special auth is required for a curve.
    auth_required = False

    # extract timeranges
    now = datetime.datetime.now()
    end_date = (kwargs['end_date'] if 'end_date' in kwargs
                else now.strftime('%Y-%m-%d'))
    start_date = kwargs['start_date'] if 'start_date' in kwargs else end_date
    start_time = kwargs['start_time'] if 'start_time' in kwargs else "00:00"
    end_time = (kwargs['end_time'] if 'end_time' in kwargs
                else now.strftime('%H:%M'))
    start = datetime.datetime.fromtimestamp(time.mktime(
        time.strptime(start_date+'_'+start_time, "%Y-%m-%d_%H:%M")))
    end = datetime.datetime.fromtimestamp(time.mktime(
        time.strptime(end_date+'_'+end_time, "%Y-%m-%d_%H:%M"))+60)
    timerange = [start, end]

    if 'renormalize' in kwargs:
        if kwargs['renormalize'].lower() in ['true', '1']:
            renormalize = True

    # STAGE 1
    # Parse curve data and scan for parameters.
    # This gets a list from all tables that are to
    # be retrieved in the next step.
    for key, value in kwargs.iteritems():
        if key.lower().startswith(u"curve_"):
            try:
                curve_name = key[6:]
                curve_info = value.split(",")
                logger.debug("curve data: %s", value)
                if len(curve_info) < 4:
                    raise Exception("Insufficient number of arguments for plot curve")
                module_instance, table_name, col_expr = curve_info[:3]
                logger.debug("Preliminary column expression: %s", col_expr)

                # join expression at \, occurences. Increase the
                # index where the curve title starts.
                title_start_idx = 3
                for fragment in curve_info[title_start_idx:]:
                    if col_expr.endswith("\\"):
                        col_expr = col_expr[:-1] + "," + fragment
                        title_start_idx += 1
                    else:
                        break
                logger.debug("Column expression: %s", col_expr)

                # Since the title was split at "," before, join them together again.
                # If it is empty, auto generate title.
                logger.debug("title_start_idx %i", title_start_idx)
                logger.debug("Curve info belonging to title: %s", str(curve_info[title_start_idx:]))
                title = ",".join(curve_info[title_start_idx:])
                if len(title) == 0:
                    title = module_instance + " " + col_expr

                if not hf.module.config.has_section(module_instance):
                    raise Exception("No such module")
                module_class = hf.module.getModuleClass(hf.module.config.get(module_instance, "module"))
                try:
                    table = module_class.module_table if len(table_name) == 0 else module_class.subtables[table_name]
                except IndexError, e:
                    raise Exception("No such subtable")
                data_sources.add((table, module_instance))
                curve_dict[curve_name] = (title, table, module_instance, col_expr, table_name)
            except Exception, e:
                logger.warning("Parsing curve failed:\n"+traceback.format_exc())
                errors.append("Curve '%s': %s" % (key, str(e)))
        elif key.lower() == u"legend":
            legend = (value.lower() == "true" or value == "1")
        elif key.lower() == u"ylabel":
            ylabel = value
        elif key.lower() == u"title":
            title = value

    return {
        "curve_dict": curve_dict,
        "data_sources": data_sources,
        "title": title,
        "legend": legend,
        "ylabel": ylabel,
        "timerange": timerange,
        "renormalize": renormalize,
        "auth_required": auth_required,
        "timerange": timerange,
        "errors": errors
    }


def __timeseriesTableQuery(curve, table, module_instance, constraint, timerange):
    logger = logging.getLogger(__name__+".__timeseriesTableQuery")
    try:
        query_columns = [hf_runs.c.time]
        query_columns.extend(__plotableColumns(table))
        if table.name.startswith("mod"):
            # query from module table
            query = select(query_columns,
                           table.c.instance == module_instance) \
                .where(table.c.run_id == hf_runs.c.id)
        else:
            # query from subtable
            mod_table = table.module_class.module_table
            #query_columns[1] = mod_table.c.id
            query = select(query_columns, \
                           mod_table.c.instance == module_instance) \
                           .where(table.c.parent_id == mod_table.c.id) \
                           .where(mod_table.c.run_id == hf_runs.c.id)
        query = query.where(or_(hf_runs.c.completed == True,
                                hf_runs.c.completed == None))
        # apply constraints
        for constr_curve in [None, curve]:
            if constr_curve in constraint['filter']:
                constraint_list = [
                    getattr(table.c, include[0]) == include[1]
                    for include in constraint['filter'][constr_curve]]
                query = query.where(or_(*constraint_list))
            if constr_curve in constraint['exclude']:
                for exclude in constraint['exclude'][constr_curve]:
                    query = query.where(getattr(table.c, exclude[0]) != exclude[1])

        # apply timerange selection
        if timerange is not None:
            query = query.where(hf_runs.c.time >= timerange[0]).where(hf_runs.c.time < timerange[1])
        # sort ascending by date
        query = query.order_by(hf_runs.c.time)
        logger.debug(query)
        return query
    except Exception, e:
        logger.warning("Retrieving plot data:\n"+traceback.format_exc())
        raise Exception("Curve '%s': %s" % (curve, str(e)))


def timeseriesPlot(category_list, **kwargs):
    """
    Supported arguments (via \**kwargs):

    :param curve_XXX: colon-separated curve info: (module_instance,[subtable],expr,title)
    :param filter: include only rows where specified column in result set matches value, can be specified more than once: col,value
    :param filter_XXX: include only rows where specified column in result set matches value for curve XXX, can be specified more than once: col,value
    :param exclude: include only rows where specified column in result set matches value, can be specified more than once: col,value
    :param exclude_XXX: include only rows where specified column in result set matches value for curve XXX, can be specified more than once: col,value
    :param legend: Show legend in image
    :param title: (string) Display a title above plot
    :param ylabel: self-explanatory
    :param start_date: Start date (Y-m-d)
    :param end_date: End date (Y-m-d)
    :param start_time: Start time (H:M)
    :param end_date: End time (H:M)
    :param renormalize: (true, false / 1, 0) Scales all curves to a [0,1] interval
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
    constraint = {'filter': {}, 'exclude': {}}
    for t in constraint.iterkeys():
        for key, value in kwargs.iteritems():
            if key.startswith(t):
                if len(key) <= len(t)+1:
                    curve = None
                else:
                    curve = key[len(t)+1:]
                if type(value) is not list:
                    value = [value,]
                for constr in value:
                    if curve not in constraint[t]:
                        constraint[t][curve] = []
                    constraint[t][curve].append(constr.split(','))
    errors = []
    try:
        # STAGE 1
        logger.debug("TEST")
        dat = getTimeseriesPlotConfig(**kwargs)
        logger.debug("config: %s", "\n".join(map(lambda x: str(x[0]) +
                                                 ": " + str(x[1]),
                                                 dat.iteritems())))
        curve_dict = dat["curve_dict"]
        data_sources = dat["data_sources"]
        title = dat["title"]
        legend = dat["legend"]
        ylabel = dat["ylabel"]
        timerange = dat["timerange"]
        renormalize = dat["renormalize"]
        auth_required = dat["auth_required"]
        timerange = dat["timerange"]
        errors.extend(dat["errors"])

        # STAGE 3
        # Calculate the data structures for each curve
        vardict_name = "__internal_column_value_dict__"
        regexp_dollarvar = re.compile(r"\$([_a-zA-Z0-9]+)")
        for curve_name, (title, table, module_instance, expr, table_name) in curve_dict.iteritems():
            query = __timeseriesTableQuery(curve_name, table, module_instance, constraint, timerange)
            try:
                result = query.execute()
                try:
                    column_index = dict((col, i)
                                        for i, col in enumerate(result.keys()))
                except TypeError:  # backward compatibility
                    column_index = dict((col, i)
                                        for i, col in enumerate(result.keys))

                source_data = result.fetchall()
            except Exception, e:
                logger.warning("Retrieving plot data:\n"+traceback.format_exc())
                errors.append("Data '%s': %s" % (key, str(e)))
                continue
            try:
                num_rows = len(source_data)
                if num_rows == 0:
                    logger.debug("no data downloaded for curve")
                    curve_dict[curve_name] = (title, [], [])
                    continue

                logger.debug("Entries in sources: %i" % num_rows)
                dates = np.zeros(num_rows)
                data_points = np.zeros(num_rows)
                min_val = max_val = None

                use_matheval = False
                math_expr = expr
                # does the expression not match a column name?
                # Replace $varnames by a dict call to create valid math expression.
                if expr not in column_index:
                    use_matheval = True
                    math_expr = regexp_dollarvar.sub(vardict_name+"['\\1']", expr)
                    logger.debug("Math expression "+repr(math_expr))

                for i, row in enumerate(source_data):
                    variables = dict((col, row[i])
                                     for col, i
                                     in column_index.iteritems())
                    dates[i] = date2num(row[0])

                    if use_matheval:
                        val = hf.utility.matheval(math_expr,
                                                  {vardict_name: variables})
                    else:
                        val = variables[expr]

                    data_points[i] = val
                    if min_val is None: min_val = val
                    elif min_val > val: min_val = val
                    if max_val is None: max_val = val
                    elif max_val < val: max_val = val

                if renormalize and max_val - min_val != 0:
                    data_points = (data_points - min_val)/(max_val - min_val)
                elif renormalize:
                    data_points = np.zeros(len(data_points)) + 0.5

                curve_dict[curve_name] = (title, dates, data_points)
            except Exception, e:
                curve_dict[curve_name] = (title, [], [])
                logger.warning("Retrieving plot data:\n"+traceback.format_exc())
                errors.append("Data '%s': %s" % (key, str(e)))

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

        for num, curve in enumerate(curve_dict.itervalues()):
            logger.debug(curve)
            if len(curve[1]) == 0:
                continue
            options = {
                'fmt': plot_format_list[num % len(plot_format_list)],
                'label': curve[0],
                'markersize': 4.0,
            }
            ax.plot_date(curve[1], curve[2], **options)
        # custom date formats
        ax.xaxis.get_major_formatter().scaled = {
            365.0  : '%Y',
            30.    : '%Y-%m',
            1.0    : '%Y-%m-%d',
            1./24. : '%H:%M %y-%m-%d',
        }
        if 'title' in kwargs:
            ax.set_title(kwargs['title'])
        if 'legend' in kwargs:
                ax.legend(loc=int(kwargs['legend']), numpoints=1)
        ax.set_ylabel(ylabel)
        if auth_required:
            ax.text(0.02, 0.5, "One or more curves require certificate authentification", color="#ff0000", fontsize=14)
    except Exception, e:
        logger.error("Plotting Failed: %s" % str(e))
        logger.error(traceback.format_exc())
        errors.append("Plotting Failed: %s" % str(e))

    logger.debug("errors gatherd during run: %s", "\n".join(errors))

    img_data = StringIO.StringIO()
    try:
        fig.savefig(img_data, transparent=True)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()
