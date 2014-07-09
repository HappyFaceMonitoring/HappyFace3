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
from cherrypy.lib.static import serve_file
import hf
import datetime
import time
import logging
import traceback
import os
import subprocess
from hf.module.database import hf_runs
import hf.plotgenerator
from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from mako.template import Template
from datetime import timedelta
from cherrypy import _cperror


class RootDispatcher(object):
    """
    The main HF Dispatcher
    """
    _cp_config = {
        'tools.cert_auth.on': True,
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.switch_css.on': True,
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.category_list = hf.category.createCategoryObjects()
        self.category = hf.category.Dispatcher(self.category_list)
        self.ajax = hf.category.AjaxDispatcher(self.category_list)
        self.plot = hf.plotgenerator.Dispatcher(self.category_list)
        self.upload = hf.upload.Dispatcher()
        self.module_map = {}
        for category in self.category_list:
            for module in category.module_list:
                self.module_map[module.instance_name] = module
        cp.config.update({
            'error_page.default': self.errorPage,
        })

    @cp.expose
    def index(self):
        raise cp.HTTPRedirect(hf.url.join(hf.config.get('paths',
                                                        'happyface_url'),
                                          'category'))

    @cp.expose
    @cp.tools.caching()
    def static(self, *args):
        cp.lib.caching.expires(secs=timedelta(1), force=True)

        path = os.path.join(hf.hf_dir,
                            hf.config.get('paths', 'static_dir'),
                            *args)
        # archive/Y/M/D/H/M/file -> 7
        if len(args) == 7 and args[0] == 'archive':
            authorized = self.archiveFileAuthorized(args[6])
            if authorized:
                return serve_file(path)
            else:
                raise cp.HTTPError(status=403, message="You are not allowed to access this resource.")
        else:
            return serve_file(path)

    def archiveFileAuthorized(self, filename):
        for instance, module in self.module_map.iteritems():
            if filename.startswith(instance):
                return not module.isUnauthorized()
        self.logger.warning("""Unable to map file '%s' to module!
Perhaps the corresponding module was removed from the HF config or the file does not start with the module instance name (this is an error in the module).""" % filename)
        return False

    def errorPage(self, **kwargs):
        self.logger.debug(_cperror.format_exc())
        try:
            args = {
                "message": kwargs['status'],
                "details": "Please consult the log files for more information.",
                "hint": '',
                "automatic_reload": False,
            }
            exception_class = _cperror._exc_info()[0]
            if issubclass(exception_class, DatabaseError):
                args['details'] = "An database error occured, please consult the log files."
                args['hint'] = "Maybe the database schema needs to be updated after an code update?"
            elif args["message"].startswith("4"):
                args["details"] = kwargs["message"]

            try:
                template_context, category_dict, run = self.category.prepareDisplay()
                template_context.update(args)

                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "error.html")
                template = Template(filename=filename, lookup=hf.template_lookup)
                return template.render_unicode(**template_context).encode("utf-8")

            except Exception, e:
                self.logger.debug("Fancy error page generation failed\n" + traceback.format_exc())
                filename = os.path.join(hf.hf_dir, hf.config.get("paths", "hf_template_dir"), "plain_error.html")
                template = Template(filename=filename, lookup=hf.template_lookup)
                return template.render_unicode(**args).encode("utf-8")

        except Exception, e:
            self.logger.error(u"error page generation failed: " + unicode(e))
            self.logger.error(traceback.format_exc())
            return u"""<h1>Error Inception</h1>
            <p>An error occured while displaying an error. Embarrasing.</p>
            <p>Please consult the log files!</p>""".encode("utf-8")


class CachegrindHandler(cp.dispatch.LateParamPageHandler):
    """Callable which profiles the subsequent handlers and writes the results to disk.

    Based on _`http://tools.cherrypy.org/wiki/Cachegrind`
    """

    def __init__(self, next_handler):
        self.next_handler = next_handler

    def __call__(self):
        """
        Profile this request and output results in a cachegrind compatible format.
        """
        import cProfile
        try:
            import lsprofcalltree
        except ImportError:
            import hf.external.lsprofcalltree as lsprofcalltree
        try:
            p = cProfile.Profile()
            p.runctx('self._real_call()', globals(), locals())
        finally:
            count = 1
            filename = None
            path = cp.request.path_info.strip("/").replace("/", "_")
            script = cp.request.app.script_name.strip("/").replace("/", "_")
            path = path + "_" + script
            while not filename or os.path.exists(filename):
                filename = os.path.join(hf.hf_dir, "cachegrind.out.%s_%d" % (path, count))
                count += 1
            print "writing profile output to %s" % filename
            k = lsprofcalltree.KCacheGrind(p)
            data = open(filename, 'w+')
            k.output(data)
            data.close()
        return self.result

    def _real_call(self):
        """Call the next handler and store its result."""
        self.result = self.next_handler()


def cachegrind():
    """A CherryPy 3 Tool for loading Profiling requests.

    To enable the tool, just put something like this in a
    HappyFace configuration file:

    .. code-block:: ini

        [/category]
        tools.cachegrind.on = True

    This will enable profiling of the CherryPy code only for the category pages,
    not static content or the plot generator. As a result the performance
    impact is reduced and no files with uninteressting data are created.
    """
    cp.request.handler = CachegrindHandler(cp.request.handler)

# Priority of 100 is meant to ensure that this tool runs later than all others, such that
# CachegrindHandler wraps all other handlers and therefore can profile them along with
# the controller.
cp.tools.cachegrind = cp.Tool('before_handler', cachegrind, priority=100)
