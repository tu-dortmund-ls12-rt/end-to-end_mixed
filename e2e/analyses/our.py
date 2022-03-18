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


def sporadic():
    pass


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
