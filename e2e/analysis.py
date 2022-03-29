import math
import itertools
from tasks.task import Task
from tasks.taskset import TaskSet
from cechains.chain import CEChain


#####
# Homogeneous
#####

# Sporadic + implicit

def davare(chain):
    """Analysis from Davare et al. 2007, DAC:
    Period optimization for hard real-time distributed automotive systems.
    - implicit
    - sporadic
    """
    wcrts = chain.base_ts.wcrts
    result = 0
    for tsk in chain:
        result += tsk.rel.maxiat + wcrts[tsk]
    return result


def duerr(chain):
    """Analysis from Duerr et al. 2019, CASES:
    End-to-end timing analysis of sporadic cause-effect chains in distributed systems.
    - implicit
    - sporadic
    """
    wcrts = chain.base_ts.wcrts
    result = 0
    for idx in range(len(chain)):
        if idx == len(chain) - 1 or chain.base_ts.higher_prio(chain[idx + 1], chain[idx]):
            result += chain[idx].rel.maxiat + wcrts[chain[idx]]
        else:
            result += chain[idx].rel.maxiat + max(wcrts[chain[idx]] - chain[idx + 1].rel.maxiat, 0)
    return result


# Sporadic + LET

def LET_spor(chain):
    """Upper bound for sporadic tasks under LET.
    - LET
    -sporadic
    """
    result = 0
    for tsk in chain:
        result += tsk.rel.maxiat + tsk.dl.dl
    return result


# Periodic + Implicit

def kloda(chain):
    """Upper bound for periodic tasks under LET.
    - LET
    - periodic
    """
    # Compute chain hyperperiod and phase:
    hyper = chain.hyperperiod()
    max_phase = chain.max_phase()

    lengths = []

    for mvar in itertools.count(start=1):
        # Principle 1 and chain definition
        zvar = _release(mvar, chain[0])
        relvar = _release(mvar + 1, chain[0])

        # check conditions
        if relvar < max_phase:
            continue
        if zvar > max_phase + hyper:
            break

        for this_tsk, next_tsk in zip(chain[:-1], chain[1:]):
            # Principle 2 (Compute release of next job in the job chain)
            if chain.base_ts.higher_prio(this_tsk, next_tsk):
                compare_value = relvar
            else:
                compare_value = relvar + chain.base_ts.wcrts[this_tsk]
            relvar = _release_after(compare_value, next_tsk)

        # Principle 3
        zprimevar = relvar + chain.base_ts.wcrts[chain[-1]]

        lengths.append(zprimevar - zvar)

    return max(lengths)


# Periodic + LET

def LET_per(chain):
    """Upper bound for periodic tasks under LET.
    - LET
    - periodic
    """
    # Compute chain hyperperiod and phase:
    hyper = chain.hyperperiod()
    max_phase = chain.max_phase()

    lengths = []

    for mvar in itertools.count(start=1):
        # Principle 1 and chain definition
        zvar = _release(mvar, chain[0])
        relvar = _release(mvar + 1, chain[0])

        # check conditions
        if relvar < max_phase:
            continue
        if zvar > max_phase + hyper:
            break

        for this_tsk, next_tsk in zip(chain[:-1], chain[1:]):
            # Principle 2 (Compute release of next job in the job chain)
            compare_value = relvar + this_tsk.dl.dl
            relvar = _release_after(compare_value, next_tsk)

        # Principle 3
        zprimevar = relvar + chain[-1].dl.dl

        lengths.append(zprimevar - zvar)

    return max(lengths)


#####
# Mixed
#####

def mix_pessimistic(chain):
    """Pessimistic Analysis for mixed chains."""
    result = 0
    for tsk in chain:
        if tsk.comm.type == 'implicit':
            result += tsk.rel.maxiat + chain.base_ts.wcrts[tsk]
        elif tsk.comm.type == 'LET':
            result += tsk.rel.maxiat + tsk.dl.dl
        else:
            raise ValueError(f"{tsk.comm.type=} cannot be handled by the analysis.")

    return result


def mix(
        chain,
        impl_spor=duerr,
        impl_per=kloda,
        let_spor=LET_spor,
        let_per=LET_per
):
    """Our analysis. Cut to make homogeneous, then apply analyses."""
    cutted_chains = _cut_chain(chain, communication=True, release=True)
    result = 0
    for ch in cutted_chains:
        if ch.check_feature('comm') == 'implicit' and ch.check_feature('rel') == 'sporadic':
            result += impl_spor(ch)
        elif ch.check_feature('comm') == 'implicit' and ch.check_feature('rel') == 'periodic':
            result += impl_per(ch)
        elif ch.check_feature('comm') == 'LET' and ch.check_feature('rel') == 'sporadic':
            result += let_spor(ch)
        elif ch.check_feature('comm') == 'LET' and ch.check_feature('rel') == 'periodic':
            result += let_per(ch)
        else:
            raise ValueError(
                f"{ch.check_feature('comm')=} and {ch.check_feature('rel')=} cannot be handled by the analysis.")

    return result


def _cut_chain(chain, communication=True, release=True):
    """Cut cause-effect chain into homogeneous chains."""
    new_chains = []

    for idx, tsk in enumerate(chain):
        if (
                idx == 0 or
                (communication and tsk.comm.type != curr_comm) or
                (release and tsk.rel.type != curr_rel)
        ):
            curr_comm = tsk.comm.type
            curr_rel = tsk.rel.type
            new_chains.append(CEChain(tsk, base_ts=chain.base_ts))
        else:
            new_chains[-1].append(tsk)
    return new_chains


def mix_improved(chain):
    """Our analysis. Cut only when release constraint changes."""
    cutted_chains = _cut_chain(chain, communication=False, release=True)

    result = 0
    for ch in cutted_chains:
        if ch.check_feature('rel') == 'sporadic':
            result += mix_sporadic(ch)
        elif ch.check_feature('rel') == 'periodic':
            result += mix_periodic(ch)
        else:
            raise ValueError(f"{ch.check_feature('rel')=} cannot be handled by the analysis.")
    return result


def mix_sporadic(chain):
    """Analysis for sporadic tasks and mixed communication means."""
    assert all([tsk.comm.type in ['LET', 'implicit'] for tsk in chain])
    result = 0
    for idx in range(len(chain)):
        result += chain[idx].rel.maxiat + _CX(idx, chain)
    return result


def _CX(idx, chain):
    """CX from our work."""
    if chain[idx].comm.type == 'LET':
        return chain[idx].dl.dl
    elif (idx != len(chain) - 1 and
          chain[idx + 1].comm.type == 'implicit' and
          chain.base_ts.higher_prio(chain[idx], chain[idx + 1])):
        return max(chain.base_ts.wcrts[chain[idx]] - chain[idx + 1].rel.maxiat, 0)
    else:
        return chain.base_ts.wcrts[chain[idx]]


def mix_periodic(chain):
    """Analysis for periodic tasks and mixed communication means."""
    # Compute chain hyperperiod and phase:
    hyper = chain.hyperperiod()
    max_phase = chain.max_phase()

    lengths = []

    for mvar in itertools.count(start=1):
        # Principle 1 and chain definition
        zvar = _release(mvar, chain[0])
        relvar = _release(mvar + 1, chain[0])

        # check conditions
        if relvar < max_phase:
            continue
        if zvar > max_phase + hyper:
            break

        for idx, (this_tsk, next_tsk) in enumerate(zip(chain[:-1], chain[1:])):
            # Principle 2 (Compute release of next job in the job chain)
            compare_value = relvar + _add_to_compare_value_from_table(idx, chain)
            relvar = _release_after(compare_value, next_tsk)

        # Principle 3
        if chain[-1].comm.type == 'LET':
            zprimevar = relvar + chain[-1].dl.dl
        elif chain[-1].comm.type == 'implicit':
            zprimevar = relvar + chain.base_ts.wcrts[chain[-1]]

        lengths.append(zprimevar - zvar)

    return max(lengths)


def _add_to_compare_value_from_table(idx, chain):
    """The compare value used in the periodic analysis to find the next job.
    Please note: idx in range {0,1, ... , len(chain)-2}"""
    this_tsk = chain[idx]
    next_tsk = chain[idx + 1]

    if this_tsk.comm.type == 'LET':
        return this_tsk.dl.dl
    elif this_tsk.comm.type == 'implicit' and next_tsk.comm.type == 'LET':
        return chain.base_ts.wcrts[this_tsk]
    elif this_tsk.comm.type == 'implicit' and next_tsk.comm.type == 'implicit':
        if chain.base_ts.higher_prio(this_tsk, next_tsk):
            return 0
        else:
            return chain.base_ts.wcrts[this_tsk]
    else:
        raise ValueError(f"{this_tsk.comm.type=} and {next_tsk.comm.type=} cannot be handled by the analysis.")


#####
# Help functions
#####

def _release_after(time, tsk):
    """Next release of tsk at or after 'time' for periodic tasks."""
    return tsk.rel.phase + math.ceil((time - tsk.rel.phase) / tsk.rel.period) * tsk.rel.period


def _release(m, tsk):
    """Time of the m-th job release of a periodic task.
    (First job is at m=1.)"""
    return tsk.rel.phase + (m - 1) * tsk.rel.period


if __name__ == "__main__":
    """Debug."""
    # # Sporadic + implicit
    # ts_spor_impl = TaskSet(
    #     Task(release='s', maxiat=10, miniat=5, communication='implicit', execution='bcwc', wcet=1),
    #     Task(release='s', maxiat=20, miniat=10, communication='implicit', execution='bcwc', wcet=2)
    # )
    # ts_spor_impl.compute_wcrts()
    #
    # ce_spor_impl = CEChain(*ts_spor_impl, base_ts=ts_spor_impl)  # all tasks of the task set are in the chain
    # ce_spor_impl_inv = CEChain(*ts_spor_impl[::-1], base_ts=ts_spor_impl)  # all tasks of the task set are in the chain
    #
    # # Sporadic + LET
    # ts_spor_let = TaskSet(
    #     Task(release='s', maxiat=10, miniat=5, communication='LET', execution='bcwc', wcet=1, deadline='arbitrary',
    #          dl=7),
    #     Task(release='s', maxiat=20, miniat=10, communication='LET', execution='bcwc', wcet=2, deadline='arbitrary',
    #          dl=8)
    # )
    # ts_spor_let.compute_wcrts()
    #
    # ce_spor_let = CEChain(*ts_spor_let, base_ts=ts_spor_let)  # all tasks of the task set are in the chain
    # ce_spor_let_inv = CEChain(*ts_spor_let[::-1], base_ts=ts_spor_let)  # all tasks of the task set are in the chain
    #
    # # Periodic + implicit
    # ts_per_impl = TaskSet(
    #     Task(release='p', period=10, communication='implicit', execution='bcwc', wcet=1, phase=0),
    #     Task(release='p', period=20, communication='implicit', execution='bcwc', wcet=2, phase=0)
    # )
    # ts_per_impl.compute_wcrts()
    #
    # ce_per_impl = CEChain(*ts_per_impl, base_ts=ts_per_impl)
    # ce_per_impl_inv = CEChain(*ts_per_impl[::-1], base_ts=ts_per_impl)
    #
    # # Periodic + LET
    # ts_per_let = TaskSet(
    #     Task(release='p', period=10, phase=0, communication='LET', deadline='arbitrary', dl=7, execution='bcwc',
    #          wcet=1),
    #     Task(release='p', period=20, phase=0, communication='LET', deadline='arbitrary', dl=8, execution='bcwc', wcet=2)
    # )
    # ts_per_let.compute_wcrts()
    #
    # ce_per_let = CEChain(*ts_per_let, base_ts=ts_per_let)
    # ce_per_let_inv = CEChain(*ts_per_let[::-1], base_ts=ts_per_let)
    #
    # # Tests
    # print('== Sporadic, implicit ==')
    # print(davare(ce_spor_impl), '10+1+20+3=34 (Davare)')
    # print(davare(ce_spor_impl_inv), '20+3+10+1=34 (Davare)')
    #
    # print(duerr(ce_spor_impl), '10+0+20+3=33 (Duerr)')
    # print(duerr(ce_spor_impl_inv), '20+3+10+1=34 (Duerr)')
    #
    # print('== Sporadic, LET ==')
    # print(LET_spor(ce_spor_let), '10+7+20+8=45 (Spor, LET)')
    # print(LET_spor(ce_spor_let_inv), '20+8+10+7=45 (Spor, LET)')
    #
    # print('== Periodic, implicit ==')
    # print(kloda(ce_per_impl), '10+10+3=23 (Kloda)')
    # print(kloda(ce_per_impl_inv), '20+10+1=31 (Kloda)')
    #
    # print(davare(ce_per_impl), '10+1+20+3=34 (Davare)')
    # print(davare(ce_per_impl_inv), '20+3+10+1=34 (Davare)')
    #
    # print(duerr(ce_per_impl), '10+0+20+3=33 (Duerr)')
    # print(duerr(ce_per_impl_inv), '20+3+10+1=34 (Duerr)')
    #
    # print('== Periodic, LET ==')
    # print(LET_per(ce_per_let), 'max(28, 38) (Per, LET)')
    # print(LET_per(ce_per_let_inv), '37 (Per, LET)')
    #
    # print('== Test Cutting ==')
    # ce_mix_cut = CEChain(
    #     Task(release='p', communication='LET'),
    #     Task(release='p', communication='LET'),
    #     Task(release='p', communication='LET'),
    #     Task(release='p', communication='implicit'),
    #     Task(release='p', communication='implicit'),
    #     Task(release='s', communication='implicit'),
    #     Task(release='s', communication='LET'),
    #     Task(release='s', communication='LET'),
    #     Task(release='p', communication='LET'),
    #     Task(release='p', communication='LET')
    # )
    # ce_mix_cut.print()
    # ce_mix_cut.print_tasks()
    # print('')
    #
    # for ce in _cut_chain(ce_mix_cut):
    #     ce.print()
    #     ce.print_tasks()
    #     print('')

    print("== Test our mixed analysis ==")
    ts_mix = TaskSet(
        Task(release='p', period=20, phase=0, communication='LET', deadline='arbitrary', dl=8, execution='bcwc',
             wcet=1),
        Task(release='p', period=20, phase=3, communication='implicit', execution='bcwc', wcet=1),
        Task(release='s', maxiat=20, miniat=18, communication='LET', deadline='arbitrary', dl=8, execution='bcwc',
             wcet=1),
        Task(release='s', maxiat=30, miniat=28, communication='implicit', execution='bcwc', wcet=1)
    )
    ts_mix.compute_wcrts()
    ce_mix = CEChain(*ts_mix, base_ts=ts_mix)

    print('Mixed Analysis:', mix(ce_mix))
    print('Improved mixed Analysis:', mix_improved(ce_mix))
    print('Pessimistic mixed Analysis:',
          mix_pessimistic(ce_mix))  # Please note: both do the same in this simple analysis scenario
    print('Our sporadic', mix_sporadic(ce_mix))
    breakpoint()
