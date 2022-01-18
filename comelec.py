from heapq import merge
import json
from sys import path
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
import requests
import pandas as pd
import numpy as np

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
    if not os.path.exists("./current"):
        return

    with open("./current", 'rt', newline='') as infile:
        return infile.read()


def fetch(options):
    """
    docstring
    """
    found = False

    pls = {}
    with open('5567.json', 'rt') as infile:
        j = json.loads(infile.read())
        pls = {p['boc']: p['bon'] for p in j['bos']}

    response = requests.get(
        f"{BASE_URL}/2019NLEResults/data/regions/0/8.json", headers=headers)
    provinces = response.json()["srs"]

    for province_key in provinces.keys():
        response = requests.get(
            f"{BASE_URL}/2019NLEResults/data/regions/{provinces[province_key]['url']}.json")
        cities = response.json()['srs']
        for city_key in cities.keys():
            response = requests.get(
                f"{BASE_URL}/2019NLEResults/data/regions/{cities[city_key]['url']}.json")
            barangays = response.json()['srs']
            for brgy_key in barangays:
                province_name = provinces[province_key]['rn']
                city_name = cities[city_key]['rn']
                brgy_name = barangays[brgy_key]['rn']

                filename = os.path.join(
                    options.folder, f"{province_name}-{city_name}-{brgy_name}.csv")

                current = get_current()
                if current:
                    if not found:
                        head, tail = os.path.split(filename)
                        if not current in tail:
                            continue

                found = True

                with open(filename, 'wt', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(('Province', 'City/Mun', 'Brgy', 'Precint',
                                    'RegisteredVoters', 'ActualVoters', 'ValidVotes', 'Partylist', 'Votes'))
                    response = requests.get(
                        f"{BASE_URL}/2019NLEResults/data/regions/{barangays[brgy_key]['url']}.json")
                    precints = response.json()['pps']

                    for precint in precints:
                        response = requests.get(
                            f"{BASE_URL}/2019NLEResults/data/results/{precint['vbs'][0]['url']}.json")
                        if response.status_code == 404:
                            continue

                        common = {c['cn']: c['ct']
                                  for c in response.json()['cos']}

                        # pl_votes = [{**v, "bon": pls[v['bo']], "reg":common['expected-voters'],
                        #              "act":common['number-of-voters-who-actually-voted'], "valid":common['valid-votes']} for
                        #             v in response.json()['rs'] if v['cc'] == PL_election_id]
                        pl_votes = [v for v in response.json()['rs'] if
                                    v['cc'] == PL_election_id]
                        for vote_info in pl_votes:
                            row = (province_name, city_name, brgy_name, precint['ppcc'], common['expected-voters'],
                                   common['number-of-voters-who-actually-voted'], common['valid-votes'], pls[vote_info['bo']], vote_info['v'])

                            print(row)
                            writer.writerow(row)


def get_no(plname):
    """
    docstring
    """
    return plname[:plname.index(" ")]


def merge_csvs(options):
    """
    docstring
    """
    dfmaster = pd.DataFrame()

    for root, dir, files in os.walk(options.folder):
        for f in files:
            if not f.lower().endswith(".csv"):
                continue
            print("Processing %s..." % (f,))
            fn = os.path.join(root, f)
            df = pd.read_csv(fn, encoding='latin-1')
            if df.empty:
                continue

            df = df.drop(columns=['Precint'])
            grouped = df.groupby(
                ["Province", "City/Mun", "Brgy", "Partylist"], as_index=False).sum()
            grouped['IOverE'] = grouped['Votes'] / grouped['ValidVotes']
            grouped['Percentage'] = grouped['IOverE'] * 100

            conditions = [
                (grouped['Percentage']) >= (19.5),
                (grouped['Percentage'] >= 14.5) & (
                    grouped['Percentage'] < 19.5),
                (grouped['Percentage'] >= 9.5) & (
                    grouped['Percentage'] < 14.5),
                (grouped['Percentage'] >= 4.5) & (grouped['Percentage'] < 9.5),
                (grouped['Percentage'] >= 1) & (grouped['Percentage'] < 4.5),
                (grouped['Percentage'] < 1),
            ]
            values = ['A', 'B', 'C', 'D', 'E', 'CLEARED']
            grouped['Level'] = np.select(conditions, values)
            grouped['No'] = grouped['Partylist'].apply(get_no)
            dfmaster = dfmaster.append(grouped)
            #fn, _ = os.path.splitext(fn)
            # grouped.to_excel(fn+".xlsx")

    print("Writing to master excel file...")
    master_file = os.path.join(options.folder, "master-output.xlsx")
    if os.path.isfile(master_file):
        os.remove(master_file)

    dfmaster.to_excel(master_file)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default='./data')
    parser.add_argument("--merge", action='store_true')
    parser.add_argument("--fetch", action='store_true')

    options = parser.parse_args()

    if not os.path.exists(options.folder):
        os.makedirs(options.folder)

    if options.fetch:
        fetch(options)

    if options.merge:
        merge_csvs(options)


if __name__ == "__main__":
    main()
