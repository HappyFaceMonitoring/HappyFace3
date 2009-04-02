#!/bin/bash 

LOGFILES="logx  logxfromfzk  logxfromfzkDebug  logxprod  monjobs_happyface_summary.xml qstat.xml";

for i in $LOGFILES; do
    wget http://ekpganglia.physik.uni-karlsruhe.de/~happyface/logs/out/$i -O ../inputFiles/$i
done
