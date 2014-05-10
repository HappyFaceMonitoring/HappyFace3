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
import os
import cherrypy as cp
import logging
from time import time
from email.utils import formatdate

logger = logging.getLogger()


def init():
    try:
        dn_file_path = os.path.join(hf.hf_dir,
                                    hf.config.get('auth', 'dn_file'))
        with open(dn_file_path) as f:
            hf.auth.authorized_dn_list = [line.strip() for line in f
                                          if len(line.strip()) > 0]
        cp.engine.autoreload.files.add(dn_file_path)
    except IOError:
        logger.debug("No DN file found for authorization.")

# list compiled with fragments from
# http://www.useragentstring.com/pages/Mobile%20Browserlist/
__mobile_useragent_fragments = (
    'android', 'blackberry', 'blazer', 'bolt', 'symbian', 's60', 'series60',
    'doris', 'dorothy', 'fennec', 'gobrowser', 'windows phone', 'iemobile',
    'iris', 'maemo', 'mib', 'minimo', 'netfront', 'opera mini', 'symbos',
    'opera mobi', 'skyfire', 'teashark', 'uzardweb'
)


def autoselect_css():
    if "User-Agent" in cp.request.headers:
        useragent = cp.request.headers["User-Agent"].lower()
        mobile_browser = any(fragment in useragent
                             for fragment in __mobile_useragent_fragments)
    else:
        mobile_browser = False
    return hf.config.get("paths", "hf_mobile_css"
                         if mobile_browser else
                         "hf_default_css")


def __set_css_handler__():
    if "css" in cp.request.params:
        logger.error("CSS GET parameter set: {0}".format(repr(cp.request.params["css"])))
        set_css(cp.request.params["css"])
        del cp.request.params["css"]
    else:
        css = ''
        if "css" in cp.request.cookie:
            css = cp.request.cookie["css"].value
        if not css:
            css = autoselect_css()
        if not css:
            css = hf.config.get("paths", "hf_default_css")
        cp.request.hf_css = css


def set_css(css_file):
    cp.response.cookie["css"] = css_file if css_file else ""
    cp.response.cookie["css"]["expires"] = (formatdate(time() + 30758400,
                                                       usegmt=True)
                                            if css_file else 0)
    cp.response.cookie["css"]["version"] = 1
    cp.response.cookie["css"]["path"] = hf.config.get("paths", "happyface_url")
    cp.request.hf_css = css_file if css_file else autoselect_css()

cp.tools.switch_css = cp.Tool('before_request_body', __set_css_handler__)
