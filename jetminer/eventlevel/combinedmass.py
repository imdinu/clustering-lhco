from .helpers import combined_mass
from itertools import chain, combinations


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(2, len(s)+1))


def make_mass_fn(jets):
    def f(jets):
        return combined_mass(jets)
    exec(f"global mjj; mjj = f")


def mjj(jets):
    return combined_mass(jets)


__all__ = ["mjj"]

if __name__ != "__main__":
    pass
