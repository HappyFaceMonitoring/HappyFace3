
"""
A command-line interface to GraphTool, for users who'd rather deal in CSV than
with python.
"""

import os
import sys
import time
import datetime

from graphtool.tools.common import parseOpts
from graphtool.database.query_handler import new_data, add_data
import graphtool.graphs.basic as graphs

def parse_csv_pg(fp, **kw):
    metadata = {}
    pgdata = {}
    header = False
    if 'header' in kw:
        info = kw['header'].split(',')
        metadata['pivot_name'] = info[0]
        metadata['grouping_col'] = info[1]
        metadata['column_names'] = ','.join(info[2:])
        header = True
    pivot_col = int(kw.get('pivot_col', 0))
    grouping_col = int(kw.get('grouping_col', 1))
    grouping_format = kw.get('grouping_format', False)
    results_col = [int(i.strip()) for i in kw.get('results_col','2').split(',')]
    for line in fp.readlines():
        info = line.split(',')
        if len(info) < 3:
            raise Exception("Not enough fields in line:\n%s" % line.strip())
        pivot = info[pivot_col]
        group = info[grouping_col]
        if not header:
            metadata['pivot_name'] = pivot
            metadata['grouping_name'] = group
            columns = ['Unknown']*len(results_col)
            for col in range(len(results_col)):
                columns[col] = info[results_col[col]]
            metadata['column_names'] = ','.join(columns)
            header = True
            continue
        if pivot not in pgdata:
            pgdata[pivot] = {}
        group_dict = pgdata.get(pivot, {})
        if grouping_format:
            #grouping_tuple = time.strptime('080413', grouping_format)
            grouping_tuple = time.strptime(group, grouping_format)
            group = datetime.datetime(*grouping_tuple[:6])
        if group not in group_dict:
            group_dict[group] = new_data(info, results_col)
        else:
            group_dict[group] = add_data(group_dict[group], info, results_col)
    return pgdata, metadata

def parse_csv_p(fp, **kw):
    metadata = {}
    pdata = {}
    header = False
    pivot_col = int(kw.get('pivot_col', 0))
    results_col = [int(i.strip()) for i in kw.get('results_col','1').split(',')]
    for line in fp.readlines():
        info = line.split(',')
        if len(info) < 2:
            raise Exception("Not enough fields in line:\n%s" % line.strip())
        pivot = info[pivot_col]
        if not header:
            metadata['pivot_name'] = pivot
            columns = ['Unknown']*len(results_col)
            for col in range(len(results_col)):
                columns[col] = info[results_col[col]]
            metadata['column_names'] = ','.join(columns)
            header = True
            continue
        if pivot not in pdata:
            pdata[pivot] = new_data(info, results_col)
        else:
            pdata[pivot] = add_data(pdata[group], info, results_col)
    return pdata, metadata

def main():
    kw, given, args = parseOpts(sys.argv[1:])
    output = kw.get('output', 'graphtool.png')
    graph = kw.get('graph', 'QualityMap')
    try:
        Graph = getattr(graphs, 'Basic' + graph)
    except:
        raise
        print >> sys.stderr, "Unknown graph type: %s" % graph
        sys.exit(1)
    g = Graph()
    if graph in ['QualityMap', 'Cumulative', 'StackedBar', 'SimpleStackedBar', \
            'StackedLine']:
        data, metadata = parse_csv_pg(sys.stdin, **kw)
    elif graph in ['Bar', 'Pie']:
        data, metadata = parse_csv_p(sys.stdin, **kw)
    else:
        print >> sys.stderr, "Unknown graph type: %s" % graph
        sys.exit(1)
    if output == '-':
        fp = sys.stdout
    else:
        fp = open(os.path.expandvars(os.path.expanduser(output)), 'w')
    for key, val in kw.items():
        metadata[key] = val
    g.run(data, fp, metadata)

if __name__ == '__main__':
    main()

