#!/usr/bin/env python3

class Task:
    """A task."""

    def __init__(self,
                 release=None,
                 deadline=None,
                 execution=None,
                 communication=None,
                 **kwargs):
        kwargs['tsk'] = self
        if release is None:
            pass
        elif release in ('sporadic', 'spor', 's'):
            self.rel = Sporadic(**kwargs)
        elif release in ('periodic', 'per', 'p'):
            self.rel = Periodic(**kwargs)
        else:
            raise ValueError(f'{release=} is no valid option.')

        if deadline is None:
            pass
        elif deadline in ('arbitrary', 'arb', 'a'):
            self.dl = ArbitraryDeadline(**kwargs)
        elif deadline in ('constrained', 'constr', 'c'):
            self.dl = ConstrainedDeadline(**kwargs)
        elif deadline in ('implicit', 'impl', 'i'):
            self.dl = ImplicitDeadline(**kwargs)
        else:
            raise ValueError(f'{deadline=} is no valid option.')

        if execution is None:
            pass
        elif execution in ('wcet', 'bcet', 'wc', 'bc', 'bcwc'):
            self.ex = BCWCExecution(**kwargs)
        else:
            raise ValueError(f'{execution=} is no valid option.')

        if communication is not None:
            self.comm = Communication(communication, **kwargs)

    def features(self):
        return self.__dict__

    def print(self):
        print(self)
        feat_dict = self.features()
        for feat in feat_dict.keys():
            print(feat, feat_dict[feat])


class TaskFeature:
    pass


# Task Features: Release Pattern
class ReleasePattern(TaskFeature):
    type = None

    def __str__(self):
        return super().__str__() + f' type={self.type}'


class Sporadic(ReleasePattern):
    type = 'sporadic'

    def __init__(self, maxiat=None, miniat=None, **kwargs):
        if maxiat is not None:
            assert maxiat >= 0
        if miniat is not None:
            assert miniat > 0
        if maxiat is not None and miniat is not None:
            assert maxiat >= miniat

        # this
        self.max = maxiat
        self.min = miniat

    def __str__(self):
        return super().__str__() + f' min={self.min}, max={self.max}'


class Periodic(Sporadic):
    type = 'periodic'

    def __init__(self, period=None, **kwargs):
        if period is not None:
            assert period > 0

        # super
        kwargs['miniat'] = period
        kwargs['maxiat'] = period
        super().__init__(**kwargs)

        # this
        self.period = period

    def __str__(self):
        return super().__str__() + f' period={self.period}'


# Task Features: Deadline
class Deadline(TaskFeature):
    type = None

    def __str__(self):
        return super().__str__() + f' type={self.type}'


class ArbitraryDeadline(Deadline):
    type = 'arbitrary'

    def __init__(self, dl=None, **kwargs):
        # this
        self.dl = dl

    def __str__(self):
        return super().__str__() + f' dl={self.dl}'


class ConstrainedDeadline(ArbitraryDeadline):
    type = 'constrained'

    def __init__(self, dl=None, tsk=None, **kwargs):
        if tsk is not None and hasattr(tsk, 'rel') and hasattr(tsk.rel, 'min'):
            assert tsk.rel.min >= dl

        # super
        super().__init__(dl=dl, **kwargs)
        # this
        pass


class ImplicitDeadline(ConstrainedDeadline):
    type = 'implicit'

    def __init__(self, tsk=None, **kwargs):
        self.base_tsk = tsk

    @property
    def dl(self):
        """Deadline is always the minimum inter-arrival time of a task."""
        return self.base_tsk.rel.min


# Task Features: Execution Behavior
# TODO add suspension
# TODO this place can also be used to implement tasks with probabilistic execution behavior
class Execution(TaskFeature):
    type = None

    def __str__(self):
        return super().__str__() + f' type={self.type}'


class BCWCExecution(Execution):
    type = 'bcwc'

    def __init__(self, bcet=None, wcet=None, **kwargs):
        if bcet is not None:
            assert bcet >= 0
        if wcet is not None:
            assert wcet >= 0
        if bcet is not None and wcet is not None:
            assert bcet <= wcet

        self.bcet = bcet
        self.wcet = wcet

    def __str__(self):
        return super().__str__() + f' bcet={self.bcet}, wcet={self.wcet}'


# Task Features: Communication Policy
class Communication(TaskFeature):
    def __init__(self, type, **kwargs):
        assert type in ('implicit', 'LET')
        self.type = type

    def __str__(self):
        return super().__str__() + f' type={self.type}'


if __name__ == '__main__':
    """Debugging."""
    tsks = dict()
    tsks['tnone'] = Task()

    tsks['tspor1'] = Task(release='s', miniat=100)
    tsks['tspor2'] = Task(release='s', miniat=10, maxiat=20)
    tsks['tper1'] = Task(release='p', period=10)

    tsks['tsporid'] = Task(release='spor', deadline='implicit', miniat=100)
    tsks['tsporcd'] = Task(release='spor', deadline='constrained', miniat=100, dl=80)

    tsks['timpl'] = Task(communication='implicit')
    tsks['tLET'] = Task(communication='LET')

    tsks['texec1'] = Task(execution='bcwc', bcet=10, wcet=20)
    tsks['texec2'] = Task(execution='wc', wcet=100)

    for t in tsks.keys():
        print('\n', t)
        tsks[t].print()

    breakpoint()
