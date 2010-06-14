#!/usr/bin/python

# This script creates an XML file joins information from both a chimera dump
# and DBS to find out how many files are staged, pinned, etc. for each dataset
# individually.

#dump_file = 'http://ekpwww.physik.uni-karlsruhe.de/~zvada/chimera-dump/cms-chimera-dump-marian-test-20100526-v0.9.0-pool.xml.bz2'
dump_file = 'http://ekpwww.physik.uni-karlsruhe.de/~zvada/chimera-dump/cms-chimera-dump-marian-test-20100601-v0.9.0-pool.xml.bz2'
size_file = 'http://ekpwww.physik.uni-karlsruhe.de/~zvada/chimera-dump/cms-chimera-dump-marian-test-20100531-v0.9.0-dump.xml.bz2'

import urllib2
import xml.sax
import calendar
import time
import sys
import bz2
import os

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
    headers = {}
    try:
        headers['If-Modified-Since'] = file(last_modified_file, 'r').read()
    except:
        pass

    try:
        req = urllib2.Request(dump_file, None, headers)
        dl = urllib2.urlopen(req)
        info = dl.info()
	return dl
    except urllib2.HTTPError, ex:
        if ex.code == 304:
            sys.stdout.write('Chimera dump not updated since last execution\n')
            return None
        raise ex

# Queries DBS to obtain a mapping from files to dataset
def query_dataset_files():
    # TODO
    sys.path.extend(['grid-control/python', '.'])
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
    #for line in file:
    #    line = line.replace('&', '&amp;')
    #    parser.feed(line)

    parser.parse(file)
    return xml_handler

def write_xml_output(result, filename, info):
    total_data = {}

    f = file(filename, 'w')
    f.write('<datasets>\n')

    if 'Last-Modified' in info:
        timestamp = calendar.timegm(time.strptime(info['Last-Modified'], '%a, %d %b %Y %H:%M:%S GMT'))
    else:
        timestamp = time.time()
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

dl = query_chimera_dump(dump_file, 'last_modified')
if dl is None:
    sys.exit(0)
info = dl.info()

# Great, we have a new chimera dump to parse. Before doing so, get dataset
# information from DBS to assign files in the chimera dump to datasets. Since
# this might take a while however store the chimera dump to a file so that we
# don't rely on the HTTP connection still open when that has finished.
sys.stdout.write('New Chimera dump available, downloading...\n')
file('chimera_dump', 'w').write(dl.read())
dl.close()

sys.stdout.write('Querying DBS...\n')
datasets = query_dataset_files()
#datasets = {}

sys.stdout.write('Loading file size dump...\n')
sizes_dl= urllib2.urlopen(size_file)
file('chimera_size', 'w').write(sizes_dl.read()) # TODO: Direct streaming decompression, without writing to disk first
parse_chimera_sizes(bz2.BZ2File('chimera_size'), datasets)
os.unlink('chimera_size')

sys.stdout.write('Parsing Chimera dump...\n')
bzfile = bz2.BZ2File('chimera_dump')
result = parse_chimera_dump(bzfile, datasets)
bzfile.close()
os.unlink('chimera_dump')

# Write XML output for HappyFace
write_xml_output(result, 'out.xml', info)

if 'Last-Modified' in info:
    file('last_modified', 'w').write(info['Last-Modified'])
