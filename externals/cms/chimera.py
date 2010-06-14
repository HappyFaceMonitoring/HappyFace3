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

class Config:
    def __init__(self, filename):
	config = ConfigParser.ConfigParser()
	config.read(filename)

	self.input_directory = self.get_default(config, 'chimera', 'input_directory', '')
	self.output_file = self.get_default(config, 'chimera', 'output_file', '')
	self.upload_url = self.get_default(config, 'chimera', 'upload_url', '')
	self.password = self.get_default(config, 'chimera', 'password', '')

    def get_default(self, parser, section, option, default):
        try:
	    return parser.get(section, option)
        except:
	    return default

# XML parser callback handler, merging filesizes into file<->dataset mapping
class SizeHandler(xml.sax.ContentHandler):
    def __init__(self, datasets):
        self.datasets = datasets

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
	        if not index in self.datasets:
	            self.datasets[index] = {'size': self.entry_size}
	        else:
	            self.datasets[index]['size'] = self.entry_size

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

    def __init__(self, datasets):
        self.datasets = datasets
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

		if not index in self.datasets or not 'path' in self.datasets[index]:
		    dataset = 'Unassigned'
		else:
		    dataset = self.datasets[index]['path']

		if not dataset in self.records:
		    self.records[dataset] = Handler.Record()

		# Get entry size directly from <size> or from pre-parsed
		# dump in self.datasets[index]['size'] as a fallback
                entry_size = 0
		if self.entry_size is not None:
		    entry_size = self.entry_size
		elif index in self.datasets and 'size' in self.datasets[index]:
		    entry_size = self.datasets[index]['size']
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

def query_chimera_dump(url, last_modified_file):
    prev_timestamp = 0
    try:
        prev_timestamp = int(file(last_modified_file, 'r').read())
    except:
        pass

    most_recent = None
    most_recent_dump_path = None
    most_recent_pool_path = None

    for filename in os.listdir(url):
        # Only scan dumps
        if not filename.startswith('chimera_dump'):
	    continue

        path = url + '/' + filename
	timestamp = os.stat(path).st_mtime
	if timestamp > prev_timestamp and (most_recent == None or timestamp > most_recent):
	    # The dump is more recent than the one we scanned the last time
	    # Check whether there is also a sizes file.
	    pool_filename = 'chimera_pool' + filename[12:]
	    pool_path = url + '/' + pool_filename
	    if os.path.exists(pool_path):
	        most_recent = timestamp
	        most_recent_dump_path = path
		most_recent_pool_path = pool_path

    if most_recent is None:
        return None

    return [bz2.BZ2File(most_recent_pool_path), bz2.BZ2File(most_recent_dump_path), int(most_recent)]

# Queries DBS to obtain a mapping from files to dataset
def query_dataset_files():
    sys.path.append('dbsapi')
    import provider_dbsv2

    api = provider_dbsv2.createDBSAPI('')

    paths = set(map(lambda x: x['Path'], api.listBlocks(storage_element_name="cmssrm-fzk.gridka.de")))

    datasets = {}
    for p in paths:
        for f in map(lambda x: x['LogicalFileName'], api.listDatasetFiles(p)):
            datasets[f] = {'path': p}
    return datasets

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

def write_xml_output(result, filename, timestamp):
    total_data = {}

    f = file(filename, 'w')
    f.write('<datasets>\n')

    f.write('\t<time>' + str(timestamp) + '</time>\n')
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

def run(config):
    # Check whether there is a new chimera dump available
    chimera = query_chimera_dump(config.input_directory, 'chimera.last_modified')
    if chimera is None:
        sys.stdout.write('Chimera dump not updated since last execution\n')
	return

    # Great, we have a new chimera dump to parse. Before doing so, get dataset
    # information from DBS to assign files in the chimera dump to datasets.
    sys.stdout.write('New Chimera dump available...\n')

    sys.stdout.write('Querying DBS...\n')
    datasets = query_dataset_files()
    #datasets = {}

    sys.stdout.write('Parsing sizes dump...\n')
    parse_chimera_sizes(chimera[1], datasets)

    sys.stdout.write('Parsing pool dump...\n')
    result = parse_chimera_dump(chimera[0], datasets)
    chimera[0].close()
    chimera[1].close()

    # Write XML output for HappyFace, chimera[2] is timestamp of chimera dump
    write_xml_output(result, config.output_file, chimera[2])

    if config.upload_url != '':
        # Upload
	upload_url = config.upload_url
	if config.password != '':
	    split = config.upload_url.split('//')
	    upload_url = split[0] + '//' + config.password + '@' + split[1]
	sub_p = subprocess.Popen(['curl', '-F', 'Datei=@' + config.output_file, upload_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	sub_p.communicate()
	if sub_p.returncode != 0:
            sys.stderr.write('Upload failed: %s...\n' % sub_p.stderr)
	    sys.exit(-1)

    file('chimera.last_modified', 'w').write(str(chimera[2]))

# Don't do anything if the script is already running (so it's save to run it
# frequently in a cronjob).
try:
    file('chimera.py.pid', 'r').read()
    sys.stdout.write('PID file exists already\n')
except:
    try:
        file('chimera.py.pid', 'w').write(str(os.getpid()))

        parser = optparse.OptionParser()
	parser.add_option('-c', '--config', dest='config', help='Config file to use', metavar='CONFIG')
        (options, args) = parser.parse_args()

	config_file = options.config
	if not config_file: config_file = 'chimera.cfg'

        run(Config(config_file))
    finally:
        os.unlink('chimera.py.pid')
