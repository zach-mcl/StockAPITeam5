import requests
import pygal
from datetime import datetime
import os
import webbrowser

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
        # Identify the correct key containing the time series data
        time_series_key = next((key for key in data if "Time Series" in key), None)
        if time_series_key:
            return data[time_series_key]
        else:
            print(f"Error: Could not find time series data in the response. Response: {data}")
            return None
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        return None

def sort_data(data, start, end):
    filtered_data = {}
    for date, values in data.items():
        if start <= date <= end:
            close_price = values.get("4. close")
            if close_price:
                try:
                    filtered_data[date] = float(close_price)
                except ValueError:
                    print(f"Warning: Invalid close price data for {date}, skipping this date.")
            else:
                print(f"Warning: Missing data for {date}, skipping this date.")
    return filtered_data

def create_stock_chart(stock_data, symbol, chart_type, start_date, end_date):
    chart_types = {"line": pygal.Line, "bar": pygal.Bar}
    # Validate chart type until a proper one is given
    while chart_type not in chart_types:
        print("Invalid chart type. Please enter 'line' or 'bar'.")
        chart_type = input("Enter chart type: ").strip().lower()
    
    # Sort the dates to display the data in chronological order
    sorted_dates = sorted(stock_data.keys())
    chart = chart_types[chart_type](title=f"{symbol} Stock Prices", x_label_rotation=45)
    chart.x_labels = sorted_dates
    chart.add(symbol, [stock_data[date] for date in sorted_dates])
    
    # Incorporate the date range into the filename
    filename = f"{symbol}_{start_date}_to_{end_date}_stock_chart.svg"
    chart.render_to_file(filename)
    print(f"Chart saved as '{filename}'.")
    
    # Open the created graph in the default browser
    full_path = os.path.abspath(filename)
    webbrowser.open('file://' + full_path)

def main():
    # Prompt for symbol and desired time series function before fetching data
    symbol = input("Enter stock symbol (e.g., AAPL, TSLA): ").upper()
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

    # Fetch the data once using the selected function
    data = fetch_stock_data(symbol, function=function)
    if not data:
        print("Error: No data available. Please verify the stock symbol.")
        return

    chart_type = input("Enter chart type (line/bar): ").strip().lower()
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()

    try:
        # Validate and reformat the dates
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = start_date_obj.strftime("%Y-%m-%d")
        end_date = end_date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print("Error: Incorrect date format. Use YYYY-MM-DD.")
        return

    if end_date < start_date:
        print("Error: End date cannot be before start date.")
        return

    filtered_data = sort_data(data, start_date, end_date)
    if filtered_data:
        create_stock_chart(filtered_data, symbol, chart_type, start_date, end_date)
    else:
        print("No stock data available for the given date range.")

if __name__ == "__main__":
    main()
