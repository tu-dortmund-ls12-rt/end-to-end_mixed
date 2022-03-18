#!/usr/bin/env python3

####################
# Task Features.
####################
class TaskFeature:
    pass


# Task Features: Release Pattern
class ReleasePattern(TaskFeature):
    type = None

    def __str__(self):
        return super().__str__() + f'\t type={self.type}'


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
        self.maxiat = maxiat
        self.miniat = miniat

    def __str__(self):
        return super().__str__() + f' miniat={self.miniat}, maxiat={self.maxiat}'


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
        return super().__str__() + f'\t type={self.type}'


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
        if tsk is not None and hasattr(tsk, 'rel') and hasattr(tsk.rel, 'miniat'):
            assert tsk.rel.miniat >= dl

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
        return self.base_tsk.rel.miniat


# Task Features: Execution Behavior
# TODO add suspension
# TODO this place can also be used to implement tasks with probabilistic execution behavior
class Execution(TaskFeature):
    type = None

    def __str__(self):
        return super().__str__() + f'\t type={self.type}'


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
    def __init__(self, communication, **kwargs):
        assert communication in ('implicit', 'LET')
        self.type = communication

    def __str__(self):
        return super().__str__() + f'\t type={self.type}'


####################
# Task.
####################
class Task:
    """A task."""
    features = {  # list of features that can be set.
        'release': ['rel', {
            **dict.fromkeys(['sporadic', 'spor', 's'], Sporadic),
            **dict.fromkeys(['periodic', 'per', 'p'], Periodic)
        }],
        'deadline': ['dl', {
            **dict.fromkeys(['arbitrary', 'arb', 'a'], ArbitraryDeadline),
            **dict.fromkeys(['constrained', 'constr', 'c'], ConstrainedDeadline),
            **dict.fromkeys(['implicit', 'impl', 'i'], ImplicitDeadline)
        }],
        'execution': ['ex', {
            **dict.fromkeys(['wcet', 'bcet', 'wc', 'bc', 'bcwc'], BCWCExecution)
        }],
        'communication': ['comm', {
            **dict.fromkeys(['implicit', 'LET'], Communication)
        }]
    }

    def __init__(self,
                 release=None,
                 deadline=None,
                 execution=None,
                 communication=None,
                 **kwargs):
        """Parameters that can be provided for different features:

        - rel: release in ['sporadic', 'periodic']:
            miniat, maxiat, period
        - dl: deadline in ['arbitrary', 'constrained', 'implicit']:
            dl
        - ex: execution in ['bcwc']:
            wcet, bcet
        - comm: communication in ['implicit', 'LET']:
            --
        """
        kwargs['tsk'] = self  # add pointer to task

        # Add features.
        if release is not None:
            self.add_feature('release', release, **kwargs)

        if deadline is not None:
            self.add_feature('deadline', deadline, **kwargs)

        if execution is not None:
            self.add_feature('execution', execution, **kwargs)

        if communication is not None:
            self.add_feature('communication', communication, **kwargs)

    def add_feature(self, feature, argument, **kwargs):
        feature_attribute, possible_arguments = self.features[feature]
        assert argument in possible_arguments.keys()
        kwargs[feature] = argument  # add feature and argument back

        feature_class = possible_arguments[argument]
        setattr(self, feature_attribute, feature_class(**kwargs))

    def print(self):
        print(self)
        feat_dict = self.__dict__
        for feat in feat_dict.keys():
            print(feat, feat_dict[feat])

    def utilization(self):
        """Task utilization."""
        return (self.ex.wcet / self.rel.miniat)


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

    # Add features
    tsks['texec2'].add_feature('release', 'periodic', period=10)
    tsks['texec2'].add_feature('communication', 'LET')

    for t in tsks.keys():
        print('\n', t)
        tsks[t].print()

    breakpoint()
