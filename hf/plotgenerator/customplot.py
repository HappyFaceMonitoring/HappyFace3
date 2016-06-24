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
import os
import sys
import importlib
import numpy as np
import timeit
from sqlalchemy.sql import select, func, or_
from sqlalchemy import Integer, Float, Numeric
from hf.module.database import hf_runs

@hf.url.absoluteUrl
def getCustomPlotUrl():
    return "/plot/custom/"

def __getCustomPlotTemplateDict(module_instance_name):

    logger = logging.getLogger(__name__ + "__getCustomPlotTemplateDict")
    
    if not hf.module.config.has_section(module_instance_name):
        raise Exception("No such module")
    
    template_name = module_instance_name + "_template" 
    template_dir = os.path.join(hf.hf_dir, hf.config.get("paths", "customplot_template_dir"))
    sys.path.append(template_dir)
    try:
        template = importlib.import_module(template_name)
    except ImportError, e:
        raise Exception("No such plot template")
    return template.custom_plot_dict

def __getDataPoints(module_instance_name,subtable_name,x_name,y_name,quantity_column_name,chosen_quantity_name):

    logger = logging.getLogger(__name__ + "__getDataPoints")
    
    if not hf.module.config.has_section(module_instance_name):
        raise Exception("No such module")
    
    module_class = hf.module.getModuleClass(hf.module.config.get(module_instance_name, "module"))
    try:
        subtable = module_class.subtables[subtable_name]
    except IndexError, e:
        raise Exception("No such subtable")
    
    x_column = col in subtable.columns if col.name == x_name
    y_column = col in subtable.columns if col.name == y_name
    quantity_column = col in subtable.columns if col.name == quantity_column_name
    
    data_point_columns = [quantity_column,x_column,y_column]
    
    mod_table = subtable.module_class.module_table
    data_point_query = select(data_point_columns, \
        mod_table.c.instance == module_instance_name) \
        .where(subtable.c.parent_id == mod_table.c.id) \
        .where(mod_table.c.run_id == hf_runs.c.id) \
        .where(getattr(subtable.c, quantity_column_name) == chosen_quantity_name)
    
    data_point_query = data_point_query.where(or_(hf_runs.c.completed == True,
        hf_runs.c.completed == None))
    result = data_point_query.execute()
    source_data = result.fetchall()
    logger.error(source_data)
    return

def customPlot(**kwargs):

    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__ + ".customPlot")
    ylabel_list = ["other", "error", "warning", "ok"]
    color_list = ["gray", "red", "orange", "green"]
    fig, ax = plt.subplots()
    custom_plot_dict = __getCustomPlotTemplateDict(kwargs["module_instance_name"])
    ax.set_title(custom_plot_dict["title"])
    for color, statusnumber in zip(color_list, np.arange(1,5)):
        ax.axhline(y=statusnumber, color=color, linewidth=8)
    
    __getDataPoints(kwargs["module_instance_name"],kwargs["subtable_name"],kwargs["x_name"],kwargs["y_name"],
        kwargs["quantity_column_name",kwargs["chosen_quantity_name"])
    
    img_data = StringIO.StringIO()
    try:
        fig.savefig(img_data, transparent=True)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()

