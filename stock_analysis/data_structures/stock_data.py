import pandas as pd # Keep for potential type checks if not using cuDF
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

class StockData:
    """
    A class to encapsulate stock-related data, including historical prices,
    technical indicators, and trading recommendations. Uses DataFrame and Series
    types from setup.config for potential GPU acceleration.
    """
    def __init__(self, symbol: str, historical_data: DataFrame = None):
        self.symbol = symbol
        # Initialize historical_data using the imported DataFrame type
        self.historical_data = historical_data if historical_data is not None else DataFrame()
        self.technical_indicators = {}
        self.trading_recommendations = {}
        self.note = None # Added for potential notes about data fetching

    def __repr__(self):
        return f"StockData(symbol='{self.symbol}', data_shape={self.historical_data.shape})"

    def add_historical_data(self, data: DataFrame):
        """
        Adds historical price data to the StockData object.

        Args:
            data: A DataFrame containing historical data with a DatetimeIndex.
        """
        # Check if the incoming data is already the correct type or pandas DataFrame
        # If using cuDF, check if the incoming data is pandas and convert
        if USE_GPU_PANDAS and isinstance(data, pd.DataFrame):
             print("Converting pandas DataFrame to cuDF DataFrame.")
             data = pd_module.DataFrame(data)
        elif not USE_GPU_PANDAS and not isinstance(data, pd.DataFrame):
             # If not using cuDF, and data is not pandas, this might be an issue
             # Depending on how data is passed, might need conversion from cuDF to pandas
             # For simplicity, assume incoming data is either pandas or the expected type
             if isinstance(data, DataFrame): # Check if it's the expected DataFrame type (could be cuDF or pandas)
                 pass # It's already the correct type
             else:
                 raise TypeError(f"Historical data must be a {DataFrame.__name__} or pandas DataFrame (if using GPU).")


        if not isinstance(data.index, pd.DatetimeIndex):
             # Attempt to convert index to DatetimeIndex if it's not already
            try:
                # Convert index to pandas DatetimeIndex first if it's a cuDF index
                if USE_GPU_PANDAS and isinstance(data.index, pd_module.core.index.DatetimeIndex):
                     data = data.to_pandas() # Convert entire DataFrame to pandas temporarily for index conversion
                     data.index = pd.to_datetime(data.index)
                     data = pd_module.DataFrame(data) # Convert back to cuDF if needed
                else:
                     data.index = pd.to_datetime(data.index)
            except Exception as e:
                raise TypeError(f"Historical data index could not be converted to DatetimeIndex: {e}")

        self.historical_data = data

    def add_technical_indicator(self, indicator_name: str, indicator_value):
        """
        Adds a calculated technical indicator to the StockData object.

        Args:
            indicator_name: The name of the technical indicator (e.g., 'SMA_50').
            indicator_value: The calculated value(s) of the indicator (can be scalar or Series).
        """
        # If the indicator value is a pandas Series and we are using cuDF, convert it
        if USE_GPU_PANDAS and isinstance(indicator_value, pd.Series):
             print(f"Converting pandas Series for indicator '{indicator_name}' to cuDF Series.")
             self.technical_indicators[indicator_name] = pd_module.Series(indicator_value)
        # If the indicator value is a cuDF Series and we are not using cuDF, convert it to pandas
        # This might be needed if models calculate cuDF Series but the rest of the system expects pandas
        elif not USE_GPU_PANDAS and isinstance(indicator_value, Series) and not isinstance(indicator_value, pd.Series):
             print(f"Converting cuDF Series for indicator '{indicator_name}' to pandas Series.")
             self.technical_indicators[indicator_name] = indicator_value.to_pandas()
        else:
            self.technical_indicators[indicator_name] = indicator_value

    def add_trading_recommendation(self, model_name: str, recommendation: dict):
        """
        Adds a trading recommendation from a specific model.

        Args:
            model_name: The name of the trading model.
            recommendation: A dictionary containing the recommendation details
                            (e.g., {'recommendation': 'BUY', 'reasoning': '...', 'confidence': 0.8}).
        """
        self.trading_recommendations[model_name] = recommendation

    def get_historical_data(self) -> DataFrame:
        """
        Returns the historical price data.
        """
        return self.historical_data

    def get_technical_indicators(self) -> dict:
        """
        Returns the dictionary of technical indicators.
        """
        return self.technical_indicators

    def get_trading_recommendations(self) -> dict:
        """
        Returns the dictionary of trading recommendations from different models.
        """
        return self.trading_recommendations
