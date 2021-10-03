from itertools import chain, combinations
from functools import reduce
from this import d

import numpy as np

from .helpers import combined_mass


def powerset(iterable):
    """Returns all subset combinantions containing at least two elements.

    Args:
        iterable (list): The initial set

    Returns:
        Chain of subsets of `iterable` containing at least two elements.

    Examples: 
        powerset([1,2,3]) --> (1,2) (1,3) (2,3) (1,2,3)
    """
    ""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(2, len(s)+1))


def make_mass_fns(njets):
    """Creates functions calculating the combined mass of `jets` subsets.

    A separate function will be created for each subset of `jets` containing
    at least two elements. The function will be named accordingly.

    Args:
        njets (list of `PseudoJet`): The number of jets expected within
            clustered every event
    
    Returns:
        List of functions for calculation all possible combinened masses.
    """
    idx = np.arange(njets)
    combs = powerset(idx)
    
    return [mass_clojure(idx) for idx in combs]

def mass_clojure(idx):
    """Makes a function to calculate the combined masss, using given indices
    
    This clojure creates a function that computes the combined mass of a 
    subset of jets within an event. It works under the assumption that all 
    clustered events have the same number of jets.

    Args:
        idx (list of 'int'): The indices of the jets taken into account when
            computing the combined masss.

    Returns:
        the funtion created
    """
    def f(jets):
        return combined_mass(jets[np.array(idx)])

    # generate a unique name based on the indices
    name = [f"j{i+1:d}" for i in idx]
    name.insert(0, "m")
    f.__name__ = reduce(str.__add__, name)

    return f

# def mjj(jets):
#     return combined_mass(jets)

