import unittest

import os
import requests
import shutil
from pathlib import Path

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
    
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.tmp)
        os.remove(DATA_PATH)

    def test_single_core(self):

        default_args = {
            "j": 1,
            "path": DATA_PATH,
            "chunk_size": 200,
            "max_events": 500,
            "tmp_dir": self.tmp,
            "out_dir": self.out_dir
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
            "j": 0,
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

class TestResults(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result_files = [Path("results_scalars_bkg.h5"), 
                       Path("results_scalars_sig.h5")]

    @classmethod
    def tearDownClass(self):
        for f in self.result_files:
            os.remove(f)

    def test_file_integrity(self):
        for f in self.result_files:
            try:
                pd.read_hdf(f)
            except Exception:
                self.fail("Exceptions raised during clustering")

    def test_data_format(self):
        sig_col = set(pd.read_hdf(self.result_files[1]).columns)
        bkg_col = set(pd.read_hdf(self.result_files[0]).columns)

        with open('./tests/columns.txt', "r") as f:
            col = f.read()
        true_col = set(col.split(","))

        self.assertTrue(sig_col == bkg_col == true_col)

    def test_data_content(self):
        sig = pd.read_hdf(self.result_files[1])
        bkg = pd.read_hdf(self.result_files[0])

        self.assertEqual(sig.shape[0], 35)
        self.assertEqual(bkg.shape[0], 365)

        sig_ref = pd.read_hdf("./tests/sig_desc.h5")
        bkg_ref = pd.read_hdf("./tests/bkg_desc.h5")

        self.assertTrue(np.all(sig.describe() == sig_ref))
        self.assertTrue(np.all(bkg.describe() == bkg_ref))




