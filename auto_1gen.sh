#!/bin/bash
#
# Automatic task generation.

########################################
# Start this shell script with
# 	./auto_1gen.sh 
###
# We use the screen command to parallelize the execution.
# 'screen -ls' shows all current screens
# 'killall screen' aborts all current screens.
########################################

###
# Specify number of concurrent processes
###
if [ $# -eq 0 ]
then
  echo "Specify maximal number of concurrent processes for the experiment (e.g. './auto_1gen.sh 5' )."
  exit 1
else
  var=$1
  echo "with $var concurrent processes"
fi

tsnmb=100 # number of task sets

date
echo "=====1gen====="

# g=0 r=100 with different utilization
echo "-----automotive benchmark-----"
for util in {50..90..10}
do
	echo "---utilization: $util---"
  python3.7 main.py -j10 -u=$util -g0 -r$tsnmb -n=0 -p$var
done

# g=1 r=100 with different utilization
echo "-----uunifast benchmark-----"
for util in {50..90..10}
do
	echo "---utilization: $util---"
  python3.7 main.py -j10 -u=$util -g1 -r100 -n=0 -p$var
done