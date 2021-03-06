import multiprocessing as mpi
import json
from operator import attrgetter
from collections import ChainMap
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyjet import cluster, DTYPE_PTEPM, JetDefinition

from jetminer import substructure
from jetminer import eventlevel
from jetminer.image import image_from_jets
from jetminer.eventlevel.combinedmass import make_mass_fns


FEATURES_PYJET = ["pt", "eta", "phi", "mass", "e", ]
"""list: features taken directly from ``PseudoJet`` objects 

"""
FEATURES_EVENT = ["mjj", "nj"]
"""list: features calculated at the event level
"""


def cluster_event(event, cluster_algo="antikt", R=1):
    """Clusters particle flow event data into jets.

    Args:
        events (np.array): 1-dimensional array of particle information 
            (pT, eta, phi).
        cluster_algo (str): Selection of clustering algorithm. Possible 
            options are `kt`, `antikt`, `cambridge`, `genkt`.
        R (float): Jet radius used for clustering.

    Returns:
        Sequence of clustered jets.
    """
    pseudojets_input = np.zeros(
        np.count_nonzero(event)//3, dtype=DTYPE_PTEPM)
    tmp = event[event.nonzero()].reshape(-1, 3)
    pseudojets_input["pT"] = tmp[:, 0]
    pseudojets_input["eta"] = tmp[:, 1]
    pseudojets_input["phi"] = tmp[:, 2]
    jdef = JetDefinition(cluster_algo, R)
    return cluster(pseudojets_input, jdef)


def pyjet_features(jet, idx):
    """Creates feature dictionary with pyjet attributes.

    Args:
        jet (`PseudoJet`): input jet
        idx (int): input jet's index number (in pT ordering)

    Returns:
        Dictionary of pyjet features, with jet index included in key names.
    """
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
    """Creates feature dictionary with jet's substructure variables.

    Args:
        jet (`PseudoJet`): Input jet.
        idx (int): Input jet's index number (in pT ordering).
        **kwargs: Arguments used in substructure variable calculation.

    Returns:
        Dictionary of jet's substructure variables, with jet index included 
        in key names.
    """
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
    """Creates feature dictionary event-level features.

    Args:
        jets (list of `PseudoJet`): Event clustered as a list of jets.

    Returns:
        Dictionary of event-level features.
    """
    masses = {
        f"{fn.__name__}": fn(jets)
        for fn in make_mass_fns(len(jets))
    }
    misc = {
        f"{feature}": getattr(eventlevel, feature)(jets)
        for feature in eventlevel.__all__
    }
    return {**misc, **masses}


def pad_list(l, size):
    """Pads the list with `None` up the required number of elements

    Args:
        l (list): the input list to be padded
        size (int): size of the padded list

    Returns:
        The original list padded with `None` up to the given size
    """
    while len(l) < size:
        l.append(None)
    return l


def clustering_LHCO(path_in, start, stop, path_out, scalars=True,
                    images=False, img_config=None, bars=None, **kwargs):
    """Runs a clustering algorithm on LHC Olympics data.

    Args:
        path_in (Path): Path of input LHCO dataset.
        start (int): Index of first desired event of the dataset.
        stop (int): Index of last desired event of the dataset.
        path_out (str or `Path`): Path of output folder, where results
             are stored.
        scalars (bool): compute the scalar features after clustering
        images (bool): generate jet images after clustering
        img_config (Path): json configuration file for image generation
        bars (tqdm.std.tqdm): Progress bar objects defined with ``tqdm``
        **kwargs: jet clustering parameters

    Returns:
        Return code 0 for success. None otherwise
    """
    pno = mpi.current_process()._identity[0]
    if bars:
        bar = bars[(pno-1) % len(bars)]
    data = pd.read_hdf(path_in, start=start, stop=stop).to_numpy()

    if kwargs["masterkey"]:
        if data.shape[1] % 3 == 1:
            raise ValueError("Masterkey given for data with truth bit")
        else:
            truth_bit = np.fromfile(kwargs["masterkey"], dtype=float, 
                                    sep='\n').astype(int)[start:stop]

    elif data.shape[1] % 3 == 1:
        data, truth_bit = data[:, :-1], data[:, -1]
    else:
        truth_bit = None

    if images:
        img_def = load_json(img_config)

    datachunk = []
    imagechunk = []
    for row in data:
        seq = cluster_event(row, kwargs["cluster_algo"], kwargs["R"])
        jets = pad_list(seq.inclusive_jets(ptmin=kwargs["ptmin"])[
                            :kwargs["njets"]], kwargs["njets"])
        if scalars:
            features = [pyjet_features(jet, i) for i, jet in enumerate(jets)]
            features += [substructure_features(jet, i, **kwargs)
                        for i, jet in enumerate(jets)]
            features += [event_features(np.array(jets))]
            feature_dict = dict(ChainMap(*features))
            datachunk.append(feature_dict)
        if images:
            imagechunk.append(image_from_jets(jets, **img_def))
        bar.desc = f"Chunk {pno:02d}"
        bar.update(1)

    if scalars:
        _save_scalars(pd.DataFrame(datachunk), truth_bit, pno, path_out)
    if images:
        _save_images(np.stack(imagechunk), truth_bit, pno, path_out)

    return 0

def _save_scalars(datachunk, truth_bit, pno, path_out):
    folder_out = Path(path_out)
    if truth_bit is not None:
        mask_sig = truth_bit == 1
        datachunk[~mask_sig].to_hdf(
            folder_out.joinpath(f"scalars_bkg{pno:02d}.h5"),
            key="bkg")
        datachunk[mask_sig].to_hdf(
            folder_out.joinpath(f"scalars_sig{pno:02d}.h5"),
            key="sig")
    else:
        datachunk.to_hdf(folder_out.joinpath(f"scalars_bkg{pno:02d}.h5"),
                    key="bkg")

def _save_images(imagechunk, truth_bit, pno, path_out):
    folder_out = Path(path_out)
    if truth_bit is not None:
        mask_sig = truth_bit == 1
        imgs_file_sig = folder_out.joinpath(f"images_sig{pno:02d}.h5")
        hf = h5py.File(imgs_file_sig, 'w')
        hf.create_dataset('sig', data=imagechunk[mask_sig])
        hf.close()
    imgs_file_bkg = folder_out.joinpath(f"images_bkg{pno:02d}.h5")
    hf = h5py.File(imgs_file_bkg, 'w')
    hf.create_dataset('bkg', data=imagechunk[~mask_sig] 
                                if mask_sig is not None 
                                else imagechunk)
    hf.close()


def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

    
