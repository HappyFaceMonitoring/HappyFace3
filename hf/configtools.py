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

import ConfigParser
import os, hf, cherrypy, traceback, logging, subprocess, re
import logging.config
from mako.lookup import TemplateLookup

def _getCfgInDirectory(dir):
    return sorted(filter(lambda x: x.lower().endswith(".cfg") and os.path.isfile(x), map(lambda x:os.path.join(dir,x), os.listdir(dir))))

def _getSvnRevision():
    try:
        try:
            proc = subprocess.Popen(['svnversion'], 0, None, None, subprocess.PIPE)
            return proc.stdout.read().strip()
        finally:
            proc.poll()
            if proc.returncode is None:
                proc.kill()
    except Exception, e:
        return 'exported'

def _getGitSvnRevision():
    """
    Use git-svn to find out local SVN repository revision. Error-checking is quite bad here, it
    will produce 'exported' in that case and logs nothing to the logfiles =(
    """
    try:
        revision = 0
        try:
            proc = subprocess.Popen(['git', 'svn', 'info'], 0, None, None, subprocess.PIPE)
            git_svn_info = proc.stdout.read()
            match = re.search(r"Revision: ([0-9]+)", git_svn_info)
            if match:
                revision = int(match.group(1))
            else:
                return "exported"
        finally:
            proc.poll()
            if proc.returncode is None:
                proc.kill()
        # TODO: possible extensions:
        #     Check for newer git-commits and modifications for displayal
        return str(revision)
    except Exception, e:
        return 'exported'
    
class ConfigDict(dict):
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except IndexError:
            raise hf.ConfigError("Required parameter '{0}' not specified".format(key))
        except KeyError:
            raise hf.ConfigError("Required parameter '{0}' not specified".format(key))

def readConfigurationAndEnv():
    logger = logging.getLogger(__name__)
    
    if hf.__version__ is None:
        hf.__version__ = _getSvnRevision()
        rev_number_regex = re.compile(r"[0-9]+(:[0-9]+)?(M|S|P)*")
        if rev_number_regex.search(hf.__version__) is None:
            hf.__version__ = _getGitSvnRevision()
        if rev_number_regex.search(hf.__version__) is None:
            hf.__version__ = "exported"
            
    '''
    Read configuration files for HappyFace from defaultconf directory and subsequently from
    the local HappyFace config directory. The HappyFace config is then accessible by hf.config
    
    After the default configuration is read, the environment variables are searched for
    HF_DEBUG (controls exception output on webpage, implies HF_LOGLEVEL=DEBUG), HF_LOGLEVEL
    and HF_WGETOPTIONS (extra global options)
    
    Also, read category and module config in hf.category.config and hf.module.config and create
    a template lookup object in hf.template_lookup with the appropriate paths from the configuration.
    '''
    defaults = {}
    
    hf.config = ConfigParser.ConfigParser(defaults=defaults)
    for file in _getCfgInDirectory(os.path.join(hf.hf_dir, "defaultconfig")):
        try:
            hf.config.read(file)
            cherrypy.engine.autoreload.files.add(os.path.join(file))
        except Exception, e:
            logger.exception("Cannot import default config '%s'" % file)
            raise
    if os.path.exists(hf.config.get("paths", "local_happyface_cfg_dir")):
        for file in _getCfgInDirectory(os.path.join(hf.hf_dir, hf.config.get("paths", "local_happyface_cfg_dir"))):
            try:
                hf.config.read(file)
                cherrypy.engine.autoreload.files.add(os.path.join(file))
            except Exception, e:
                logger.exception("Cannot import config '%s'" % file)
                raise
    else:
        logger.info('Configuration directory does not exist, use only defaults')
    
    directories = [hf.config.get("paths", "hf_template_dir"), hf.config.get("paths", "module_template_dir")]
    directories = map(lambda x: os.path.join(hf.hf_dir, x), directories)
    hf.template_lookup = TemplateLookup(directories=directories,
        module_directory=hf.config.get("paths", "template_cache_dir"))
    try:
        import markupsafe
        hf.template_escape_lookup = TemplateLookup(directories=directories,
            module_directory=hf.config.get("paths", "template_cache_dir"), 
            default_filters=["unicode", 'markupsafe.escape'],
            imports=["import markupsafe"])
    except ImportError:
        hf.template_escape_lookup = hf.template_lookup
        logger.warning("Python module 'markupsafe' not found. Web-output will not be HTML escaped!")
    
    if not os.path.exists(hf.config.get("paths", "category_cfg_dir")):
        raise hf.exceptions.ConfigError("Category config directory not found")
    if not os.path.exists(hf.config.get("paths", "module_cfg_dir")):
        raise hf.exceptions.ConfigError("Module config directory not found")
    
    hf.category.config = ConfigParser.ConfigParser()
    category_config_files = os.path.join(hf.hf_dir, hf.config.get("paths", "category_cfg_dir"))
    for file in _getCfgInDirectory(category_config_files):
        try:
            hf.category.config.read(file)
            cherrypy.engine.autoreload.files.add(file)
        except Exception, e:
            logger.error("Cannot parse category config '%s'" % file)
            logger.error(traceback.format_exc())
    
    hf.module.config = ConfigParser.ConfigParser(defaults=hf.module.ModuleBase.config_defaults)
    module_config_files = os.path.join(hf.hf_dir, hf.config.get("paths", "module_cfg_dir"))
    for file in _getCfgInDirectory(module_config_files):
        try:
            hf.module.config.read(file)
            cherrypy.engine.autoreload.files.add(file)
        except Exception, e:
            logger.error("Cannot parse category config '%s'" % file)
            logger.error(traceback.format_exc())
    

def setupLogging(logging_cfg):
    """
    Setup the python logging module and apply loglevel from
    environment variables if specified.
    
    The argument to this function is the name of the configuration key
    in the 'paths' section containing the path to the loggin configuration.
    For the format of the config, please see the Python docs
    http://docs.python.org/library/logging.config.html#configuration-file-format
    
    If None is specified, console logging only is setup. This is particularily
    useful for tools e.g. for migration or cleanup.
    
    The environment variable HF_LOGLEVEL can contain a level from DEFAULT, INFO,
    WARNING, ERROR or CRITICAL. If HF_DEBUG is set, HF_LOGLEVEL=DEBUG is implied.
    """
    if logging_cfg is None:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.config.fileConfig(hf.config.get("paths", logging_cfg), disable_existing_loggers=False)
    if "HF_LOGLEVEL" in os.environ:
        logging.root.setLevel(getattr(logging, os.environ["HF_LOGLEVEL"].upper()))
    if "HF_DEBUG" in os.environ:
        logging.root.setLevel(logging.DEBUG)