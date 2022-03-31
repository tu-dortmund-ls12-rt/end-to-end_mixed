#!/usr/bin/env python3
import getopt
import sys

import benchmark_WATERS as bench
from tasks.taskset import transform
import helpers
import analysis as ana

import random
import numpy as np
from multiprocessing import Pool
import plot

from copy import deepcopy  # to duplicate the system under analysis. TODO do we need this?

# set seed
random.seed(314159)
np.random.seed(314159)

# output paths
path1 = 'output/step1/'
path2 = 'output/step2/'
path3 = 'output/step3/'


# Analysis class
###
# Analysis result class
###
class AnaRes:
    def __init__(self):
        self.res_dict = dict()
        self.spor = []
        self.let = []
        self.analysis = []

    def store_res(self, spor, let, analysis, vals=None):
        """Store an analysis result."""
        if spor not in self.res_dict:
            self.res_dict[spor] = dict()
            if spor not in self.spor:
                self.spor.append(spor)

        if let not in self.res_dict[spor]:
            self.res_dict[spor][let] = dict()
            if let not in self.let:
                self.let.append(let)

        if analysis not in self.res_dict[spor][let]:
            self.res_dict[spor][let][analysis] = dict()
            if analysis not in self.analysis:
                self.analysis.append(analysis)

        self.res_dict[spor][let][analysis] = vals

    def results(self, spor, let, analysis):
        """Get analysis result."""
        return self.res_dict[spor][let][analysis]


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
if code_switch in [0, 1]:
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

        # Modify tasks
        for ts in ts_sets:
            for tsk in ts:
                # Set phase to 0
                tsk.rel.phase = 0
                # Make implicit communication
                tsk.add_feature('communication', 'implicit')
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
        helpers.check_or_make_directory(path1)
        helpers.write_data(path1 + f'ts_ces_n={number}_u={ut}.pickle', ts_ces)

##
# Do analyses
##
spor_ratios = [0.2, 0.5, 0.8]  # ratio of tasks per chain that are sporadic
LET_ratios = [0.2, 0.5, 0.8]  # ratio of tasks per chain have communicate with LET
if code_switch in [0, 2]:

    # Load data
    ts_ces_all = []
    for ut in utils:
        ts_ces_all.extend(helpers.load_data(path1 + f'ts_ces_n={number}_u={ut}.pickle'))

    ana_res = AnaRes()  # store analysis results here

    # iterate through cases
    for spor_rat, LET_rat in [(sp, let) for sp in spor_ratios for let in LET_ratios]:
        # Copy task set
        ts_ces = deepcopy(ts_ces_all)

        # Modify the tasks
        for ts, _ in ts_ces:
            for tsk in random.sample(ts[:], int(len(ts) * spor_rat)):
                tsk.rel.type = 'sporadic'
            for tsk in random.sample(ts[:], int(len(ts) * LET_rat)):
                tsk.comm.type = 'LET'

        # Flat list
        ces = [ce for _, ces in ts_ces for ce in ces]

        # Do analyses
        with Pool(processors) as p:
            res_pess = p.map(ana.mix_pessimistic, ces)
            res_mix = p.map(ana.mix, ces)
            res_mix_improved = p.map(ana.mix_improved, ces)

        # Store in Analysis object
        ana_res.store_res(spor=spor_rat, let=LET_rat, analysis='Pess', vals=res_pess)
        ana_res.store_res(spor=spor_rat, let=LET_rat, analysis='Mix', vals=res_mix)
        ana_res.store_res(spor=spor_rat, let=LET_rat, analysis='Improved', vals=res_mix_improved)

    # Store analysis result object
    helpers.check_or_make_directory(path2)
    helpers.write_data(path2 + f'ana_res_n={number}.pickle', ana_res)

##
# Plot data
##

if code_switch in [0, 3]:
    # Load data
    ana_res = helpers.load_data(path2 + f'ana_res_n={number}.pickle')

    analyses = ['Mix', 'Improved']
    baseline = 'Pess'

    x_axes = {}

    # Plot
    helpers.check_or_make_directory(path3)
    for analysis, spor in [(x, y) for x in analyses for y in spor_ratios]:
        data = []
        for let in LET_ratios:
            data.append([
                (y - x) / y for x, y in zip(
                    ana_res.results(spor=spor, let=let, analysis=analysis),
                    ana_res.results(spor=spor, let=let, analysis=baseline)
                )
            ])
        plot.plot(
            data,
            path3 + f'{analysis=}_{spor=}.pdf',
            ylimits=[0.0, 1.0],
            xticks=[f'{int(let * 100)}% LET' for let in LET_ratios],
            yaxis_label='Latency Reduction',
            title=f'{analysis=}, {int(spor * 100)}% sporadic'
        )
