#!/usr/bin/env python3

class TaskSet:
    """A set of Task-Objects."""

    def __init__(self, *args):
        """Input: Task-Objects"""
        self._lst = list(args)

    def __len__(self):
        return self._lst.__len__()

    def __getitem__(self, item):
        return self._lst.__getitem__(item)

    def __setitem__(self, key, value):
        self._lst.__setitem__(key, value)

    def __delitem__(self, key):
        self._lst.__delitem__(key)

    def __iter__(self):
        yield from self._lst

    def append(self, obj):
        self._lst.append(obj)

    def utilization(self):
        return sum(tsk.utilization() for tsk in self)

    def communication(self):
        if all('implicit' == tsk.comm.type for tsk in self):
            return 'implicit'
        elif all('LET' == tsk.comm.type for tsk in self):
            return 'LET'
        else:
            return 'mixed'

    def check_feature(self, feature):
        assert feature in ['comm', 'ex', 'rel', 'dl']
        # First value
        val = getattr(self[0], feature).type

        if all(val == getattr(tsk, feature).type for tsk in self):
            return val
        else:
            return 'mixed'

    def print(self, length=True, utilization=False, communication=False, execution=False, release=False,
              deadline=False):
        printstr = ''
        printstr += self.__str__() + '\t'
        if length is True:
            printstr += f'length: {len(self)}, '
        if utilization is True:
            printstr += f'utilization: {self.utilization()}, '
        if communication is True:
            printstr += f"communication: {self.check_feature('comm')}, "
        if execution is True:
            printstr += f"execution: {self.check_feature('ex')}, "
        if release is True:
            printstr += f"release: {self.check_feature('rel')}, "
        if deadline is True:
            printstr += f"deadline: {self.check_feature('dl')}, "
        print(printstr)

    def print_tasks(self):
        for tsk in self:
            tsk.print()


def transform(taskset, precision=10000000):
    """"Multiplies the following values for each task with precision and makes integer.
    (Important for analyses with hyperperiod)."""
    transform_arguments = {
        'rel': ['miniat', 'maxiat', 'period', 'phase'],
        'dl': ['dl'],
        'ex': ['bcet', 'wcet'],
        'comm': []
    }
    for tsk in taskset:
        for targ in transform_arguments:
            if targ in tsk.__dict__.keys():
                feature = getattr(tsk, targ)
                for targarg in transform_arguments[targ]:
                    if targarg in feature.__dict__.keys():
                        old_val = getattr(feature, targarg)
                        if old_val is not None:
                            new_val = int(old_val * precision)
                            setattr(feature, targarg, new_val)


if __name__ == '__main__':
    """Debug."""
    from task import Task

    tset = (
        Task(release='periodic', period=10, execution='bcwc', wcet=1 / 3, communication='LET'),
        Task(release='periodic', period=20, execution='bcwc', wcet=1 / 2, communication='implicit'),
        Task(release='periodic', period=50, execution='bcwc', wcet=1 / 7, communication='LET')
    )

    ts = TaskSet(*tset)
    breakpoint()
