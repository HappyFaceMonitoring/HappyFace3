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
import logging
from crypt import crypt
import cherrypy as cp
from cherrypy.lib import httpauth


class Dispatcher(object):
    _cp_config = {}

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enabled = hf.config.get("upload", "enabled").lower() == "true"
        self.realm = hf.config.get("upload", "realm")
        self.method = hf.config.get("upload", "auth_method")
        self.htpasswd_file = hf.config.get("upload", "htpasswd")
        self.directory = hf.config.get("upload", "directory")
        try:
            os.makedirs(self.directory)
        except OSError, e:
            # ignore error if it is "file exists (errno 17)"
            if e.errno != 17:
                raise
        # Do this to display error right after startup, if necessary
        try:
            with open(self.htpasswd_file) as f:
                    pass
        except FileNotFoundError:
            if self.enabled:
                self.logger.error("Cannot open htpasswd!")

        Dispatcher._cp_config.update(
            {
                "tools.auth_basic.on": True,
                "tools.auth_basic.realm": self.realm,
                "tools.auth_basic.checkpassword": self.checkBasicPassword,
            })

    def checkBasicPassword(self, realm, username, password):
        if realm != self.realm:
            return False
        cred = self.getCredentials()
        try:
            enc_pw = cred[username]
            given_pw = crypt(password, enc_pw)
            if given_pw == enc_pw:
                return True
            elif not given_pw:
                self.logger.error("Failed to encrypt password with given\
salt, maybe algorithm is not supported?\
 User: {0}, Hash: {1}".format(username, enc_pw))
        except IndexError:
            return False
        return False

    def getCredentials(self):
        if not self.enabled:
            return {}
        credentials = {}
        try:
            with open(self.htpasswd_file) as f:
                for line in f:
                    line = line.strip()
                    try:
                        user, passwd = line.split(":")
                    except Exception:
                        continue
                    credentials[user] = passwd
        except FileNotFoundError:
            self.logger.error("Cannot open htpasswd!")
        return credentials

    @cp.expose
    def default(self, file=None):
        if not self.enabled:
            raise cp.HTTPError(404)
        if not cp.request.login:
            raise cp.HTTPError(403)
        if file:
            filename = os.path.join(self.directory,
                                    # prevent name forgery attacks
                                    os.path.basename(file.filename)
                                    )
            with open(filename, "wb") as new_file:
                while True:
                    tschunk = file.file.read(8192)
                    if not tschunk:
                        break
                    new_file.write(tschunk)
            return u"File upload successful"
        else:
            return u"No file!"
