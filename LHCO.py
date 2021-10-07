#!/usr/bin/env python
"""Main script for LHC Olympics data processing.

This script is designed to apply jet clustering and feature engineering to the
LHC olympics datasets, which are available as a collection of 4-vectors
associated with events' constituent particles. Given that all events are 
independent, this process can be heavily parallelized resulting in significant
execution time reduction.  

Example:

    For script usage details use::

        $ ./LHCO --help

    Alternatively you can import this module for use within your custom 
    pipeline::

        from LHCO import clustering_mpi, params, merge
     
    
At the moment the full scope of this project is yet to be realized, but the 
remaining features are soon to be implemented.

"""


import argparse
from email.policy import default
import os
import shutil
import psutil
import requests
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

data_urls = {
    "RnD": "https://zenodo.org/record/4536377/files/"
           "events_anomalydetection.h5?download=1",
    "RnD_3prong": "https://zenodo.org/record/4536377/files/"
                  "events_anomalydetection_Z_XY_qqq.h5?download=1",
    "BBOXMC": "https://zenodo.org/record/4536624/files/"
              "events_LHCO2020_backgroundMC_Pythia.h5?download=1",
    "BBOX1": "https://zenodo.org/record/4536624/files/"
             "events_LHCO2020_BlackBox1.h5?download=1",
    "BBOX2": "https://zenodo.org/record/4536624/files/"
             "events_LHCO2020_BlackBox2.h5?download=1",
    "BBOX3": "https://zenodo.org/record/4536624/files/"
             "events_LHCO2020_BlackBox3.h5?download=1"
}
"""dict: URLs for all LHC Olympics datasets Zenodo download links.

Key-value pairs of Dataset Identifiers and URLs.

Available datasets are: 
    ``RnD``, ``RnD_3prong``, ``BBOXMC``, ``BBOX1``, ``BBOX2``, 
    ``BBOX3``
"""

masterkey_urls = {
    "BBOX1": "https://zenodo.org/record/4536624/files/"
             "events_LHCO2020_BlackBox1.masterkey?download=1",
    "BBOX3": "https://zenodo.org/record/4536624/files/"
             "events_LHCO2020_BlackBox3.masterkey?download=1"
}
"""dict: URLs for LHC Olympics datasets' masterkeys.

Key-value pairs of Dataset Identifiers and URLs. Only ``BBOX1`` and ``BBOX3``
datasets have masterkeys.
"""

def download_file(url, path, descriptor=None, chunk_size=1024**2, timeout=None):
    """Downloads a file to the specified path
    
    Args:
        url (str): URL of the file
        path (Path): The location where the file will be saved
        descriptor (string): Progres bar annotation
        chunksize  (int): Number of bytes per chunk
        timeout (float or tuple): Seconds to wait for the response

    Returns:
        None
    """
    ans = requests.get(url, stream=True, timeout=timeout)
    with open(path, "wb") as file:
        for chunk in tqdm.tqdm(ans.iter_content(chunk_size),
                          unit='MB',
                          desc=descriptor):
            if chunk:
                file.write(chunk)

def merge(path, feature):
    """Merge all *.hdf* files in given directory.

    This function is called once at the end of the clustering run in order to 
    unite all the partial results obtained from parallell clustering 
    execution.

    Return:
      ``pd.DataFrame`` from merged *.hdf* files
    """
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

def run_procs(procs, n_workers, bar=None):
    """Paralell execution of a collection of processes across `n_workers`.

    Called by the `clusterin_mpi` function after setting up the jobs,
    this function manages the execution of the parallel processes. Optionally
    can display a progress bar for completed jobs.

    Args:
        procs (list): Collection of `mpi.Process` objects to be executed
        n_workers (int): Number of physicals cores available for parallel 
            execution of jobs
        bar (obj): Instance of `tqdm.tqdm` used for displaying progress
    """
    process_queue = deque(procs)
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
            if bar:
                bar.update(done)
            finished = exited
            if len(process_queue) > 0:
                process_queue.popleft().start()

def clustering_mpi(path, j, max_events, chunk_size, tmp_dir, out_dir, 
                   out_prefix="results", quiet=False, **kwargs):
    """Applies clustering to LHC Olympics data using multiprocessing.

    Main function performing the clustering. It spreads the input events
    across ``j`` logical cores and prints a progress bar for each process'
    progress towards completing a chunk of events. Each process stores its
    result in a temporary fille; at the end of the clustering all filles
    will be merged.

    Args:
        path (Path): Path of `.hdf` input file containing LHCO data.
        j (int): Number of logical cores to distribute the load. If 0, then all
            available cores will be used.
        max_events (int): Maximum number of events to be used. If 0, all events
            in the file will be used.
        chunk_size (int): Number of events to be distributed to each job. If
            0, then the chunk size will e adjusted so that the number of jobs 
            is equal to the number of logical cores
        tmp_dir (Path): Path of the directory where temporary result files
            will be stored. *All contents of the directory will be erased.* 
            If the directory does not exist, it will be created.
        out_dir (Path): Path of the directory where the merged result will be
            saved.
        out_prefix (str): Prefix used for the results' filenames. 
        quiet (bool): Suppresses the output of ``tqdm`` progress bars
        **kwargs: Keyword arguments for specifing clustering parameters. 
            Default values can be found in the ``LHCO.params`` dict. 
    Return:
        None
    """

    # Get number of availabe cores and workers
    n_max = psutil.cpu_count(logical=False)
    n_workers = n_max if j == 0 else j

    # Get the number of events in the input file
    f = h5py.File(path, "r")
    n_events = f['df']["block0_values"].shape[0]
    f.close()
    if max_events < n_events and max_events != 0:
        n_events = max_events

    # Get the chunk size and number of chunks
    if chunk_size == 0:
        chunk_size = n_events // n_workers
    n_chunks = n_events // chunk_size

    # Define work directory tree
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    Path.mkdir(tmp_dir)

    # Create progress bars for all parallel processes
    pbars = [tqdm.tqdm(total=chunk_size, position=i+1, colour="cyan",
                       leave=0, ncols=79, bar_format='{l_bar}{bar}',
                       disable=quiet)
             for i in range(n_workers)]

    # Define all chunks as processes
    procs = [mpi.Process(target=clustering_LHCO,
                         args=(path, i*chunk_size,
                               (i+1)*chunk_size, tmp_dir),
                         kwargs={**{"bars": pbars}, **kwargs})
             for i
             in range(n_chunks)]

    # Define overall progress bar
    main_bar = tqdm.tqdm(total=len(procs), desc="Finished chunks", ncols=79,
                         position=0, bar_format='{l_bar}{bar}{elapsed}',
                         colour="green", disable=quiet)

    # Run the processes
    # finished = np.zeros(n_workers).astype(bool)
    # while sum(finished) < len(procs):
    #     # Count the number of active cores
    #     working = np.sum(list(map(lambda obj: obj.is_alive(), procs)))

    #     # If all cores are busy wait, otherwise start new chunks
    #     if working >= n_workers:
    #         sleep(0.1)
    #     else:
    #         exited = np.array(
    #             list(map(lambda obj: obj.exitcode, procs))) != None
    #         done = np.sum(exited) - np.sum(finished)
    #         main_bar.update(done)
    #         finished = exited
    #         if len(process_queue) > 0:
    #             process_queue.popleft().start()
    run_procs(procs, n_workers, main_bar)

    # In case of `None` prefix revert to default
    if out_prefix is None:
        out_prefix = "results"

    # Merge files
    for features in ["scalars"]:
        bkg_df, sig_df = merge(tmp_dir, features)

        if bkg_df is not None:
            bkg_df.to_hdf(
                out_dir.joinpath(f"{out_prefix}_{features}_bkg.h5"), 
                key="bkg")
        if sig_df is not None:
            sig_df.to_hdf(
                out_dir.joinpath(f"{out_prefix}_{features}_sig.h5"), 
                key="bkg")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Jet clustering and feature extraction script")
    subparsers = parser.add_subparsers()
    download = subparsers.add_parser("download", 
                                     help="download the LHCO dataset")
    run = subparsers.add_parser("cluster", help="run jet clustering")
    run.add_argument("path", action="store", type=Path, default=None,
                     help="input hdf data file, if [-D] argument is given, "
                     "the file will first be downloaded and saved with this "
                     "path")
    run.add_argument("-R", action="store", default=1.0, type=float,
                     help="radius used for primary clustering")
    run.add_argument("-j", action="store", default=0, type=int,
                     help="number of parallel processes")
    run.add_argument("--max-events", action="store", default=0, type=int,
                     help="maximum number of events to cluster")
    run.add_argument("--chunk-size", action="store", default=0, type=int,
                     help="number of events per process")
    run.add_argument("--tmp-dir", action="store", default="./tmp",
                     type=Path, help="path to temporary storage folder")
    run.add_argument("--out-dir", action="store", default=".", type=Path,
                     help="directory used for storing final results")
    run.add_argument("--out-prefix", action="store", default=None, 
                     type=str, help="prefix used for results' filenames")
    run.add_argument("-Q", "--quiet", help="suppress all printing to"
                     "stdout", action="store_true")
    run.add_argument("-D", "--download", action="store", type=str, 
                     choices=data_urls.keys(), default=None,
                     help="identifier of the LHC Olympics dataset to "
                     "download")
    run.add_argument("-K", "--masterkey", type=Path, const=os.devnull,
                     default=None,  nargs="?",
                     help="path to the masterkey to separate signal/"
                     "background; if [-D] option is given, the masterkey will"
                     " be downloaded first and stored in the file path "
                     "provided, use this as a flag if you want the masterkey "
                     "stored in the same directory as the dataset")
    run.add_argument("--njets", action="store", default=2, type=int,
                     help="Expected number of jets per event")
    run.set_defaults(run=True)
    download.add_argument("download", action="store", type=str,
                          choices=data_urls.keys(), 
                          help="LHC Olympics dataset identifier")
    download.add_argument("path", action="store", type=Path,
                          help="path used for saving the file, if it is a "
                          "dir, an appropriately named file will be created"
                          " there")
    download.add_argument("-K", "--masterkey", type=Path, const=os.devnull, 
                          nargs="?", default=None, 
                          help="download the masterkey (if applicable); use"
                          "this a flag if you want it downloaded in the same "
                          "directory with the default name or specify a file "
                          "path where you want the masterkey to be stored")
    download.set_defaults(run=False)

    # Parse command line arguments
    args = parser.parse_args()

    if args.download:

        # If path is directory choose default filename for download
        if os.path.isdir(args.path):
            args.path = args.path.joinpath(f"LHCO_{args.download}.h5")

        if args.masterkey:
            # Check if masterkey exists for dataset
            if args.download not in masterkey_urls.keys():
                raise ValueError("No masterkey available for dataset "
                        f"{args.download}")
            # Use default masterkey filename if noting is provided
            if os.path.samefile(args.masterkey, os.devnull):
                args.masterkey = args.path.parent.joinpath(
                    f"LHCO_{args.download}.masterkey")
            # Download the masterkey
            download_file(masterkey_urls[args.download], 
                args.masterkey, 
                descriptor=f"Downloading {args.download} masterkey")

        download_file(data_urls[args.download], args.path, 
                      descriptor=f"Downloading {args.download} dataset")

    if args.run:
        
        # If output dir is not specified, the path directory will be used 
        if not args.out_dir:
            args.out_dir = args.path.parent

        # If there is no prefix the URL identifier will be used if it exists
        if not args.out_prefix and args.download:
            args.out_prefix = args.download

        # Update run parameters based on comand line arguments
        params.update(vars(args))

        # Execute clustering
        clustering_mpi(**params)
