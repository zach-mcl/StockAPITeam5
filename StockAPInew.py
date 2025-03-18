import requests
import pygal
from datetime import datetime

AV_API_KEY = "IMTO1H6UEKUDNM2G"

def fetch_stock_data(symbol, function):
    url = "https://www.alphavantage.co/query"
    stock_info = {
        "function": function,
        "symbol": symbol,
        "apikey": AV_API_KEY,
        "datatype": "json"
    }

    response = requests.get(url, params=stock_info)

    if response.ok:
        data = response.json()

        if "Error Message" in data:
            print(f"Error: Invalid stock symbol '{symbol}'. Please check the ticker symbol.")
            return None

        for key in data.keys():
            if "Time Series" in key:
                return data[key]

        print("Error: Time series data not found. Check API function or response format.")
        return None
    else:
        print("Error: Failed to fetch data. Check your API key and stock symbol.")
        return None

def sort_data(data, start, end, debug=False):
    filter_data = {}
    if debug:
        print("Raw data fetched from API:", data)
    for date, values in data.items():
        if debug:
            print(f"Date in data: {date}")
        if start <= date <= end:
            close_price = values.get("4.close")
            if close_price:
                filter_data[date] = float(close_price)
            else:
                if debug:
                    print(f"Warning: Missing '4.close' data for {date}")
    return filter_data

def create_stock_chart(stock_data, symbol, chart_type):
    print("Please type 'Line' or 'L' for a Line Graph. Please type 'Bar' or 'B' for a Bar Graph")
    chart_types = {"line": pygal.Line, "l": pygal.Line, "bar": pygal.Bar, "b": pygal.Bar}

    while chart_type not in chart_types:
        print("Invalid chart type. Please enter 'line' or 'bar'.")
        chart_type = input("Enter chart type: ").strip().lower()

    chart = chart_types[chart_type](title=f"{symbol} Stock Prices", x_label_rotation=45, style=LightColorizedStyle)
    chart.x_labels = list(stock_data.keys())
    chart.add(symbol, list(stock_data.values()))

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{symbol}_{date_str}_stock_chart.svg"
    chart.render_to_file(filename)

    print(f"Chart saved as '{filename}'. Open in a browser to view.")

def get_chart_type():
    chart_types = {"line": pygal.Line, "l": pygal.Line, "bar": pygal.Bar, "b": pygal.Bar}
    while True:
        chart_type = input("Enter chart type (line/bar): ").strip().lower()
        if chart_type in chart_types:
            return chart_type
        print("Invalid chart type. Please enter 'line' or 'bar'.")

def main():
    while True:
        symbol = input("Enter stock symbol (e.g., AAPL, TSLA): ").upper()
        data = fetch_stock_data(symbol, function="TIME_SERIES_DAILY")

        if data:
            break
        else:
            print("Please enter a valid stock symbol.")

    chart_type = get_chart_type()

    print("\nChoose a time series function:")
    print("1. Daily")
    print("2. Weekly")
    print("3. Monthly")
    function_choice = input("Enter your choice (1, 2, or 3): ").strip()

    if function_choice == "1":
        function = "TIME_SERIES_DAILY"
    elif function_choice == "2":
        function = "TIME_SERIES_WEEKLY"
    elif function_choice == "3":
        function = "TIME_SERIES_MONTHLY"
    else:
        print("Invalid input, defaulting to TIME_SERIES_DAILY.")
        function = "TIME_SERIES_DAILY"

    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Incorrect date format. Use YYYY-MM-DD.")
        return

    if end_date < start_date:
        print("Error: End date cannot be before start date.")
        return

    filtered_data = sort_data(data, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    if filtered_data:
        create_stock_chart(filtered_data, symbol, chart_type)
    else:
        print("No stock data available for the given date range.")

if __name__ == "__main__":
    main()
