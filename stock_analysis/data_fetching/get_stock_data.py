import yfinance as yf
import pandas as pd # Keep for potential type checks if not using cuDF
from datetime import datetime, timedelta
import sys
import os

# Add the project root to sys.path to allow importing modules
# This is needed to import modules from the stock_analysis package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import DataFrame, Series, and pd_module from the setup config
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS
from ..data_structures.stock_data import StockData


def get_stock_data(symbol: str, end_date: str) -> StockData:
    """
    Fetches historical stock data for a given symbol, ensuring enough data
    is retrieved for technical indicator calculations, prioritizing daily data
    and falling back to weekly if necessary. Uses DataFrame and Series
    types from setup.config.

    Args:
        symbol: The stock symbol (e.g., 'AAPL').
        end_date: The end date for historical data (YYYY-MM-DD).

    Returns:
        A StockData object populated with the historical data.
        Returns None if data fetching fails.
    """
    try:
        ticker = yf.Ticker(symbol)
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # Calculate start date to get enough data for indicators (e.g., 200-day MA)
        # Request data for ~280 days (40 weeks) to be safe, prior to the end date
        required_days = 280
        start_date_dt = end_date_dt - timedelta(days=required_days)
        start_date_str = start_date_dt.strftime('%Y-%m-%d')

        print(f"Attempting to fetch daily data for {symbol} from {start_date_str} to {end_date}...")
        # Fetch data using yfinance, which returns a pandas DataFrame
        historical_data_pandas = ticker.history(start=start_date_str, end=end_date)

        # Convert the pandas DataFrame to the configured DataFrame type if necessary
        if USE_GPU_PANDAS and not historical_data_pandas.empty:
             historical_data = pd_module.DataFrame(historical_data_pandas)
        else:
            historical_data = historical_data_pandas


        # Check if enough daily data was fetched
        if len(historical_data) < 200:
            print(f"Insufficient daily data ({len(historical_data)} data points) for {symbol}. Attempting to fetch weekly data...")
            # Calculate start date for weekly data (approx. 40 weeks)
            required_weeks = 40
            start_date_weekly_dt = end_date_dt - timedelta(weeks=required_weeks)
            start_date_weekly_str = start_date_weekly_dt.strftime('%Y-%m-%d')

            # Fetch weekly data, which also returns a pandas DataFrame
            historical_data_weekly_pandas = ticker.history(start=start_date_weekly_str, end=end_date, interval='1wk')

            # Convert the pandas DataFrame to the configured DataFrame type if necessary
            if USE_GPU_PANDAS and not historical_data_weekly_pandas.empty:
                 historical_data = pd_module.DataFrame(historical_data_weekly_pandas)
            else:
                historical_data = historical_data_weekly_pandas


            if historical_data.empty:
                 print(f"Warning: No weekly data fetched for symbol {symbol} in the specified date range.")
                 return None

            print(f"Fetched weekly data for {symbol}. Data shape: {historical_data.shape}")
            stock_data = StockData(symbol=symbol)
            stock_data.add_historical_data(historical_data) # StockData's method handles internal type conversion
            # Add a note about using weekly data
            stock_data.note = "Data fetched using weekly interval due to insufficient daily data."
            return stock_data


        if historical_data.empty:
            print(f"Warning: No daily data fetched for symbol {symbol} in the specified date range.")
            return None

        print(f"Successfully fetched daily data for {symbol}. Data shape: {historical_data.shape}")
        stock_data = StockData(symbol=symbol)
        stock_data.add_historical_data(historical_data) # StockData's method handles internal type conversion
        return stock_data

    except Exception as e:
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None
