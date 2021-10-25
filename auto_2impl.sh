#!/bin/bash
#
# Automatic task generation.

########################################
# Start this shell script with
# 	./auto_gen.sh 
###
# We use the screen command to parallelize the execution.
# 'screen -ls' shows all current screens
# 'killall screen' aborts all current screens.
########################################

# g=0 r=100 with different utilization
echo "automotive benchmark"
for util in {50..90..10}
do
	echo "utilization: $util"
	date

  # start a new screen
  screen -dmS ascr$i python3.7 main.py -j10 -u=$util -g0 -r100 -n=0
done

# g=1 r=100 with different utilization
echo "uunifast benchmark"
for util in {50..90..10}
do
	echo "utilization: $util"
	date
  
  # start a new screen
  screen -dmS ascr$i python3.7 main.py -j10 -u=$util -g1 -r100 -n=1
done
echo " "

# wait until all are closed
while screen -list | grep -q ascr.*
do
  sleep 1
done