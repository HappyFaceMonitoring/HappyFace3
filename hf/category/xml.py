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
import logging
import traceback
import os
import cherrypy as cp
from mako.template import Template

logger = logging.getLogger(__name__)


def renderXmlOverview(run, template_context):
    '''
    Create a summary of the status of all categories
    and their modules in an XML format.

    Useful for the HappyFace Firefox Icon or the
    HappyFace AndroidApp.
    '''
    try:
        filename = os.path.join(hf.hf_dir,
                                hf.config.get("paths", "hf_template_dir"),
                                "overview.xml")
        template = Template(filename=filename, lookup=hf.template_lookup)
    except Exception, e:
        logger.error("Cannot load XML overview template: %s" % str(e))
        logger.error(traceback.format_exc())
        return u''
    cp.response.headers['Content-Type'] = "text/xml"
    template_context['protocol_host'] = cp.request.base
    return template.render_unicode(**template_context)
