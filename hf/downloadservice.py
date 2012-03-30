
import hf, threading, time, os, subprocess, shutil, traceback

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
                shutil.copy(path, self.file.filename)
            else:
                command = "wget --output-document=\"%s\" %s %s \"%s\"" % (self.file.filename, "" if self.file.config_source == "local" else self.global_options, self.file.options, self.file.url)
                subprocess.call(command, shell=True)
        except Exception, e:
            self.file.error += "Failed to download file: %s" % e
            traceback.print_exc()
        except:
            self.file.error += "Failed to download file"
            traceback.print_exc()
            
class DownloadService:
    def __init__(self):
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
            # TODO logging
            pass
        slaves = [DownloadSlave(file, self.global_options, self.archive_dir) for file in self.file_list]
        
        timeout = hf.config.getint("downloadService", "timeout")
        
        file_prefix = os.path.join(hf.config.get("paths", "tmp_dir"), runtime.strftime("%Y%m%d_%H%M%s"))
        
        for number, slave in enumerate(slaves):
            slave.file.filename = file_prefix + "%03i.download"%number
            slave.start()
        
        for slave in slaves:
            start_time = int(time.time())
            slave.join(timeout)
            if slave.isAlive():
                # timeout occured
                break
            timeout -= int(time.time()) - start_time
        
        for slave in slaves:
            if slave.isAlive():
                slave.file.error += "Download didn't finish in time"
                slave._Thread__stop()
            else:
                slave.file.is_downloaded = True
    
    def cleanup(self):
        for file in self.file_list:
            if not file.keep:
                os.unlink(file.filename)

    class DownloadFile:
        def __init__(self, downloadCommand):
            try:
                self.config_source, self.options, self.url = downloadCommand.split("|")
                self.config_source = self.config_source.lower()
                if self.config_source == "global":
                    self.options = ""
            except ValueError:
                raise hf.ConfigError("Download command string malformed")
            hf.downloadService._addFile(self)
            self.is_downloaded = False
            self.error = ""
            self.filename = ""
            self.keep = False
        
        def isDownloaded(self):
            return self.is_downloaded
        
        def errorOccured(self):
            return len(self.error) > 0
            
        def getFile(self):
            return None
        
        def getFilename(self):
            return self.filename
        
        def getSourceUrl(self):
            return self.url
        
        def copyToArchive(self, name):
            self.keep = True
            dest = os.path.join(hf.downloadService.archive_dir, name)
            shutil.move(self.filename, dest)
            self.filename = os.path.join(hf.downloadService.archive_url, name)
    
    
    
downloadService = DownloadService()