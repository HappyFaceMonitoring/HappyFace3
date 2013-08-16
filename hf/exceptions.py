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


class ConfigError(Exception):
    pass


class ConsistencyError(Exception):
    pass


class ModuleError(Exception):
    pass


class ModuleRuntimeError(Exception):
    pass


class DownloadError(Exception):
    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "Download of %s failed: %s" % (self.file.url, self.file.error)

    def __unicode__(self):
        return u"Download of %s failed: %s" % (self.file.url, self.file.error)


class ModuleProgrammingError(Exception):
    def __init__(self, module, msg):
        self.module = module
        super(ModuleProgrammingError, self).__init__(msg)

    def __str__(self):
        return "%s: %s" % (self.module, super(ModuleProgrammingError, self).__str__())

    def __unicode__(self):
        return "%s: %s" % (self.module, super(ModuleProgrammingError, self).__unicode__())
