#!/bin/bash
#
# Automatic task generation.

########################################
# Start this shell script with
# 	./auto_3mixedinter.sh 
########################################

###
# Specify number of concurrent processes
###
if [ $# -eq 0 ]
then
  echo "Specify maximal number of concurrent processes for the experiment (e.g. './auto_3mixedinter.sh 5' )."
  exit 1
else
  var=$1
  echo "with $var concurrent processes"
fi

nmbchains=100 # number of interconnected chains

date
echo "=====3mixedinter====="

# g=0 r=100 with different utilization
echo "-----automotive benchmark-----"
for util in {50..90..10}
do
	echo "---utilization: $util---"
  python3.7 main.py -j12 -u=$util -g0 -n=0 -p=$var -m$nmbchains
done

# g=1 r=100 with different utilization
echo "-----uunifast benchmark-----"
for util in {50..90..10}
do
	echo "---utilization: $util---"
  python3.7 main.py -j12 -u=$util -g1 -n=0 -p=$var -m$nmbchains
done
echo "DONE"