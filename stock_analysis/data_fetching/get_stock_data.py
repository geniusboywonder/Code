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


def get_stock_data(symbol: str, end_date: str = None) -> StockData:
    """
    Fetches historical stock data for a given symbol, ensuring enough data
    is retrieved for technical indicator calculations (200 work days + 18 day buffer).
    Prioritizes daily data and falls back to weekly if necessary. Uses DataFrame and Series
    types from setup.config.

    Args:
        symbol: The stock symbol (e.g., 'AAPL').
        end_date: The end date for historical data (YYYY-MM-DD). Defaults to yesterday.

    Returns:
        A StockData object populated with the historical data.
        Returns None if data fetching fails.
    """
    try:
        # Default end_date to yesterday if not provided
        if end_date is None:
            end_date_dt = datetime.now() - timedelta(days=1)
            end_date = end_date_dt.strftime('%Y-%m-%d')
        else:
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

        ticker = yf.Ticker(symbol)

        # Calculate start date to get 200 work days + 18 day buffer
        # Work days are approximately 5/7 of calendar days
        # To get 200 work days, we need approximately 200 * 7/5 = 280 calendar days
        # Adding 18 day buffer: 280 + 18 = 298 calendar days
        # Adding extra buffer for weekends and holidays: 298 * 1.4 ≈ 417 calendar days
        required_calendar_days = int((200 * 7/5) + 18 + 100)  # 398 days with extra buffer
        start_date_dt = end_date_dt - timedelta(days=required_calendar_days)
        start_date_str = start_date_dt.strftime('%Y-%m-%d')

        print(f"Attempting to fetch daily data for {symbol} from {start_date_str} to {end_date} (targeting 200+ work days)...")
        # Fetch data using yfinance, which returns a pandas DataFrame
        historical_data_pandas = ticker.history(start=start_date_str, end=end_date)

        # Convert the pandas DataFrame to the configured DataFrame type if necessary
        if USE_GPU_PANDAS and not historical_data_pandas.empty:
             historical_data = pd_module.DataFrame(historical_data_pandas)
        else:
            historical_data = historical_data_pandas


        # Check if enough daily data was fetched (need at least 200 work days)
        # Approximate work days by counting weekdays in the data
        work_days_count = len(historical_data)  # For daily data, this is approximately work days
        
        if work_days_count < 200:
            print(f"Insufficient daily data ({work_days_count} data points) for {symbol}. Attempting to fetch weekly data...")
            # Calculate start date for weekly data to get equivalent of 200 work days
            # 200 work days ≈ 40 work weeks, request 50 weeks + buffer
            required_weeks = 60  # 50 weeks + 10 week buffer
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

            # Check if we have enough weekly data (should be at least 40 weeks for 200 work days equivalent)
            if len(historical_data) < 40:
                print(f"Warning: Insufficient weekly data ({len(historical_data)} weeks) for {symbol}. Need at least 40 weeks.")
                return None

            print(f"Fetched weekly data for {symbol}. Data shape: {historical_data.shape} ({len(historical_data)} weeks)")
            stock_data = StockData(symbol=symbol)
            stock_data.add_historical_data(historical_data) # StockData's method handles internal type conversion
            # Add a note about using weekly data and actual count
            stock_data.note = f"Data fetched using weekly interval due to insufficient daily data. {len(historical_data)} weeks of data available."
            return stock_data


        if historical_data.empty:
            print(f"Warning: No daily data fetched for symbol {symbol} in the specified date range.")
            return None

        print(f"Successfully fetched daily data for {symbol}. Data shape: {historical_data.shape} (approximately {work_days_count} work days)")
        stock_data = StockData(symbol=symbol)
        stock_data.add_historical_data(historical_data) # StockData's method handles internal type conversion
        stock_data.note = f"Daily data fetched. {work_days_count} data points available."
        return stock_data

    except Exception as e:
        print(f"Error fetching data for symbol {symbol}: {e}")
        return None
