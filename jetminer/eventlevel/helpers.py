from operator import attrgetter


def sum_attributes(objs, attr):
    return sum([attrgetter(attr)(obj) for obj in objs])


def combined_mass(jets):
    E = sum_attributes(jets, "e")
    px = sum_attributes(jets, "px")
    py = sum_attributes(jets, "py")
    pz = sum_attributes(jets, "pz")
    return (E**2-px**2-py**2-pz**2)**0.5
