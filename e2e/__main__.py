#!/usr/bin/env python3
import getopt
import sys

import benchmark_WATERS as bench
from tasks.taskset import transform
import helpers

import random
import numpy as np

from copy import deepcopy  # to duplicate the system under analysis. TODO do we need this?

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
    set phase to 0, transform the tasks, store.
    Please note: Task sets are periodic with phase=0 and implicit deadline, and have implicit communication."""
    for ut in utils:
        print(f'{helpers.time_now()}: Utilization={ut}')
        # Make "number" many tasksets
        ts_sets = [bench.gen_taskset(ut) for _ in range(number)]

        # Order by Deadline
        for ts in ts_sets:
            ts.sort_dm()

        for ts in ts_sets:
            # Set phase to 0
            for tsk in ts:
                tsk.rel.phase = 0
            # Transform task sets
            transform(ts)
            # TDA
            ts.compute_wcrts()

        # Remove task sets with wcrt > dl
        ts_sets = [ts for ts in ts_sets if all([tsk.dl.dl >= ts.wcrts[tsk] for tsk in ts])]

        # Generate 30 to 60 cause-effect chains for each task set (some of them may be discarded during generation)
        ce_sets = [bench.gen_ce_chains(ts) for ts in ts_sets]

        # Discard those without ce_chains and match ts with ce_set
        ts_ces = [(ts, ce_set) for ts, ce_set in zip(ts_sets, ce_sets) if len(ce_set) != 0]

        if __debug__:
            for ts, ces in ts_ces:
                for ce in ces:
                    assert ce.base_ts == ts

        # Store data
        path = '../output/step1/'
        helpers.check_or_make_directory(path)
        helpers.write_data(path + f'ts_ces_n={number}_u={ut}.pickle', ts_ces)

##
# Do analyses
##
if code_switch == 2:
    ts_ces_all = []

    # Load data
    load_path = '../output/step1/'
    for ut in utils:
        ts_ces_all.extend(helpers.load_data('../output/step1/' + f'ts_ces_n={number}_u={ut}.pickle'))

    spor_ratios = [0.0, 0.5, 1.0]  # ratio of tasks per chain that are sporadic
    LET_ratios = [0.2, 0.5, 0.8]  # ratio of tasks per chain have communicate with LET

    # create masks for all 9 cases

    # apply masks and do analyses

    # store in analysis result class

##
# Plot data
##
