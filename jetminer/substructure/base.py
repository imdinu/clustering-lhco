from functools import lru_cache

import numpy as np
from pyjet import cluster

from .helpers import subjettiness

cluster_lru = lru_cache(maxsize=16)(cluster)


def nisj(jet, **kwargs):
    seq = cluster_lru(jet, R=kwargs["R2"], algo='kt')
    return len(seq.inclusive_jets(ptmin=kwargs["ptmin2"]))


def nesj(jet, **kwargs):
    seq = cluster_lru(jet, R=kwargs["R2"], algo='kt')
    return seq.n_exclusive_jets(kwargs["dcut"])


@lru_cache(maxsize=8)
def tau(jet, i, **kwargs):
    cnsts = jet.constituents()
    if len(cnsts) >= i:
        seq = cluster_lru(jet, R=kwargs["R"], algo='kt')
        cndts = seq.exclusive_jets(i)
        return subjettiness(cndts, cnsts)
    else:
        return 0


def tau3(jet, **kwargs):
    return tau(jet, 3, **kwargs)


def tau2(jet, **kwargs):
    return tau(jet, 2, **kwargs)


def tau1(jet, **kwargs):
    return tau(jet, 1, **kwargs)


def tau32(jet, **kwargs):
    t3 = tau3(jet, **kwargs)
    t2 = tau2(jet, **kwargs)
    return t3/t2 if t2 > 0 else np.inf


def tau21(jet, **kwargs):
    t2 = tau2(jet, **kwargs)
    t1 = tau1(jet, **kwargs)
    return t2/t1 if t1 > 0 else np.inf
