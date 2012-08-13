# -*- coding: utf-8 -*-

import cherrypy as cp
import hf, datetime, time, logging, traceback, os, subprocess
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
                self.logger.debug(traceback.format_exc())
    

    @cp.expose
    def default(self, plt_type=None, img=None, **kwargs):
        if hf.config.get('plotgenerator', 'enabled').lower() != 'true':
            return "Plot Generator disabled by HappyFace configuration"
        
        if img == "img":
            if plt_type == "time":
                return hf.plotgenerator.timeseriesPlot(self.category_list, **kwargs)
        else:
            try:
                # just get the lastest run, we don't really need it
                run = hf_runs.select().\
                    where(or_(hf_runs.c.completed==True, hf_runs.c.completed==None)).\
                    order_by(hf_runs.c.time.desc()).\
                    execute().fetchone()
                category_list = [cat.getCategory(run) for cat in self.category_list]
                
                start_date = kwargs['start_date'] if 'start_date' in kwargs else run["time"].strftime('%Y-%m-%d')
                start_time = kwargs['start_time'] if 'start_time' in kwargs else run["time"].strftime('%H:%M')
                
                start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start_date+'_'+start_time, "%Y-%m-%d_%H:%M")))
                past = start - datetime.timedelta(days=2)
                
                end_date = kwargs['end_date'] if 'end_date' in kwargs else past.strftime('%Y-%m-%d')
                end_time = kwargs['end_time'] if 'end_time' in kwargs else past.strftime('%H:%M')
                
                end = datetime.datetime.fromtimestamp(time.mktime(time.strptime(end_date+'_'+end_time, "%Y-%m-%d_%H:%M")))
                
                def extractCurve(d):
                    try:
                        d = d.split(',')
                        data = d[0:3]
                        data.append(','.join(d[3:]))
                        return data
                    except Exception:
                        return None
                
                curve_dict = dict((int(name[6:]), extractCurve(val)) \
                    for name,val in kwargs.iteritems() \
                    if name.startswith("curve_"))
                curve_dict = dict(filter(lambda x: x is not None, curve_dict.iteritems()))
                
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
                        cond_list = [cond_list,]
                    for cond in cond_list:
                        var = cond.split(',')[0]
                        value = ','.join(cond.split(',')[1:])
                        if name in constraint_dict:
                            constraint_dict[name].append([include, var, value])
                        else:
                            constraint_dict[name] = [[include, var, value],]
                trendplot = (kwargs['renormalize'].lower() if 'renormalize' in kwargs else 'false') in ['1', 'true']
                
                template_context = {
                        "static_url": hf.config.get('paths', 'static_url'),
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
                    }
                
                for cat in category_list:
                    template_context["module_list"].extend(cat.module_list)
                if plt_type == "time":
                    test= self.timeseries_template.render(**template_context)
                    return test
            except Exception,e:
                self.logger.error("Plot interface hander failed: "+str(e))
                self.logger.debug(traceback.format_exc())
                raise
        # if we get here, 404!
        return "404" # TODO 404!