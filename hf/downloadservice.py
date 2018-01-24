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
"""
"""

import hf
import threading
import time
import os
import subprocess
import shutil
import traceback
import shlex
import re
import inspect
import logging
import urllib2
import httplib

logger = logging.getLogger(__name__)


class DownloadSlave(threading.Thread):
    def __init__(self, file, global_options, archive_dir):
        threading.Thread.__init__(self)
        self.file = file
        self.archive_dir = archive_dir

        self.options = file.options
        if file.config_source != "local":
            self.options += " " + global_options

    def run(self):
        try:
            if self.file.url.startswith("file://"):
                path = self.file.url[len("file://"):]
                shutil.copy(path, self.file.getTmpPath(True))
            elif '<native>' not in self.options:
                self._download_wget()
            else:
                self._download_native()
        except Exception, e:
            self.file.error += "Failed to download file: %s" % e
            traceback.print_exc()
        except:
            self.file.error += "Failed to download file"
            traceback.print_exc()

    def _download_wget(self):
        command = "wget --output-document=\"%s\" %s \"%s\"" % \
                  (self.file.getTmpPath(True),
                   self.options,
                   self.file.url
                   )
        process = subprocess.Popen(shlex.split(command), stderr=subprocess.PIPE)
        stderr = process.communicate()[1]
        if process.returncode != 0:
            match = re.search("ERROR ([0-9][0-9][0-9])", stderr)
            http_errorcode = 0
            if match:
                http_errorcode = int(match.group(1))
            self.file.error = "Downloading failed"
            if http_errorcode != 0:
                self.file.error += " with error code %i" % http_errorcode
            try:
                os.unlink(self.file.getTmpPath(True))
            except Exception:
                pass

    def _download_native(self):
        # monkey patch for python 2.7.9+
        # see https://bugs.python.org/issue22417
        import ssl
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

        proxy_fn = hf.config.get('downloadService', 'voms_proxy_file')
        if proxy_fn == '$X509_USER_PROXY':
            proxy_fn = os.environ['X509_USER_PROXY']

        https_opener = self._HTTPSAuthHandler.build_opener(proxy_fn)
        response = https_opener.open(self.file.url)
        with open(self.file.getTmpPath(True), 'w') as out_f:
            out_f.write(response.read())

    class _HTTPSAuthHandler(urllib2.HTTPSHandler):
        def __init__(self, proxy_fn):
            urllib2.HTTPSHandler.__init__(self)
            self.proxy_fn = proxy_fn

        def https_open(self, request):
            return self.do_open(self.get_connection, request)

        def get_connection(self, host, **kwargs):
            return httplib.HTTPSConnection(host,
                                           key_file=self.proxy_fn,
                                           cert_file=self.proxy_fn)

        @classmethod
        def build_opener(cls, proxy_fn):
            return urllib2.build_opener(cls(proxy_fn))


class DownloadService:
    '''
    The globaly shared download service, available as the
    singleton *hf.downloadService*.

    Note when copying files to the archive directory:
    The name must start with the name of the module instance,
    otherwise certificate auth will always disable the file!
    '''

    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.file_list = {}
        self.module_files = {}
        self.archive_dir = None
        self.archive_url = None
        self.remote_archive_dir = None
        self.clean_local_archive_dir = False
        self.runtime = None

    def addDownload(self, download_command):
        if download_command in self.file_list:
            return self.file_list[download_command]
        self.file_list[download_command] = DownloadFile(download_command)
        # get calling module from stack and remember the module<->file association
        frame = inspect.stack()[1]
        module = frame[0].f_locals.get('self', None)
        if module:
            try:
                self.module_files[module.instance_name].append(download_command)
            except KeyError:
                self.module_files[module.instance_name] = [download_command]
            except AttributeError:
                # not called by a HappyFace module. Strange, but might happen!
                pass
        return self.file_list[download_command]

    def performDownloads(self, runtime):
        try:
            self.global_options = hf.config.get("downloadService", "global_options")
            self.runtime = runtime
            self.archive_dir = os.path.join(hf.config.get("paths", "archive_dir"), self.getDatePath(runtime))
            self.archive_url = os.path.join(hf.config.get("paths", "archive_url"), self.getDatePath(runtime))
            if hf.config.get('paths', 'remote_archive_dir'):
                self.remote_archive_dir = os.path.join(hf.config.get('paths', 'remote_archive_dir'),
                                                       self.getDatePath(runtime))
                clean = hf.config.get('paths', 'clean_local_archive_dir')
                self.clean_local_archive_dir = (clean.lower() == 'true')

            try:
                os.makedirs(self.archive_dir)
            except Exception, e:
                self.logger.error("Cannot create archive directory")
                self.logger.error(traceback.format_exc())
                raise Exception("Cannot create archive directory")
            slaves = [DownloadSlave(file, self.global_options, self.archive_dir)
                      for file in self.file_list.itervalues()]

            tmp_dir = hf.config.get("paths", "tmp_dir")
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)

            file_prefix = os.path.join(tmp_dir, runtime.strftime("%Y%m%d_%H%M%s_"))

            timeout = hf.config.getint("downloadService", "timeout")

            for number, slave in enumerate(slaves):
                slave.file.tmp_filename = os.path.abspath(file_prefix + "%03i.download" % number)
                slave.start()

            for slave in slaves:
                start_time = int(time.time())
                slave.join(timeout)
                timeout -= int(time.time()) - start_time
                if timeout <= 0 or slave.isAlive():
                    self.logger.info("Download timeout!")
                    break

            for slave in slaves:
                if slave.isAlive():
                    slave.file.error += "Download didn't finish in time"
                    slave._Thread__stop()
                    self.logger.info("Download timeout for %s" % slave.file.download_command)
                elif not slave.file.errorOccured():
                    slave.file.is_downloaded = True
        except Exception, e:
            for file in self.file_list.itervalues():
                file.error = str(e)
            raise

    def getArchivePath(self, run, filename):
        return os.path.join(hf.config.get('paths', 'archive_dir'), self.getDatePath(run['time']), filename)

    def getArchiveUrl(self, run, filename):
        return os.path.join(hf.config.get('paths', 'archive_url'), self.getDatePath(run['time']), filename)

    def cleanup(self):
        for file in self.file_list.itervalues():
            if not file.keep_tmp and file.isDownloaded():
                if os.path.exists(file.getTmpPath()):
                    os.unlink(file.getTmpPath())

        if self.clean_local_archive_dir:
            archive_dir = hf.config.get("paths", "archive_dir")
            for filename in os.listdir(archive_dir):
                filepath = os.path.join(archive_dir, filename)
                if os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                elif os.path.isfile(filepath):
                    os.unlink(filepath)

    def getFilesForInstance(self, instance):
        if hasattr(instance, "instance_name"):
            instance = instance.instance_name
        try:
            download_commands = self.module_files[instance]
        except KeyError:
            return []
        return [self.file_list[cmd] for cmd in download_commands]

    @staticmethod
    def getDatePath(date):
        return date.strftime("%Y/%m/%d/%H/%M")

class DownloadFile:
    def __init__(self, download_command):
        try:
            self.download_command = download_command
            self.config_source, self.options, self.url = download_command.split("|")
            self.config_source = self.config_source.lower()
            if self.config_source == "global":
                self.options = ""
            self.tried_download = False
        except ValueError:
            raise hf.ConfigError("Download command string malformed")
        self.is_downloaded = False
        self.error = ""
        self.file_path = ""
        self.file_url = ""
        self.keep_tmp = False
        self.is_archived = False

    def isDownloaded(self):
        return self.is_downloaded

    def isArchived(self):
        return self.is_archived

    def errorOccured(self):
        return len(self.error) > 0

    def getFile(self):
        return open(self.getTmpPath(), "r")

    @hf.url.absoluteUrl
    def getTmpUrl(self):
        if hf.config.get('paths', 'tmp_url'):
            return hf.url.join(hf.config.get('paths', 'tmp_url'),
                                self.getTmpFilename())
        else:
            return "file://"+self.tmp_filename

    def getTmpPath(self, no_exception=False):
        """
        :arg no_exception: default False. If set to True, no exception is thrown
                           when there was a problem while downloading the file.
        """
        if (not self.isDownloaded() or self.errorOccured()) and not no_exception:
            raise hf.DownloadError(self)
        try:
            return os.path.join(self.tmp_filename)
        except AttributeError:
            if not no_exception:
                raise hf.DownloadError(self)

    def getArchivePath(self):
        if not self.isDownloaded() or self.errorOccured():
            raise hf.DownloadError(self)
        try:
            return os.path.join(hf.downloadService.archive_dir, self.filename)
        except AttributeError:
            raise hf.DownloadError(self)

    @hf.url.absoluteUrl
    def getArchiveUrl(self):
        if not self.isDownloaded() or self.errorOccured():
            raise hf.DownloadError(self)
        try:
            return hf.url.join(hf.downloadService.archive_url, self.filename)
        except AttributeError:
            raise hf.DownloadError(self)

    def getArchiveFilename(self):
        if not self.isDownloaded() or self.errorOccured():
            raise hf.DownloadError(self)
        return self.filename

    def getTmpFilename(self):
        if not self.isDownloaded() or self.errorOccured():
            raise hf.DownloadError(self)
        return os.path.basename(self.tmp_filename)

    def getSourceUrl(self):
        return self.url

    def copyToArchive(self, module, name):
        ''' Copy the file to the archive directory. The name is prefixed
        with the instance name of the module, thus the name should be always
        unique and the file can be associated with the module.
        '''
        if self.isDownloaded() and not self.errorOccured() and not self.isArchived():
            self.is_archived = True
            self.filename = module.instance_name + name
            shutil.copy(self.getTmpPath(), self.getArchivePath())

            remote_archive_path = hf.downloadService.remote_archive_dir
            if remote_archive_path:
                # scp to remote archive path
                remote_archive_path = os.path.join(remote_archive_path, self.filename)
                remote, rdir =  remote_archive_path.split(':')
                rdir = os.path.dirname(rdir)
                # make sure the remote directory exists
                subprocess.call(['ssh', remote, 'mkdir -p '+rdir])
                subprocess.call(['scp', '-q', self.getTmpPath(), remote_archive_path])


class File:
    def __init__(self, run, name):
        self.name = os.path.basename(name)
        self.run = run

    def getArchivePath(self):
        return hf.downloadService.getArchivePath(self.run, self.name)

    def getArchiveUrl(self):
        return hf.downloadService.getArchiveUrl(self.run, self.name)

    def getArchiveFilename(self):
        return self.name

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, repr(self.run), repr(self.name))

    def __str__(self):
        return self.getArchiveUrl()

    def __unicode__(self):
        return self.getArchiveUrl()

downloadService = DownloadService()
