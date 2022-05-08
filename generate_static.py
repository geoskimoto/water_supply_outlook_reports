# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 07:44:45 2022

@author: Beau.Uriona
"""

import re
from os import path, makedirs
from requests import Session
from requests import get as r_get

from app import BASIN_STATES, BASIN_TYPES
from utils import get_hierarchy, API_DOMAIN

STATIC_URL = "https://www.wcc.nrcs.usda.gov/ftpref/assets/"
WSOR_DOMAIN = "http://nrcscix0147.edc.ds1.usda.gov:8090"

THIS_DIR = path.dirname(path.realpath(__file__))
EXPORT_DIR = path.join(THIS_DIR, "export")
makedirs(EXPORT_DIR, exist_ok=True)


def get_basins(btype, sesh=None, domain=API_DOMAIN):
    endpoint = "/basin/getBasins"
    args = f"?type={btype}&format=json&orient=records"
    url = f"{domain}{endpoint}{args}"
    print(url)
    if sesh:
        req = sesh.get(url)
    else:
        req = r_get(url)
    if req.ok:
        return req.json()
    else:
        print("An error occurred while attempting to retrieve data from the API.")
        return []


def make_refs_relative(html_str, home_link="#", static_url=STATIC_URL):
    html_str = html_str.replace("/static/", static_url)
    html_str = html_str.replace('href="/"', 'href="{home_link}"')
    html_str = html_str.replace("<a href='/", "<a href='./")
    re_paths = re.findall(r"<a href='./(.*?)'>", html_str)
    for re_path in re_paths:
        html_str = html_str.replace(re_path, f"{re_path}.html")
    return html_str


if __name__ == "__main__":

    import sys
    import argparse
    from datetime import datetime

    now = datetime.now()

    cli_desc = """
    Create static versions of the WSOR pages created by the wsor app
    """
    parser = argparse.ArgumentParser(description=cli_desc)
    parser.add_argument(
        "-V", "--version", help="show program version", action="store_true"
    )
    parser.add_argument("-e", "--export", help="export path", default=EXPORT_DIR)
    parser.add_argument(
        "-m",
        "--month",
        help="publication month",
        default=now.month,
        type=int,
    )
    parser.add_argument(
        "-y",
        "--year",
        help="publication year",
        default=now.year,
        type=int,
    )
    args = parser.parse_args()

    if args.version:
        print("generate_static v0.1")
        sys.exit(0)

    if not path.isdir(args.export):
        print(f"Invalid export path - {args.export} - try again...")
        sys.exit(1)

    pub_month = args.month
    pub_year = args.year

    print(f"\nWorking on {pub_month}/{pub_year}...\n")
    pub_month_dir = path.join(EXPORT_DIR, f"{pub_year}_{pub_month}")
    makedirs(pub_month_dir, exist_ok=True)
    for state in BASIN_STATES:
        with Session() as sesh:
            print(f"Working on {state}...")
            state_dir = path.join(pub_month_dir, state.lower())
            makedirs(state_dir, exist_ok=True)
            print("  Getting hierarchy...")
            hierarchy = get_hierarchy(state=state)
            if not hierarchy:
                majors = [i["name"] for i in get_basins(btype=f"{state.lower()}_8")]
                minors = []
            else:
                majors = list(hierarchy.keys())
                minors = []
                for major in majors:
                    minors.extend(hierarchy[major])
            miscs = [i["name"] for i in get_basins(btype=f"{state.lower()}3")]
            bname_dict = dict(major=majors, minor=minors, misc=miscs)
            for basin_type in BASIN_TYPES:
                print(f"  Generating basin data for {basin_type} basins...")
                btype_dir = path.join(state_dir, basin_type.lower())
                makedirs(btype_dir, exist_ok=True)
                bnames = bname_dict.get(basin_type, None)
                if not bnames:
                    continue
                url = f"{WSOR_DOMAIN}?automate=true"
                data = dict(
                    state=state,
                    month=pub_month,
                    year=pub_year,
                    btype=basin_type,
                    refresh=True,
                )
                post_req = sesh.post(url=url, data=data)
                if not post_req.ok:
                    print("    Failed to produce WSOR data... - {post_req.status_code}")
                    continue
                basins_req = sesh.get(f"{WSOR_DOMAIN}/basins")
                if not basins_req.ok:
                    print("    Could not create index page - {basins_req.status_code}")
                index_html = make_refs_relative(basins_req.text, home_link="#")
                index_export_path = path.join(btype_dir, "index.html")
                with open(index_export_path, "w") as html:
                    html.write(index_html)
                for bname in bnames:
                    print(f"    Getting WSOR for {bname}...")
                    basin_filename = f"{bname.lower()}.html"
                    html_export_path = path.join(btype_dir, basin_filename)
                    wsor_req = sesh.get(f"{WSOR_DOMAIN}/{bname.lower()}")
                    if not wsor_req.ok:
                        print(f"      Failed to get WSOR - {wsor_req.status_code}")
                        continue
                    html_str = make_refs_relative(wsor_req.text, home_link="../")
                    with open(html_export_path, "w") as html:
                        html.write(html_str)
                    print("      Success!!")
