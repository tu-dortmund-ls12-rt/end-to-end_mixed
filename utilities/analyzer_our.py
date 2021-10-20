"""Our End-To-End analysis.
- implicit communication only
- periodic tasks 
"""

import itertools
import utilities.analyzer

# Method to compute the hyperperiod
compute_hyper = utilities.analyzer.Analyzer.determine_hyper_period


class re_we_analyzer():
    def __init__(self, bcet_schedule, wcet_schedule, hyperperiod):
        self.bc = bcet_schedule
        self.wc = wcet_schedule
        self.hyperperiod = hyperperiod

    def _get_entry(self, nmb, lst, tsk):
        '''get nmb-th entry of the list lst with task tsk.'''
        if nmb < 0:  # Case: out of range
            raise IndexError('nbm<0')
        # Case: index too high, has to be made smaller # TODO not sure if this is a good idea since the last entries could be wrong depending on the implementation of the scheduler ...
        elif nmb >= len(lst):
            new_nmb = nmb - self.hyperperiod/tsk.period  # check one hyperperiod earlier
            # add one hyperperiod
            return self._get_entry(new_nmb, lst, tsk) + self.hyperperiod
        else:  # Case: entry can be used
            return lst[nmb]

    def remin(self, task, nmb):
        '''returns the upper bound on read-event of the nbm-th job of a task.'''
        lst = self.bc[task]  # list that has the read-even minimum
        # choose read-event from list
        return self._get_entry(nmb, lst, task)[0]

    def remax(self, task, nmb):
        '''returns the upper bound on read-event of the nbm-th job of a task.'''
        lst = self.wc[task]  # list that has the read-even maximum
        # choose read-event from list
        return self._get_entry(nmb, lst, task)[0]

    def wemin(self, task, nmb):
        '''returns the upper bound on read-event of the nbm-th job of a task.'''
        lst = self.bc[task]  # list that has the write-even minimum
        # choose write-event from list
        return self._get_entry(nmb, lst, task)[1]

    def wemax(self, task, nmb):
        '''returns the upper bound on read-event of the nbm-th job of a task.'''
        lst = self.wc[task]  # list that has the write-even maximum
        # choose write-event from list
        return self._get_entry(nmb, lst, task)[1]

    def find_next_fw(self, curr_task_wc, nxt_task_bc, curr_index):
        '''Find next index for the abstract representation in forward manner.'''
        # wemax of current task
        curr_wemax = self.wemax(curr_task_wc, curr_index)
        curr_rel = curr_task_wc.phase + curr_index * \
            curr_task_wc.period  # release of current task

        for idx in itertools.count():
            idx_remin = self.remin(nxt_task_bc, idx)

            if (
                idx_remin >= curr_wemax  # first property
                # second property (lower priority value means higher priority!)
                or (curr_task_wc.priority < nxt_task_bc.priority and idx_remin >= curr_rel)
            ):
                break

        return idx

    def len_abstr(self, abstr, last_tsk_wc, first_tsk_bc):
        '''Length of an abstract representation.'''
        return self.wemax(last_tsk_wc, abstr[-1])-self.remin(first_tsk_bc, abstr[0])


def max_reac_local(chain, task_set_wcet, schedule_wcet, task_set_bcet, schedule_bcet):
    '''Main method for maximum reaction time.

    We construct all abstract represenations and compute the maximal length among them.
    - chain: cause-effect chain as list of tasks
    - task_set: the task set of the ECU that the ce chain lies on
    - schedule: the schedule of task_set (simulated beforehand)

    we distinguish between bcet and wcet task set and schedule.'''

    # Make analyzer
    ana = re_we_analyzer(schedule_bcet, schedule_wcet,
                         compute_hyper(task_set_wcet))

    # Chain of indeces that describes the cause-effect chain
    index_chain = [task_set_wcet.index(entry) for entry in chain.chain]

    # Set of all abstract representations
    all_abstr = []

    # useful values for break-condition
    hyper = compute_hyper(task_set_wcet)
    max_phase = max([task.phase for task in task_set_wcet])

    for idx in itertools.count():
        # Compute idx-th abstract integer representation.
        abstr = []
        abstr.append(idx)  # first entry
        abstr.append(idx+1)  # second entry

        for idtsk, nxt_idtsk in zip(index_chain[:-1], index_chain[1:]):
            abstr.append(ana.find_next_fw(
                task_set_wcet[idtsk], task_set_bcet[nxt_idtsk], abstr[-1]))  # intermediate entries

        abstr.append(abstr[-1])  # last entry

        assert len(abstr) == chain.length() + 2

        all_abstr.append(abstr[:])

        # Break loop
        if (chain.chain[0].phase + idx * chain.chain[0].period) >= (max_phase + 2*hyper):
            break

        # print([task_set_wcet[i].priority for i in index_chain])

        # print([(schedule_bcet[task_set_bcet[i]][j][0], schedule_wcet[task_set_wcet[i]][j][1])
        #       for i, j in zip(index_chain, abstr[1:-1])])

        # breakpoint()

    # maximal length
    max_length = max([ana.len_abstr(abstr, task_set_wcet[index_chain[-1]],
                     task_set_bcet[index_chain[0]]) for abstr in all_abstr])
    chain.our_new_local_mrt = max_length
    return max_length
