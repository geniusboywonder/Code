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

class BollingerBandsModel:
    """
    Trading model based on Bollinger Bands.
    Uses DataFrame and Series types from setup.config.
    """

    def __init__(self, window: int = 20, num_std_dev: int = 2):
        self.window = window
        self.num_std_dev = num_std_dev
        self.required_data_points = self.window

    def calculate_bollinger_bands(self, data: DataFrame, window: int, num_std_dev: int) -> tuple[Series, Series, Series]:
        """
        Calculates the Middle Band (SMA), Upper Band, and Lower Band.

        Args:
            data: DataFrame with a 'Close' column.
            window: The number of periods for the moving average and standard deviation.
            num_std_dev: The number of standard deviations to use for the bands.

        Returns:
            A tuple containing the Middle Band (Series), Upper Band (Series),
            and Lower Band (Series).
        """
        if 'Close' not in data.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")

        # Rolling window calculations work with both pandas and cuDF Series
        middle_band = data['Close'].rolling(window=window).mean()
        rolling_std = data['Close'].rolling(window=window).std()

        # Arithmetic operations work with both pandas and cuDF Series
        upper_band = middle_band + (rolling_std * num_std_dev)
        lower_band = middle_band - (rolling_std * num_std_dev)

        return middle_band, upper_band, lower_band

    def analyze_stock(self, stock_data: StockData) -> dict:
        """
        Analyzes stock data using the Bollinger Bands strategy.

        Args:
            stock_data: The StockData object containing historical data.

        Returns:
            A dictionary containing the analysis recommendation and details.
        """
        historical_data = stock_data.get_historical_data()

        if historical_data.empty or len(historical_data) < self.required_data_points:
            return {
                'recommendation': 'WAIT',
                'reasoning': f"Insufficient data ({len(historical_data)} data points) for {self.window}-period Bollinger Bands calculation. Need at least {self.required_data_points}.",
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


        # Calculate Bollinger Bands using the internal method
        try:
            middle_band, upper_band, lower_band = self.calculate_bollinger_bands(
                historical_data,
                window=self.window,
                num_std_dev=self.num_std_dev
            )
            # Ensure we have valid latest values using .iloc[-1] and np.nan check
            if middle_band.empty or upper_band.empty or lower_band.empty or \
               middle_band.iloc[-1] is np.nan or upper_band.iloc[-1] is np.nan or lower_band.iloc[-1] is np.nan:
                 return {
                    'recommendation': 'WAIT',
                    'reasoning': f"Bollinger Bands calculation resulted in no valid latest values.",
                    'confidence': 0.0,
                    'timeframe': timeframe,
                    'trend_direction': 'N/A',
                    'risk_level': 'N/A',
                    'support': 'N/A',
                    'resistance': 'N/A'
                }

            latest_close = historical_data['Close'].iloc[-1]
            latest_middle = middle_band.iloc[-1]
            latest_upper = upper_band.iloc[-1]
            latest_lower = lower_band.iloc[-1]
            # Safely get previous close value
            previous_close = historical_data['Close'].iloc[-2] if len(historical_data) >= 2 else latest_close


        except ValueError as e:
             return {
                'recommendation': 'WAIT',
                'reasoning': f"Could not calculate Bollinger Bands: {e}",
                'confidence': 0.0,
                'timeframe': timeframe,
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        recommendation = 'WAIT'
        reasoning = "No clear Bollinger Bands signal."
        confidence = 0.5
        risk_level = 'Medium'
        trend_direction = 'Sideways'

        # Determine the signal based on price interaction with bands
        # Comparisons work for both pandas and cuDF Series latest values
        # Bullish signal: Price closes below the lower band and then closes back above it, or crosses above lower band
        if latest_close > latest_lower and previous_close <= latest_lower:
             recommendation = 'BUY'
             reasoning = f"Price ({latest_close:.2f}) crossed above the Lower Bollinger Band ({latest_lower:.2f}). Potential mean reversion."
             confidence = 0.7
             risk_level = 'Medium-High'
             trend_direction = 'Potential Uptrend (from Oversold)'
        # Bearish signal: Price closes above the upper band and then closes back below it, or crosses below upper band
        elif latest_close < latest_upper and previous_close >= latest_upper:
             recommendation = 'SELL'
             reasoning = f"Price ({latest_close:.2f}) crossed below the Upper Bollinger Band ({latest_upper:.2f}). Potential mean reversion."
             confidence = 0.7
             risk_level = 'Medium-High'
             trend_direction = 'Potential Downtrend (from Overbought)'
        # Price is within the bands
        elif latest_lower <= latest_close <= latest_upper:
             # Check for trend direction based on Middle Band
             if latest_close > latest_middle and previous_close <= latest_middle:
                 recommendation = 'WAIT' # Or 'BUY' for momentum, but 'WAIT' for clarity
                 reasoning = f"Price ({latest_close:.2f}) crossed above the Middle Bollinger Band ({latest_middle:.2f}). Bullish momentum within bands."
                 confidence = 0.6
                 risk_level = 'Low'
                 trend_direction = 'Uptrend bias (within Bands)'
             elif latest_close < latest_middle and previous_close >= latest_middle:
                 recommendation = 'WAIT' # Or 'SELL' for momentum, but 'WAIT' for clarity
                 reasoning = f"Price ({latest_close:.2f}) crossed below the Middle Bollinger Band ({latest_middle:.2f}). Bearish momentum within bands."
                 confidence = 0.6
                 risk_level = 'Low'
                 trend_direction = 'Downtrend bias (within Bands)'
             else:
                recommendation = 'WAIT'
                reasoning = f"Price ({latest_close:.2f}) is within Bollinger Bands ({latest_lower:.2f} - {latest_upper:.2f}). Sideways or consolidating."
                confidence = 0.5
                risk_level = 'Low'
                trend_direction = 'Sideways (within Bands)'

        # Price is outside the bands (continuation signal, higher risk)
        elif latest_close > latest_upper:
             recommendation = 'WAIT' # Or BUY for strong momentum continuation
             reasoning = f"Price ({latest_close:.2f}) is above the Upper Bollinger Band ({latest_upper:.2f}), indicating potential overbought conditions or strong momentum."
             confidence = 0.4
             risk_level = 'High'
             trend_direction = 'Strong Uptrend (potentially overextended)'
        elif latest_close < latest_lower:
             recommendation = 'WAIT' # Or SELL for strong momentum continuation
             reasoning = f"Price ({latest_close:.2f}) is below the Lower Bollinger Band ({latest_lower:.2f}), indicating potential oversold conditions or strong momentum."
             confidence = 0.4
             risk_level = 'High'
             trend_direction = 'Strong Downtrend (potentially overextended)'


        # Add Bollinger Bands values to stock_data for reporting/visualization
        # The add_technical_indicator method in StockData handles type conversion if necessary
        middle_band_name = f'BB_Middle_{self.window}_{timeframe[0]}'
        upper_band_name = f'BB_Upper_{self.window}_{self.num_std_dev}_{timeframe[0]}'
        lower_band_name = f'BB_Lower_{self.window}_{self.num_std_dev}_{timeframe[0]}'

        stock_data.add_technical_indicator(middle_band_name, middle_band)
        stock_data.add_technical_indicator(upper_band_name, upper_band)
        stock_data.add_technical_indicator(lower_band_name, lower_band)

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
