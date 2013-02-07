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
import hf, datetime, time, logging, traceback, os, subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from mako.template import Template
import json

class CategoryCachingTool(cp._cptools.CachingTool):
    """
    Extends the default caching tool to distinguish between category page
    requests with and without explicit time parameter set.
    
    If no explicit time is given (-> most recent run shall be displayed)
    it is checked if the cached page is older than the most recent run
    in the database. If that is the case, all variants of the current
    URI is removed from cache (it is not possible to remove *this* variant
    as far as I know).
    """
    def _wrapper(self, **kwargs):
        params = cp.serving.request.params
        # dirty check if we want "the most current" page
        # When HappyFace is first started, there is no cp._cache variable.
        # It is created by the first call to cp.lib.caching.get() !
        if hasattr(cp, "_cache") and ("time" not in params or "date" not in params):
            cached_data = cp._cache.get()
            if cached_data is None:
                super(CategoryCachingTool, self)._wrapper(**kwargs)
                return
            cached_run_date = datetime.datetime.fromtimestamp(cached_data[3])
            hf_runs = hf.module.database.hf_runs
            newest_run_date = select([hf_runs.c.time], hf_runs.c.completed==True).order_by(hf_runs.c.time.desc()).execute().fetchone()[0]
            if cached_run_date < newest_run_date:
                cp._cache.delete()
        super(CategoryCachingTool, self)._wrapper(**kwargs)
    _wrapper.priority = 20

cp.tools.category_caching = CategoryCachingTool('before_handler', cp.lib.caching.get, 'category_caching')

class Dispatcher(object):
    """
    Show a page for displaying the contents of a category.
    """
    
    def __init__(self, category_list):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = category_list
        try:
            self.svn_rev = subprocess.Popen(['svnversion'], 0, None, None, subprocess.PIPE).stdout.read().strip()
        except Exception:
            self.svn_rev = 'exported'
            
    def prepareDisplay(self, category=None, **kwargs):
        """
        generate the data and template context required to display
        a page containing the navbar.
        
        :param string: Name of the ca
        :returns: tuple (template_context, category_dict, run)
        """
        '''
        Select a hf run based on the passed 'date' and 'time' parameters. If not
        specified, use most recent run. If they are specified, make sure they do
        not mark a point in the future.
        Because (usually) microseconds are stored in the database, too, we have
        to pad with extra 59 seconds (note: 59 because it will be the same minute
        but there will only be a single "dead" second, we can live with that).
        '''
        
        time_error_message = ''
        
        time_obj = datetime.datetime.fromtimestamp(int(time.time()))
        try:
            timestamp = kwargs['date'] if 'date' in kwargs is not None else time_obj.strftime('%Y-%m-%d')
            timestamp += '_' + (kwargs['time'] if 'time' in kwargs else time_obj.strftime('%H:%M'))
            # notice the extra seconds to avoid microsecond and minute issues
            time_obj = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timestamp, "%Y-%m-%d_%H:%M"))+59)

        except Exception:
            time_error_message = "The passed time was invalid"
        
        if time_obj > datetime.datetime.fromtimestamp(int(time.time())+59):
            time_error_message = "HappyFace is not an oracle"
            time_obj = datetime.datetime.fromtimestamp(int(time.time())+59)
            
        run = hf_runs.select(hf_runs.c.time <= time_obj).\
            where(or_(hf_runs.c.completed==True, hf_runs.c.completed==None)).\
            order_by(hf_runs.c.time.desc()).\
            execute().fetchone()
        if run is None:
            time_error_message = "No data so far in past"
            run = hf_runs.select(hf_runs.c.time >= time_obj).\
            where(or_(hf_runs.c.completed==True, hf_runs.c.completed==None)).\
            order_by(hf_runs.c.time.asc()).\
            execute().fetchone()
            time_obj = run["time"]
        run = {"id":run["id"], "time":run["time"]}
        
        # if the run is older than a certain time threshold,
        # then mark it as stale
        stale_threshold = datetime.timedelta(0, 0, 0, 0,\
            int(hf.config.get('happyface', 'stale_data_threshold_minutes')))
        data_stale = (run['time'] + stale_threshold) < datetime.datetime.now()
        run['stale'] = data_stale
        
        category_list = [cat.getCategory(run) for cat in self.category_list]
        category_dict = dict((cat.name, cat) for cat in category_list)
        
        selected_category = None
        for c in category_list:
            if c.name == category:
                selected_category = c
                break
        
        lock_icon = 'lock_icon_on.png' if cp.request.cert_authorized else 'lock_icon_off.png'
        lock_icon = os.path.join(hf.config.get('paths', 'template_icons_url'), lock_icon)
        
        template_context = {
            "static_url": hf.config.get('paths', 'static_url'),
            "happyface_url": hf.config.get('paths', 'happyface_url'),
            "category_list": category_list,
            "module_list": [],
            "hf": hf,
            "time_specified": ('date' in kwargs or 'time' in kwargs),
            "date_string": time_obj.strftime('%Y-%m-%d'),
            "time_string": time_obj.strftime('%H:%M'),
            "histo_step": kwargs['s'] if 's' in kwargs else "00:15",
            "run": run,
            'selected_module': None,
            'selected_category': selected_category,
            'time_error_message': time_error_message,
            'data_stale': data_stale,
            'svn_rev': self.svn_rev,
            'lock_icon': lock_icon,
            'include_time_in_url': ('date' in kwargs or 'time' in kwargs),
            'automatic_reload': not ('date' in kwargs or 'time' in kwargs),
            'reload_interval': int(hf.config.get('happyface', 'reload_interval')),
        }

        for cat in category_list:
            template_context["module_list"].extend(cat.module_list)
        return template_context, category_dict, run

    @cp.expose
    @cp.tools.category_caching()
    def default(self, category=None, **kwargs):
        try:
            # Don't HTTP cache, when no explicit time is set
            if "date" in kwargs or "time" in kwargs:
                cp.lib.caching.expires(secs=3600, force=True)
            else:
                cp.lib.caching.expires(secs=1, force=True)
            template_context, category_dict, run = self.prepareDisplay(category, **kwargs)
            
            doc = u""
            
            if 'action' in kwargs:
                if kwargs['action'].lower() == 'getxml':
                    template_context['category_list'] = filter(lambda x: not x.isUnauthorized(),
                        template_context['category_list'])
                    doc = hf.category.renderXmlOverview(run, template_context)
                else:
                    doc = u'''<h2>Unkown action</h2>
                    <p>The specified action <em>%s</em> is not known.<p>''' % kwargs['action']
            else:
                '''
                Show the requested category or a 'blank' overview if
                no category is specified.
                '''
                if category is None:
                    filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "index.html")
                    index_template = Template(filename=filename, lookup=hf.template_lookup)
                    doc = index_template.render_unicode(**template_context)
                elif category is not None and not category in category_dict:
                    raise cp.HTTPError(404)
                elif category is not None:
                    if run is not None:
                        doc = category_dict[category].render(template_context)
                    else:
                        doc = u"<h2>No data found at this time</h2>"
            return doc
        except cp.CherryPyException:
            raise
        except Exception, e:
            self.logger.error("Page request threw exception: %s" % str(e))
            self.logger.error(traceback.format_exc())
            raise

class AjaxDispatcher:
    def __init__(self, category_list):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = category_list
        self.modules = {}
        for category in self.category_list:
            for module in category.module_list:
                self.modules[module.instance_name] = module
        self.logger.debug(self.modules)
        
    @cp.expose
    @cp.tools.caching()
    def default(self, module, run_id, **kwargs):
        response = {"status": "unkown", "data": []}
        try:
            if module not in self.modules:
                raise Exception("Module not found")
            
            module = self.modules[module]
            
            if module.isUnauthorized():
                raise cp.HTTPError(status=403, message="You are not allowed to access this resource.")
            
            run = hf_runs.select(hf_runs.c.id==run_id).execute().fetchone()
            if run is None:
                raise Exception("The specified run ID was not found!")
            
            specific_module = module.getModule(run)
            if not hasattr(specific_module, "ajax"):
                raise Exception("Module does not export data via Ajax")
            
            if specific_module.error_string:
                raise Exception(specific_module.error_string)
            if specific_module.dataset is None:
                raise Exception("No data at this time")
            self.logger.debug(specific_module.error_string, specific_module.dataset)
            response["data"] = specific_module.ajax(**kwargs)
            response["status"] = "success"
            
            cp.lib.caching.expires(secs=9999999, force=True) # ajax data never goes bad, since it is supposed to be static
            
        except cp.HTTPError, e:
            cp.lib.caching.expires(secs=0, force=False)
            response = {
                "status": "error",
                "code": e.code,
                "reason": "%i: %s" % (e.code, e.reason),
                "data": []
            }
        except Exception, e:
            cp.lib.caching.expires(secs=30, force=True) # ajax data never goes bad, since it is supposed to be static
            self.logger.error("Ajax request threw exception: %s" % str(e))
            self.logger.error(traceback.format_exc())
            response = {
                "status": "error",
                "code": 500,
                "reason": str(e),
                "data":[]
            }
            
        finally:
            return json.dumps(response)