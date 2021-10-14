# About

This package aims at streamlining the LHC Olympics data preprocessing steps. It automates data downloading, clustering (with `pyjet`) and signal/background events segregation. The `multiprocessing` module is used for parallelizing event processing.

Full documentation is available at [this readthedocs.io page](https://clustering-lhco.readthedocs.io/en/latest/).

**Latest Update:**
- Added a new scalar feature **nc** (number of constituents)
- Jet image generation
- Minor bugfixes

## Known Issue:
- if the chunk size is not a divisor of the number of events, some events will be left out a fix is incoming

**Coming Soon 🔜**
- Clustering config via JSON
- Testing coverage for image generation
- Updated README

# Quick Start

In order to use this piece of software you just need to clone it and make sure you have all of the requirements installed:

    [~]$ git clone https://gitlab.cern.ch/idinu/clustering-lhco.git
    [~]$ cd clustering-lhco
    [clustering-lhco]$ pip install -r requirements.txt

The bulk of this package's functionalities can be accessed through the `LHCO.py` script. Available commands for this script are `cluster` and `download`

The example below shows how to download and cluster the LHC Olympics *RnD* dataset using the default clustering parameters. The ``-D`` option to the ``cluster`` command instructs the script to first download the dataset before clustering and its argument selects which dataset to download. 

    [clustering-lhco]$ mkdir data
    [clustering-lhco]$ ./LHCO.py cluster -D RnD ./data/

The downloaded fille will always be named `LHCO_{dataset_identifier}.h5` if the `path` argument is a directory, in this case it will be `LHCO_RnD.h5`. If you want to customize the dataset name you can specify a file path in the command:
>./LHCO.py cluster -D RnD ./data/mydata.h5

Resulting files from the clustering will be named `RnD_scalars_bkg.h5` and `RnD_scalars_sig.h5` containing the clustered background and signal events. The prefix of the file names can be customized with the option `--out-prefix` otherwise it defaults to `{dataset_identifier}` if the download and clustering are done through a single command. On the other hand the results default location is the same directory where the data is found; you can use the option `--out-dir` to specify a different directory.

Those download and cluster steps can be also accomplished individually. In this example the downloaded data and results will be stored in different directories.

    [clustering-lhco]$ mkdir data results
    [clustering-lhco]$ ./LHCO.py download RnD ./data/myRnD.hdf
    [clustering-lhco]$ ./LHCO.py cluster ./data/myRnD.hdf --out-dir ./results/ --out-prefix mydata



# Additional Options

As part of the anomaly detection challenge, black box datasets contain signal events that are not labeled. If you want to unblind these datasets there is a dedicated option ``-K`` for that. Include the ``-K`` option for the download command in order to download the masterkey as well. Use ``-K`` in the ``cluster`` command to specify the path of the downloaded masterkey. Alternatively you can use this together with the ``-D`` flag in order to achieve everything with a single command:

    [clustering-lhco]$ ./LHCO.py cluster -K -D BBOX1 ./data/

**Note:** masterkeys are only available for ``BBOX1`` and ``BBOX3`` datasets. 

More documentation on the available options can be displayed using `--help` flag:
> ./LHCO.py cluster --help

or 
> ./LHCO.py download --help

If you want to implement the clustering into your own pipeline check the Technical Documentation on [readthedocs.io](https://clustering-lhco.readthedocs.io/en/latest/LHCO.html) for detailed information about the contents and implementation of this package.

## Workload distribution

The main parameters you can control relative to workload distribution are: the number of logical cores used ``-j``, the number of events per job ``--chunk-size`` and the number of events read from the input file``--max-events``.

The following lines provide an example of a clustering run on the RnD dataset where all events are split among 5 cores with every job using 10.000 events:

    [clustering-lhco]$ mkdir data results
    [clustering-lhco]$ ./LHCO.py download RnD ./data/
    [clustering-lhco]$ ./LHCO.py cluster ./data/LHCO_RnD.h5 --out-dir ./results/ --out-prefix RnD -j 5 --chunk-size 10000

By default the maximum number of logical cores is used for the value of ``-j``. Do not set the value of ``-j`` unless you specifically want to reduce the load on your machine. The ``--chunk-size`` option only impacts the number of temporary files created, so feel free to use whatever value you seem fit.

## Clustering parameters

All parameters associated with the clustering process can be specified directly through command line options. Among those options you can choose: ``-R``, ``--njets``, ``--cluster_algo``, `-R2`, ``ptmin``, ``ptmin2``, ``dcut``.
The clustering parameters' description and default values can be found [here](https://clustering-lhco.readthedocs.io/en/latest/LHCO.html#LHCO.params).

## Jet images

To be written . . .



