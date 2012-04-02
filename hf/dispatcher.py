# -*- coding: utf-8 -*-

import cherrypy as cp
import hf, datetime, time, logging, traceback, os
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
	self.logger.warning(category)
        try:
            self.logger.debug(kwargs['date'] if 'date' in kwargs is not None else '')
            self.logger.debug(kwargs['time'] if 'time' in kwargs is not None else '')
            
            time_error_message = ''
            
            time_obj = datetime.datetime.fromtimestamp(int(time.time()))
            try:
                timestamp = kwargs['date'] if 'date' in kwargs is not None else time_obj.strftime('%Y-%m-%d')
                timestamp += '_' + (kwargs['time'] if 'time' in kwargs else time_obj.strftime('%H:%M'))
                # notice the extra seconds to avoid microsecond and minute issues
                time_obj = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestamp, "%Y-%m-%d_%H:%M")) + 60)
            except Exception:
                time_error_message = "The passed time was invalid"
            
            if time_obj > datetime.datetime.fromtimestamp(int(time.time())+60):
                time_error_message = "HappyFace is not an oracle"
 
            run = hf_runs.select(hf_runs.c.time <= time_obj).order_by(hf_runs.c.time.desc()).execute().fetchone()
            if run is None:
                time_error_message = "No data so far in past"
                run = hf_runs.select(hf_runs.c.time >= time_obj).order_by(hf_runs.c.time.asc()).execute().fetchone()
            run = {"id":run["id"], "time":run["time"]}
            self.logger.info(run)
            category_dict = dict((cat.name, cat.getCategory(run)) for cat in self.category_list)
            
            selected_category = None
            for c in category_dict.itervalues():
                if c.name == category:
                    selected_category = c
                    break
            
            template_context = {
                "static_url": hf.config.get('paths', 'static_url'),
                "category_list": category_dict.values(),
                "module_list": [],
                "hf": hf,
                "time_specified": ('date' in kwargs or 'time' in kwargs),
                "date_string": run["time"].strftime('%Y-%m-%d'),
                "time_string": run["time"].strftime('%H:%M'),
                "histo_step": kwargs['s'] if 's' in kwargs else "00:15",
                "run": run,
                'selected_module': None,
                'selected_category': selected_category,
                'time_error_message': time_error_message
            }

            for cat in category_dict.itervalues():
                template_context["module_list"].extend(cat.module_list)
            
            doc = u""

            if category is None:
                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "index.html")
                index_template = Template(filename=filename, lookup=hf.template_lookup)
                doc = index_template.render(**template_context)
            elif category is not None and not category in category_dict:
                raise cp.HTTPError(404, u"<h2>404 – File Not Found</h2>")
            elif category is not None:
                if run is not None:
                    doc = category_dict[category].render(template_context)
                else:
                    doc = "<h2>No data found at this time</h2>"
            return doc
        except Exception, e:
            self.logger.error("Page request threw exception: %s" % str(e))
            self.logger.debug(traceback.format_exc())
            raise cp.HTTPError(500, "HappyFace threw an exception, see logfile for detailed info")
