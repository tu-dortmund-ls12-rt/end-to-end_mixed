#!/bin/bash
#
# Automatic Evaluation for the paper 'Timing Analysis of Asynchronized Distributed Cause-Effect Chains' (2021).

########################################
# Start this shell script with
# 	./auto.sh x
# where x should be replace by the number of maximal concurrent processes (typically not more than free processor of the machine that is used)
########################################

###
# Specify number of concurrent processes
###
if [ $# -eq 0 ]
then
  echo "Specify maximal number of concurrent processes for the experiment (e.g. './auto.sh 5' )."
  exit 1
else
  var=$1
  echo "with $var concurrent processes"
fi

./auto_1gen.sh $var
./auto_2impl.sh $var
./auto_3mixedinter.sh $var
./auto_4mixedintra.sh $var
./auto_5plots.sh $var