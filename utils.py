# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 11:38:41 2022

@author: Nick.Steele
"""

from functools import reduce
from datetime import timedelta
from os import getenv, path, makedirs

import numpy as np
import pandas as pd
from requests_cache import CachedSession

API_DOMAIN = getenv("API_SERVER", "https://api.snowdata.info")
THIS_DIR = path.dirname(path.realpath(__file__))
DB_DIR = path.join(THIS_DIR, "dbs")
makedirs(DB_DIR, exist_ok=True)
CACHE_PATH = getenv("CACHE_PATH", path.join(DB_DIR, "cache.db"))
CACHE_REFRESH = timedelta(hours=24)
CACHE_ARGS = {
    "cache_name": CACHE_PATH,
    "backend": "sqlite",
    "expire_after": CACHE_REFRESH,
}


def safe_percent(row, top_col, bottom_col):
    top = row[top_col]
    bottom = row[bottom_col]
    if bottom == 0 or not all([top, bottom]):
        return "-"
    percent = f"{round(100 * top / bottom, 0):.0f}%"
    if "nan" in percent.lower():
        return "-"
    return percent


def get_wsor_data(
    endpoint,
    state,
    year,
    month,
    basin_type,
    domain=API_DOMAIN,
    cache_args=CACHE_ARGS,
    force_refresh=False,
):

    endpoint = f"/wsor/{endpoint}"
    args = f"?state={state}&pubMonth={month}&pubYear={year}&basinType={basin_type}"
    url = f"{domain}{endpoint}{args}"
    print(url)
    if force_refresh:
        cache_args["expire_after"] = 0
    with CachedSession(**cache_args) as sesh:
        req = sesh.get(url)
        if req.ok:
            wsor_json = req.json()
        else:
            print("An error occurred while attempting to retrieve data from the API.")
            wsor_json = {}

    return wsor_json


def get_hierarchy(state, domain=API_DOMAIN, cache_args=CACHE_ARGS, force_refresh=False):

    endpoint = "/basin/getParents"
    args = f"?state={state}&format=json"
    url = f"{domain}{endpoint}{args}"
    print(url)
    if force_refresh:
        cache_args["expire_after"] = 0
    with CachedSession(**cache_args) as sesh:
        req = sesh.get(url)
        if req.ok:
            basin_hierarchy_json = req.json()
        else:
            print("An error occurred while attempting to retrieve data from the API.")
            basin_hierarchy_json = {}

    return basin_hierarchy_json


def add_fcst_footer(fcst_html):
    table_title = "Streamflow Forecasts (kaf)"
    find_str = """<tr style="text-align: match-parent;">
      <th></th>
      <th></th>"""
    replace_str = f"""<tr style="text-align: match-parent;">
      <th>{table_title}</th>
      <th></th>"""
    fcst_html = fcst_html.replace(find_str, replace_str)
    fcst_caption = """
    <caption>
    *90%, 70%, 50%, 30%, 10% exceedence probabilities are the chance that observed streamflow volume will exceed the forecasted volume<br>
    1) 90% And 10% exceedance probabilities are actually 95% And 5%<br>
    2) Forecasts are for unimpaired flows. Actual flow will be dependent on management of upstream reservoirs and diversions.
    </caption>
    """
    return fcst_html.replace("</table>", f"{fcst_caption}</table>")


def forecasts(basin, wsor_json):
    def add_footnotes():
        # TODO: add footnotes, somehow...
        return

    def modify_exceedances(name, forecasts):
        for period, value_dict in forecasts.items():
            if "5" in value_dict.keys():
                forecasts[period]["10"] = value_dict["5"]
                forecasts[period]["90"] = value_dict["95"]
                del forecasts[period]["5"]
                del forecasts[period]["95"]
        return (name, forecasts)

    basin_data = wsor_json[basin]
    site_meta = basin_data["site_meta"]
    if not site_meta:
        return pd.DataFrame()
    names = {i: site_meta[i]["name"] for i in site_meta.keys()}
    medians = {
        i: wsor_json[basin]["fcst_med"][i] for i in wsor_json[basin]["fcst_med"].keys()
    }
    forecasts = {
        i: wsor_json[basin]["fcst_curr"][i]
        for i in wsor_json[basin]["fcst_curr"].keys()
    }
    for trip, forecast in forecasts.items():
        for period in forecast.keys():
            forecasts[trip][period]["30 yr. Median"] = medians[trip].get(period, np.nan)
            forecasts[trip][period]["% Median"] = safe_percent(
                forecasts[trip][period], "50", "30 yr. Median"
            )
    forecasts = dict(
        modify_exceedances(names[key], value) for (key, value) in forecasts.items()
    )
    reformat_forecasts = {
        (outerKey, innerKey): values
        for outerKey, innerDict in forecasts.items()
        for innerKey, values in innerDict.items()
    }
    forecasts = pd.DataFrame(reformat_forecasts).T
    rename_cols = {i: f"{i}%" for i in forecasts.columns if str(i).isnumeric()}
    forecasts = forecasts.rename(columns=rename_cols)
    col_sort = [
        i[1] for i in sorted(rename_cols.items(), key=lambda kv: (kv[1], kv[0]))
    ]
    col_sort = col_sort + ["30 yr. Median"]
    col_sort.insert(3, "% Median")
    forecasts = forecasts.fillna(value=np.nan)
    if forecasts.empty:
        return pd.DataFrame()
    return forecasts[col_sort].round(1)


def add_prec_footer(basin_index, prec_html):
    if not basin_index:
        return prec_html
    footer = f"""
       <tfoot>
         <tr class="table-secondary">
           <td style="text-align:center; font-weight: bold;">Basin Index</td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td style="font-weight: bold;">{basin_index['prec_mnth_curr_per_med']}%</td>
           <td style="font-weight: bold;">{basin_index['prec_mnth_ly_per_med']}%</td>
           <td style="font-weight: bold;">{basin_index['prec_ytd_curr_per_med']}%</td>
           <td style="font-weight: bold;">{basin_index['prec_ytd_ly_per_med']}%</td>
       </tfoot>
      </table>
      """.replace(
        "None%", "-"
    )

    return prec_html.replace("</table>", footer)


def precipitation(basin, wsor_json):
    table_title = "Precipitation (in.)"
    basin_data = wsor_json[basin]
    site_meta = basin_data["site_meta"]
    if not site_meta:
        return pd.DataFrame()
    elevations = {i: f"{site_meta[i]['elevation']:.0f}'" for i in site_meta.keys()}
    elevations = pd.DataFrame(elevations, index=["elevation"]).T
    names = {
        i: f'{site_meta[i]["name"]} ({site_meta[i]["stationTriplet"].split(":")[-1]})'
        for i in site_meta.keys()
    }
    names = pd.DataFrame(names, index=[table_title]).T
    prec = pd.DataFrame(
        {
            key: wsor_json[basin][key]
            for key in [
                "prec_mnth_curr",
                "prec_mnth_ly",
                "prec_mnth_med",
                "prec_ytd_curr",
                "prec_ytd_ly",
                "prec_ytd_med",
            ]
        }
    )
    prec = reduce(
        lambda left, right: pd.merge(
            left, right, left_index=True, right_index=True, how="outer"
        ),
        [i for i in [names, elevations, prec]],
    )
    prec.set_index(table_title, inplace=True)
    prec.reset_index(inplace=True)
    prec.dropna(
        inplace=True,
        how="all",
        subset=[
            "prec_mnth_curr",
            "prec_mnth_med",
            "prec_mnth_ly",
            "prec_ytd_curr",
            "prec_ytd_med",
            "prec_ytd_ly",
        ],
    )
    if prec.empty:
        return pd.DataFrame()
    prec["Monthly % Median"] = prec.apply(
        lambda c: safe_percent(c, "prec_mnth_curr", "prec_mnth_med"),
        axis=1,
    )
    prec["LY Monthly % Median"] = prec.apply(
        lambda c: safe_percent(c, "prec_mnth_ly", "prec_mnth_med"),
        axis=1,
    )
    prec["YTD % Median"] = prec.apply(
        lambda c: safe_percent(c, "prec_ytd_curr", "prec_ytd_med"),
        axis=1,
    )
    prec["LY YTD % Median"] = prec.apply(
        lambda c: safe_percent(c, "prec_ytd_ly", "prec_ytd_med"),
        axis=1,
    )
    prec = prec.rename(
        columns={
            "elevation": "Elevation",
            "prec_mnth_curr": "Current Monthly ",
            "prec_mnth_ly": "Last Year Monthly",
            "prec_mnth_med": "Monthly Median",
            "prec_ytd_curr": "Current YTD",
            "prec_ytd_ly": "Last Year YTD",
            "prec_ytd_med": "YTD Median",
        }
    )
    prec = prec.fillna(value=np.nan)
    return prec


def add_snow_footer(basin_index, snow_html):
    if not basin_index:
        return snow_html
    footer = f"""
       <tfoot>
         <tr class="table-secondary">
           <td style="text-align:center; font-weight: bold;">Basin Index</td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td></td>
           <td style="font-weight: bold;">{basin_index['wteq_curr_per_med']}%</td>
           <td style="font-weight: bold;">{basin_index['wteq_ly_per_med']}%</td>
       </tfoot>
      </table>
      """.replace(
        "None%", "-"
    )

    return snow_html.replace("</table>", footer)


def snowpack_sites(basin, wsor_json):
    table_title = "Snowpack (in.)"
    basin_data = wsor_json[basin]
    site_meta = basin_data["site_meta"]
    if not site_meta:
        return pd.DataFrame()
    elevations = {i: f"{site_meta[i]['elevation']:.0f}'" for i in site_meta.keys()}
    elevations = pd.DataFrame(elevations, index=["elevation"]).T
    names = {
        i: f'{site_meta[i]["name"]} ({site_meta[i]["stationTriplet"].split(":")[-1]})'
        for i in site_meta.keys()
    }
    names = pd.DataFrame(names, index=[table_title]).T
    snow = {
        key: wsor_json[basin][key]
        for key in ["wteq_curr", "snwd_curr", "wteq_ly", "wteq_med"]
    }
    snow = pd.DataFrame(snow)
    snow = reduce(
        lambda left, right: pd.merge(
            left, right, left_index=True, right_index=True, how="outer"
        ),
        [i for i in [names, elevations, snow]],
    )
    snow.set_index(table_title, inplace=True)
    snow.dropna(inplace=True, how="all", subset=["wteq_curr", "snwd_curr", "wteq_ly"])
    if snow.empty:
        return pd.DataFrame()
    snow["% Median"] = snow.apply(
        lambda c: safe_percent(c, "wteq_curr", "wteq_med"),
        axis=1,
    )
    snow["LY % Median"] = snow.apply(
        lambda c: safe_percent(c, "wteq_ly", "wteq_med"),
        axis=1,
    )
    snow = snow.rename(
        columns={
            "elevation": "Elevation",
            "wteq_curr": "Current SWE",
            "snwd_curr": "Current SD",
            "wteq_ly": "Last Year SWE",
            "wteq_med": "Median SWE",
        }
    )
    snow.reset_index(inplace=True)
    snow = snow.fillna(value=np.nan)
    return snow


def add_res_footer(basin_index, res_html):
    if not basin_index:
        return res_html
    footer = f"""
     <tfoot>
       <tr class="table-secondary">
         <td style="text-align:center; font-weight: bold;">Basin Index</td>
         <td></td>
         <td></td>
         <td></td>
         <td></td>
         <td style="font-weight: bold;">{basin_index['res_curr_per_cap']}%</td>
         <td style="font-weight: bold;">{basin_index['res_ly_per_cap']}%</td>
         <td style="font-weight: bold;">{basin_index['res_med_per_cap']}%</td>
         <td style="font-weight: bold;">{basin_index['res_curr_per_med']}%</td>
         <td style="font-weight: bold;">{basin_index['res_ly_per_med']}%</td>
     </tfoot>
    </table>
    """.replace(
        "None%", "-"
    )

    return res_html.replace("</table>", footer)


def reservoirs(basin, wsor_json):
    table_title = "Reservoir Storage (kaf)"
    basin_data = wsor_json[basin]
    site_meta = basin_data["site_meta"]
    if not site_meta:
        return pd.DataFrame()
    names = {i: site_meta[i]["name"] for i in site_meta.keys()}
    names = pd.DataFrame(names, index=[table_title]).T
    res = {
        key: wsor_json[basin][key]
        for key in ["res_curr", "res_ly", "res_med", "res_cap"]
    }
    res = pd.DataFrame(res)
    res = reduce(
        lambda left, right: pd.merge(
            left, right, left_index=True, right_index=True, how="outer"
        ),
        [i for i in [names, res]],
    )
    res.set_index(table_title, inplace=True)
    res.dropna(inplace=True, how="all", subset=["res_curr", "res_ly"])
    res = res.round(1)
    if res.empty:
        return pd.DataFrame()
    res["% Capacity"] = res.apply(
        lambda c: safe_percent(c, "res_curr", "res_cap"),
        axis=1,
    )
    res["LY % Capacity"] = res.apply(
        lambda c: safe_percent(c, "res_ly", "res_cap"),
        axis=1,
    )
    res["Median % Capacity"] = res.apply(
        lambda c: safe_percent(c, "res_med", "res_cap"),
        axis=1,
    )
    res["% Median"] = res.apply(
        lambda c: safe_percent(c, "res_curr", "res_med"),
        axis=1,
    )
    res["LY % Median"] = res.apply(
        lambda c: safe_percent(c, "res_ly", "res_med"),
        axis=1,
    )
    res = res.rename(
        columns={
            "res_curr": "Current",
            "res_ly": "Last Year",
            "res_med": "Median",
            "res_cap": "Capacity",
        }
    )
    res.reset_index(inplace=True)
    res = res.fillna(value=np.nan)
    return res


if __name__ == "__main__":
    print("no tests written")
