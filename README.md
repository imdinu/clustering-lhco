# About

This package aims at streamlining the LHC Olympics data preprocessing steps. It automates data downloading, clustering (with `pyjet`) and signal/background events segregation. The `multiprocessing` module is used for parallelizing event processing.

Full documentation is available at [this readthedocs.io page](https://clustering-lhco.readthedocs.io/en/latest/).

**Coming Soon 🔜**
- Automatic Handling of `nan` and `inf` values
- Masterkey Integration in data clustering for Black Boxes
- Jet image outputs

## Quick Start
The bulk of this package's functionalities can be accessed through the `LHCO.py` script. Available commands for this script: `cluster` and `download`

The example below shows how to download and cluster the LHC Olympics *RnD* dataset using the default clustering parameters. 

    [clustering-lhco]$ mkdir data
    [clustering-lhco]$ ./LHCO.py cluster -D RnD ./data/

The downloaded fille will always be named `LHCO_{dataset_identifier}.h5` if the `path` argument is a directory, in this case it will be `LHCO_RnD.h5`. If you want to customize the dataset name you can specify a file path in the command:
>./LHCO.py cluster -D RnD ./data/mydata.h5

Resulting files from the clustering will be named `RnD_scalars_bkg.h5` and `RnD_scalars_sig.h5` containing the clustered background and signal events. The prefix of the file names can be customized with the option `--out-prefix` otherwise it defaults to `{dataset_identifier}` if the download and clustering are done through a single command. On the other hand the results default location is the same directory where the data is found; you can use the option `--out-dir` to specify a different directory.

Those download and cluster steps can be also accomplished individually. In this example the downloaded data and results will be stored in different directories.

    [clustering-lhco]$ mkdir data results
    [clustering-lhco]$ ./LHCO.py download RnD ./data/myRnD.hdf
    [clustering-lhco]$ ./LHCO.py cluster ./data/myRnD.hdf --out-dir ./results/ --out-prefix mydata



## Additional Options

Documentation on the available clustering options can be displayed using `--help` flag:
> ./LHCO.py cluster --help

If you want to implement the clustering into your own pipeline check the Technical Documentation on [readthedocs.io](https://clustering-lhco.readthedocs.io/en/latest/LHCO.html) for detailed information about the contents and implementation of this package