import unittest

import os
import requests
import shutil
from pathlib import Path

from cluster import download_file, clustering_mpi

test_file = "https://github.com/lhcolympics2020/parsingscripts/raw/a464a08fa2"\
     "88d275a97148b5a063cae9aa19cfa7/events_anomalydetection_tiny.h5"

class TestDownload(unittest.TestCase):

    def test_links(self):
        try:
            requests.get(test_file, stream=True, timeout=5)
        except ConnectionError:
            self.fail(f"Test dataset url could not be reached")

    def test_download(self):
        try:
            download_file(test_file, "tiny_data.h5")
        except Exception:
            self.fail('Exception raised during dataset download')