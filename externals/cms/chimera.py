#!/usr/bin/python

# This script creates an XML file joins information from both a chimera dump
# and DBS to find out how many files are staged, pinned, etc. for each dataset
# individually.

import ConfigParser
import optparse
import subprocess
import urllib2
import xml.sax
import calendar
import time
import sys
import bz2
import os

# DBSAPI refuses to work otherwise when it is run by cron
os.environ['USER'] = 'hilfeomgcmssoftwarefrickel'

# Find dbsapi relative to the main script
root = os.path.dirname(os.path.abspath(os.path.normpath(sys.argv[0])))
sys.path.insert(0, os.path.join(root, 'dbsapi'))

class MaxTimeElapsed(Exception):
    def __str__(self):
        return "Maximum execution time reached"

# File in chimera dump.
class File:
    def __init__(self, size = -1, dataset = None):
        self.size = size
	self.dataset = dataset

class Config:
    def __init__(self, filename):
	config = ConfigParser.ConfigParser()
	config.read(filename)

	self.input_directory = self.get_default(config, 'chimera', 'input_directory', '')
	self.cache_directory = self.get_default(config, 'chimera', 'cache_directory', os.path.dirname(filename))
	self.output_file = self.get_default(config, 'chimera', 'output_file', '')
	self.log_file = self.get_default(config, 'chimera', 'log_file', 'most_recent_real_run.log')
	self.upload_url = self.get_default(config, 'chimera', 'upload_url', '')
	self.password = self.get_default(config, 'chimera', 'password', '')
	self.unassigned_file = self.get_default(config, 'chimera', 'unassigned_file', '')
	self.max_time = float(self.get_default(config, 'chimera', 'max_time', '-1'))
	self.latest_pool = self.get_default(config, 'chimera', 'latest_pool', 'chimera_pool_latest')
	self.latest_dump = self.get_default(config, 'chimera', 'latest_dump', 'chimera_dump_latest')

    def get_default(self, parser, section, option, default):
        try:
	    return parser.get(section, option)
        except:
	    return default

# XML parser callback handler, merging filesizes into file<->dataset mapping
class SizeHandler(xml.sax.ContentHandler):
    def __init__(self, files):
        self.files = files

        self.entry_name = None
        self.entry_size = None
        self.subtag = None

    def startElement(self, name, attrs):
        if name == 'entry':
	    self.entry_name = attrs['name']
	if self.entry_name is not None:
	    self.subtag = name

    def characters(self, content):
	if self.subtag == 'size':
	    self.entry_size = int(content)

    def endElement(self, name):
        if self.subtag is not None and self.subtag == name:
	    self.subtag = None
	elif name == 'entry':
            if self.entry_name.startswith('/pnfs/gridka.de/cms/store/'):
	        index = self.entry_name[19:]
	        if not index in self.files:
		    # Seems this file is not in DBS
	            self.files[index] = File(size = self.entry_size)
	        else:
	            self.files[index].size = self.entry_size

            self.entry_size = None
            self.entry_name = None

# XML parser callback handler, summing up files and sizes
class Handler(xml.sax.ContentHandler):
    class Record:
        def __init__(self):
	    self.data = {}
            self.data['bare_total_files'] = 0
	    self.data['bare_total_size'] = 0
	    self.data['bare_on_disk_files'] = 0
	    self.data['bare_on_disk_size'] = 0
	    self.data['total_on_disk_files'] = 0
	    self.data['total_on_disk_size'] = 0
	    self.incomplete_sizes = 0

    def __init__(self, files):
        self.files = files
        self.records = {}

        self.total_entries = set()
        self.disk_entries = set()

        self.entry_name = None
        self.entry_size = None
        self.entry_location = None
        self.subtag = None

    def startElement(self, name, attrs):
        if name == 'entry':
	    self.entry_name = attrs['name']
	if self.entry_name is not None:
	    self.subtag = name

    def characters(self, content):
	if self.subtag == 'size':
	    self.entry_size = int(content)
	if self.subtag == 'dCache:location':
	    self.entry_location = content

    def endElement(self, name):
        if self.subtag is not None and self.subtag == name:
	    self.subtag = None
        if name == 'entry':
            on_tape = on_read_pool = on_write_pool = False
            if self.entry_location is not None:
                on_tape = self.entry_location.startswith('osm://')
                on_read_pool = self.entry_location.endswith('rT_cms')
                on_write_pool = self.entry_location.endswith('wT_cms')

            # Ignore disk-only
            if self.entry_name.startswith('/pnfs/gridka.de/cms/store/'):
	        index = self.entry_name[19:]

		if not index in self.files or self.files[index].dataset is None:
		    dataset = 'Unassigned'
		    if index in self.files:
		        self.files[index].dataset = None
		    else:
		        self.files[index] = File(dataset=None)
		else:
		    dataset = self.files[index].dataset

		if not dataset in self.records:
		    self.records[dataset] = Handler.Record()

		# Get entry size directly from <size> or from pre-parsed
		# dump in self.files[index]['size'] as a fallback
                entry_size = 0
		if self.entry_size is not None:
		    entry_size = self.entry_size
		    if index in self.files:
		        self.files[index].size = entry_size
		    else:
		        self.files[index] = File(size = entry_size)
		elif index in self.files and self.files[index].size != -1:
		    entry_size = self.files[index].size
		else:
		    if not self.entry_name in self.total_entries:
		        # Could not get size for this file, annotate in XML
		        self.records[dataset].incomplete_sizes += 1

                if not self.entry_name in self.total_entries:
                    self.records[dataset].data['bare_total_files'] += 1
                    self.records[dataset].data['bare_total_size'] += entry_size
                    self.total_entries.add(self.entry_name)

                if on_read_pool:
                    self.records[dataset].data['total_on_disk_files'] += 1
                    self.records[dataset].data['total_on_disk_size'] += entry_size

                    if not self.entry_name in self.disk_entries:
                        self.records[dataset].data['bare_on_disk_files'] += 1
                        self.records[dataset].data['bare_on_disk_size'] += entry_size
                        self.disk_entries.add(self.entry_name)

            self.entry_size = None
            self.entry_location = None
            self.entry_name = None

def query_chimera_dump(config, last_modified_file):
    prev_timestamp = 0
    try:
        prev_timestamp = int(file(last_modified_file, 'r').read())
    except:
        pass

# [2010-08-13] The code commented out below looks for compressed XML files in
# the input directory. However when decompressing them we experienced some
# python/bzip2 incompatibility which caused the script to abort. So we are
# using uncompressed XML files now.

#    url = config.input_directory
#    most_recent = None
#    most_recent_dump_path = None
#    most_recent_pool_path = None

#    for filename in os.listdir(url):
#        # Only scan dumps
#        if not filename.startswith('chimera_dump'):
#	    continue

#        path = url + '/' + filename
#	timestamp = os.stat(path).st_mtime
#	if timestamp > prev_timestamp and (most_recent == None or timestamp > most_recent):
#	    # The dump is more recent than the one we scanned the last time
#	    # Check whether there is also a sizes file.
#	    pool_filename = 'chimera_pool' + filename[12:]
#	    pool_path = url + '/' + pool_filename
#	    if os.path.exists(pool_path):
#	        most_recent = timestamp
#	        most_recent_dump_path = path
#		most_recent_pool_path = pool_path

#    if most_recent is None:
#        return None

#    return [bz2.BZ2File(most_recent_pool_path), bz2.BZ2File(most_recent_dump_path), int(most_recent)]

    most_recent_pool_path = os.path.join(config.input_directory, config.latest_pool)
    most_recent_dump_path = os.path.join(config.input_directory, config.latest_dump)
    timestamp = int(os.stat(most_recent_dump_path).st_mtime)

    print 'Old chimera dump file timestamp: ' + str(prev_timestamp)
    print 'New chimera dump file timestamp: ' + str(timestamp)

    most_recent = None
    if timestamp > prev_timestamp and (most_recent == None or timestamp > most_recent):
        most_recent = timestamp

    if most_recent is None:
        return None

    return [open(most_recent_pool_path, 'r'), open(most_recent_dump_path, 'r'), most_recent]

def store_files(files, filename):
  f = open(filename, 'w')
  for file in files:
      f.write(file + '=' + files[file].dataset + '\n')

def restore_files(filename):
    f = open(filename, 'r')
    files = {}
    for line in f:
        line = line.strip()
        if line == '' or line[0] == '#':
            continue
        vals = line.split('=', 1)
        if len(vals) < 2:
            continue
        files[vals[0]] = File(dataset = vals[1])
    return files

# Queries DBS to obtain a mapping from files to dataset
def query_dataset_files(config, time_begin):
    sys.path.append('dbsapi')
    import provider_dbsv2

    api = provider_dbsv2.createDBSAPI('')

    paths = set(map(lambda x: x['Path'], api.listBlocks(storage_element_name="cmssrm-fzk.gridka.de")))

    # If a DBS query fails, retry in 1 minute, if it fails again, retry in
    # 15 minutes, etc. If after the last entry the query still fails then
    # abort then raise an exception (which aborts the script).
    retry_time = [1, 15, 60, 120, 600]

    files = {}
    for p in paths:
        retry_index = 0
        while retry_index < len(retry_time):
	    try:
#	        import random
#		if random.random() > 0.1:
#		    raise Exception('Fail')
                for f in map(lambda x: x['LogicalFileName'], api.listDatasetFiles(p)):
                    files[f] = File(dataset = p)
		break
	    except Exception, ex:
		print 'DBS query failed: ' + str(ex)
		if retry_index+1 >= len(retry_time):
		    print 'Giving up. Remove the PID file manually before re-running the script.'
		    raise ex

		# Determine sleeping time. If sleep would take longer than
		# maximum running time of the script then abort directly now
		# instead of sleeping.
		sleep_time = retry_time[retry_index]*60
		if config.max_time > 0 and time.time() - time_begin + sleep_time > config.max_time*60*60:
		    raise MaxTimeElapsed()

		print 'Trying again in ' + str(retry_time[retry_index]) + ' minute(s)'
		# We might want to write files to disk before sleeping,
		# to avoid eating up the machine's RAM for a long time.
		if retry_time[retry_index] > 0: #15:
		    progress_file = os.path.join(config.cache_directory, 'chimera.progress')
		    print 'Writing current progress to ' + progress_file + '...'

		    try:
		        store_files(files, progress_file)
		    except:
		        print 'Failed to write files to disk. Keeping them in memory while sleeping...'
		    del files
		    print 'Sleeping.'
                    time.sleep(sleep_time)
		    print 'Restoring progress from ' + progress_file + '...'
		    files = restore_files(progress_file)
		    os.unlink(progress_file)
		else:
		    print 'Sleeping.'
                    time.sleep(sleep_time)

	        retry_index += 1
		print 'Retrying DBS query...'
    return files

def parse_chimera_sizes(file, datasets):
    xml_handler = SizeHandler(datasets)
    parser = xml.sax.make_parser()
    parser.setContentHandler(xml_handler)
    parser.parse(file)

def parse_chimera_dump(file, datasets):
    xml_handler = Handler(datasets)
    parser = xml.sax.make_parser()
    parser.setContentHandler(xml_handler)

    # TODO: This is a temporary work-around for invalid XML in the chimera dump
#    for line in file:
#        line = line.replace('&', '&amp;')
#        parser.feed(line)

    parser.parse(file)
    return xml_handler

def write_xml_output(result, filename, timestamp, time_begin):
    total_data = {}

    f = file(filename, 'w')
    f.write('<datasets>\n')

    f.write('\t<time>' + str(timestamp) + '</time>\n')
    f.write('\t<duration>' + str(int(time.time() - time_begin)) + '</duration>\n')
    for dataset in result.records:
        record = result.records[dataset]
        f.write('\t<dataset name=%s incomplete_sizes=%s>\n' % (xml.sax.saxutils.quoteattr(dataset), xml.sax.saxutils.quoteattr(str(record.incomplete_sizes))))

	for entry in record.data:
	    f.write('\t\t<' + entry + '>' + str(record.data[entry]) + '</' + entry + '>\n')
	    if not entry in total_data:
	        total_data[entry] = 0
	    total_data[entry] += record.data[entry]
	f.write('\t</dataset>\n')

    for entry in total_data:
        f.write('\t<' + entry + '>' + str(total_data[entry]) + '</' + entry + '>\n')
    f.write('</datasets>')
    f.close()

def write_unassigned_output(result, filename, timestamp):
    f = file(filename, 'w')
    f.write('Files with no dataset assigned on ' + time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(timestamp)) + ':\n\n')
    for filename in result.files:
        if result.files[filename].dataset is None:
	    f.write(filename + "\n")
    f.close()

def run(config):
    time_begin = time.time()

    # Check whether there is a new chimera dump available
    last_modified_file = os.path.join(config.cache_directory, 'chimera.last_modified')
    chimera = query_chimera_dump(config, last_modified_file)
    if chimera is None:
        sys.stdout.write('Chimera dump not updated since last execution\n')
	return

    # Great, we have a new chimera dump to parse. Before doing so, get dataset
    # information from DBS to assign files in the chimera dump to datasets.
    sys.stdout.write('New Chimera dump available...\n')

    sys.stdout.write('Querying DBS...\n')
    files = query_dataset_files(config, time_begin)
    #files = {}

    sys.stdout.write('Parsing sizes dump...\n')
    parse_chimera_sizes(chimera[1], files)

    sys.stdout.write('Parsing pool dump...\n')
    result = parse_chimera_dump(chimera[0], files)
    chimera[0].close()
    chimera[1].close()

    # Write XML output for HappyFace, chimera[2] is timestamp of chimera dump
    sys.stdout.write('Write and Upload output...\n')
    output_file = os.path.join(config.cache_directory, config.output_file)
    write_xml_output(result, output_file, chimera[2], time_begin)

    if config.upload_url != '':
        # Upload
	upload_url = config.upload_url
	if config.password != '':
	    split = config.upload_url.split('//')
	    upload_url = split[0] + '//' + config.password + '@' + split[1]
	sub_p = subprocess.Popen(['curl', '-F', 'Datei=@' + output_file, upload_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	sub_p.communicate()
	if sub_p.returncode != 0:
            sys.stderr.write('Upload failed: %s...\n' % sub_p.stderr)
	    sys.exit(-1)

    if config.unassigned_file != '':
        unassigned_file = os.path.join(config.cache_directory, config.unassigned_file)
	write_unassigned_output(result, unassigned_file, chimera[2])


    file(last_modified_file, 'w').write(str(chimera[2]))

parser = optparse.OptionParser()
parser.add_option('-c', '--config', dest='config', help='Config file to use', metavar='CONFIG')
(options, args) = parser.parse_args()

config_file = options.config
if not config_file:
	config_file = os.path.join(os.path.dirname(sys.argv[0]), 'chimera.cfg')

cfg = Config(config_file)
pid_file = os.path.join(cfg.cache_directory, 'chimera.py.pid')

# Don't do anything if the script is already running (so it's save to run it
# frequently in a cronjob).
try:
    file(pid_file, 'r').read()
    sys.stdout.write('PID file exists already: '+pid_file+'\n')
except:
    file(pid_file, 'w').write(str(os.getpid()))

    # supposedly do not unlink the PID file in case run throws an exception
    # so that we do not run into the same problem again in the next cronjob
    # execution. Instead wait for manual intervention. However, do unlink the
    # file if the maximum execution time of the script was reached.
    try:
        # Redirect stdout to log file
        if cfg.log_file != '':
	    # Create an unbuffered file so log messages are written immediately
            sys.stdout = file(os.path.join(cfg.cache_directory, cfg.log_file), 'w', 0)
        run(cfg)
    except MaxTimeElapsed, ex:
        print str(ex)
        try:
            os.unlink(pid_file)
        except:
            pass

    try:
        os.unlink(pid_file)
    except:
        pass
