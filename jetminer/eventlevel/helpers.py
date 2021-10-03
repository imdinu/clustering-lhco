from operator import attrgetter


def sum_attributes(objs, attr):
    """Returns the sum over an attribute of a list of objects.

    Args:
        objs (list): Objects whose attributes will be summed over
        attr (str):Attribute to be accessed for all objects 

    Returns:
        Sum of all the objects' attributes, type dependent on the objects' type
    """
    return sum(attrgetter(attr)(obj) for obj in objs)


def combined_mass(jets):
    """Calculates the combined invariant mass of an arbitrary number of jets.

    Args:
        jets (list of `PseudoJet`): The list of jets whose mass will be 
            computed.
    Returns:
        The combined invariant mass of the `jets`, as `float`, in GeV. 
    """
    if None in jets:
        jets = [j for j in jets if j]
    if len(jets) == 0:
        return 0
    E = sum_attributes(jets, "e")
    px = sum_attributes(jets, "px")
    py = sum_attributes(jets, "py")
    pz = sum_attributes(jets, "pz")
    return (E**2-px**2-py**2-pz**2)**0.5
