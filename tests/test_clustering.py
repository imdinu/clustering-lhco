import unittest

import os
import requests
from pathlib import Path

import h5py
import pandas as pd
import numpy as np

from LHCO import download_file, clustering_mpi, params

DATA_PATH = Path("./tiny_data.h5")
DATA_URL =  "https://github.com/lhcolympics2020/parsingscripts/raw/a4"\
        "64a08fa288d275a97148b5a063cae9aa19cfa7/events_anomalydetection_"\
        "tiny.h5"

class TestDownload(unittest.TestCase):

    def test_links(self):
        try:
            requests.get(DATA_URL, stream=True, timeout=5)
        except ConnectionError:
            self.fail("Test dataset url could not be reached")

    def test_download(self):
        try:
            download_file(DATA_URL, DATA_PATH)
        except Exception:
            self.fail('Exception raised during dataset download')

        self.assertTrue(Path(DATA_PATH).exists())

class TestClustering(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        download_file(DATA_URL, DATA_PATH)
        cls.tmp = Path("./tmp_dir/")
        cls.out_dir = Path(".")
        cls.out_bkg = Path("./results_scalars_bkg.h5")
        cls.out_sig = Path("./results_scalars_sig.h5")
        cls.img_bkg = Path("./results_images_bkg.h5")
        cls.img_sig = Path("./results_images_sig.h5")

    def test_single_core(self):

        default_args = {
            "j": 1,
            "path": DATA_PATH,
            "chunk_size": 150,
            "max_events": 500,
            "tmp_dir": self.tmp,
            "out_dir": self.out_dir,
            "quiet": True
        }
        default_args.update(params)

        try:
            clustering_mpi(**default_args)
        except Exception:
            self.fail("Exceptions raised during clustering")

        self.assertTrue(self.tmp.is_dir())
        self.assertTrue(os.listdir(self.tmp))
        self.assertTrue(self.out_bkg.is_file())
        self.assertTrue(self.out_sig.is_file())


    def test_mpi(self):

        mpi_args = {
            "j": 10,
            "path": DATA_PATH,
            "chunk_size": 0,
            "max_events": 0,
            "tmp_dir": self.tmp,
            "quiet": True,
            "out_dir": self.out_dir
        }
        mpi_args.update(params)
        mpi_args['njets'] = 4
        mpi_args['R'] = 0.3
        try:
            clustering_mpi(**mpi_args)
        except Exception:
            self.fail("Exceptions raised during clustering")

        self.assertTrue(self.tmp.is_dir())
        self.assertTrue(os.listdir(self.tmp))
        self.assertTrue(self.out_bkg.is_file())
        self.assertTrue(self.out_sig.is_file())

    def test_imgs(self):

        mpi_args = {
            "j": 10,
            "path": DATA_PATH,
            "chunk_size": 0,
            "max_events": 0,
            "scalars": False,
            "images": True,
            "img_config": "./img_config.json",
            "tmp_dir": self.tmp,
            "quiet": True,
            "out_dir": self.out_dir
        }
        mpi_args.update(params)
        mpi_args['njets'] = 2
        mpi_args['R'] = 1
        try:
            clustering_mpi(**mpi_args)
        except Exception:
            self.fail("Exceptions raised during clustering")

        self.assertTrue(self.tmp.is_dir())
        self.assertTrue(os.listdir(self.tmp))
        self.assertTrue(self.img_bkg.is_file())
        self.assertTrue(self.img_sig.is_file())


class TestScalars(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result_files = [Path("results_scalars_bkg.h5"), 
                       Path("results_scalars_sig.h5")]


    def test_file_integrity(self):
        for f in self.result_files:
            try:
                pd.read_hdf(f)
            except Exception:
                self.fail("scalar results could not be read")

    def test_data_format(self):
        sig_col = set(pd.read_hdf(self.result_files[1]).columns)
        bkg_col = set(pd.read_hdf(self.result_files[0]).columns)

        with open('./tests/columns.txt', "r") as f:
            col = f.read()
        true_col = set(col.split(","))

        self.assertTrue(sig_col == bkg_col == true_col)

    def test_data_size(self):
        sig = pd.read_hdf(self.result_files[1])
        bkg = pd.read_hdf(self.result_files[0])

        self.assertEqual(sig.shape[0], 44)
        self.assertEqual(bkg.shape[0], 456)

class TestImages(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result_files = [Path("results_images_bkg.h5"), 
                       Path("results_images_sig.h5")]


    def test_file_integrity(self):
        for f in self.result_files:
            try:
               self._read_img(f)
            except Exception:
                self.fail("Images could not be read")

    def test_data_format(self):
        self.sig = self._read_img(self.result_files[1])
        self.bkg = self._read_img(self.result_files[0])

        self.assertTrue(self.sig.shape == (82, 32, 32, 2))
        self.assertTrue(self.bkg.shape == (818, 32, 32, 2))

    def _read_img(self, path):
        hf = h5py.File(path, 'r')
        key = list(hf.keys())[0]
        return np.array(hf[key][:])




