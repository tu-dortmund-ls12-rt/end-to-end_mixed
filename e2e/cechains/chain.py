from tasks.taskset import TaskSet


class CEChain(TaskSet):
    """A cause-effect chain."""
    pass


if __name__ == '__main__':
    from tasks.task import Task

    ce = CEChain(Task(), Task(), Task())
    breakpoint()
