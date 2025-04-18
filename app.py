#!/usr/bin/env python3
"""
Stock Data Visualizer Web App
=============================

A Flask application that fetches stock data from Alpha Vantage,
filters by date range, and renders interactive charts via Pygal.

Dependencies:
  - Flask
  - pandas
  - requests
  - pygal
  - python-dotenv
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from flask import (
    Flask, render_template, request,
    flash, redirect, url_for
)
import pandas as pd
import requests
import pygal
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
AV_API_KEY: str = os.getenv("AV_API_KEY", "")
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev_secret")

if not AV_API_KEY:
    raise RuntimeError("Missing AV_API_KEY in environment")  # Fail fast

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


@app.route("/", methods=["GET"])
def home() -> str:
    """
    Render the home page with the stock symbol dropdown.
    Reads symbols from static/stocks.csv; flashes error if loading fails.
    """
    try:
        csv_path = os.path.join(app.static_folder, "stocks.csv")
        df = pd.read_csv(csv_path)
        symbols = df["Symbol"].dropna().tolist()
    except FileNotFoundError:
        app.logger.error("stocks.csv not found at %s", csv_path)
        flash("Stock list unavailable.", "danger")
        symbols = []
    except pd.errors.EmptyDataError:
        app.logger.error("stocks.csv is empty")
        flash("Stock list is empty.", "warning")
        symbols = []
    return render_template("index.html", symbols=symbols)


@app.route("/chart", methods=["POST"])
def chart() -> str:
    """
    Handle chart form submission:
    - Validate inputs
    - Fetch data from Alpha Vantage
    - Filter by date range
    - Generate a Pygal chart SVG URI
    """
    # Reload symbols for validation
    try:
        csv_path = os.path.join(app.static_folder, "stocks.csv")
        symbols = pd.read_csv(csv_path)["Symbol"].dropna().tolist()
    except Exception as e:
        app.logger.error("Failed to load symbols: %s", e)
        flash("Unable to load stock list.", "danger")
        return redirect(url_for("home"))

    # Extract and validate form inputs
    symbol = request.form.get("symbol", "").upper()
    if symbol not in symbols:
        flash("Please select a valid symbol.", "danger")
        return redirect(url_for("home"))

    chart_type = request.form.get("chart_type", "line")
    if chart_type not in ("line", "bar"):
        flash("Chart type invalid.", "danger")
        return redirect(url_for("home"))

    time_series = request.form.get("time_series", "Daily")
    func_map = {
        "Daily": "TIME_SERIES_DAILY",
        "Weekly": "TIME_SERIES_WEEKLY",
        "Monthly": "TIME_SERIES_MONTHLY",
    }
    function = func_map.get(time_series)

    # Parse dates with clear error messages
    try:
        start_date = datetime.fromisoformat(request.form["start_date"]).date()
        end_date = datetime.fromisoformat(request.form["end_date"]).date()
    except ValueError:
        flash("Dates must be in YYYY-MM-DD format.", "danger")
        return redirect(url_for("home"))

    if end_date < start_date:
        flash("End date cannot be before start date.", "danger")
        return redirect(url_for("home"))

    # Fetch and filter data
    raw_data = fetch_stock_data(symbol, function)
    if raw_data is None:
        flash("API error fetching data.", "danger")
        return redirect(url_for("home"))

    filtered = sort_data(raw_data, start_date.isoformat(), end_date.isoformat())
    if not filtered:
        flash("No data for selected range.", "warning")
        return redirect(url_for("home"))

    # Build chart with error handling
    try:
        ChartClass = pygal.Line if chart_type == "line" else pygal.Bar
        chart = ChartClass(
            title=f"{symbol} Closing Prices",
            x_label_rotation=20,
            show_legend=False,
        )
        dates = sorted(filtered.keys())
        chart.x_labels = dates
        chart.add(symbol, [filtered[d] for d in dates])
        chart_data = chart.render_data_uri()
    except Exception as exc:
        app.logger.exception("Chart build failed")
        flash(f"Could not create chart: {exc}", "danger")
        return redirect(url_for("home"))

    return render_template("index.html", symbols=symbols, chart_data=chart_data)


def fetch_stock_data(symbol: str, function: str) -> Optional[Dict[str, Any]]:
    """
    Query Alpha Vantage for the given symbol and function.
    Returns a dict keyed by date of closing price.
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": AV_API_KEY,
        "datatype": "json",
    }
    resp = requests.get(url, params=params, timeout=10)
    try:
        resp.raise_for_status()
        data = resp.json()
        ts_key = next(k for k in data if "Time Series" in k)
        return data.get(ts_key)
    except (requests.HTTPError, KeyError, StopIteration) as err:
        app.logger.error("API fetch error: %s", err)
        return None


def sort_data(
    data: Dict[str, Dict[str, str]],
    start: str,
    end: str
) -> Dict[str, float]:
    """
    Filter raw_data between start/end (YYYY-MM-DD).
    Returns a date→closing_price map.
    """
    out: Dict[str, float] = {}
    for date, vals in data.items():
        if start <= date <= end:
            try:
                out[date] = float(vals["4. close"])
            except (KeyError, ValueError):
                continue
    return out


if __name__ == "__main__":
    # Bind to PORT environment variable for flexible hosting
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)