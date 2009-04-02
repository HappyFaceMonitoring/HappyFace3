#!/usr/bin/env python

import os, sys

sys.path.insert(0, os.path.expandvars('../src'))
#sys.path.insert(0, os.path.expandvars('/usr/users/mauch/work/temp/python/imaging/COMP/WEBTOOLS/Tools/GraphTool/src'))

from graphtool.graphs.common_graphs import StackedBarGraph
from graphtool.tools.common import expand_string

# Einlesen der Daten
try:
	datei = file('../results/qstat_jobs.txt')
except:
	datei = none
	print 'Datei kann nicht geoeffnet werden.'

jobs = []
jobs = datei.readlines()

i = 0
while i < len(jobs):
	jobs[i] = jobs[i].split()
	i = i+1

entry100 = {}
entry80 = {}
entry30 = {}
entry10 = {}
queue = {}

i = 0
while i < len(jobs):
	entry10[jobs[i][0]] = int(jobs[i][4])
	entry30[jobs[i][0]] = int(jobs[i][5])
	entry80[jobs[i][0]] = int(jobs[i][6])
	entry100[jobs[i][0]] = int(jobs[i][7])
	i = i+1


data = { 'critical efficiency: under 10%':entry10, 'efficiency between 10% and 30%':entry30,  'efficiency between 30% and 80%':entry80, 'efficiency between 80% and 100%':entry100 }

#entry1 = {'foo':3, 'bar':5}
#entry2 = {'foo':4, 'bar':6}
#data = {'Team A':entry1, 'Team B':entry2}

metadata = {'title':'Qstat Plots: Efficiency of Running Jobs'}

file = open(expand_string('../plots/qstat_jobs.png',os.environ),'w')

SBG = StackedBarGraph()
SBG(data, file, metadata)
