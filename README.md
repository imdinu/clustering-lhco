# About

This package aims at streamlining the LHC Olympics data preprocessing steps. It automates data downloading, clustering (with `pyjet`) and signal/background events segregation. The `multiprocessing` module is used for parallelizing event processing.

Full documentation is available at [this readthedocs.io page](https://clustering-lhco.readthedocs.io/en/latest/).

## Latest Update:
- Added a new scalar feature **nc** (number of constituents)
- Jet image generation
- Fixed chunk bug related to chunk size rounding errors. Now no events are ignored, even if the chunk size is not among the divisors of the number of events.
- Test coverage for image generation

**Known Issues:**
- Occasional exceptions `FloatingPointError('Image had no particles!')` thrown on the RnD dataset when attempting to generate images. Investigations are in progress.

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

    [clustering-lhco]$ ./LHCO.py cluster -D RnD ./data/mydata.h5

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

    [clustering-lhco]$ ./LHCO.py cluster --help

or 

    [clustering-lhco]$ ./LHCO.py download --help

If you want to implement the clustering into your own pipeline check the Technical Documentation on [readthedocs.io](https://clustering-lhco.readthedocs.io/en/latest/LHCO.html) for detailed information about the contents and implementation of this package.

## Workload distribution

The main parameters you can control relative to workload distribution are: the number of logical cores used ``-j``, the number of events per job ``--chunk-size`` and the number of events read from the input file``--max-events``.

The following lines provide an example of a clustering run on the RnD dataset where all events are split among 5 cores with every job using 10.000 events:

    [clustering-lhco]$ mkdir data results
    [clustering-lhco]$ ./LHCO.py download RnD ./data/
    [clustering-lhco]$ ./LHCO.py cluster ./data/LHCO_RnD.h5 --out-dir ./results/ --out-prefix RnD -j 5 --chunk-size 10000

By default the maximum number of logical cores is used for the value of ``-j``. Do not set the value of ``-j`` unless you specifically want to reduce the load on your machine. The ``--chunk-size`` option only impacts the number of temporary files created, so feel free to use whatever value you seem fit.

## Clustering parameters

All parameters associated with the clustering process can be specified directly through command line options. Among those options you can choose: ``-R``, ``--njets``, ``--cluster_algo``, `-R2`, ``--ptmin``, ``--ptmin2``, ``--dcut``.
The clustering parameters' description and default values can be found [here](https://clustering-lhco.readthedocs.io/en/latest/LHCO.html#LHCO.params).

# Jet images

This package also offers the option to represent the clustered data as jet images. In order to use this, just add the flag `--images=True` to any clustering job. New output filles will be created, with names such as `RnD_images_bkg.h5` alongside the usual `RnD_scalars_bkg.h5`. The example below shows a one-liner that downloads the RnD dataset, performs clustering and generates both scalar features and jet images:

    [clustering-lhco]$ mkdir test_images
    [clustering-lhco]$ ./LHCO.py cluster -D RnD --images=True ./test_images/

If you are not interested in computing the scalar features and want to save up some execution time, the scalar computation can be disabled with `--scalars=False`

Image generation can be customized through a json file. The default parameters are accessible through [img_config.json](img_config.json). The meaning of those options is the following:
- `stitch_jets`: option to place multiple jets on the same image. If enabled, every event will be represented as a single jet image, in this case, it is recommended to use higher values for the covered width in the ($\eta$,$\phi$)-plane $\Rightarrow$ `img_width` $\ge 3$. When this option is disabled, every jet will be represented a different *channel* of the image. In this case, smaller image widths could be used in order to capture finer jet substructure details. The resulting dataset will have the shape `(n_events, npix, npix, njets)` when `stitch_jets=false` and `(n_events, npix, npix, 1)` if `stitch_jets=true`
- `npix`: width (and height) of the jet image, in pixels. At the moment only square images are supported
- `img_width`: the width (and height) covered by the image in the ($\eta$,$\phi$)-plane, in units of $\Delta R$. The smaller the width, the more *zoomed-in* the jet image appears
- `rotate`: option to rotate the image, such that the two leading secondary clusters are aligned on the vertical axis. The next-to-leading cluster will **always** be placed under the leading cluster,on the vertical axis. 
- `offset`: position of the jet primary cluster relative to the bottom axis of the image. A value of `0.5` will place the primary cluster in the center of the image, while a value of `0.66` will pace it two thirds of the image width away from the bottom axis. It is recommended to use values between (0.5, 1) if the `rotate` option is set to `true`, and `offset=0.5` otherwise.
- `norm`: option to normalize the resulting jet image, if `false`, the values of the pixels will represent the $p_T$ bins in $GeV$.

Besides editing the default configuration file, you may also want to create your own configurations. The path to a custom configuration file can be passed to the clustering code through the flag `--img-config`.