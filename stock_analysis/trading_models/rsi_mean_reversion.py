import pandas as pd # Keep for potential type checks if not using cuDF
import numpy as np # Keep for numpy operations like nan checks
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

class RsiMeanReversionModel:
    """
    Trading model based on the Relative Strength Index (RSI) mean reversion strategy.
    Uses DataFrame and Series types from setup.config.
    """

    def __init__(self, rsi_window: int = 14, buy_threshold: int = 30, sell_threshold: int = 70):
        self.rsi_window = rsi_window
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.required_data_points = self.rsi_window + 1 # Need window + 1 for initial diff calculation

    def calculate_rsi(self, data: DataFrame, window: int) -> Series:
        """
        Calculates the Relative Strength Index (RSI).

        Args:
            data: DataFrame with a 'Close' column.
            window: The number of periods to include in the RSI calculation.

        Returns:
            A Series containing the RSI values.
        """
        if 'Close' not in data.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")

        # Ensure data has enough points for the window
        if len(data) < window + 1: # Need window + 1 for the first diff
             return Series([np.nan] * len(data), index=data.index)


        delta = data['Close'].diff()
        gain = delta.mask(delta < 0, 0)
        loss = delta.mask(delta > 0, 0).abs()

        # Exponential Moving Average calculation works with both pandas and cuDF Series
        # min_periods can be set to window to match standard RSI calculation where first 'real' value appears after window periods
        avg_gain = gain.ewm(com=window - 1, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(com=window - 1, adjust=False, min_periods=window).mean()


        # Handle division by zero for RS calculation
        # Replace inf with NaN, then handle NaN
        rs = avg_gain / avg_loss
        rs = rs.replace([np.inf, -np.inf], np.nan)

        # Where avg_loss is 0, and avg_gain is > 0, RSI should be 100.
        # Where avg_gain is 0, and avg_loss is > 0, RSI should be 0.
        # Where both are 0, RSI is undefined (NaN).

        rsi = 100 - (100 / (1 + rs))

        # Specific handling for cases where avg_loss is zero
        rsi = pd_module.Series(np.where((avg_loss == 0) & (avg_gain > 0), 100, rsi), index=data.index)
        # Specific handling for cases where avg_gain is zero
        rsi = pd_module.Series(np.where((avg_gain == 0) & (avg_loss > 0), 0, rsi), index=data.index)


        return rsi

    def analyze_stock(self, stock_data: StockData) -> dict:
        """
        Analyzes stock data using the RSI Mean Reversion strategy.

        Args:
            stock_data: The StockData object containing historical data.

        Returns:
            A dictionary containing the analysis recommendation and details.
        """
        historical_data = stock_data.get_historical_data()

        if historical_data.empty or len(historical_data) < self.required_data_points:
            return {
                'recommendation': 'WAIT',
                'reasoning': f"Insufficient data ({len(historical_data)} data points) for {self.rsi_window}-period RSI calculation. Need at least {self.required_data_points}.",
                'confidence': 0.0,
                'timeframe': 'N/A',
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        # Determine timeframe based on data frequency (simple heuristic)
        # Access the index and calculate time differences using the configured Series type
        time_diffs = historical_data.index.to_series().diff().dropna()
        avg_time_diff = time_diffs.mean()

        # Use pd.Timedelta for comparison
        timeframe = 'Weekly' if avg_time_diff > pd.Timedelta(days=1) else 'Daily'


        # Calculate RSI using the internal method, which uses configured types
        try:
            rsi_values = self.calculate_rsi(historical_data, window=self.rsi_window)
            # Ensure we have a valid RSI value at the end using .iloc[-1] and np.nan check
            if rsi_values.empty or rsi_values.iloc[-1] is np.nan:
                return {
                    'recommendation': 'WAIT',
                    'reasoning': f"RSI calculation resulted in no valid latest value.",
                    'confidence': 0.0,
                    'timeframe': timeframe,
                    'trend_direction': 'N/A',
                    'risk_level': 'N/A',
                    'support': 'N/A',
                    'resistance': 'N/A'
                }
            latest_rsi = rsi_values.iloc[-1]

        except ValueError as e:
             return {
                'recommendation': 'WAIT',
                'reasoning': f"Could not calculate RSI: {e}",
                'confidence': 0.0,
                'timeframe': timeframe,
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        recommendation = 'WAIT'
        reasoning = f"RSI ({latest_rsi:.2f}) is within the neutral range ({self.buy_threshold}-{self.sell_threshold})."
        confidence = 0.5
        risk_level = 'Medium'
        trend_direction = 'Sideways'


        # Determine the signal based on RSI thresholds
        # Comparisons like < and > work with both pandas and cuDF Series latest values
        if latest_rsi < self.buy_threshold:
            recommendation = 'BUY'
            reasoning = f"RSI ({latest_rsi:.2f}) is below the buy threshold ({self.buy_threshold}), indicating potentially oversold conditions."
            confidence = 0.7
            risk_level = 'Medium-High'
            trend_direction = 'Potential Uptrend (from Oversold)'

        elif latest_rsi > self.sell_threshold:
            recommendation = 'SELL'
            reasoning = f"RSI ({latest_rsi:.2f}) is above the sell threshold ({self.sell_threshold}), indicating potentially overbought conditions."
            confidence = 0.7
            risk_level = 'Medium-High'
            trend_direction = 'Potential Downtrend (from Overbought)'

        else: # RSI is between buy_threshold and sell_threshold
            recommendation = 'WAIT'
            reasoning = f"RSI ({latest_rsi:.2f}) is within the neutral range ({self.buy_threshold}-{self.sell_threshold}). Waiting for a clearer signal."
            confidence = 0.5
            risk_level = 'Low' # Lower risk waiting


        # Add RSI values to stock_data for reporting/visualization
        # The add_technical_indicator method in StockData handles type conversion if necessary
        rsi_indicator_name = f'RSI_{self.rsi_window}_{timeframe[0]}'
        stock_data.add_technical_indicator(rsi_indicator_name, rsi_values)


        return {
            'recommendation': recommendation,
            'reasoning': reasoning,
            'confidence': round(confidence, 2),
            'timeframe': timeframe,
            'trend_direction': trend_direction,
            'risk_level': risk_level,
            'support': 'N/A', # Placeholder
            'resistance': 'N/A' # Placeholder
        }
