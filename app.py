import requests
import pygal
import os
from datetime import datetime

from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd

AV_API_KEY = "IMTO1H6UEKUDNM2G"  # keep your key here or load from .env

app = Flask(__name__)
app.secret_key = 'supersecretkey'


@app.route('/', methods=['GET'])
def home():
    try:
        csv_path = os.path.join(app.static_folder, 'stocks.csv')
        df = pd.read_csv(csv_path)
        symbols = df['Symbol'].tolist()
    except Exception:
        symbols = []
        flash('Could not load stock symbols.', 'danger')
    return render_template('index.html', symbols=symbols)


@app.route('/chart', methods=['POST'])
def chart():
    # load symbols for validation and the dropdown
    try:
        csv_path = os.path.join(app.static_folder, 'stocks.csv')
        symbols = pd.read_csv(csv_path)['Symbol'].dropna().tolist()
    except Exception:
        flash('Could not load stock symbols.', 'danger')
        return redirect(url_for('home'))

    # get form input
    symbol      = request.form.get('symbol')
    chart_type  = request.form.get('chart_type')
    time_series = request.form.get('time_series')
    start_date  = request.form.get('start_date')
    end_date    = request.form.get('end_date')

    # input validation
    if not symbol or symbol not in symbols:
        flash('Invalid symbol selected.', 'danger')
        return redirect(url_for('home'))
    if end_date < start_date:
        flash('End date must be after start date.', 'danger')
        return redirect(url_for('home'))

    # map human-friendly to API function
    func_map = {
        'Daily':   'TIME_SERIES_DAILY',
        'Weekly':  'TIME_SERIES_WEEKLY',
        'Monthly': 'TIME_SERIES_MONTHLY'
    }
    function = func_map.get(time_series, 'TIME_SERIES_DAILY')

    # fetch & filter data
    raw_data = fetch_stock_data(symbol, function)
    if not raw_data:
        flash('No data returned from API.', 'danger')
        return redirect(url_for('home'))

    filtered = sort_data(raw_data, start_date, end_date)
    if not filtered:
        flash('No data in the given date range.', 'warning')
        return redirect(url_for('home'))

    try:
      chart_classes = {'line': pygal.Line, 'bar': pygal.Bar}
      chart_cls      = chart_classes.get(chart_type, pygal.Line)
      chart          = chart_cls(title=f'{symbol} Prices', x_label_rotation=45)
      chart.x_labels = list(filtered.keys())
      chart.add(symbol, list(filtered.values()))
      chart_data     = chart.render_data_uri()
    except Exception as e:
      flash(f'Chart generation failed: {e}', 'danger')
      return redirect(url_for('home'))

    return render_template('index.html', symbols=symbols, chart_data=chart_data)


def fetch_stock_data(symbol, function):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey":  AV_API_KEY,
        "datatype": "json"
    }
    resp = requests.get(url, params=params)
    if not resp.ok:
        print(f"API error: {resp.status_code}")
        return None

    data = resp.json()
    # find the “Time Series” key
    ts_key = next((k for k in data if "Time Series" in k), None)
    return data.get(ts_key)


def sort_data(data, start, end):
    out = {}
    for date, vals in data.items():
        if start <= date <= end:
            try:
                out[date] = float(vals["4. close"])
            except Exception:
                continue
    return out


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)