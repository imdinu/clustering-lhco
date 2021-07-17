import types

import numpy as np

from .helpers import energy_ring
rings = __import__(__name__)

DEFAULT_RINGS = [[0, 0.01], [0.01, 0.01668101], [0.01668101, 0.02782559],
                 [0.02782559, 0.04641589], [0.04641589, 0.07742637],
                 [0.07742637, 0.12915497], [0.12915497, 0.21544347],
                 [0.21544347, 0.35938137], [0.35938137, 0.59948425],
                 [0.59948425, 1]]


def make_ring_fn(ring, no):
    def f(jet, **kwargs):
        return energy_ring(jet, *ring)
    globals()[f"eRing{no:d}"] = f
    #exec(f"global eRing{no:d}; eRing{no:d} = f")


if __name__ != "__main__":
    for no, ring in enumerate(DEFAULT_RINGS):
        make_ring_fn(ring, no)
