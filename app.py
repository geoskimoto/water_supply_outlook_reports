# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 11:38:41 2022

@author: Nick.Steele & beau.uriona
"""

from pytz import timezone
from datetime import datetime as dt
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, BooleanField
from utils import (
    get_wsor_data,
    get_hierarchy,
    forecasts,
    precipitation,
    snowpack_sites,
    reservoirs,
    add_fcst_footer,
    add_snow_footer,
    add_prec_footer,
    add_res_footer,
)


app = Flask(
    __name__,
)

app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "filesystem"
# app.config["SESSION_PERMANENT"] = False
Session(app)

BASIN_STATES = ("AK", "AZ", "CA", "CO", "ID", "MT", "NM", "NV", "OR", "UT", "WA", "WY")
BASIN_TYPES = ("major", "minor", "misc")


class BasinForm(FlaskForm):
    today = dt.now()
    state = SelectField(
        "Select State:",
        choices=[(i, i) for i in BASIN_STATES],
    )
    month = SelectField(
        "Select Month:",
        default=today.month if today.month in range(1, 13) else 1,
        choices=[
            (1, "January"),
            (2, "February"),
            (3, "March"),
            (4, "April"),
            (5, "May"),
            (6, "June"),
            (7, "July"),
            (8, "August"),
            (9, "September"),
            (10, "October"),
            (11, "November"),
            (12, "December"),
        ],
    )
    year = SelectField(
        "Select Year:", choices=sorted(range(1980, today.year + 1), reverse=True)
    )
    btype = SelectField(
        "Select Basin Type:", choices=[(i, f"{i.title()} Basins") for i in BASIN_TYPES]
    )
    refresh = BooleanField(
        "Force Data Refresh",
    )
    submit = SubmitField("Submit")


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@app.errorhandler(404)
def server_error(e):
    return render_template("404.html"), 404


@app.route("/", methods=("POST", "GET"))
def pull_data():
    args = request.args
    scrape_request = False
    if request.method == "POST" and args.get("automate", False):
        scrape_request = True
    if request.method == "GET":
        form = BasinForm(data=args)
    else:
        form = BasinForm()
    if form.validate_on_submit() or scrape_request:
        state = form.state.data
        month_digit = form.month.data
        year = form.year.data
        basin_type = form.btype.data
        refresh = form.refresh.data
        basin_hierarchy = {}
        if basin_type == "minor":
            basin_hierarchy = get_hierarchy(state=state, force_refresh=refresh)
            basin_hierarchy = {
                k.lower(): [i.lower() for i in v] for k, v in basin_hierarchy.items()
            }
        fcst_json = get_wsor_data(
            endpoint="getFcstData",
            state=state,
            year=year,
            month=month_digit,
            basin_type=basin_type,
            force_refresh=refresh,
        )
        snow_json = get_wsor_data(
            endpoint="getSnowData",
            state=state,
            year=year,
            month=month_digit,
            basin_type=basin_type,
            force_refresh=refresh,
        )
        prec_json = get_wsor_data(
            endpoint="getPrecData",
            state=state,
            year=year,
            month=month_digit,
            basin_type=basin_type,
            force_refresh=refresh,
        )
        res_json = get_wsor_data(
            endpoint="getResData",
            state=state,
            year=year,
            month=month_digit,
            basin_type=basin_type,
            force_refresh=refresh,
        )

        session["updated"] = f'{dt.now(tz=timezone("US/Pacific")):%x %X %Z}'
        session["state"] = state
        session["month_digit"] = month_digit
        session["year"] = year
        session["basin_type"] = basin_type
        session["basins"] = [i.lower() for i in fcst_json.keys()]
        session["hierarchy"] = basin_hierarchy
        session["fcst_json"] = fcst_json
        session["snow_json"] = snow_json
        session["prec_json"] = prec_json
        session["res_json"] = res_json

        return redirect(url_for("wsor"))
    return render_template("index.html", form=form)


@app.route("/basins", methods=("POST", "GET"))
def wsor():
    return render_template("basins.html")


@app.route("/<basin>", methods=("POST", "GET"))
def basin_reports(basin):

    fcst_json = session.get("fcst_json")
    if not basin.lower() in [i.lower() for i in fcst_json.keys()]:
        return render_template("404.html")
    snow_json = session.get("snow_json")
    prec_json = session.get("prec_json")
    res_json = session.get("res_json")
    fcst = forecasts(basin, fcst_json)
    snow = snowpack_sites(basin, snow_json)
    prec = precipitation(basin, prec_json)
    res = reservoirs(basin, res_json)

    rendered = render_template(
        "wsor.html",
        basin_name=basin.lower(),
        title=f"{dt(int(session['year']), int(session['month_digit']), 1):%B, %Y}",
        fcst_df=[
            None
            if fcst.empty
            else add_fcst_footer(
                fcst.to_html(
                    table_id="fcst",
                    classes="table table-sm table-hover",
                    justify="match-parent",
                    na_rep="-",
                    border=0,
                    bold_rows=False,
                )
            )
        ],
        res_df=[
            None
            if res.empty
            else add_res_footer(
                res_json[basin].get("basin_index", None),
                res.to_html(
                    table_id="res",
                    classes="table table-sm table-hover",
                    justify="match-parent",
                    index=False,
                    na_rep="-",
                    border=0,
                ),
            )
        ],
        snow_df=[
            None
            if snow.empty
            else add_snow_footer(
                snow_json[basin].get("basin_index", None),
                snow.to_html(
                    table_id="snow",
                    classes="table table-sm table-hover",
                    justify="match-parent",
                    index=False,
                    na_rep="-",
                    border=0,
                ),
            )
        ],
        prec_df=[
            None
            if prec.empty
            else add_prec_footer(
                prec_json[basin].get("basin_index", None),
                prec.to_html(
                    table_id="prec",
                    classes="table table-sm table-hover",
                    justify="match-parent",
                    index=False,
                    na_rep="-",
                    border=0,
                ),
            )
        ],
    )

    # =============================================================================
    #     options = {'page-size': 'Letter'}
    #     config = pdfkit.configuration(wkhtmltopdf=r"C:\USDA\Work\WSOR\wkhtmltopdf.exe")
    #     pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
    #
    #     response = make_response(pdf)
    #     response.headers['Content-Type'] = 'application/pdf'
    #     response.headers['Content-Disposition'] = f'inline; filename = {basin}_{month}_2022.pdf'
    #
    # =============================================================================
    return rendered


if __name__ == "__main__":

    app.run(host="0.0.0.0", debug=True)
