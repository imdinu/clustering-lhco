"""Package containing logic for event-level variable calculation.

The currently supported features are:
  * ``nj``: number of jets in the event passing the selection criteria

"""


def nj(jets):
    """Returns the number of elements of `jets`"""
    return len(jets)


__all__ = ["nj"]
