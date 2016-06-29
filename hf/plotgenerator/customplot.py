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
import StringIO
import time
import os
import sys
import importlib
import numpy as np
from sqlalchemy.sql import select

@hf.url.absoluteUrl
def getCustomPlotUrl():
    return "/plot/custom/img/"

def __getCustomPlotTemplateDict(module_instance_name):
    """
    This function retrieves a dictionary from the configuration template stored for corresponding module.
    Dictionary's name should be "custom_plot_dict".

    Keys used in the dictionary:

    title: Title of the plot, where placeholders can be used. These should be enclosed by the following marker: [@]
           The placeholders should match exactly the names of the keyword arguments used in the corresponding
           module.
    additional_hlines: Defines additional horizontal lines, which can be added to the plot. This keyword has
                       a list of dictionaries as value. Syntax of one of these dictionaries:
                       {"y_value" : your_y_value, "color" : your_color, "linewidth" : your_linewidth}
                       All values in the dictionary are in matplotlib syntax.
    custom_y_ticks: Can be used to customize the ticks of y-axis. This keyword has a list of dictionaries as value.
                    Syntax of one of these dictionaries:
                    {"y_value" : your_y_value, "color" : your_color, "y_tick_label" : your_y_tick_label}
                    All values in the dictionary are in matplotlib syntax. "y_value" defines where the corresponding
                    "y_tick_label" should be placed.
    plot_position_changes: Can be used to adjust the position of the plot itself in the canvas with respect to the 
                           old position chosen by matplotlib. This keyword has a dictionary as value.
                           Syntax of this dictionary:
                           {"x0_shift" : your_x0_shift, "y0_shift" : your_y0_shift,
                           "x_width_change" : your_x_width_change, "y_height_change" : your_y_height_change}
    curve_style: Defines the style of the plotted curve. This keyword has a dictionary as value.
                 Syntax of this dictionary:
                 {"color" : your_color, "marker" : your_marker, "linestyle" : "your_linestyle}
                 All values in the dictionary are in matplotlib syntax.
    x_is_time: If you use time for x-axis data in time format, an additional formatting on the ticks is applied.
               Possible values: True, False.
    y_lims: Here the lower and upper limit of the y-axis can be chosen. If so, this should be a list with two elements.
    x_label: Label chosen for x-axis.
    y_label: Label chosen for y-axis.

    Minimal example of such a dictionary template you can start from:

    custom_plot_dict = {}

    custom_plot_dict["title"] = ""
    custom_plot_dict["additional_hlines"] = []
    custom_plot_dict["custom_y_ticks"] = []
    custom_plot_dict["plot_position_changes"] = {"x0_shift":0.,"y0_shift": 0., "x_width_change": 0., "y_height_change": 0.}
    custom_plot_dict["curve_style"] = {"color" : "white", "marker" : "o", "linestyle" : "None"}
    custom_plot_dict["x_is_time"] = False
    custom_plot_dict["x_label"] = ""
    custom_plot_dict["y_label"] = ""

    Please use this example to avoid 'KeyError' from an empty dictionary.
    """
    if not hf.module.config.has_section(module_instance_name):
        raise Exception("No such module")

    template_name = module_instance_name + "_template" 
    template_dir = os.path.join(hf.hf_dir, hf.config.get("paths", "customplot_template_dir"))
    sys.path.append(template_dir)
    try:
        template = importlib.import_module(template_name)
    except ImportError:
        raise Exception("No such plot template")
    return template.custom_plot_dict

def __getDataPoints(module_instance_name,subtable_name,x_name,y_name,quantity_column_name,chosen_quantity_name,run_id):
    """
    This function retrieves data from the database. It accepts for now the following format of the data:

    Data must be saved in a subtable of the corresponding module. This subtable should contain columns:

    1) Data for the x axis (as a list).
    2) Data for the y axis (as a list).
    3) Quantity names, which give the y value a meaning (as a list).

    In that way, multiple y-quantities depending on one x-quantity can be stored and chosen for plotting.
    """
    if not hf.module.config.has_section(module_instance_name):
        raise Exception("No such module")

    module_class = hf.module.getModuleClass(hf.module.config.get(module_instance_name, "module"))
    try:
        subtable = module_class.subtables[subtable_name]
    except IndexError:
        raise Exception("No such subtable")

    x_column = [col for col in subtable.columns if col.name == x_name][0]
    y_column = [col for col in subtable.columns if col.name == y_name][0]

    data_point_columns = [x_column,y_column]
    mod_table = subtable.module_class.module_table
    data_point_query = select(data_point_columns, \
        mod_table.c.instance == module_instance_name) \
        .where(subtable.c.parent_id == mod_table.c.id) \
        .where(mod_table.c.run_id == run_id ) \
        .where(getattr(subtable.c, quantity_column_name) == chosen_quantity_name)
    result = data_point_query.execute()
    source_data = result.fetchall()
    if not source_data:
        raise Exception("No data found for used database selection")
    elif len(source_data) == 1:
        raise Exception("Only one datapoint found for used database selection")
    return source_data

def customPlot(**kwargs):
    """
    This is the main function to produce the plot. For now, only one curve per plot is possible.
    Computation of the limits and ticks for x-axis are calculated automaticaly.

    Necessary arguments given by keyword arguments **kwargs built by corresponding .html file:

    module_instance_name: Name of the module instance of the .html file used. Needed to access the corresponding data
                          and configuration.
    subtable_name: Name of the subtable, where the data to be plotted is stored.
    x_name: Name of the column in the subtable, which contains data for the x-axis.
    y_name: Name of the column in the subtable, which contains data for the y-axis.
    quantity_column_name: Name of the column in the subtable, which contains the quantity names
                          defining the meaning of y values.
    chosen_quantity_name: Quantity specified for plotting. Chosen from the names in the column 'quantity_column_name'.
    run_id: Plotting is done only for one explicit run given by the run id. Needed to proper select data.

    Additional arguments can be given to replace 'placeholders' in the title of the plot.
    See 'setting and modifying title'.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()

    # retrieving configuration
    custom_plot_dict = __getCustomPlotTemplateDict(kwargs["module_instance_name"])

    # setting and modifying title
    title = custom_plot_dict["title"]
    placeholder_list = re.findall(r"\[\@\](.*?)\[\@\]", title)
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
    if len(custom_plot_dict["y_lims"]) == 2:
        ax.set_ylim(custom_plot_dict["y_lims"][0],custom_plot_dict["y_lims"][1])
    ax.set_ylabel(custom_plot_dict["y_label"])

    if len(custom_plot_dict["custom_y_ticks"]) > 0:

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
    for x,y in source_data:
        x_list.append(x)
        y_list.append(y)
    ax.plot(np.array(x_list),np.array(y_list), color=custom_plot_dict["curve_style"]["color"],
        marker=custom_plot_dict["curve_style"]["marker"], linestyle=custom_plot_dict["curve_style"]["linestyle"])

    # modifying x axis (here is assumed, that len(data) > 1)
    step_size = (x_list[-1]-x_list[0])/10.
    x_tick_list = np.arange(x_list[0], x_list[-1], step_size)
    ax.set_xlim([x_tick_list[0]-step_size,x_tick_list[-1]+step_size])
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

