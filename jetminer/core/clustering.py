import multiprocessing as mpi
from operator import attrgetter
from collections import ChainMap
from pathlib import Path

import numpy as np
import pandas as pd
from pyjet import cluster, DTYPE_PTEPM, JetDefinition

from jetminer import substructure
from jetminer import eventlevel

FEATURES_PYJET = ["pt", "eta", "phi", "mass", "e", ]


FEATURES_RINGS = []
FEATURES_EVENT = ["mjj", "nj"]


def cluster_event(event, cluster_algo="antikt", R=1):
    pseudojets_input = np.zeros(
        np.count_nonzero(event)//3, dtype=DTYPE_PTEPM)
    tmp = event[event.nonzero()].reshape(-1, 3)
    pseudojets_input["pT"] = tmp[:, 0]
    pseudojets_input["eta"] = tmp[:, 1]
    pseudojets_input["phi"] = tmp[:, 2]
    jdef = JetDefinition(cluster_algo, R)
    sequence = cluster(pseudojets_input, jdef)
    return sequence


def pyjet_features(jet, idx):
    if jet is not None:
        return {
            f"{feature}_{idx+1}": attrgetter(feature)(jet)
            for feature in FEATURES_PYJET
        }
    else:
        return {
            f"{feature}_{idx+1}": 0
            for feature in FEATURES_PYJET
        }


def substructure_features(jet, idx, **kwargs):
    if jet is not None:
        return {
            f"{feature}_{idx+1}": getattr(substructure, feature)(jet, **kwargs)
            for feature in substructure.__all__
        }
    else:
        return {
            f"{feature}_{idx+1}": 0
            for feature in substructure.__all__
        }


def event_features(jets):
    return {
        f"{feature}": getattr(eventlevel, feature)(jets)
        for feature in eventlevel.__all__
    }


def pad_list(l, size):
    while len(l) < size:
        l.appen(None)
    return l


def clustering_LHCO(path_in, start, stop, path_out, bars=None, **kwargs):

    if bars:
        pno = mpi.current_process()._identity[0]
        bar = bars[(pno-1) % len(bars)]
    data = pd.read_hdf(path_in, start=start, stop=stop).to_numpy()
    if kwargs["masterkey"]:
        if data.shape[1] % 3 == 1:
            raise ValueError("Masterkey given for data with truth bit")
        else:
            raise NotImplementedError(
                "Labels from masterkey not implemented yet")
    else:
        if data.shape[1] % 3 == 1:
            data, truth_bit = data[:, :-1], data[:, -1]
        else:
            truth_bit = None

    datachunk = []
    for row in data:
        seq = cluster_event(row, kwargs["cluster_algo"], kwargs["R"])
        jets = pad_list(seq.inclusive_jets(ptmin=kwargs["ptmin"])[
                        :kwargs["njets"]], kwargs["njets"])
        features = [pyjet_features(jet, i) for i, jet in enumerate(jets)]
        features += [substructure_features(jet, i, **kwargs)
                     for i, jet in enumerate(jets)]
        features += [event_features(jets)]
        feature_dict = dict(ChainMap(*features))
        datachunk.append(feature_dict)
        bar.desc = f"Chunk {pno:02d}"
        bar.update(1)

    dfchunk = pd.DataFrame(datachunk)
    folder_out = Path(path_out)
    if truth_bit is not None:
        mask_sig = truth_bit == 1
        dfchunk[~mask_sig].to_hdf(
            folder_out.joinpath(f"scalars_bkg{pno:02d}.h5"),
            key="bkg")
        dfchunk[mask_sig].to_hdf(
            folder_out.joinpath(f"scalars_sig{pno:02d}.h5"),
            key="sig")
    else:
        dfchunk.to_hdf(folder_out.joinpath(f"scalars_bkg{pno:02d}.h5"),
                       key="bkg")

    return 0
