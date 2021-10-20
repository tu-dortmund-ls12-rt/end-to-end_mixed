#!/bin/bash
#
# Automatic Evaluation for the paper 'Timing Analysis of Asynchronized Distributed Cause-Effect Chains' (2021).

########################################
# Start this shell script with
# 	./auto.sh x
# where x should be replace by the number of maximal concurrent jobs (typically not more than free processor of the machine that is used)
###
# We use the screen command to parallelize the execution.
# 'screen -ls' shows all current screens
# 'killall screen' aborts all current screens.
########################################

###
# Specify number of concurrent jobs
###
if [ $# -eq 0 ]
then
  echo "Specify maximal number of concurrent jobs for the experiment (e.g. './auto.sh 5' )."
  exit 1
else
  var=$1
  echo "with $var concurrent jobs"
fi

num_tries=100  # number of runs
runs_per_screen=10  # number of runs per screen

###
# Single ECU analysis
###
echo "===Start single ECU analysis"
date

# g=0 r=10 with different utilization
echo "automotive benchmark"
for util in {50..90..10}
do
	echo "utilization: $util"
	date
  for ((i=0;i<num_tries;i++))
	do
    # start a new screen
    screen -dmS ascr$i python3.7 main.py -j1 -u=$util -g0 -r$runs_per_screen -n=$i

    numberrec=$(screen -list | grep -c ascr.*)

    # wait until variable is reached
    while (($numberrec >= $var))
   	do
   		sleep 1
      numberrec=$(screen -list | grep -c ascr.*)
   	done
	done
done

  # g=1 r=10 with different utilization
echo "uunifast benchmark"
for util in {50..90..10}
do
	echo "utilization: $util"
	date
  for ((i=0;i<num_tries;i++))
	do
    # start a new screen
    screen -dmS ascr$i python3.7 main.py -j1 -u=$util -g1 -r$runs_per_screen -n=$i

    numberrec=$(screen -list | grep -c ascr.*)

    # wait until variable is reached
    while (($numberrec >= $var))
   	do
   		sleep 1
      numberrec=$(screen -list | grep -c ascr.*)
   	done
	done
done
echo " "

# wait until all are closed
while screen -list | grep -q ascr.*
do
  sleep 1
done

###
# Interconnected ECU analysis.
###
# Or manually with:
# 	for i in {50..90..10}; do  screen -dmS g0util_$i python3 main.py -j2 -u=$i -g0; done
# 	for i in {50..90..10}; do  screen -dmS g1util_$i python3 main.py -j2 -u=$i -g1; done
###

echo "===Start interconnected ECU analysis"
date

echo "automotive benchmark"
for i in {50..90..10}
do
  screen -dmS ascrg0util_$i python3.7 main.py -j2 -u=$i -g0 -n=$num_tries
  # wait until variable is reached
  while (($numberrec >= $var))
  do
    sleep 1
    numberrec=$(screen -list | grep -c ascr.*)
  done
done

echo "uunifast benchmark"
for i in {50..90..10}
do
  screen -dmS ascrg1util_$i python3.7 main.py -j2 -u=$i -g1 -n=$num_tries
  # wait until variable is reached
  while (($numberrec >= $var))
  do
    sleep 1
    numberrec=$(screen -list | grep -c ascr.*)
  done
done

# wait until all are closed
while screen -list | grep -q ascr.*
do
  sleep 1
done

echo " "

###
# Draw plots.
###
# Or manually with:
# 	screen -dmS j3g0 python3 main.py -j3 -g0
# 	screen -dmS j3g1 python3 main.py -j3 -g1
###

echo "===Draw plots."
date

screen -dmS ascrj3g0 python3.7 main.py -j3 -g0
screen -dmS ascrj3g1 python3.7 main.py -j3 -g1
while screen -list | grep -q ascr.*
do
  sleep 1
done

echo "DONE"
date
