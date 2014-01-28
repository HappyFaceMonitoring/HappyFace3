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


def staticUrl(file):
    return join(hf.config.get("paths", "static_url"), file)


def join(url, suffix):
    if len(suffix) == 0:
        return url
    if len(url) == 0:
        return suffix
    if url[-1] != "/" and suffix[0] != "/":
        url = url+"/"
    elif url[-1] == "/" and suffix[0] == "/":
        url = url[0:-1]
    return url+suffix


def absoluteUrl(arg):
    """
    Decorator!
    Take an URL that is relative to the root URL
    of happyface and make it absolute respective to
    that root URL
    """
    def joinCfg(*args, **kwargs):
        return join(hf.config.get("paths", "happyface_url"),
                    arg(*args, **kwargs))
    if isinstance(arg, str):
        return join(hf.config.get("paths", "happyface_url"),
                    arg)
    return joinCfg


def get(**kwargs):
    """
    Generate a GET line from a dictionary
    """
    opt_list = [(key, val)
                for key, val in kwargs.iteritems()
                if type(val) is not list and type(val) is not tuple]
    for key, val in kwargs.iteritems():
        if type(val) is not list and type(val) is not tuple:
            continue
        opt_list.extend((key, v) for v in val)
    return u"?" + u"&".join(unicode(key) + "=" + unicode(val)
                            for key, val in opt_list)


def create_link_here(additional_get_params):
    """
    Create a link pointing to the currently requested page
    (relative URL with GET parameters) and append any
    specified parameters from the input dictionary.
    """
    params = cp.request.params
    params.update(additional_get_params)
    query = get(**params)
    url = hf.url.join(cp.request.script_name,
                      cp.request.path_info)
    return url + (query if len(params) else "")

