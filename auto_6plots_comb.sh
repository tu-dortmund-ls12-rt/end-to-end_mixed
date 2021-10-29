#!/bin/bash
#
# Automatic task generation.

########################################
# Start this shell script with
# 	./auto_5plots.sh 
########################################

###
# Specify number of concurrent processes
###
if [ $# -eq 0 ]
then
  echo "Specify maximal number of concurrent processes for the experiment (e.g. './auto_5plots.sh 5' )."
  exit 1
else
  var=$1
  echo "with $var concurrent processes"
fi

date
echo "=====5plots====="
echo "-----automotive benchmark-----"
python3.7 main.py -j101 -g0 -n=0 -p=$var
echo "-----uunifast benchmark-----"
python3.7 main.py -j101 -g1 -n=0 -p=$var
echo "DONE"