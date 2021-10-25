#!/usr/bin/env python3
"""Evaluation for the paper 'Timing Analysis of Asynchronized Distributed
Cause-Effect Chains' (2021).

It includes (1) local analysis (2) global analysis and (3) plotting of the
results.
"""

import gc  # garbage collector
import argparse
import math
import numpy as np
import utilities.chain as c
import utilities.communication as comm
import utilities.generator_WATERS as waters
import utilities.generator_UUNIFAST as uunifast
import utilities.transformer as trans
import utilities.event_simulator as es
import utilities.analyzer as a
import utilities.analyzer_our as a_our
import utilities.evaluation as eva

import time
import sys

import random  # randomization
from multiprocessing import Pool  # multiprocessing
import itertools  # better performance


debug_flag = True  # flag to have breakpoint() when errors occur

random.seed(331)  # set seed for same results


########################
# Some help functions: #
########################

def time_now():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time


def task_set_generate(argsg, argsu, argsr):
    '''Generates task sets.
    Input:
    - argsg = benchmark to choose
    - argsu = utilization in %
    - argsr = number of task sets to generate
    Output: list of task sets.'''
    try:
        if argsg == 0:
            # WATERS benchmark
            print("WATERS benchmark.")

            # Statistical distribution for task set generation from table 3
            # of WATERS free benchmark paper.
            profile = [0.03 / 0.85, 0.02 / 0.85, 0.02 / 0.85, 0.25 / 0.85,
                       0.25 / 0.85, 0.03 / 0.85, 0.2 / 0.85, 0.01 / 0.85,
                       0.04 / 0.85]
            # Required utilization:
            req_uti = argsu/100.0
            # Maximal difference between required utilization and actual
            # utilization is set to 1 percent:
            threshold = 1.0

            # Create task sets from the generator.
            # Each task is a dictionary.
            print("\tCreate task sets.")
            task_sets_waters = []
            while len(task_sets_waters) < argsr:
                task_sets_gen = waters.gen_tasksets(
                    1, req_uti, profile, True, threshold/100.0, 4)
                task_sets_waters.append(task_sets_gen[0])

            # Transform tasks to fit framework structure.
            # Each task is an object of utilities.task.Task.
            trans1 = trans.Transformer("1", task_sets_waters, 10000000)
            task_sets = trans1.transform_tasks(False)

        elif argsg == 1:
            # UUniFast benchmark.
            print("UUniFast benchmark.")

            # Create task sets from the generator.
            print("\tCreate task sets.")

            # The following can be used for task generation with the
            # UUniFast benchmark without predefined periods.

            # # Generate log-uniformly distributed task sets:
            # task_sets_generator = uunifast.gen_tasksets(
            #         5, args.r, 1, 100, args.u, rounded=True)

            # Generate log-uniformly distributed task sets with predefined
            # periods:
            periods = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
            # Interval from where the generator pulls log-uniformly.
            min_pull = 1
            max_pull = 2000

            task_sets_uunifast = uunifast.gen_tasksets_pred(
                50, argsr, min_pull, max_pull, argsu/100.0, periods)

            # Transform tasks to fit framework structure.
            trans2 = trans.Transformer("2", task_sets_uunifast, 10000000)
            task_sets = trans2.transform_tasks(False)

        else:
            print("Choose a benchmark")
            raise SystemExit  # exit the program

    except Exception as e:
        print(e)
        print("ERROR: task creation")
        if debug_flag:
            breakpoint()
        raise

    return task_sets


def TDA(task_set):
    '''TDA analysis for a task set.
    Return True if succesful and False if not succesful.'''
    try:
        ana = a.Analyzer()
        # TDA.
        i = 1
        for task in task_set:
            # Prevent WCET = 0 since the scheduler can
            # not handle this yet. This case can occur due to
            # rounding with the transformer.
            if task.wcet == 0:
                raise ValueError("WCET == 0")
            task.rt = ana.tda(task, task_set[:(i - 1)])
            if task.rt > task.deadline:
                raise ValueError(
                    "TDA Result: WCRT bigger than deadline!")
            i += 1
    except ValueError as e:
        print(e)
        return False
    return True


def schedule_task_set(task_set, ce_chains, print_status=True):
    '''Return the schedule of some task_set.
    ce_chains is a list of ce_chains that will be computed later on.
    We need this to compute latency_upper_bound to determine the additional simulation time at the end.
    Note:
    - In case of error, None is returned.
    - E2E Davare has to be computed beforehand!'''

    try:
        # Preliminary: compute latency_upper_bound
        latency_upper_bound = max([ce.davare for ce in ce_chains])

        # Main part: Simulation part
        simulator = es.eventSimulator(task_set)

        # Determination of the variables used to compute the stop
        # condition of the simulation
        max_phase = max(task_set, key=lambda task: task.phase).phase
        max_period = max(task_set, key=lambda task: task.period).period
        hyper_period = a.Analyzer.determine_hyper_period(task_set)

        sched_interval = (
            2 * hyper_period + max_phase  # interval from paper
            + latency_upper_bound  # upper bound job chain length
            + max_period)  # for convenience

        if print_status:
            # Information for end user.
            print("\tNumber of tasks: ", len(task_set))
            print("\tHyperperiod: ", hyper_period)
            number_of_jobs = 0
            for task in task_set:
                number_of_jobs += sched_interval/task.period
            print("\tNumber of jobs to schedule: ",
                  "%.2f" % number_of_jobs)

        # Stop condition: Number of jobs of lowest priority task.
        simulator.dispatcher(
            int(math.ceil(sched_interval/task_set[-1].period)))

        # Simulation without early completion.
        schedule = simulator.e2e_result()

    except Exception as e:
        print(e)
        if debug_flag:
            breakpoint()
        schedule = None

    return schedule


def flatten(ce_ts_sched):
    '''Used to flatten the list ce_ts_sched'''
    ce_ts_sched_flat = [(ce, ts, sched)
                        for ce_lst, ts, sched in ce_ts_sched for ce in ce_lst]
    return ce_ts_sched_flat


def change_taskset_bcet(task_set, rat):
    '''Copy task set and change the wcet/bcet of each task by a given ratio.'''
    new_task_set = [task.copy() for task in task_set]
    for task in new_task_set:
        task.wcet = math.ceil(rat * task.wcet)
        task.bcet = math.ceil(rat * task.bcet)
    # Note: ceiling function makes sure there is never execution of 0
    return new_task_set


###############################
# Help functions for Analysis #
###############################
ana = a.Analyzer()

# Note:
# lst_flat = (ce, ts, sched)
# lst = ([ces], ts, sched)


def davare(lst_flat):
    ce = lst_flat[0]
    return ana.davare_single(ce)


def kloda(lst_flat):
    ce = lst_flat[0]
    hyper = ana.determine_hyper_period(lst_flat[1])
    return ana.kloda(ce, hyper)


def D19_mrt(lst_flat):
    ce = lst_flat[0]
    return ana.reaction_duerr_single(ce)


def D19_mda(lst_flat):
    ce = lst_flat[0]
    return ana.age_duerr_single(ce)


def G21_mda(lst_flat):
    sched = lst_flat[2]
    ts = lst_flat[1]
    ce = lst_flat[0]
    max_phase = max(t.phase for t in ts)
    hyper = ana.determine_hyper_period(ts)
    return ana.max_age_our(sched, ts, ce, max_phase, hyper, reduced=False)


def G21_mrda(lst_flat):
    sched = lst_flat[2]
    ts = lst_flat[1]
    ce = lst_flat[0]
    max_phase = max(t.phase for t in ts)
    hyper = ana.determine_hyper_period(ts)
    return ana.max_age_our(sched, ts, ce, max_phase, hyper, reduced=True)


def G21_mrt(lst_flat):
    sched = lst_flat[2]
    ts = lst_flat[1]
    ce = lst_flat[0]
    max_phase = max(t.phase for t in ts)
    hyper = ana.determine_hyper_period(ts)
    return ana.reaction_our(sched, ts, ce, max_phase, hyper)


def our_mrt_mRda(lst, bcet):
    '''Takes non-flattened list as input, because the schedules can be reused.'''
    ts = lst[1]  # wcet task set
    rat_ts = change_taskset_bcet(ts, bcet)  # bcet task set
    ce_lst = lst[0]  # list of ce chains
    if bcet != 0:  # the dispatcher can only handle execution != 0
        rat_sched = schedule_task_set(
            rat_ts, ce_lst, print_status=False)  # schedule with bcet
    else:
        rat_sched = a_our.execution_zero_schedule(rat_ts)
    sched = lst[2]  # schedule with wcet

    # maximum reaction time result
    mrt_res = [a_our.max_reac_local(
        ce, ts, sched, rat_ts, rat_sched) for ce in ce_lst]
    mRda_res = [a_our.max_age_local(
        ce, ts, sched, rat_ts, rat_sched) for ce in ce_lst]

    mda_res, mrda_res = list(zip(*mRda_res))
    mda_res = list(mda_res)  # maximum data age result
    mrda_res = list(mrda_res)  # maximum reduced data age result

    return (mrt_res, mda_res, mrda_res)


def let_mrt(lst_flat):
    '''analysis with LET communication policy'''
    return a_our.mrt_let(lst_flat[0], lst_flat[1])


def let_mRda(lst_flat):
    '''analysis with LET communication policy
    Note: Returns tuple of mda and mrda result.'''
    return a_our.mda_let(lst_flat[0], lst_flat[1])


def analyze_mixed_mrt(lst_inter, scenario):
    '''Analyze a mixed setup. 
    lst_inter is a list where each entry is a list of ce chain, task set and schedule
    '''

    e2e_latency = 0

    for entry, sc in zip(lst_inter, scenario[1]):
        if sc == 'impl':
            e2e_latency += entry[0].our_mrt[0]
        elif sc == 'let':
            e2e_latency += entry[0].let_mrt

    return e2e_latency


def analyze_mixed_mda(lst_inter, scenario):
    '''Analyze a mixed setup. 
    lst_inter is a list where each entry is a list of ce chain, task set and schedule
    '''

    e2e_latency = 0

    for entry, sc in zip(lst_inter, scenario[1]):
        if sc == 'impl':
            e2e_latency += entry[0].our_mda[0]
        elif sc == 'let':
            e2e_latency += entry[0].let_mda

    return e2e_latency


def analyze_mixed_mrda(lst_inter, scenario):
    '''Analyze a mixed setup. 
    lst_inter is a list where each entry is a list of ce chain, task set and schedule
    '''

    e2e_latency = 0

    for entry, sc in zip(lst_inter, scenario[1]):
        if sc == 'impl':
            e2e_latency += entry[0].our_mrda[0]
        elif sc == 'let':
            e2e_latency += entry[0].let_mrda

    return e2e_latency


#################
# Main function #
#################


def main():
    """Main Function."""
    ###
    # Argument Parser
    ###
    parser = argparse.ArgumentParser()

    # which part of code should be executed:
    parser.add_argument("-j", type=int, default=0)
    # utilization in 0 to 100 [percent]:
    parser.add_argument("-u", type=float, default=50)
    # task generation (0: WATERS Benchmark, 1: UUnifast):
    parser.add_argument("-g", type=int, default=0)

    # number of concurrent processes:
    parser.add_argument("-p", type=int, default=1)

    # only for args.j==1:
    # name of the run:
    parser.add_argument("-n", type=int, default=-1)
    # number of task sets to generate:
    parser.add_argument("-r", type=int, default=5)

    args = parser.parse_args()
    del parser

    if args.j == 10:
        """Create task sets, local cause-effect chains and produce schedule."""

        ###
        # Create task set.
        # output:
        ###
        print('=Task set generation')

        task_sets = task_set_generate(args.g, args.u, args.r)

        ###
        # CE-Chain generation.
        ###
        print('=CE-Chain generation')

        ce_chains = waters.gen_ce_chains(task_sets)
        # ce_chains contains one set of cause effect chains for each
        # task set in task_sets.

        # match both
        assert len(task_sets) == len(ce_chains)
        ce_ts = list(zip(ce_chains, task_sets))

        ###
        # Schedule generation
        ###
        print('=Schedule generation')

        # Preparation: TDA (for Davare)
        # Only take those that are succesful.
        ce_ts = [entry for entry in ce_ts if TDA(entry[1])]

        # Preparation: Davare (for schedule generation)
        ana = a.Analyzer()
        for ce, ts in ce_ts:
            ana.davare([ce])

        # Main: Generate the schedule # TODO do this with starmap
        schedules = [schedule_task_set(ts, ce) for ce, ts in ce_ts]

        # match ce_ts with schedules:
        assert len(ce_ts) == len(schedules)
        ce_ts_sched = [cets + (sched,)
                       for cets, sched in zip(ce_ts, schedules)]
        # Note: Each entry is now a 3-tuple of list of cause-effect chain,
        # corresponding task set, and corresponding schedule

        ###
        # Save the results
        ###
        print("=Save data.=")

        try:
            np.savez("output/1generation/ce_ts_sched_u="+str(args.u)
                     + "_n=" + str(args.n)
                     + "_g=" + str(args.g) + ".npz", gen=ce_ts_sched)

        except Exception as e:
            print(e)
            print("ERROR: save")
            if debug_flag:
                breakpoint()
            else:
                return

    elif args.j == 11:
        '''Implicit communication analyses.

        Input:
        - args.u
        - args.n
        - args.g
        - args.p
        '''

        ###
        # Load data
        ###
        print(time_now(), "= Load data =")

        filename = ("output/1generation/ce_ts_sched_u="+str(args.u)
                    + "_n=" + str(args.n)
                    + "_g=" + str(args.g) + ".npz")
        data = np.load(filename, allow_pickle=True)
        ce_ts_sched = data.f.gen  # this one is used

        ce_ts_sched_flat = flatten(ce_ts_sched)  # this one is used

        ###
        # Other analyses
        # - Davare
        # - Kloda
        # - D19
        # - G21
        ###
        # ana = a.Analyzer()
        print(time_now(), '= Other analyses =')

        ###
        # ==Davare
        print(time_now(), 'Davare')

        # Get result
        with Pool(args.p) as p:
            res_davare = p.map(davare, ce_ts_sched_flat)

        # Set results
        assert len(res_davare) == len(ce_ts_sched_flat)
        for res, entry in zip(res_davare, ce_ts_sched_flat):
            entry[0].davare = res

        ###
        # ==Kloda
        print(time_now(), 'Kloda')

        # Get result
        with Pool(args.p) as p:
            res_kloda = p.map(kloda, ce_ts_sched_flat)

        # Set results
        assert len(res_kloda) == len(ce_ts_sched_flat)
        for res, entry in zip(res_kloda, ce_ts_sched_flat):
            entry[0].kloda = res

        ###
        # ==Duerr (D19): MDA
        print(time_now(), 'D19: MDA')

        # Get result
        with Pool(args.p) as p:
            res_d19_mda = p.map(D19_mda, ce_ts_sched_flat)

        # Set results
        assert len(res_d19_mda) == len(ce_ts_sched_flat)
        for res, entry in zip(res_d19_mda, ce_ts_sched_flat):
            entry[0].d19_mrda = res

        # ==Duerr (D19): MRT
        print(time_now(), 'D19: MRT')

        # Get result
        with Pool(args.p) as p:
            res_d19_mrt = p.map(D19_mrt, ce_ts_sched_flat)

        # Set results
        assert len(res_d19_mrt) == len(ce_ts_sched_flat)
        for res, entry in zip(res_d19_mrt, ce_ts_sched_flat):
            entry[0].d19_mrt = res

        ###
        # ==Guenzel (G21): MDA
        print(time_now(), 'G21: MDA')

        # Get result
        with Pool(args.p) as p:
            res_g21_mda = p.map(G21_mda, ce_ts_sched_flat)

        # Set results
        assert len(res_g21_mda) == len(ce_ts_sched_flat)
        for res, entry in zip(res_g21_mda, ce_ts_sched_flat):
            entry[0].g21_mda = res

        # ==Guenzel (G21): MRDA
        print(time_now(), 'G21: MRDA')

        # Get result
        with Pool(args.p) as p:
            res_g21_mrda = p.map(G21_mrda, ce_ts_sched_flat)

        # Set results
        assert len(res_g21_mrda) == len(ce_ts_sched_flat)
        for res, entry in zip(res_g21_mrda, ce_ts_sched_flat):
            entry[0].g21_mrda = res

        # ==Guenzel (G21): MRT
        print(time_now(), 'G21: MRT')

        # Get result
        with Pool(args.p) as p:
            res_g21_mrt = p.map(G21_mrt, ce_ts_sched_flat)

        # Set results
        assert len(res_g21_mrt) == len(ce_ts_sched_flat)
        for res, entry in zip(res_g21_mrt, ce_ts_sched_flat):
            entry[0].g21_mrt = res

        # print(ce_ts_sched_flat[0][0].g21_mda, ce_ts_sched_flat[0][0].g21_mrda,
        #       ce_ts_sched_flat[0][0].g21_mrt)
        # breakpoint()

        ###
        # Our analysis
        ###

        # Note: given some bcet ratio, make new schedule, analyse, put value to ce chain.

        print(time_now(), '= Our analysis =')

        bcet_ratios = [1.0, 0.7, 0.3, 0.0]

        # Add dictionary for each cause-effect chain
        for ce, _, _ in ce_ts_sched_flat:
            ce.our_mrt = dict()
            ce.our_mda = dict()
            ce.our_mrda = dict()

        for bcet in bcet_ratios:
            print(time_now(), 'BCET/WCET =', bcet)

            # Get result
            with Pool(args.p) as p:
                res_our = p.starmap(our_mrt_mRda, zip(
                    ce_ts_sched, itertools.repeat(bcet)))

            # Set results
            assert len(res_our) == len(ce_ts_sched)
            for res, entry in zip(res_our, ce_ts_sched):
                for idxx, ce in enumerate(entry[0]):
                    ce.our_mrt[bcet] = res[0][idxx]
                    ce.our_mda[bcet] = res[1][idxx]
                    ce.our_mrda[bcet] = res[2][idxx]

        print(ce_ts_sched_flat[0][0].our_mrt,
              ce_ts_sched_flat[0][0].our_mda,
              ce_ts_sched_flat[0][0].our_mrda)

        # breakpoint()

        ###
        # Store data
        ###
        print(time_now(), '= Store data =')

        output_filename = ("output/2implicit/ce_ts_sched_u=" + str(args.u) +
                           "_n=" + str(args.n) + "_g=" + str(args.g) + ".npz")
        np.savez(output_filename, gen=ce_ts_sched)

        print(time_now(), '= Done =')

    if args.j == 12:
        '''mixed setup evaluation -- interconnected
        Note:
        - for implicit we assume BCET/WCET = 0
        '''

        scenarios = [
            [2, ['impl', 'let']],
            [2, ['let', 'impl']],
            [4, ['impl', 'let', 'impl', 'let']],
            [4, ['let', 'impl', 'let', 'impl']],
        ]

        ###
        # Load data
        ###
        print(time_now(), "= Load data =")

        filename = ("output/2implicit/ce_ts_sched_u="+str(args.u)
                    + "_n=" + str(args.n)
                    + "_g=" + str(args.g) + ".npz")
        data = np.load(filename, allow_pickle=True)
        ce_ts_sched = data.f.gen  # this one is used

        ce_ts_sched_flat = flatten(ce_ts_sched)  # this one is used

        ###
        # Make interconnected mixed chain
        ###
        nmb_inter = 10

        ce_ts_sched_inter = []

        for nmb_sc, _ in scenarios:
            ce_ts_sched_inter.append([random.sample(
                ce_ts_sched_flat, nmb_sc) for _ in range(nmb_inter)])
            # Note: each entry is a list of nmb_sc ce chains with corresponding task set and schedule

        assert len(ce_ts_sched_inter) == len(scenarios)

        ###
        # Analyze
        ###
        print(time_now(), '= Analysis =')

        # == LET: MRT
        print(time_now(), 'LET: MRT')

        # Get result
        with Pool(args.p) as p:
            res_let_mrt = p.map(let_mrt, ce_ts_sched_flat)

        # Set results
        assert len(res_let_mrt) == len(ce_ts_sched_flat)
        for res, entry in zip(res_let_mrt, ce_ts_sched_flat):
            entry[0].let_mrt = res

        # == LET: M(R)DA
        print(time_now(), 'LET: M(R)DA')

        # Get result
        with Pool(args.p) as p:
            res_let_mRda = p.map(let_mRda, ce_ts_sched_flat)

        # Set results
        assert len(res_let_mRda) == len(ce_ts_sched_flat)
        for res, entry in zip(res_let_mRda, ce_ts_sched_flat):
            entry[0].let_mda = res[0]
            entry[0].let_mrda = res[1]

        # == mixed scenario
        print(time_now(), 'Mixed Scenarios')

        final_results = []

        for sc, entry_inter in zip(scenarios, ce_ts_sched_inter):
            # Get result
            with Pool(args.p) as p:
                res_mix_mrt = p.starmap(analyze_mixed_mrt, zip(
                    entry_inter, itertools.repeat(sc)))
                res_mix_mda = p.starmap(analyze_mixed_mda, zip(
                    entry_inter, itertools.repeat(sc)))
                res_mix_mrda = p.starmap(analyze_mixed_mrda, zip(
                    entry_inter, itertools.repeat(sc)))

            # Set results
            assert len(res_mix_mrt) == len(entry_inter)
            assert len(res_mix_mda) == len(entry_inter)
            assert len(res_mix_mrda) == len(entry_inter)

            final_results.append([res_mix_mrt, res_mix_mda, res_mix_mrda])

        # # DEBUG
        # this, this_ts, _ = ce_ts_sched_inter[0][0][1]
        # print(this.chain, [t.period for t in this.chain],
        #       this.let_mrt, this.let_mda, this.let_mrda)
        # breakpoint()

        # a_our.mda_let(this, this_ts)

        ###
        # Store data
        ###
        print(time_now(), '= Store data =')
        output_filename = ("output/3mixedinter/inter_res_u=" + str(args.u) +
                           "_n=" + str(args.n) + "_g=" + str(args.g) + ".npz")
        np.savez(output_filename, result=final_results, scenarios=scenarios)

        print(time_now(), '= Done =')

    if args.j == 13:
        '''mixed setup evaluation -- intraconnected
        '''

        ###
        # Load data
        ###

        ###
        # Make intraconnected mixed chain
        ###

        ###
        # Analyze
        ###

        ###
        # Store data
        ###

    if args.j == 0:
        """Comparison IMPLICIT COMMUNICATION.

        Required arguments:
        -j1
        -u : utilization [%]
        -g : task generation setting
        -r : number of runs
        -n : name of the run

        Create task sets and cause-effect chains, use TDA, Davare, D19, G21,
        Our analysis, and save the data
        """
        ###
        # Task set and intra-ecu cause-effect chain generation.
        # TODO: include phase
        ###
        print("=Task set and cause-effect chain generation.=")

        # Create args.r task sets

        try:
            if args.g == 0:
                # WATERS benchmark
                print("WATERS benchmark.")

                # Statistical distribution for task set generation from table 3
                # of WATERS free benchmark paper.
                profile = [0.03 / 0.85, 0.02 / 0.85, 0.02 / 0.85, 0.25 / 0.85,
                           0.25 / 0.85, 0.03 / 0.85, 0.2 / 0.85, 0.01 / 0.85,
                           0.04 / 0.85]
                # Required utilization:
                req_uti = args.u/100.0
                # Maximal difference between required utilization and actual
                # utilization is set to 1 percent:
                threshold = 1.0

                # Create task sets from the generator.
                # Each task is a dictionary.
                print("\tCreate task sets.")
                task_sets_waters = []
                while len(task_sets_waters) < args.r:
                    task_sets_gen = waters.gen_tasksets(
                        1, req_uti, profile, True, threshold/100.0, 4)
                    task_sets_waters.append(task_sets_gen[0])

                # Transform tasks to fit framework structure.
                # Each task is an object of utilities.task.Task.
                trans1 = trans.Transformer("1", task_sets_waters, 10000000)
                task_sets = trans1.transform_tasks(False)

            elif args.g == 1:
                # UUniFast benchmark.
                print("UUniFast benchmark.")

                # Create task sets from the generator.
                print("\tCreate task sets.")

                # The following can be used for task generation with the
                # UUniFast benchmark without predefined periods.

                # # Generate log-uniformly distributed task sets:
                # task_sets_generator = uunifast.gen_tasksets(
                #         5, args.r, 1, 100, args.u, rounded=True)

                # Generate log-uniformly distributed task sets with predefined
                # periods:
                periods = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
                # Interval from where the generator pulls log-uniformly.
                min_pull = 1
                max_pull = 2000

                task_sets_uunifast = uunifast.gen_tasksets_pred(
                    50, args.r, min_pull, max_pull, args.u/100.0, periods)

                # Transform tasks to fit framework structure.
                trans2 = trans.Transformer("2", task_sets_uunifast, 10000000)
                task_sets = trans2.transform_tasks(False)

            else:
                print("Choose a benchmark")
                return

            # Create cause effect chains.
            print("\tCreate cause-effect chains")
            ce_chains = waters.gen_ce_chains(task_sets)
            # ce_chains contains one set of cause effect chains for each
            # task set in task_sets.

        except Exception as e:
            print(e)
            print("ERROR: task + ce creation")
            if debug_flag:
                breakpoint()
            else:
                task_sets = []
                ce_chains = []

        ###
        # Old Analyses.
        ###
        print("=Old analyses.=")
        analyzer = a.Analyzer("0")

        try:
            ###
            # TDA for each task set.
            ###
            print("TDA.")
            for idxx in range(len(task_sets)):
                try:
                    # TDA.
                    i = 1
                    for task in task_sets[idxx]:
                        # Prevent WCET = 0 since the scheduler can
                        # not handle this yet. This case can occur due to
                        # rounding with the transformer.
                        if task.wcet == 0:
                            raise ValueError("WCET == 0")
                        task.rt = analyzer.tda(task, task_sets[idxx][:(i - 1)])
                        if task.rt > task.deadline:
                            raise ValueError(
                                "TDA Result: WCRT bigger than deadline!")
                        i += 1
                except ValueError:
                    # If TDA fails, remove task and chain set and continue.
                    task_sets.remove(task_sets[idxx])
                    ce_chains.remove(ce_chains[idxx])
                    continue

            ###
            # Numerical End-to-End Analyses.
            # Note: also used to find fitting length of schedule interval
            ###
            print("=Numerical Analyses")
            print("Test: Davare.")
            analyzer.davare(ce_chains)

            print("Test: Duerr Reaction Time.")
            analyzer.reaction_duerr(ce_chains)

            print("Test: Duerr Data Age.")
            analyzer.age_duerr(ce_chains)

            ###
            # Simulation based Analyses.
            ###
            print("=Simulation based Analyses.=")

            schedules = []
            for i, task_set in enumerate(task_sets):
                print("=Task set ", i+1)

                # Skip if there is no corresponding cause-effect chain.
                if len(ce_chains[i]) == 0:
                    continue

                # Event-based simulation.
                print("Simulation.")

                simulator = es.eventSimulator(task_set)

                # Determination of the variables used to compute the stop
                # condition of the simulation
                max_e2e_latency = max(ce_chains[i], key=lambda chain:
                                      chain.davare).davare
                max_phase = max(task_set, key=lambda task: task.phase).phase
                max_period = max(task_set, key=lambda task: task.period).period
                hyper_period = analyzer.determine_hyper_period(task_set)

                sched_interval = (
                    2 * hyper_period + max_phase  # interval from paper
                    + max_e2e_latency  # upper bound job chain length
                    + max_period)  # for convenience

                # Information for end user.
                print("\tNumber of tasks: ", len(task_set))
                print("\tHyperperiod: ", hyper_period)
                number_of_jobs = 0
                for task in task_set:
                    number_of_jobs += sched_interval/task.period
                print("\tNumber of jobs to schedule: ",
                      "%.2f" % number_of_jobs)

                # Stop condition: Number of jobs of lowest priority task.
                simulator.dispatcher(
                    int(math.ceil(sched_interval/task_set[-1].period)))

                # Simulation without early completion.
                schedule = simulator.e2e_result()
                schedules.append(schedule)

                # Analyses.
                for chain in ce_chains[i]:
                    print("Test: G21 Data Age.")
                    analyzer.max_age_our(schedule, task_set, chain, max_phase,
                                         hyper_period, reduced=False)
                    analyzer.max_age_our(schedule, task_set, chain, max_phase,
                                         hyper_period, reduced=True)

                    print("Test: G21 Reaction Time.")
                    analyzer.reaction_our(schedule, task_set, chain, max_phase,
                                          hyper_period)

                    # Kloda analysis, assuming synchronous releases.
                    print("Test: Kloda.")
                    analyzer.kloda(chain, hyper_period)

                    # # TODO remove here
                    # # LET anlysis
                    # a_our.mrt_let(chain, task_set)

                    # # Test.
                    # if chain.kloda < chain.our_react:
                    #     if debug_flag:
                    #         breakpoint()
                    #     else:
                    #         raise ValueError(
                    #             ".kloda is shorter than .our_react")

            ###
            # Our Maximum data age and maximum reaction time analysis
            # for different BCET/WCET-ratios we compare the performance of our method.
            ###

            # make bcet task sets
            bcet_ratios = [1.0, 0.7, 0.3, 0.0]

            def change_taskset_bcet(task_set, rat):
                new_task_set = [task.copy() for task in task_set]
                for task in new_task_set:
                    task.wcet = math.ceil(rat * task.wcet)
                    task.bcet = math.ceil(rat * task.bcet)
                return new_task_set

            # make bcet task sets
            all_bcet_task_sets = [[change_taskset_bcet(
                task_set, rat) for rat in bcet_ratios] for task_set in task_sets]

            # simulate
            for idxx, bcet_task_sets, task_set in zip(itertools.count(), all_bcet_task_sets, task_sets):
                schedule = schedules[idxx]  # WCET schedule (computed above)

                # Determination of the variables used to compute the stop
                # condition of the simulation
                max_e2e_latency = max(ce_chains[idxx], key=lambda chain:
                                      chain.davare).davare
                max_phase = max(task_set, key=lambda task: task.phase).phase
                max_period = max(task_set, key=lambda task: task.period).period
                hyper_period = analyzer.determine_hyper_period(task_set)

                sched_interval = (
                    2 * hyper_period + max_phase  # interval from paper
                    + max_e2e_latency  # upper bound job chain length
                    + max_period)  # for convenience

                bcet_schedules = []
                for bcet_task_set, bcet_rat in zip(bcet_task_sets, bcet_ratios):
                    if bcet_rat > 0:
                        # make the simulator
                        simulator = es.eventSimulator(bcet_task_set)

                        # Simulate! # TODO make schedule for execution 0 manually!
                        # Stop condition: Number of jobs of lowest priority task.
                        simulator.dispatcher(
                            int(math.ceil(sched_interval/task_set[-1].period)))

                        # Schedules for the task sets with reduced wcet
                        bcet_schedules.append(simulator.e2e_result())
                    else:
                        bcet_schedules.append(
                            a_our.execution_zero_schedule(bcet_task_set))

                # breakpoint()
                # Do the analyses:
                for id, chain in enumerate(ce_chains[idxx]):
                    chain.our_analysis_mrt_bcet = []
                    chain.our_analysis_mda_bcet = []
                    chain.our_analysis_mrda_bcet = []

                    for bc_ts, bc_sched in zip(bcet_task_sets, bcet_schedules):
                        mrt_latency = a_our.max_reac_local(
                            chain, task_set, schedule, bc_ts, bc_sched)
                        mda_latency, mrda_latency = a_our.max_age_local(
                            chain, task_set, schedule, bc_ts, bc_sched)

                        chain.our_analysis_mrt_bcet.append(mrt_latency)
                        chain.our_analysis_mda_bcet.append(mda_latency)
                        chain.our_analysis_mrda_bcet.append(mrda_latency)

                    print(id, chain.davare, chain.duerr_react, chain.kloda,
                          chain.our_analysis_mrt_bcet[::-1],
                          # chain.our_analysis_mda_bcet[::-1], chain.our_analysis_mrda_bcet[::-1],
                          chain.our_react,
                          chain.mrt_let)

                ################################

                breakpoint()

        except Exception as e:
            print(e)
            print("ERROR: analysis")
            if debug_flag:
                breakpoint()
            else:
                task_sets = []
                ce_chains = []

        ###
        # Save the results
        ###
        print("=Save data.=")

        try:
            np.savez("output/1single/task_set_u="+str(args.u)
                     + "_n=" + str(args.n)
                     + "_g=" + str(args.g) + ".npz", task_sets=task_sets,
                     chains=ce_chains)
        except Exception as e:
            print(e)
            print("ERROR: save")
            if debug_flag:
                breakpoint()
            else:
                return

    if args.j == 1:
        """Single ECU analysis.

        Required arguments:
        -j1
        -u : utilization [%]
        -g : task generation setting
        -r : number of runs
        -n : name of the run

        Create task sets and cause-effect chains, use TDA, Davare, Duerr, our
        analysis, Kloda, and save the Data
        """
        ###
        # Task set and cause-effect chain generation.
        ###
        print("=Task set and cause-effect chain generation.=")

        try:
            if args.g == 0:
                # WATERS benchmark
                print("WATERS benchmark.")

                # Statistical distribution for task set generation from table 3
                # of WATERS free benchmark paper.
                profile = [0.03 / 0.85, 0.02 / 0.85, 0.02 / 0.85, 0.25 / 0.85,
                           0.25 / 0.85, 0.03 / 0.85, 0.2 / 0.85, 0.01 / 0.85,
                           0.04 / 0.85]
                # Required utilization:
                req_uti = args.u/100.0
                # Maximal difference between required utilization and actual
                # utilization is set to 1 percent:
                threshold = 1.0

                # Create task sets from the generator.
                # Each task is a dictionary.
                print("\tCreate task sets.")
                task_sets_waters = []
                while len(task_sets_waters) < args.r:
                    task_sets_gen = waters.gen_tasksets(
                        1, req_uti, profile, True, threshold/100.0, 4)
                    task_sets_waters.append(task_sets_gen[0])

                # Transform tasks to fit framework structure.
                # Each task is an object of utilities.task.Task.
                trans1 = trans.Transformer("1", task_sets_waters, 10000000)
                task_sets = trans1.transform_tasks(False)

            elif args.g == 1:
                # UUniFast benchmark.
                print("UUniFast benchmark.")

                # Create task sets from the generator.
                print("\tCreate task sets.")

                # The following can be used for task generation with the
                # UUniFast benchmark without predefined periods.

                # # Generate log-uniformly distributed task sets:
                # task_sets_generator = uunifast.gen_tasksets(
                #         5, args.r, 1, 100, args.u, rounded=True)

                # Generate log-uniformly distributed task sets with predefined
                # periods:
                periods = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
                # Interval from where the generator pulls log-uniformly.
                min_pull = 1
                max_pull = 2000

                task_sets_uunifast = uunifast.gen_tasksets_pred(
                    50, args.r, min_pull, max_pull, args.u/100.0, periods)

                # Transform tasks to fit framework structure.
                trans2 = trans.Transformer("2", task_sets_uunifast, 10000000)
                task_sets = trans2.transform_tasks(False)

            else:
                print("Choose a benchmark")
                return

            # Create cause effect chains.
            print("\tCreate cause-effect chains")
            ce_chains = waters.gen_ce_chains(task_sets)
            # ce_chains contains one set of cause effect chains for each
            # task set in task_sets.

        except Exception as e:
            print(e)
            print("ERROR: task + ce creation")
            if debug_flag:
                breakpoint()
            else:
                task_sets = []
                ce_chains = []

        ###
        # First analyses (TDA, Davare, Duerr).
        ###
        print("=First analyses (TDA, Davare, Duerr).=")
        analyzer = a.Analyzer("0")

        try:
            # TDA for each task set.
            print("TDA.")
            for idxx in range(len(task_sets)):
                try:
                    # TDA.
                    i = 1
                    for task in task_sets[idxx]:
                        # Prevent WCET = 0 since the scheduler can
                        # not handle this yet. This case can occur due to
                        # rounding with the transformer.
                        if task.wcet == 0:
                            raise ValueError("WCET == 0")
                        task.rt = analyzer.tda(task, task_sets[idxx][:(i - 1)])
                        if task.rt > task.deadline:
                            raise ValueError(
                                "TDA Result: WCRT bigger than deadline!")
                        i += 1
                except ValueError:
                    # If TDA fails, remove task and chain set and continue.
                    task_sets.remove(task_sets[idxx])
                    ce_chains.remove(ce_chains[idxx])
                    continue

            # End-to-End Analyses.
            print("Test: Davare.")
            analyzer.davare(ce_chains)

            print("Test: Duerr Reaction Time.")
            analyzer.reaction_duerr(ce_chains)

            print("Test: Duerr Data Age.")
            analyzer.age_duerr(ce_chains)

            ###
            # Second analyses (Simulation, Our, Kloda).
            ###
            print("=Second analyses (Simulation, Our, Kloda).=")
            i = 0  # task set counter
            schedules = []
            for task_set in task_sets:
                print("=Task set ", i+1)

                # Skip if there is no corresponding cause-effect chain.
                if len(ce_chains[i]) == 0:
                    continue

                # Event-based simulation.
                print("Simulation.")

                simulator = es.eventSimulator(task_set)

                # Determination of the variables used to compute the stop
                # condition of the simulation
                max_e2e_latency = max(ce_chains[i], key=lambda chain:
                                      chain.davare).davare
                max_phase = max(task_set, key=lambda task: task.phase).phase
                max_period = max(task_set, key=lambda task: task.period).period
                hyper_period = analyzer.determine_hyper_period(task_set)

                sched_interval = (
                    2 * hyper_period + max_phase  # interval from paper
                    + max_e2e_latency  # upper bound job chain length
                    + max_period)  # for convenience

                # Information for end user.
                print("\tNumber of tasks: ", len(task_set))
                print("\tHyperperiod: ", hyper_period)
                number_of_jobs = 0
                for task in task_set:
                    number_of_jobs += sched_interval/task.period
                print("\tNumber of jobs to schedule: ",
                      "%.2f" % number_of_jobs)

                # Stop condition: Number of jobs of lowest priority task.
                simulator.dispatcher(
                    int(math.ceil(sched_interval/task_set[-1].period)))

                # Simulation without early completion.
                schedule = simulator.e2e_result()
                schedules.append(schedule)

                # Analyses.
                for chain in ce_chains[i]:
                    print("Test: Our Data Age.")
                    analyzer.max_age_our(schedule, task_set, chain, max_phase,
                                         hyper_period, reduced=False)
                    analyzer.max_age_our(schedule, task_set, chain, max_phase,
                                         hyper_period, reduced=True)

                    print("Test: Our Reaction Time.")
                    analyzer.reaction_our(schedule, task_set, chain, max_phase,
                                          hyper_period)

                    # Kloda analysis, assuming synchronous releases.
                    print("Test: Kloda.")
                    analyzer.kloda(chain, hyper_period)

                    # Test.
                    if chain.kloda < chain.our_react:
                        if debug_flag:
                            breakpoint()
                        else:
                            raise ValueError(
                                ".kloda is shorter than .our_react")
                i += 1
        except Exception as e:
            print(e)
            print("ERROR: analysis")
            if debug_flag:
                breakpoint()
            else:
                task_sets = []
                ce_chains = []

        ###
        # Save data.
        ###
        print("=Save data.=")

        try:
            np.savez("output/1single/task_set_u="+str(args.u)
                     + "_n=" + str(args.n)
                     + "_g=" + str(args.g) + ".npz", task_sets=task_sets,
                     chains=ce_chains)
        except Exception as e:
            print(e)
            print("ERROR: save")
            if debug_flag:
                breakpoint()
            else:
                return

    elif args.j == 2:
        """Interconnected ECU analysis.

        Required arguments:
        -j2
        -u : utilization (for loading)
        -g : task generation setting (for loading)

        Load data, create interconnected chains and then do the analysis by
        Davare, Duerr and Our.
        """

        if args.n == -1:
            print("ERROR: The number of runs -n is not specified.")
            return

        # Variables.
        utilization = args.u
        gen_setting = args.g
        num_runs = args.n
        number_interconn_ce_chains = 10000

        try:
            ###
            # Load data.
            ###
            print("=Load data.=")
            chains_single_ECU = []
            for i in range(num_runs):
                name_of_the_run = str(i)
                data = np.load(
                    "output/1single/task_set_u=" + str(utilization)
                    + "_n=" + name_of_the_run
                    + "_g=" + str(gen_setting)
                    + ".npz", allow_pickle=True)
                for chain_set in data.f.chains:
                    for chain in chain_set:
                        chains_single_ECU.append(chain)

                # Close data file and run the garbage collector.
                data.close()
                del data
                gc.collect()
        except Exception as e:
            print(e)
            print("ERROR: inputs from single are missing")
            if debug_flag:
                breakpoint()
            else:
                return

        ###
        # Interconnected cause-effect chain generation.
        ###
        print("=Interconnected cause-effect chain generation.=")
        chains_inter = []
        for j in range(0, number_interconn_ce_chains):
            chain_all = []  # sequence of all tasks (from chains + comm tasks)
            i_chain_all = []  # sequence of chains and comm_tasks

            # Generate communication tasks.
            com_tasks = comm.generate_communication_taskset(20, 10, 1000, True)

            # Fill chain_all and i_chain_all.
            k = 0
            for chain in list(np.random.choice(
                    chains_single_ECU, 5, replace=False)):  # randomly choose 5
                i_chain_all.append(chain)
                for task in chain.chain:
                    chain_all.append(task)
                if k < 4:  # communication tasks are only added in between
                    chain_all.append(com_tasks[k])
                    i_chain_all.append(com_tasks[k])
                k += 1

            chains_inter.append(c.CauseEffectChain(0, chain_all, i_chain_all))

            # End user notification
            if j % 100 == 0:
                print("\t", j)

        ###
        # Analyses (Davare, Duerr, Our).
        # Kloda is not included, since it is only for synchronized clocks.
        ###
        print("=Analyses (Davare, Duerr, Our).=")
        analyzer = a.Analyzer("0")

        print("Test: Davare.")
        analyzer.davare([chains_inter])

        print("Test: Duerr.")
        analyzer.reaction_duerr([chains_inter])
        analyzer.age_duerr([chains_inter])

        print("Test: Our.")
        # Our test can only be used when the single processor tests are already
        # done.
        analyzer.max_age_inter_our(chains_inter, reduced=True)
        analyzer.reaction_inter_our(chains_inter)

        ###
        # Save data.
        ###
        print("=Save data.=")
        np.savez(
            "./output/2interconn/chains_" + "u=" + str(utilization)
            + "_g=" + str(gen_setting) + ".npz",
            chains_inter=chains_inter, chains_single_ECU=chains_single_ECU)

    elif args.j == 3:
        """Evaluation.

        Required arguments:
        -j3
        -g : task generation setting (for loading)
        """
        # Variables.
        gen_setting = args.g
        utilizations = [50.0, 60.0, 70.0, 80.0, 90.0]

        try:
            ###
            # Load data.
            ###
            print("=Load data.=")
            chains_single_ECU = []
            chains_inter = []
            for ut in utilizations:
                data = np.load(
                    "output/2interconn/chains_" + "u=" + str(ut)
                    + "_g=" + str(args.g) + ".npz", allow_pickle=True)

                # Single ECU.
                for chain in data.f.chains_single_ECU:
                    chains_single_ECU.append(chain)

                # Interconnected.
                for chain in data.f.chains_inter:
                    chains_inter.append(chain)

                # Close data file and run the garbage collector.
                data.close()
                del data
                gc.collect()
        except Exception as e:
            print(e)
            print("ERROR: inputs for plotter are missing")
            if debug_flag:
                breakpoint()
            else:
                return

        ###
        # Draw plots.
        ###
        print("=Draw plots.=")

        myeva = eva.Evaluation()

        # Single ECU Plot.
        myeva.davare_boxplot_age(
            chains_single_ECU,
            "output/3plots/davare_single_ecu_age"
            + "_g=" + str(args.g) + ".pdf",
            xaxis_label="", ylabel="Latency reduction [%]")
        myeva.davare_boxplot_reaction(
            chains_single_ECU,
            "output/3plots/davare_single_ecu_reaction"
            + "_g=" + str(args.g) + ".pdf",
            xaxis_label="", ylabel="Latency reduction [%]")

        # Interconnected ECU Plot.
        myeva.davare_boxplot_age_interconnected(
            chains_inter,
            "output/3plots/davare_interconnected_age"
            + "_g=" + str(args.g) + ".pdf",
            xaxis_label="", ylabel="Latency reduction [%]")
        myeva.davare_boxplot_reaction_interconnected(
            chains_inter,
            "output/3plots/davare_interconnected_reaction"
            + "_g=" + str(args.g) + ".pdf",
            xaxis_label="", ylabel="Latency reduction [%]")

        # # Heatmap.
        # myeva.heatmap_improvement_disorder_age(
        #         chains_single_ECU,
        #         "output/3plots/heatmap" + "_our_age"
        #         + "_g=" + str(args.g) + ".pdf",
        #         yaxis_label="")
        # myeva.heatmap_improvement_disorder_react(
        #         chains_single_ECU,
        #         "output/3plots/heatmap" + "_our_react"
        #         + "_g=" + str(args.g) + ".pdf",
        #         yaxis_label="")


if __name__ == '__main__':
    main()
