from functools import lru_cache

import numpy as np


@lru_cache
def delta_r(jet1, jet2):
    return ((jet1.phi-jet2.phi)**2 + (jet1.eta-jet2.eta)**2)**0.5


def subjettiness(candidates, constituents):
    d0 = sum(c.pt for c in constituents)
    ls = []
    for c in constituents:
        dRs = [delta_r(c, cd) for cd in candidates]
        ls += [c.pt * min(dRs)]
    return np.sum(ls)/d0


def energy_ring(jet, dR_min, dR_max):
    cnsts = jet.constituents()
    energy = 0
    for c in cnsts:
        dr = delta_r(jet, c)
        if dr >= dR_min and dr <= dR_max:
            energy += c.e
    return energy/jet.e
