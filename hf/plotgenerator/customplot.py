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
import numpy as np
import timeit
from sqlalchemy.sql import select, func, or_
from sqlalchemy import Integer, Float, Numeric
from hf.module.database import hf_runs

@hf.url.absoluteUrl
def getCustomPlotUrl():
    return "/plot/custom/"

def customPlot(category_list, **kwargs):
    
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__ + ".customPlot")
    ylabel_list = ["other", "error", "warning", "ok"]
    color_list = ["gray", "red", "orange", "green"]
    fig, ax = plt.subplots()
    
    for color, statusnumber in zip(color_list, np.arange(1,5)):
        ax.axhline(y=statusnumber, color=color, linewidth=8)
    
    img_data = StringIO.StringIO()
    try:
        fig.savefig(img_data, transparent=True)
        cp.response.headers['Content-Type'] = "image/png"
        return img_data.getvalue()
    finally:
        img_data.close()

