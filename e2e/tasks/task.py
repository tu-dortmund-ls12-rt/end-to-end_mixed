#!/usr/bin/env python3

####################
# Task Features.
####################
class TaskFeature:
    _features = []

    def __str__(self):
        ret_str = self.__repr__() + ':\t'
        for feat in self._features:
            ret_str += f'{feat}={getattr(self, feat)}, '
        return ret_str


# Task Features: Release Pattern
class ReleasePattern(TaskFeature):
    _features = TaskFeature._features + ['type']
    type = None


class Sporadic(ReleasePattern):
    type = 'sporadic'
    _features = ReleasePattern._features + ['miniat', 'maxiat']

    def __init__(self, maxiat=None, miniat=None, **kwargs):
        # this
        self.maxiat = maxiat
        self.miniat = miniat

    @property
    def maxiat(self):
        return self._maxiat

    @maxiat.setter
    def maxiat(self, value):
        if value is not None:
            if value < 0:
                raise ValueError(f'Non-negative value expected. Received {value=}.')
            if hasattr(self, '_miniat') and self.miniat is not None and value < self._miniat:
                raise ValueError(f'miniat <= value expected. Received {self._miniat=} > {value=}.')
        self._maxiat = value

    @property
    def miniat(self):
        return self._miniat

    @miniat.setter
    def miniat(self, value):
        if value is not None:
            if value < 0:
                raise ValueError(f'Non-negative value expected. Received {value=}.')
            if hasattr(self, '_maxiat') and self._maxiat is not None and value > self._maxiat:
                raise ValueError(f'value <= maxiat expected. Received {value=} > {self._maxiat=}.')
        self._miniat = value


class Periodic(Sporadic):
    type = 'periodic'
    _features = Sporadic._features + ['period', 'phase']

    def __init__(self, period=None, phase=None, **kwargs):
        # super
        kwargs['miniat'] = period
        kwargs['maxiat'] = period
        super().__init__(**kwargs)

        # this
        self.period = period
        self.phase = phase

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        if value is not None and value < 0:
            raise ValueError(f'Non-negative value expected. Received {value=}.')
        self._period = value


# Task Features: Deadline
class Deadline(TaskFeature):
    type = None
    _features = TaskFeature._features + ['type']


class ArbitraryDeadline(Deadline):
    type = 'arbitrary'
    _features = Deadline._features + ['dl']

    def __init__(self, dl=None, **kwargs):
        # this
        self.dl = dl


class ConstrainedDeadline(ArbitraryDeadline):
    type = 'constrained'

    def __init__(self, dl=None, tsk=None, **kwargs):
        self._base_tsk = tsk  # base task
        # super
        super().__init__(dl=dl, **kwargs)  # set deadline

    @property
    def dl(self):
        return self._dl

    @dl.setter
    def dl(self, value):
        if (hasattr(self, '_base_tsk') and self._base_tsk is not None and value is not None
                and hasattr(self._base_tsk, 'rel')
                and hasattr(self._base_tsk.rel, 'miniat')):
            if self._base_tsk.rel.miniat < value:
                raise ValueError(f'Expected value <= miniat. Received {value=} > {self._base_tsk.rel.miniat=}.')
        self._dl = value


class ImplicitDeadline(ConstrainedDeadline):
    type = 'implicit'

    @property
    def dl(self):
        """Deadline is always the minimum inter-arrival time of a task."""
        if (hasattr(self, '_base_tsk')
                and hasattr(self._base_tsk, 'rel')
                and hasattr(self._base_tsk.rel, 'miniat')):
            return self._base_tsk.rel.miniat
        else:
            return None

    @dl.setter
    def dl(self, value):
        """No setting allowed, just a quick check."""
        if value is not None and self.dl is not None and self.dl != value:
            raise ValueError(f'DL=miniat expected for implicit deadline tasks. Want to set {self.dl=} to {value=}?')
        else:
            pass


# Task Features: Execution Behavior
# TODO add suspension
# TODO this place can also be used to implement tasks with probabilistic execution behavior
class Execution(TaskFeature):
    type = None
    _features = TaskFeature._features + ['type']


class BCWCExecution(Execution):
    type = 'bcwc'
    _features = Execution._features + ['bcet', 'wcet']

    def __init__(self, bcet=None, wcet=None, **kwargs):
        self.bcet = bcet
        self.wcet = wcet

    @property
    def bcet(self):
        return self._bcet

    @bcet.setter
    def bcet(self, value):
        if value is not None:
            if value < 0:
                raise ValueError(f'Non-negative value expected. Received {value=}.')
            if hasattr(self, 'wcet') and self.wcet is not None:
                if self.wcet < value:
                    raise ValueError(f'wcet>=value expected. Received: {self.wcet=}<{value=}.')
        self._bcet = value

    @property
    def wcet(self):
        return self._wcet

    @wcet.setter
    def wcet(self, value):
        if value is not None:
            if value < 0:
                raise ValueError(f'Non-negative value expected. Received {value=}.')
            if hasattr(self, 'bcet') and self.bcet is not None:
                if self.bcet > value:
                    raise ValueError(f'bcet<=value expected. Received: {self.bcet=}>{value=}.')
        self._wcet = value


# Task Features: Communication Policy
class Communication(TaskFeature):
    _features = TaskFeature._features + ['type']
    _comm_possibilities = ('implicit', 'LET')

    def __init__(self, communication, **kwargs):
        self.type = communication

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if value is not None:
            if value not in self._comm_possibilities:
                raise ValueError(f'{value} is not in {self._comm_possibilities}.')
        self._type = value


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
        if argument not in possible_arguments.keys():
            raise ValueError(f'{argument} is not a possible argument.')
        kwargs[feature] = argument  # add feature and argument back

        feature_class = possible_arguments[argument]
        setattr(self, feature_attribute, feature_class(**kwargs))

    def print(self):
        """Quick print of all features for debugging."""
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
