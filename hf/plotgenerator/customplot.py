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
from hf.module.database import hf_runs
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

def __getDataPoints(module_instance_name,subtable_name,x_name,y_name,quantity_column_name,chosen_quantity_name,run_id):

    logger = logging.getLogger(__name__ + "__getDataPoints")
    
    if not hf.module.config.has_section(module_instance_name):
        raise Exception("No such module")
    
    module_class = hf.module.getModuleClass(hf.module.config.get(module_instance_name, "module"))
    try:
        subtable = module_class.subtables[subtable_name]
    except IndexError, e:
        raise Exception("No such subtable")
    
    x_column = [col for col in subtable.columns if col.name == x_name][0]
    y_column = [col for col in subtable.columns if col.name == y_name][0]
    quantity_column = [col for col in subtable.columns if col.name == quantity_column_name][0]
    
    data_point_columns = [quantity_column,x_column,y_column]
    mod_table = subtable.module_class.module_table
    data_point_query = select(data_point_columns, \
        mod_table.c.instance == module_instance_name) \
        .where(subtable.c.parent_id == mod_table.c.id) \
        .where(mod_table.c.run_id == run_id ) \
        .where(getattr(subtable.c, quantity_column_name) == chosen_quantity_name)
    logger.error(data_point_query)
    result = data_point_query.execute()
    source_data = result.fetchall()
    logger.error(source_data)
    return source_data

def customPlot(**kwargs):

    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__ + ".customPlot")

    fig, ax = plt.subplots()
    
    # retrieving configuration
    custom_plot_dict = __getCustomPlotTemplateDict(kwargs["module_instance_name"])
    
    # setting and modifying title
    title = custom_plot_dict["title"]
    if custom_plot_dict["search_for_title_placeholders"]:
        placeholder_list = re.findall(r"\[\@\](.*?)\[\@\]", custom_plot_dict["title"])
        for placeholder in placeholder_list:
            for key,value in kwargs.iteritems():
                if key == placeholder:
                    title = title.replace("[@]"+placeholder+"[@]",value)
                    break
    ax.set_title(title)
    
    # adding horizontal lines if available
    for add_hline in custom_plot_dict["additional_hlines"]:
        ax.axhline(y=add_hline["y_value"], color=add_hline["color"], linewidth=add_hline["linewidth"])
    
    # modifying y axis
    ax.set_ylim(custom_plot_dict["y_lims"][0],custom_plot_dict["y_lims"][1])
    ax.set_ylabel(custom_plot_dict["y_label"])
    
    custom_y_ticks = [d["y_value"] for d in custom_plot_dict["custom_y_ticks"]]
    custom_y_tick_labels = [d["y_tick_label"] for d in custom_plot_dict["custom_y_ticks"]]
    custom_y_tick_colors = [d["color"] for d in custom_plot_dict["custom_y_ticks"]]
    
    ax.set_yticks(custom_y_ticks)
    ax.set_yticklabels(custom_y_tick_labels)
    
    tick_labels = ax.get_yticklabels()
    for color,label in zip(custom_y_tick_colors,tick_labels):
        label.set_color(color)
        label.set_weight('bold')
    
    # changing plot position
    pos_old = ax.get_position()
    ax.set_position([
        pos_old.x0+custom_plot_dict["plot_position_changes"]["x0_shift"],
        pos_old.y0+custom_plot_dict["plot_position_changes"]["y0_shift"],
        pos_old.width+custom_plot_dict["plot_position_changes"]["x_width_change"],
        pos_old.height+custom_plot_dict["plot_position_changes"]["y_height_change"]
        ])
    
    # retrieving data
    source_data = __getDataPoints(kwargs["module_instance_name"],kwargs["subtable_name"],kwargs["x_name"],kwargs["y_name"],
        kwargs["quantity_column_name"],kwargs["chosen_quantity_name"],kwargs["run_id"])
    x_list = []
    y_list = []
    for name,x,y in source_data:
        x_list.append(x)
        y_list.append(y)
    logger.error(x_list)
    ax.plot(np.array(x_list),np.array(y_list), color='white', marker='o', linestyle='None')
    
    # modifying x axis (here is assumed, that len(data) > 1)
    step_size = (x_list[-1]-x_list[0])/10.
    x_tick_list = np.arange(x_list[0], x_list[-1], step_size)
    ax.set_xlim([x_tick_list[0]-step_size*0.8,x_tick_list[-1]+step_size*0.8])
    ax.set_xticks(x_tick_list)
    if custom_plot_dict["x_is_time"]:
        x_ticklabel_list = [time.asctime(time.gmtime(t)) for t in x_tick_list]
        ax.set_xticklabels(x_ticklabel_list, rotation='vertical', fontsize=9)
    ax.set_xlabel(custom_plot_dict["x_label"])
    
    # saving figure
    img_data = StringIO.StringIO()
    try:
        fig.savefig(img_data, transparent=True)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()

