"""Package containing logic for jet substructure variable calculation.

The currently supported features are:
  * ``nisj``: number of subjets (in the inclusive sense)
  * ``nesj``: number of subjets (in the exclusive sense)
  * ``tau``N: N-subjetiness
  * ``eRing``N: N-th energy ring
"""

from jetminer.substructure.base import *
from jetminer.substructure.rings import *


__all__ = ["nisj", "nesj", "tau1", "tau2", "tau3", "tau32", "tau21"] \
    + ["eRing0", "eRing1", "eRing2", "eRing3", "eRing4",
        "eRing5", "eRing6", "eRing7", "eRing8", "eRing9"]
