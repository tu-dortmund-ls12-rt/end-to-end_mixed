"""Our Analysis"""
from cechains.chain import CEChain
from tasks.task import Task


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


def prin_based(chain):
    """Our principle based analysis."""
    # TODO check if periodic or sporadic and apply the corresponding analysis
    return None


def _prin_based_periodic(chain):
    """Our principle based analysis for periodic tasks."""
    # TODO TBD
    return None


def _prin_based_sporadic(chain):
    """Our principle based analysis for sporadic tasks."""
    # TODO ensure that each communication type is LET or impl (use assert and if __debug__)
    # TODO ensure that all tasks have wcrts set, otherwise set them
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
