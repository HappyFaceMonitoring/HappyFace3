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

import cherrypy as cp
import hf
import datetime
import time
import logging
import traceback
import os
import subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from mako.template import Template


class Dispatcher(object):
    """
    The Plot Generator subsystem dispatcher
    """

    def __init__(self, category_list):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = category_list

        if hf.config.get('plotgenerator', 'enabled').lower() == 'true':
            hf.plotgenerator.init()
            try:
                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "plot_timeseries.html")
                cp.engine.autoreload.files.add(filename)
                self.timeseries_template = Template(filename=filename, lookup=hf.template_lookup)
            except Exception:
                self.logger.error("Cannot initialize timeseries template")
                self.logger.error(traceback.format_exc())

    @cp.expose
    def default(self, plt_type=None, img=None, **kwargs):
        if hf.config.get('plotgenerator', 'enabled').lower() != 'true':
            return "Plot Generator disabled by HappyFace configuration"

        if img == "img":
            if plt_type == "time":
                return hf.plotgenerator.timeseriesPlot(self.category_list, **kwargs)
        else:
            if plt_type == "custom":
                return hf.plotgenerator.customPlot(**kwargs)
            try:
                # just get the lastest run, we don't really need it
                run = hf_runs.select(). \
                    where(or_(hf_runs.c.completed == True, hf_runs.c.completed == None)). \
                    order_by(hf_runs.c.time.desc()). \
                    execute().fetchone()
                category_list = [cat.getCategory(run) for cat in self.category_list]

                start_date = kwargs['start_date'] if 'start_date' in kwargs else run["time"].strftime('%Y-%m-%d')
                start_time = kwargs['start_time'] if 'start_time' in kwargs else run["time"].strftime('%H:%M')

                start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start_date + '_' + start_time, "%Y-%m-%d_%H:%M")))
                past = start - datetime.timedelta(days=2)

                end_date = kwargs['end_date'] if 'end_date' in kwargs else past.strftime('%Y-%m-%d')
                end_time = kwargs['end_time'] if 'end_time' in kwargs else past.strftime('%H:%M')

                end = datetime.datetime.fromtimestamp(time.mktime(time.strptime(end_date + '_' + end_time, "%Y-%m-%d_%H:%M")))

                plot_cfg = hf.plotgenerator.getTimeseriesPlotConfig(**kwargs)

                curve_dict = {}
                for name, curve in plot_cfg["curve_dict"].iteritems():
                    #curve <=> (title, table, module_instance, col_expr)
                    curve_dict[name] = (curve[2], \
                        curve[4], \
                        curve[3], \
                        curve[0])
                self.logger.debug(curve_dict)

                # Parse the constraints
                constraint_dict = {}
                for name, cond_list in kwargs.iteritems():
                    if name.startswith('filter'):
                        include = True
                        name = name[6:] if len(name) > 6 else ''
                    elif name.startswith('exclude'):
                        include = False
                        name = name[7:] if len(name) > 7 else ''
                    else:
                        continue
                    if not isinstance(cond_list, list):
                        cond_list = [cond_list, ]
                    for cond in cond_list:
                        var = cond.split(',')[0]
                        value = ','.join(cond.split(',')[1:])
                        if name in constraint_dict:
                            constraint_dict[name].append([include, var, value])
                        else:
                            constraint_dict[name] = [[include, var, value], ]
                trendplot = (kwargs['renormalize'].lower() if 'renormalize' in kwargs else 'false') in ['1', 'true']

                legend_select = dict((i, "") for i in xrange(11))
                if 'legend' in kwargs:
                    legend_select[int(kwargs['legend'])] = "selected='selected'"
                    

                template_context = {
                        "static_url": hf.config.get('paths', 'static_url'),
                        "url_short_api_key": hf.config.get('plotgenerator', 'url_short_api_key'),
                        "happyface_url": hf.config.get('paths', 'happyface_url'),
                        "category_list": category_list,
                        "module_list": [],
                        "start": start,
                        "end": end,
                        "curve_dict": curve_dict,
                        "constraint_dict": constraint_dict,
                        "trendplot": trendplot,
                        "title": kwargs["title"] if 'title' in kwargs else '',
                        "hf": hf,
                        "legend_select": legend_select,
                    }

                for cat in category_list:
                    template_context["module_list"].extend(cat.module_list)
                if plt_type == "time":
                    test = self.timeseries_template.render_unicode(**template_context)
                    return test
            except Exception, e:
                self.logger.error("Plot interface hander failed: " + str(e))
                self.logger.error(traceback.format_exc())
                raise
        # if we get here, 404!
        raise cp.HTTPError(404)
