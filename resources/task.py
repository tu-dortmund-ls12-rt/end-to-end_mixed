#!/usr/bin/env python3

class Task:
    """A task."""

    def __init__(self, release=None, deadline=None, execution=None, communication=None, **kwargs):
        kwargs['tsk'] == self
        if release is None:
            pass
        elif release in ('sporadic', 'spor', 's'):
            self.rel = Sporadic(**kwargs)
        elif release in ('periodic', 'per', 'p'):
            self.rel = Periodic(**kwargs)
        else:
            ValueError(f'{release=} is no valid option.')

        if deadline is None:
            pass
        elif deadline in ('arbitrary', 'arb', 'a'):
            self.dl = ArbitraryDeadline(**kwargs)
        elif deadline in ('constrained', 'constr', 'c'):
            self.dl = ConstrainedDeadline(**kwargs)
        elif deadline in ('implicit', 'impl', 'i'):
            self.dl = ImplicitDeadline(**kwargs)
        else:
            ValueError(f'{deadline=} is no valid option.')

        if execution is not None:
            self.ex = Execution(execution, **kwargs)

        if communication is not None:
            self.comm = Communication(communication, **kwargs)


class TaskFeature:
    pass


# Task Features: Release Pattern
class ReleasePattern(TaskFeature):
    pass


class Sporadic(ReleasePattern):
    pass


class Periodic(Sporadic):
    pass


# Task Features: Deadline
class Deadline(TaskFeature):
    pass


class ArbitraryDeadline(Deadline):
    pass


class ConstrainedDeadline(ArbitraryDeadline):
    pass


class ImplicitDeadline(Deadline):
    pass


# Task Features: Execution Behavior
# TODO add suspension
class Execution(TaskFeature):
    pass


# Task Features: Communication Policy
class Communication(TaskFeature):
    pass
