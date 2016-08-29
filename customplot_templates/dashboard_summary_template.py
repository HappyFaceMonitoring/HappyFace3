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

import numpy as np

custom_plot_dict = {}

custom_plot_dict["title"] = "Metric [@]chosen_quantity_name[@] for [@]tier_name[@]"

custom_plot_dict["additional_hlines"] = []

custom_plot_dict["y_lims"] = [0.5,4.5]
custom_plot_dict["y_label"] = ""
custom_plot_dict["custom_y_ticks"] = []

custom_plot_dict["plot_position_changes"] = {"x0_shift":0.,"y0_shift": 0.3, "x_width_change": 0.0, "y_height_change":-0.3}

custom_plot_dict["x_is_time"] = True
custom_plot_dict["x_label"] = "UTC Time"

custom_plot_dict["curve_style"] = {"color" : "white", "marker" : "o", "linestyle" : "None"}

color_list = ["gray", "red", "orange", "green"]
y_tick_label_list = ["other", "error", "warning", "ok"]

for color, y_tick_label, statusnumber in zip(color_list, y_tick_label_list, np.arange(1,5)):
    custom_plot_dict["additional_hlines"].append({"y_value" : statusnumber, "color" : color, "linewidth" : 8})
    custom_plot_dict["custom_y_ticks"].append({"y_value" : statusnumber, "color" : color, "y_tick_label" : y_tick_label})
