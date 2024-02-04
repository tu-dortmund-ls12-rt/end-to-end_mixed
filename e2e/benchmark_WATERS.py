"""Task set and cause-effect chain generation with WATERS benchmark.
From the paper: 'Real world automotive benchmark for free' (WATERS 2015).
Basis from https://github.com/tu-dortmund-ls12-rt/end-to-end/blob/master/utilities/generator_WATERS.py
"""
from scipy import stats
import numpy as np
import random
from scipy.stats import exponweib
from collections import Counter
from tasks.task import Task
from tasks.taskset import TaskSet
from cechains.chain import CEChain


###
# Task set generation.
###

class task(dict):
    """A task according to our task model.
    Used only for the purpose of task creation.
    """

    def __init__(self, execution, period, deadline):
        """Initialize a task."""
        dict.__setitem__(self, "execution", float(execution))
        dict.__setitem__(self, "period", float(period))
        dict.__setitem__(self, "deadline", float(deadline))


def task_transormation(tsk):
    """Transform task for creation to our task model for analysis."""
    return Task(release='periodic', period=tsk['period'],
                execution='wcet', wcet=tsk['execution'],
                deadline='implicit')  # make implicit


def sample_runnable_acet(period, amount=1, scalingFlag=False):
    """Create runnables according to the WATERS benchmark.
    scalingFlag: make WCET out of ACET with scaling
    """
    # Parameters from WATERS 'Real World Automotive Benchmarks For Free'
    if period == 1:
        # Pull scaling factor.
        scaling = np.random.uniform(1.3, 29.11, amount)  # between fmin fmax
        # Pull samples with weibull distribution.
        dist = exponweib(1, 1.044, loc=0, scale=1.0 / 0.214)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                # Check if they are in the range.
                if samples[i] < 0.34 or samples[i] > 30.11:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            # Case: Some samples had to be pulled again.
            if outliers_detected:
                continue
            # Case: All samples are in the range.
            if scalingFlag:  # scaling
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    # In the following same structure but different values.

    if period == 2:
        scaling = np.random.uniform(1.54, 19.04, amount)
        dist = exponweib(1, 1.0607440083, loc=0, scale=1.0 / 0.2479463059)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.32 or samples[i] > 40.69:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 5:
        scaling = np.random.uniform(1.13, 18.44, amount)
        dist = exponweib(1, 1.00818633, loc=0, scale=1.0 / 0.09)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.36 or samples[i] > 83.38:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 10:
        scaling = np.random.uniform(1.06, 30.03, amount)
        dist = exponweib(1, 1.0098, loc=0, scale=1.0 / 0.0985)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.21 or samples[i] > 309.87:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 20:
        scaling = np.random.uniform(1.06, 15.61, amount)
        dist = exponweib(1, 1.01309699673984310, loc=0, scale=1.0 / 0.1138186679)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.25 or samples[i] > 291.42:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 50:
        scaling = np.random.uniform(1.13, 7.76, amount)
        dist = exponweib(1, 1.00324219159296302, loc=0,
                         scale=1.0 / 0.05685450460)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.29 or samples[i] > 92.98:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 100:
        scaling = np.random.uniform(1.02, 8.88, amount)
        dist = exponweib(1, 1.00900736028318527, loc=0,
                         scale=1.0 / 0.09448019812)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.21 or samples[i] > 420.43:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 200:
        scaling = np.random.uniform(1.03, 4.9, amount)
        dist = exponweib(1, 1.15710612360723798, loc=0,
                         scale=1.0 / 0.3706045664)
        samples = dist.rvs(size=amount)
        while True:
            outliers_detected = False
            for i in range(len(samples)):
                if samples[i] < 0.22 or samples[i] > 21.95:
                    outliers_detected = True
                    samples[i] = dist.rvs(size=1)
            if outliers_detected:
                continue
            if scalingFlag:
                return list(0.001 * samples * scaling)
            else:
                return list(0.001 * samples)

    if period == 1000:
        # No weibull since the range from 0.37 to 0.46 is too short to be
        # modeled by weibull properly.
        scaling = np.random.uniform(1.84, 4.75, amount)
        if scalingFlag:
            return list(0.001 * np.random.uniform(0.37, 0.46, amount) * scaling)
        else:
            return list(0.001 * np.random.uniform(0.37, 0.46, amount))


def gen_taskset(
        util_target,
        period_pdf=[0.03 / 0.85, 0.02 / 0.85, 0.02 / 0.85, 0.25 / 0.85, 0.25 / 0.85, 0.03 / 0.85, 0.2 / 0.85,
                    0.01 / 0.85, 0.04 / 0.85],
        scaling_flag=True,
        threshold=0.01):
    """Main function to generate a task set with the WATERS benchmark.
    Output: tasksets as given in tasks.taskset.TaskSet
    with tasks as tasks.task.Task
    - periodic
    - implicit communication

    Variables:
    util_target: targeted utilization
    period_pdf: statistical distribution
    scalingFlag: make WCET out of ACET with scaling
    threshold: accuracy of the targeted utilization
    """

    periods = [1, 2, 5, 10, 20, 50, 100, 200, 1000]

    # Create runnable periods.
    dist = stats.rv_discrete(name='periods',
                             values=(periods, period_pdf))
    runnables = 30000  # number of runnables
    sys_runnable_periods = dist.rvs(size=runnables)  # list all periods

    # Count runnables.
    amount_sys_runnables = dict(Counter(sys_runnable_periods))
    assert sum(amount_sys_runnables.values()) == runnables

    # Build tasks from runnables.
    taskset = []
    for per in periods:
        # Random WCETs.
        wcets = sample_runnable_acet(per, amount_sys_runnables[per], scaling_flag)
        # Create Tasks.
        assert len(wcets) == amount_sys_runnables[per]
        for wcet in wcets:
            taskset.append(task(wcet, per, per))

    # Shuffle the task set.
    random.shuffle(taskset)

    # Select subset of tasks using the subset-sum approximation algorithm.
    util = 0.0
    i = 0
    this_taskset = []
    while True:
        if util < util_target:  # add a task
            if len(taskset) == 0:
                raise ValueError('Under this setting the targeted utilization of {util_target=} cannot be reached.')
            new_tsk = taskset.pop()
            this_taskset.append(new_tsk)
            util += new_tsk['execution'] / new_tsk['period']
        elif util > util_target + threshold:  # remove a task
            old_tsk = this_taskset.pop()
            util -= new_tsk['execution'] / old_tsk['period']
        else:
            break

    # Transform to our taskset model
    this_taskset = TaskSet(*[task_transormation(tsk) for tsk in this_taskset])

    return this_taskset


###
# Cause-effect chain generation.
###

def gen_ce_chains(task_set):  # TODO update
    """Generate CE chains based on task sets as object of tasks.taskset.TaskSet.
    Each task is object of tasks.task.Task."""
    distribution_involved_activation_patterns = stats.rv_discrete(
        values=([1, 2, 3], [0.7, 0.2, 0.1]))
    distribution_number_of_tasks = stats.rv_discrete(
        values=([2, 3, 4, 5], [0.3, 0.4, 0.2, 0.1]))
    ce_chains = []

    # Determine different periods of the tasks set.
    activation_patterns = list(set(map(
        lambda tsk: tsk.rel.period, task_set)))

    # there need to be at least 3 activation patterns, otherwise no chain for the taskset is created
    if len(activation_patterns) < 3:
        return []

    # Generate 30 to 60 cause-effect chains for each input task set
    for _ in range(int(np.random.randint(30, 60))):
        tasks_in_chain = []

        # Activation patterns of the cause-effect chain.
        involved_activation_patterns = list(np.random.choice(
            activation_patterns,
            size=int(distribution_involved_activation_patterns.rvs()),
            replace=False))

        # Tasks ordered from that specific activation pattern.
        period_filtered_task_set = []
        for period in involved_activation_patterns:
            period_filtered_task_set.append(
                [tsk for tsk in task_set if tsk.rel.period == period])

        try:
            for filt_task_set in period_filtered_task_set:
                # Try to add 2-5 tasks for each selected activation pattern
                # into the chain.
                tasks_in_chain.extend(list(np.random.choice(
                    filt_task_set,
                    size=distribution_number_of_tasks.rvs(),
                    replace=False)))
        except ValueError:
            # If we draw distribution_number_of_tasks such that it is
            # larger than the number of tasks with filtered period then
            # this task_set is skipped
            tasks_in_chain = []
            continue

        # Randomize order of the tasks in the chain.
        np.random.shuffle(tasks_in_chain)

        # Create chain if there are tasks in the chain.
        if len(tasks_in_chain) != 0:
            ce_chains.append(CEChain(*list(tasks_in_chain), base_ts=task_set))

    return ce_chains


if __name__ == '__main__':
    """Debug."""
    ts_set = [gen_taskset(0.5) for _ in range(5)]
    ce_set = [gen_ce_chains(ts) for ts in ts_set]
    from tasks.taskset import transform

    [transform(x) for x in ts_set]

    breakpoint()
