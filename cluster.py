"""Main script for LHC Olympics data processing.

This script is designed to apply jet clustering and feature engineering to the
LHC olympics datasets, which are available as a collection of 4-vectors
associated with events' constituent particles. Given that all events are 
independent, this process can be heavily parallelized resulting in significant
execution time reduction.  

Example:

    For script usage details use::

        $ python cluster --help

At the moment the full scope of this project is yet to be realized, but the 
remaining features are soon to be implemented.

"""


import argparse
import os
import shutil
import psutil
import multiprocessing as mpi
from time import sleep
from collections import deque
from pathlib import Path

import h5py
import tqdm
import numpy as np
import pandas as pd

from jetminer import clustering_LHCO

mpi.set_start_method('fork')


def merge(path, feature):
    '''
    Merge all *.hdf* files in given directory.

    This function is called once at the end of the clustering run in order to 
    unite all the partial results obtained from parallell clustering 
    execution.

    Returns:
      ``pd.DataFrame`` from merged *.hdf* files

    '''
    signal_files = sorted(path.glob(f"{feature}_sig*"))
    background_files = sorted(path.glob(f"{feature}_bkg*"))

    files_list = [background_files, signal_files]
    dfs_merged = []

    for files in files_list:
        df_list = []
        if files:
            for filename in files:
                df = pd.read_hdf(filename)
                df.reset_index(drop=True)
                df_list.append(df)
        dfs_merged.append(pd.concat(df_list, axis=0, ignore_index=True)
                          if df_list else None)

    return dfs_merged[0], dfs_merged[1]


params = {
    "R": 1.,
    "njets": 2,
    "cluster_algo": "antikt",
    "masterkey": None,
    "R2": 0.2,
    "ptmin": 0,
    "ptmin2": 0,
    "dcut": 0.1
}
"""dict: default values for data clustering parameters

The parameters in question are:
    * ``R``: Radius used in primary clustering.
    * ``njets``: Number of jets expected per event.
    * ``cluster_algo``: Algorithm used for primary clustering (see `pyjet`
        documentation).
    * ``masterkey``: Path to masterkey file containing truth information.
    * ``R2``: Radius for secondary clustering, used in the calculation of several 
        substructure features which are dependent on sub-jets.
    * ``ptmin``: Minimum pT cutoff of expected primary jets.
    * ``ptmin2``: Minimum pT cutoff applied to subjets.
    * ``dcut``: Minimmum distance between exclusive sub-jets (also used for
        calculating substructure features).
"""

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Jet clustering and feature extraction tool")
    parser.add_argument("path", action="store", type=str,
                        help="input hdf file of particles")
    parser.add_argument("-r", action="store", default=1.0, type=float,
                        help="radius used for primary clustering")
    parser.add_argument("-j", action="store", default=0, type=int,
                        help="number of parallel processes")
    parser.add_argument("--max-events", action="store", default=0, type=int,
                        help="maximum number of events to cluster")
    parser.add_argument("--chunk-size", action="store", default=0, type=int,
                        help="number of events per process")
    parser.add_argument("--tmp", action="store", default="./tmp",
                        type=Path, help="path to temporary storage folder")
    args = parser.parse_args()

    # Get number of availabe cores and workers
    n_max = psutil.cpu_count(logical=False)
    if args.j == 0:
        n_workers = n_max
    else:
        n_workers = args.j

    # Get the number of events in the input file
    f = h5py.File(args.path, "r")
    n_events = f['df']["block0_values"].shape[0]
    f.close()
    if args.max_events < n_events and args.max_events != 0:
        n_events = args.max_events

    # Get the chunk size and number of chunks
    if args.chunk_size == 0:
        args.chunk_size = n_events // n_workers
    n_chunks = n_events // args.chunk_size

    # Define work directory tree
    if args.tmp.exists():
        shutil.rmtree(args.tmp)
    Path.mkdir(args.tmp)

    # Create progress bars for all parallel processes
    pbars = [tqdm.tqdm(total=args.chunk_size, position=i+1, colour="cyan",
                       leave=0, ncols=79, bar_format='{l_bar}{bar}')
             for i in range(n_workers)]

    # Define all chunks as processes
    procs = [mpi.Process(target=clustering_LHCO,
                         args=(args.path, i*args.chunk_size,
                               (i+1)*args.chunk_size, args.tmp),
                         kwargs={**{"bars": pbars}, **params})
             for i
             in range(n_chunks)]
    process_queue = deque(procs)

    # Define overall progress bar
    main_bar = tqdm.tqdm(total=len(procs), desc="Overall progress", ncols=79,
                         position=0, bar_format='{l_bar}{bar}{elapsed}',
                         colour="green")

    # Run the processes
    finished = np.zeros(n_workers).astype(bool)
    while sum(finished) < len(procs):
        # Count the number of active cores
        working = np.sum(list(map(lambda obj: obj.is_alive(), procs)))

        # If all cores are busy wait, otherwise start new chunks
        if working >= n_workers:
            sleep(0.1)
        else:
            exited = np.array(
                list(map(lambda obj: obj.exitcode, procs))) != None
            done = np.sum(exited) - np.sum(finished)
            main_bar.update(done)
            finished = exited
            if len(process_queue) > 0:
                process_queue.popleft().start()

    # Merge files
    for features in ["scalars"]:
        bkg_df, sig_df = merge(args.tmp, features)

        if bkg_df is not None:
            bkg_df.to_hdf(f"./{features}_bkg.h5", key="bkg")
        if sig_df is not None:
            sig_df.to_hdf(f"./{features}_sig.h5", key="bkg")
