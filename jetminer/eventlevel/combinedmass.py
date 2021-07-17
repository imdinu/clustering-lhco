from .helpers import combined_mass
from itertools import chain, combinations


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


def make_mass_fn(jets):
    """Creates functions calculating the combined mass of `jets` subsets.

    A separate function will be created for each subset of `jets` containing
    at least two elements. The function will be named accordingly.

    Args:
        jets (list of `PseudoJet`): The jets whose mass the returned function
            will compute
    
    Returns:
        None.
    """
    def f(jets):
        return combined_mass(jets)
    #exec(f"global mjj; mjj = f")
    raise NotImplementedError("This is not yet available")

def mjj(jets):
    return combined_mass(jets)


__all__ = ["mjj"]

if __name__ != "__main__":
    pass
