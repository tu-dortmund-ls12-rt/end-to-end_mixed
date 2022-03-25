"""Analyses by other authors dedicated to only implicit or only LET."""
import math


#####
# implicit communication
#####

def davare(chain):
    """Analysis from Davare et al. 2007, DAC:
    Period optimization for hard real-time distributed automotive systems.
    - implicit
    - sporadic
    """
    wcrts = chain.base_ts.wcrts
    result = 0
    for tsk in chain:
        result += tsk.rel.maxiat + wcrts[tsk]
    return result


def duerr(chain):
    """Analysis from Duerr et al. 2019, CASES:
    End-to-end timing analysis of sporadic cause-effect chains in distributed systems.
    - implicit
    - sporadic
    """
    wcrts = chain.base_ts.wcrts
    result = 0
    result += chain[0].rel.maxiat + wcrts[chain[-1]]
    for current_tsk, next_tsk in zip(chain[:-1], chain[1:]):
        if chain.base_ts.higher_prio(current_tsk, next_tsk):
            result += next_tsk.rel.maxiat
        else:
            result += next_tsk.rel.maxiat + wcrts[current_tsk]
    return result


def kloda(chain):
    """Analysis from Kloda et al. 2019, ETFA:
    Latency analysis for data chains of real-time periodic tasks.
    - implicit
    - periodic
    """
    wcrts = chain.base_ts.wcrts

    # Compute hyperperiod:
    hyper = chain.base_ts.hyperperiod()
    max_phase = chain.base_ts.max_phase()

    zvar = chain[0].rel.phase
    lengths = []

    while zvar <= max_phase + hyper:
        # read-event at z
        # compute length of one job chain
        relvar = zvar + chain[0].rel.period  # first job in job chain
        for this_tsk, next_tsk in zip(chain[:-1], chain[1:]):
            # Compute release of next job in the job chain
            if chain.base_ts.higher_prio(this_tsk, next_tsk):
                relvar = _release_after(relvar, next_tsk)
            else:
                relvar = _release_after(relvar + wcrts[this_tsk], next_tsk)
        # actuation event at zprime
        zprimevar = relvar + wcrts[chain[-1]]

        lengths.append(zprimevar - zvar)
        zvar += chain[0].rel.period  # next job

    return max(lengths)


# TODO: compare with our variable execution time analysis?

#####
# LET
#####

def LET_spor(chain):
    """Upper bound for sporadic tasks under LET.
    - LET
    -sporadic
    """
    result = 0
    for tsk in chain:
        result += tsk.rel.maxiat + tsk.dl.dl
    return result


def LET_per(chain):
    """Upper bound for periodic tasks under LET.
    - LET
    - periodic
    """
    # Compute hyperperiod:
    hyper = chain.base_ts.hyperperiod()
    max_phase = chain.base_ts.max_phase()

    zvar = chain[0].rel.phase
    lengths = []

    while zvar <= max_phase + hyper:
        # read-event at z
        # compute length of one job chain
        relvar = zvar + chain[0].rel.period  # first job in job chain
        for this_tsk, next_tsk in zip(chain[:-1], chain[1:]):
            # Compute release of next job in the job chain
            relvar = _release_after(relvar + this_tsk.dl.dl)
        # actuation event at zprime
        zprimevar = relvar + chain[-1].dl.dl

        lengths.append(zprimevar - zvar)
        zvar += chain[0].rel.period  # next job

    return max(lengths)


#####
# Helpers
#####

def _release_after(time, tsk):
    """Next release of tsk at or after 'time' for periodic tasks."""
    return tsk.rel.phase + math.ceil((time - tsk.rel.phase) / tsk.rel.period) * tsk.rel.period
