# -*- coding: utf-8 -*-

import cherrypy as cp
import hf, datetime
from hf.module.database import hf_runs
from sqlalchemy import *

class CategoryDispatcher(object):
    """
    Show a page for displaying the contents of a category.
    """
    
    def __init__(self, category_list):
        self.category_dict = dict((cat.config["name"], cat) for cat in category_list)
    
    @cp.expose
    def default(self, category=None, date=None, time=None):
        doc = u"<html><body>"
        
        doc += u"<ul>"
        for cat in self.category_dict.iterkeys():
            doc += u"<li><a href=\"/%s\">%s</a></li>" % (cat,cat)
        doc += u"</ul>"
        
        run = hf_runs.select(hf_runs.c.time <= datetime.datetime.now()).order_by(hf_runs.c.time.desc()).execute().fetchone()
        print run, repr(run), type(run)
        
        if category is not None and not category in self.category_dict:
            doc += u"<h2>404 – File Not Found</h2>"
        elif category is not None:
            if run is not None:
                doc += self.category_dict[category].render(run)
            else:
                doc += "<h2>No data found at this time</h2>"
        doc += u"</body></html>"
        return doc