# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 11:38:41 2022

@author: Nick.Steele
"""

import pandas as pd

def style_fcst(bfcst, basin_name):
    if not bfcst:
        return pd.DataFrame()

    table_title = "Forecast Exceedance Probabilities for Risk Assessment*"
    symbol = "<----Drier-----Future Conditions-----Wetter---->"

    c_tuples = [
        (table_title, "", "Streamflow Forecasts"),
        (table_title, "", "Forecast Period"),
        (table_title, symbol, "90% (KAF)"),
        (table_title, symbol, "70% (KAF)"),
        (table_title, symbol, "50% (KAF)"),
        (table_title, symbol, "% Median"),
        (table_title, symbol, "30% (KAF)"),
        (table_title, symbol, "10% (KAF)"),
        (table_title, "", "30yr Median (KAF)"),
    ]

    columns = pd.MultiIndex.from_tuples(c_tuples)

    df = pd.DataFrame.from_dict(bfcst[basin_name])
    df = pd.DataFrame(df.to_numpy(), columns=columns)
    f = {
        (table_title, symbol, "90% (KAF)"): "{:.0f}",
        (table_title, symbol, "70% (KAF)"): "{:.0f}",
        (table_title, symbol, "50% (KAF)"): "{:.0f}",
        (table_title, symbol, "30% (KAF)"): "{:.0f}",
        (table_title, symbol, "10% (KAF)"): "{:.0f}",
        (table_title, "", "30yr Median (KAF)"): "{:.0f}",
    }
    s = df.style.format(f)

    headers = [
        {
            "selector": "th:not(.index_name)",
            "props": "background-color: white; color: black;",
        },
        {"selector": "th.col_heading", "props": "text-align: center;"},
        {"selector": "th.col_heading.level0", "props": "font-size: 1.3em;"},
        {
            "selector": "th.col_heading.level1",
            "props": "font-size: 1.1em; white-space: nowrap",
        },
        {"selector": "th.col_heading.level2", "props": "font-size: 1.1em;"},
        {"selector": "td", "props": "font-weight: bold;"},
        {"selector": "th:nth-child(5)", "props": [("background-color", "#D3D3D3")]},
        {"selector": "th:nth-child(6)", "props": [("background-color", "#D3D3D3")]},
        {"selector": "th:nth-child(2)", "props": [("border-right", "2px solid black")]},
        {"selector": "th:nth-child(2)", "props": [("border-left", "2px solid black")]},
        {"selector": "th:nth-child(1)", "props": [("border-right", "2px solid black")]},
        {"selector": "th:nth-child(8)", "props": [("border-right", "2px solid black")]},
    ]

    s.set_properties(
        **{"border": "1.3px solid white", "color": "black", "background-color": "white"}
    )

    idx = pd.IndexSlice
    slice_ = idx[:, idx[:, :, ["50% (KAF)", "% Median"]]]
    # TODO: weird artifact with left border being smaller than right, so have to define all four borders
    s.set_properties(
        subset=slice_,
        **{"border": "0px", "background-color": "#D3D3D3"},  # solid #D3D3D3',
    )

    slice_ = idx[:, idx[:, :, ["90% (KAF)"]]]
    s.set_properties(subset=slice_, **{"border-left": "2px solid black"})

    slice_ = idx[:, idx[:, :, ["30yr Median (KAF)"]]]
    s.set_properties(subset=slice_, **{"border-left": "2px solid black"})

    slice_ = idx[idx[0], idx[:, :, :]]
    s.set_properties(subset=slice_, **{"border-top": "2.5px solid black"})

    slice_ = idx[:, idx[:, :, ["Forecast Period"]]]
    s.set_properties(
        subset=slice_,
        **{
            "border-right": "2px solid black",
            "border-left": "2px solid black",
        },
    )

    slice_ = idx[:, idx[:, :, ["Streamflow Forecasts"]]]
    s.set_properties(subset=slice_, **{"text-align": "right"})

    slice_ = idx[
        :,
        idx[
            :,
            :,
            [
                "Forecast Period",
                "90% (KAF)",
                "70% (KAF)",
                "50% (KAF)",
                "% Median",
                "30% (KAF)",
                "10% (KAF)",
                "30yr Median (KAF)",
            ],
        ],
    ]
    s.set_properties(subset=slice_, **{"text-align": "center"})

    s.set_table_styles(headers)
    s.hide_index()

    return s


def style_res(bres, basin_name):
    if not bres:
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(bres[basin_name])
    df = df.iloc[:-3, :].copy()
    df.rename(
        columns={
            f"{basin_name}": "Reservoir Storage",
            "Current % Median": "% of Median",
            "Capacity (KAF)": "Usable Capacity (KAF)",
        },
        inplace=True,
    )
    df = df[
        [
            "Reservoir Storage",
            "Current (KAF)",
            "Last Year (KAF)",
            "Median (KAF)",
            "% of Median",
            "Usable Capacity (KAF)",
        ]
    ]
    df.replace("", float("NaN"), inplace=True)
    f = {
        "Current (KAF)": "{:.0f}",
        "Last Year (KAF)": "{:.0f}",
        "Median (KAF)": "{:.0f}",
        "Usable Capacity (KAF)": "{:.0f}",
    }
    s = df.style.format(na_rep="", formatter=f)

    headers = [
        {
            "selector": "th:not(.index_name)",
            "props": "background-color: white; color: black;",
        },
        {"selector": "th.col_heading", "props": "text-align: center;"},
        {"selector": "th.col_heading.level0", "props": "font-size: 1.2em;"},
        {
            "selector": "th:nth-child(1)",
            "props": [
                ("background-color", "#D3D3D3"),
                ("border-right", "2px solid black"),
            ],
        },
    ]
    s.set_table_styles(headers)

    s.set_properties(
        **{
            "border": "1.3px solid white",
            "color": "black",
            "background-color": "white",
            "font-weight": "bold",
        }
    )
    idx = pd.IndexSlice
    slice_ = idx[0, :]
    s.set_properties(subset=slice_, **{"border-top": "2px solid black"})

    slice_ = idx[:, "Reservoir Storage"]
    s.set_properties(
        subset=slice_, **{"border-right": "2px solid black", "text-align": "right"}
    )

    slice_ = idx[
        :,
        [
            "Current (KAF)",
            "Last Year (KAF)",
            "Median (KAF)",
            "% of Median",
            "Usable Capacity (KAF)",
        ],
    ]
    s.set_properties(subset=slice_, **{"text-align": "center"})

    s.hide_index()
    return s


def style_snow(bsnow, basin_name):
    if not bsnow:
        return pd.DataFrame()

    c_tuples = [
        ("Basin Snowpack Measurement Sites", ""),
        ("", "Network"),
        ("", "Elevation (ft)"),
        ("", "Snow Depth (in)"),
        ("Snow Water Equivalent (in)", "Current SWE (in)"),
        ("Snow Water Equivalent (in)", "Median (in)"),
        ("Snow Water Equivalent (in)", "Last Yr SWE (in)"),
        ("Snow Water Equivalent (in)", "% of Median"),
        # ('','')
    ]

    columns = pd.MultiIndex.from_tuples(c_tuples)
    df = pd.DataFrame.from_dict(bsnow[basin_name]).iloc[:-3, :].copy()
    df = df[(df["Network"] != "SNOWLITE") & (df["Network"] != "SNOLITE")]
    df.sort_values(by=["Elevation (ft)"], inplace=True, ascending=False)
    df = pd.DataFrame(
        df.loc[
            :,
            [
                f"{basin_name}",
                "Network",
                "Elevation (ft)",
                "Depth (in)",
                "SWE (in)",
                "Median (in)",
                "Last Year SWE (in)",
                "% Median",
            ],
        ].to_numpy(),
        columns=columns,
    )

    df.replace("", float("nan"), inplace=True)

    f = {
        ("", "Elevation (ft)"): "{:.0f}",
        ("", "Snow Depth (in)"): "{:.0f}",
        ("Snow Water Equivalent (in)", "Current SWE (in)"): "{:.1f}",
        ("Snow Water Equivalent (in)", "Median (in)"): "{:.1f}",
        ("Snow Water Equivalent (in)", "Last Yr SWE (in)"): "{:.1f}",
    }

    s = df.style.format(na_rep="", formatter=f)

    headers = [
        {
            "selector": "th:not(.index_name)",
            "props": "background-color: white; color: black",
        },
        {
            "selector": "th.col_heading.level0",
            "props": "font-size: 1.2em; text-align: center",
        },
        {
            "selector": "th.col_heading.level1",
            "props": "font-size: 1.05em; font-weight: bold",
        },
        {
            "selector": "th:nth-child(1)",
            "props": [
                ("background-color", "#D3D3D3"),
                ("border-right", "2px solid black"),
                ("text-align", "center"),
                ("vertical-align", "middle"),
            ],
        },
        {"selector": "th:nth-child(5)", "props": [("border-left", "2px solid black")]},
    ]

    s.set_table_styles(headers)

    s.set_properties(
        **{
            "border": "1.3px solid white",
            "color": "black",
            "font-weight": "bold",
            "background-color": "white",
        }
    )
    idx = pd.IndexSlice
    slice_ = idx[0, :]
    s.set_properties(subset=slice_, **{"border-top": "2px solid black"})

    slice_ = idx[:, [("Basin Snowpack Measurement Sites", "")]]  #
    s.set_properties(
        subset=slice_,
        **{
            "border-right": "2px solid black",
            "text-align": "right",
        },
    )
    slice_ = idx[
        :,
        [
            ("", "Network"),
            ("", "Elevation (ft)"),
            ("", "Snow Depth (in)"),
            ("Snow Water Equivalent (in)", "Current SWE (in)"),
            ("Snow Water Equivalent (in)", "Median (in)"),
            ("Snow Water Equivalent (in)", "Last Yr SWE (in)"),
            ("Snow Water Equivalent (in)", "% of Median"),
        ],
    ]

    s.set_properties(subset=slice_, **{"text-align": "center", "font-weight": "bold"})

    slice_ = idx[
        :,
        [
            ("Snow Water Equivalent (in)", "Current SWE (in)"),
            ("Snow Water Equivalent (in)", "Median (in)"),
            ("Snow Water Equivalent (in)", "Last Yr SWE (in)"),
            ("Snow Water Equivalent (in)", "% of Median"),
        ],
    ]
    s.set_properties(subset=slice_, **{"text-align": "center"})

    s.hide_index()

    return s


def style_snowpack(snowpack):
    if not snowpack:
        return pd.DataFrame()

    snowpack = pd.DataFrame.from_dict(snowpack)
    snowpack.columns = [
        "Snowpack Summary by Basin",
        "# of Sites",
        "% Median",
        "Last Yr % Median",
    ]

    s = snowpack.style
    headers = [
        {
            "selector": "th:not(.index_name)",
            "props": "background-color: white; color: black;",
        },
        {"selector": "th.col_heading", "props": "text-align: center;"},
        {"selector": "th.col_heading.level0", "props": "font-size: 1.2em;"},
        {"selector": "td", "props": "font-weight: bold;"},
        {
            "selector": "th:nth-child(1)",
            "props": [
                ("background-color", "#D3D3D3"),
                ("border-right", "2px solid black"),
            ],
        },
    ]
    s.set_table_styles(headers)

    s.set_properties(
        **{"border": "1.3px solid white", "color": "black", "background-color": "white"}
    )
    idx = pd.IndexSlice
    slice_ = idx[0, :]
    s.set_properties(subset=slice_, **{"border-top": "2px solid black"})

    slice_ = idx[:, "Snowpack Summary by Basin"]
    s.set_properties(
        subset=slice_, **{"border-right": "2px solid black", "text-align": "right"}
    )

    slice_ = idx[:, ["# of Sites", "% Median", "Last Yr % Median"]]
    s.set_properties(subset=slice_, **{"text-align": "center"})

    s.hide_index()

    return s


if __name__ == "__main__":

    print("This module contains formatting and styling for the html tables")
