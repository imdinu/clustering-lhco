import unittest

import os
import requests
import shutil
from pathlib import Path

from cluster import download_file, clustering_mpi, params

DATA_PATH = Path("tiny_data.h5")
DATA_URL =  "https://github.com/lhcolympics2020/parsingscripts/raw/a4"\
        "64a08fa288d275a97148b5a063cae9aa19cfa7/events_anomalydetection_"\
        "tiny.h5"

class TestDownload(unittest.TestCase):

    def test_links(self):
        try:
            requests.get(DATA_URL, stream=True, timeout=5)
        except ConnectionError:
            self.fail(f"Test dataset url could not be reached")

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
        cls.out_bkg = Path("./scalars_bkg.h5")
        cls.out_sig = Path("./scalars_sig.h5")
    
    def tearDown(self):
        os.remove("./scalars_bkg.h5")
        os.remove("./scalars_sig.h5")

    def test_single_core(self):

        default_args = {
            "j": 1,
            "path": DATA_PATH,
            "chunk_size": 200,
            "max_events": 500,
            "tmp_dir": self.tmp
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
            "quiet": True
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
