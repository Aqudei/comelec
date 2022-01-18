import json
from sys import path
from openpyxl.worksheet.worksheet import Worksheet
import requests
import time
import os
import csv
import json
import re
import shutil
import openpyxl
import argparse
import itertools
import pandas as pd
import numpy as np
import requests

PL = [
    'BAYAN MUNA',
    'ACT TEACHERS',
    'GABRIELA',
    'KABATAAN',
    "ANAKPAWIS"
]

BASE_URL = "https://comelec.gov.ph"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
headers = {
    'User-Agent': USER_AGENT,
    "content-type": "application/json"
}

PL_election_id = 5567


def get_current():
    """
    docstring
    """
    with open("./current", 'rt', newline='') as infile:
        return infile.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default='./data')
    options = parser.parse_args()

    for root, dirs, files in os.walk(options.folder):
        for f in files:
            df = pd.read_csv(os.path.join(root, f))


if __name__ == "__main__":
    main()
