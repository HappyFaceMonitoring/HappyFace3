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

import hf, os, logging, subprocess, traceback
import cherrypy as cp

authorized_dn_list = []

logger = logging.getLogger()

def init():
    try:
        dn_file_path = os.path.join(hf.hf_dir, hf.config.get('auth', 'dn_file'))
        with open(dn_file_path) as f:
            hf.auth.authorized_dn_list = [line.strip() for line in f if len(line.strip()) > 0]
        cp.engine.autoreload.files.add(dn_file_path)
    except IOError:
        logger.debug("No DN file found for authorization.")

def cert_auth():
    cp.request.cert_authorized = False
    cp.request.cert_info = []
    try:
        s_dn = cp.request.wsgi_environ['SSL_CLIENT_S_DN'].strip()
        i_dn = cp.request.wsgi_environ['SSL_CLIENT_I_DN'].strip()
        cp.request.cert_info = [s_dn, i_dn]
        logging.debug("Subject DN: " + s_dn)
    except KeyError:
        logging.debug("No certificate information found in WSGI environment")
        return
    
    if s_dn in hf.auth.authorized_dn_list:
        cp.request.cert_authorized = True
    try:            
        script_file = hf.config.get('auth', 'auth_script')
        if not cp.request.cert_authorized and len(script_file) > 0:
            script_file = os.path.join(hf.hf_dir, script_file)
            if subprocess.call([script_file, s_dn]) == 1:
                cp.request.cert_authorized = True
    except Exception:
        logging.error("Script authorization failed")
        logging.debug(traceback.format_exc())

    
cp.tools.cert_auth = cp.Tool('before_handler', cert_auth)