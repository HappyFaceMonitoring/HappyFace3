
import hf, threading, time, os, subprocess, shutil, traceback, shlex, re, logging

logger = logging.getLogger(__name__)

class DownloadSlave(threading.Thread):
    def __init__(self, file, global_options, archive_dir):
        threading.Thread.__init__(self)
        self.file = file
        self.archive_dir = archive_dir
        self.global_options = global_options
        
    def run(self):
        try:
            if self.file.url.startswith("file://"):
                path = self.file.url[len("file://"):]
                shutil.copy(path, self.file.file_path)
            else:
                command = "wget --output-document=\"%s\" %s %s \"%s\"" % (self.file.file_path, "" if self.file.config_source == "local" else self.global_options, self.file.options, self.file.url)
                process = subprocess.Popen(shlex.split(command), stderr=subprocess.PIPE)
                stderr = process.communicate()[1]
                if process.returncode != 0:
                    match = re.search("ERROR ([0-9][0-9][0-9])", stderr)
                    http_errorcode = 0
                    if match:
                        http_errorcode = int(match.group(1))
                    self.file.error = "Downloading failed" + " with error code %i"%http_errorcode if http_errorcode>0 else ""
                    try:
                        os.unlink(self.file.file_path)
                    except Exception:
                        pass
        except Exception, e:
            self.file.error += "Failed to download file: %s" % e
            traceback.print_exc()
        except:
            self.file.error += "Failed to download file"
            traceback.print_exc()
            
class DownloadService:
    def __init__(self):
        self.logger = logging.getLogger(self.__module__)
        self.file_list = []
        self.archive_dir = None
        self.archive_url = None
        self.runtime = None
        
    def _addFile(self, file):
        self.file_list.append(file)

    def performDownloads(self, runtime):
        self.global_options = hf.config.get("downloadService", "global_options")
        self.runtime = runtime
        self.archive_dir = os.path.join(hf.config.get("paths", "archive_dir"), runtime.strftime("%Y/%m/%d/%H/%M"))
        self.archive_url = os.path.join(hf.config.get("paths", "archive_url"), runtime.strftime("%Y/%m/%d/%H/%M"))
        
        try:
            os.makedirs(self.archive_dir)
        except Exception, e:
            self.logger.error("Cannot create archive directory")
            self.logger.debug(traceback.format_exc())
            raise Exception("Cannot create archive directory")
        slaves = [DownloadSlave(file, self.global_options, self.archive_dir) for file in self.file_list]
        
        tmp_dir = hf.config.get("paths", "tmp_dir")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        
        file_prefix = os.path.join(tmp_dir, runtime.strftime("%Y%m%d_%H%M%s_"))
        
        timeout = hf.config.getint("downloadService", "timeout")
        
        for number, slave in enumerate(slaves):
            slave.file.file_path = os.path.abspath(file_prefix + "%03i.download"%number)
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
    
    def cleanup(self):
        for file in self.file_list:
            if not file.keep and hasattr(file, "file_path"):
                if os.path.exists(file.file_path) > 0:
                    os.unlink(file.file_path)
        
    class DownloadFile:
        def __init__(self, download_command):
            try:
                self.download_command = download_command
                self.config_source, self.options, self.url = download_command.split("|")
                self.config_source = self.config_source.lower()
                if self.config_source == "global":
                    self.options = ""
            except ValueError:
                raise hf.ConfigError("Download command string malformed")
            hf.downloadService._addFile(self)
            self.is_downloaded = False
            self.error = ""
            self.file_path = ""
            self.file_url = ""
            self.keep = False
        
        def isDownloaded(self):
            return self.is_downloaded
        
        def errorOccured(self):
            return len(self.error) > 0
            
        def getFile(self):
            return open(self.getFilePath(), "r")
            
        def getFilePath(self):
            return self.file_url
        
        def getFileUrl(self):
            return self.file_path
        
        def getSourceUrl(self):
            return self.url
        
        def copyToArchive(self, name):
            logging.debug('%s %s %s %s' % (name, self.isDownloaded(), self.errorOccured(), self.file_path))
            if self.isDownloaded() and not self.errorOccured():
                self.keep = True
                dest = os.path.join(hf.downloadService.archive_dir, name)
                shutil.move(self.file_path, dest)
                self.file_path = dest
                self.file_url = os.path.join(hf.downloadService.archive_url, name)
    
    
    
downloadService = DownloadService()