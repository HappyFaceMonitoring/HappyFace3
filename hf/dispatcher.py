# -*- coding: utf-8 -*-

import cherrypy as cp
import hf, datetime, time, logging, traceback
from hf.module.database import hf_runs
from sqlalchemy import *
from mako.template import Template

class CategoryDispatcher(object):
    """
    Show a page for displaying the contents of a category.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = hf.category.createCategoryObjects()
    
    @cp.expose
    def default(self, category=None, **kwargs):
        try:
            time_obj = datetime.datetime.now()
            timestamp = kwargs['date'] if 'date' in kwargs is not None else time_obj.strftime('%Y-%m-%d')
            timestamp += '_' + (kwargs['time'] if 'time' in kwargs else time_obj.strftime('%H:%M'))
            time_obj = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestamp, "%Y-%m-%d_%H:%M")))
            
            run = hf_runs.select(hf_runs.c.time <= time_obj).order_by(hf_runs.c.time.desc()).execute().fetchone()
            run = {"id":run["id"], "time":run["time"]}
            self.logger.info(run)
            category_dict = dict((cat.name, cat.getModule(run)) for cat in hf.category.createCategoryObjects())
            
            template_context = {
                "static_url": hf.config.get('paths', 'static_url'),
                "category_list": category_dict.values(),
                "module_list": [],
                "hf": hf,
                "date_string": run["time"].strftime('%Y-%m-%d'),
                "time_string": run["time"].strftime('%H:%M'),
                "histo_step": kwargs['s'] if 's' in kwargs else "00:15"
            }

            for cat in category_dict.itervalues():
                template_context["module_list"].extend(cat.module_list)
            
            doc = u""

            doc += u"<ul>"
            for cat in category_dict.iterkeys():
                doc += u"<li><a href=\"/%s\">%s</a></li>" % (cat,cat)
            doc += u"</ul>"
            
            
            if category is not None and not category in category_dict:
                doc += u"<h2>404 – File Not Found</h2>"
            elif category is not None:
                if run is not None:
                    
                    doc = category_dict[category].render(template_context)
                else:
                    doc = "<h2>No data found at this time</h2>"
            return doc
        except Exception, e:
            self.logger.error("Page request threw exception: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            raise