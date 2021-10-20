"""Our End-To-End analysis.
- implicit communication only
- periodic tasks 
"""


class re_we_analyzer():
    def __init__(self, bcet_schedule, wcet_schedule, hyperperiod):
        self.bc = bcet_schedule
        self.wc = wcet_schedule
        self.hyperperiod = hyperperiod

    def _get_entry(self, nmb, lst, tsk):
        '''get nmb-th entry of the list lst with task tsk.'''
        if nmb < 0:  # out of range
            raise IndexError('nbm<0')
        elif nmb >= len(lst):  # index too high, has to be made smaller
            new_nmb = nmb - self.hyperperiod/tsk.period  # check one period earlier
            return self._get_entry(new_nmb, lst, tsk)
        else:
            return lst[nmb]

    def remin(self, task, nmb):
        '''returns the upper bound on read-event of the nbm-th job of a task.'''


def max_age_our_local(chain, task_set_wcet, schedule_wcet, task_set_bcet, schedule_bcet):
    '''Main method.

    We construct all abstract represenations and compute the maximal length among them.
    - chain: cause-effect chain as list of tasks
    - task_set: the task set of the ECU that the ce chain lies on
    - schedule: the schedule of task_set (simulated beforehand)

    we distinguish between bcet and wcet task set and schedule.'''
