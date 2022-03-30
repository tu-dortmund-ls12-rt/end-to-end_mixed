#!/usr/bin/env python3
import getopt
import sys

import benchmark_WATERS as bench
from tasks.taskset import transform

import random
import numpy as np

# set seed
random.seed(314159)
np.random.seed(314159)

##
# Handle Options
##
opts, args = getopt.getopt(sys.argv[1:], "s:p:n:")

for opt, arg in opts:
    if opt == '-s':  # define which part of the code is being executed
        code_switch = int(arg)
    elif opt in '-p':  # number of processors that are used for the computations
        processors = int(arg)
    elif opt in '-n':  # number
        number = int(arg)
    else:
        breakpoint()

utils = [0.5, 0.6, 0.7, 0.8, 0.9]

##
# Make Taskset and chains
##
if code_switch == 1:
    """Make 'number' many task sets, generate ce_chains accordingly, discard those that have no ce_chains, 
    transform the tasks, store."""
    for ut in utils:
        # Make "number" many tasksets
        ts_sets = [bench.gen_taskset(ut) for _ in range(number)]
        # Generate 30 to 60 cause-effect chains for each task set (some of them may be discarded during generation)
        ce_sets = [bench.gen_ce_chains(ts) for ts in ts_sets]

        # Discard those without ce_chains and match ts with ce_set
        ts_ces = [(ts, ce_set) for ts, ce_set in zip(ts_sets, ce_sets) if len(ce_set) != 0]

        # Transform task sets
        for ts, _ in ts_ces:
            transform(ts)

        if __debug__:
            for ts, ces in ts_ces:
                for ce in ces:
                    assert ce.base_ts == ts

        # Store data
        # TODO
##
# Do analyses
##

##
# Plot data
##
