"""Our Analysis"""
from cechains.chain import CEChain
from tasks.task import Task
import math


def _cut_chain(ch):
    """Cut chain into parts with same configuration."""
    new_chains = []
    for tsk in ch:
        if 'curr_comm' not in vars() or tsk.comm.type != curr_comm:
            curr_comm = tsk.comm.type
            new_chains.append(CEChain(tsk))
        else:
            new_chains[-1].append(tsk)
    return new_chains


def cut_based(chain, LET=None, impl=None):
    """Our cutting theorem based analysis."""
    base_analyses = {  # TODO add other analyses
        'duerr': None,
    }  # Base analyses that can be utilized for LET and implicit communication analysis

    # cut chain
    cutted_chain = _cut_chain(chain)

    # perform analysis
    result = 0
    for ch in cutted_chain:
        comm = ch.check_feature('comm')  # check communication
        if comm == 'impl':
            result += base_analyses[impl](ch)
        elif comm == 'LET':
            result += base_analyses[LET](ch)
        else:
            raise RuntimeError(f'The communication behavior {comm=} is not covered by the analysis.')

    return result


def prin_based(chain, switch=None):
    """Our principle based analysis."""
    # Determine the code switch
    if switch in ('periodic', 'sporadic'):
        pass
    else:
        switch = chain.check_feature('rel')

    # Choose correct analysis
    if switch == 'periodic':
        return _prin_based_periodic(chain)
    elif switch == 'sporadic':
        return _prin_based_sporadic()
    else:
        raise ValueError(f"{switch} release behavior in chain cannot be handled by our analysis.")


def _prin_based_periodic(chain):
    """Our principle based analysis for periodic tasks."""
    # Compute hyperperiod:
    hyper = chain.base_ts.hyperperiod()
    max_phase = chain.base_ts.max_phase()

    zvar = chain[0].rel.phase
    lengths = []

    while zvar <= max_phase + hyper:
        # read-event at z
        # compute length of one job chain
        relvar = zvar + chain[0].rel.period  # first job in job chain
        for this_tsk, next_tsk in zip(chain[:-1], chain[1:]):
            # Compute release of next job in the job chain
            relvar = _next_release_job_chain(relvar, this_tsk, next_tsk, chain.base_ts)
        # actuation event at zprime
        if chain[-1].comm.type == 'impl':
            zprimevar = relvar + chain.base_ts.wcrt[chain[-1]]
        elif chain[-1].comm.type == 'LET':
            zprimevar = relvar + chain[-1].dl.dl
        lengths.append(zprimevar - zvar)

        zvar += chain[0].rel.period  # next job

    return max(lengths)


def _next_release_job_chain(curr_rel, curr_tsk, nxt_tsk, task_set):
    """Upper bound on the release time of the next job in the chain.
    Current job is from curr_tsk and released no later than at time curr_rel.
    nxt_tsk is the task of the next job."""
    # Cases from Table 1
    if curr_tsk.comm.type == 'impl' and nxt_tsk.comm.type == 'impl':
        if task_set.higher_prio(curr_tsk, nxt_tsk):
            return _release_after(curr_rel, nxt_tsk)
        else:
            return _release_after(curr_rel + task_set.wcrts[curr_tsk], nxt_tsk)
    elif curr_tsk.comm.type == 'impl' and nxt_tsk.comm.type == 'LET':
        return _release_after(curr_rel + task_set.wcrts[curr_tsk], nxt_tsk)
    elif curr_tsk.comm.type == 'LET':
        return _release_after(curr_rel + curr_tsk.dl.dl, nxt_tsk)
    else:
        raise ValueError(
            f"The communication pattern {curr_tsk.comm.type=} and {nxt_tsk.comm.type=} is not covered by the analysis")


def _release_after(time, tsk):
    """Next release of tsk at or after 'time' for periodic tasks."""
    return math.ceil((time - tsk.rel.phase) / tsk.rel.period) * tsk.rel.period


def _prin_based_sporadic(chain):
    """Our principle based analysis for sporadic tasks."""

    if __debug__:
        """Ensure that each communication type is LET or impl"""
        for tsk in chain:
            assert tsk.comm.type in ('impl', 'LET'), f"{tsk.comm.type=} expected to be in ('impl', 'LET')"

    if not hasattr(chain.base_ts.wcrts):
        """Ensure that wcrts are computed."""
        chain.base_ts.compute_wcrts()
        if __debug__:
            print("Compute WCRTs")

    result = 0
    for idx, tsk in enumerate(chain):
        # inter-arrival time part
        result += tsk.rel.maxiat
        # additional part
        if tsk.comm.type == 'LET':
            result += tsk.dl.dl
        elif (idx != len(chain) - 1 and  # not the last task
              chain[idx + 1].comm.type == 'impl' and  # both are implicit
              chain.base_ts.higher_prio(tsk, chain[idx + 1])):  # next has lower priority
            result += 0
        else:
            result += chain.base_ts.wcrts[tsk]  # add wcrt of tsk
    return result


if __name__ == '__main__':
    """Debugging."""
    ce = CEChain(
        Task(communication='implicit'),
        Task(communication='implicit'),
        Task(communication='implicit'),
        Task(communication='LET'),
        Task(communication='implicit'),
        Task(communication='implicit'),
        Task(communication='LET'),
        Task(communication='LET'),
        Task(communication='LET'),
    )
    cut_ce = _cut_chain(ce)

    print('== Communication')
    ce.print(communication=True)
    for ch in cut_ce:
        ch.print(communication=True)

    print('==All Tasks')
    ce.print_tasks()
    for ch in cut_ce:
        print(' ')
        ch.print_tasks()

    breakpoint()
