#!/usr/bin/python

import time
import re

class Agent:
    def __init__(self):
        self.recent_time = -1
        self.rss = 0.0
        self.vsize = 0.0
        self.dstime = 0.0
        self.dutime = 0.0

def parse_line(line):
    match = re.match("(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): (\w*)\[(\d*)\]: AGENT_STATISTICS RSS=(\d*(\.\d*)?) VSize=(\d*(\.\d*)?) Stime=(\d*(\.\d*)?) Utime=(\d*(\.\d*)?) dRSS=(\d*(\.\d*)?) dVSize=(\d*(\.\d*)?) dStime=(\d*(\.\d*)?) dUtime=(\d*(\.\d*)?)", line)

    if not match:
        return None
    try:
        tm = time.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(tm)
    except:
        return None

    service = match.group(2)
    pid = int(match.group(3))

    rss = float(match.group(4))
    vsize = float(match.group(6))
    stime = float(match.group(8))
    utime = float(match.group(10))
    drss = float(match.group(12))
    dvsize = float(match.group(14))
    dstime = float(match.group(16))
    dutime = float(match.group(18))

    return {'time': timestamp,
            'service': service,
            'pid': pid,
            'rss': rss,
            'vsize': vsize,
            'stime': stime,
            'utime': utime,
            'drss': drss,
            'dvsize': dvsize,
            'dstime': dstime,
            'dutime': dutime}

def parse_log(log, timep, agents):
    min_time = time.time() - timep
    for line in log:
        res = parse_line(line)
        # We only care about AGENT_STATISTICS lines
        if not res:
            continue
        if res['time'] < min_time:
            continue

        if not res['service'] in agents:
            agents[res['service']] = Agent()

        # Use most recent sizes, accumulate time over the period given by timep
        if res['time'] > agents[res['service']].recent_time:
            agents[res['service']].recent_time = res['time']
            agents[res['service']].rss = res['rss']
            agents[res['service']].vsize = res['vsize']
        agents[res['service']].dstime += res['dstime']
        agents[res['service']].dutime += res['dutime']

agents = {}
timep = 12*60*60 # accumalte utime and stime for 12 hours
#parse_log(file('log'), 10000000000, agents)
parse_log(file('log'), timep, agents)

for agent in agents:
    print 'Agent: %s\nRSS: %d\nVSize: %d\ndStime: %d\ndUtime: %d\n' % (agent, agents[agent].rss, agents[agent].vsize, agents[agent].dstime, agents[agent].dutime)
