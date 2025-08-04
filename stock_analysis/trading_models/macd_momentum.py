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

class MacdMomentumModel:
    """
    Trading model based on the Moving Average Convergence Divergence (MACD) indicator.
    Uses DataFrame and Series types from setup.config.
    """

    def __init__(self, short_window: int = 12, long_window: int = 26, signal_window: int = 9):
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window
        # Need enough data for the longest EMA (long_window) + signal EMA (signal_window)
        # The first valid MACD is at long_window, the first valid signal is at long_window + signal_window - 1
        self.required_data_points = self.long_window + self.signal_window - 1


    def calculate_macd(self, data: DataFrame, short_window: int, long_window: int, signal_window: int) -> tuple[Series, Series]:
        """
        Calculates the MACD line and Signal line.

        Args:
            data: DataFrame with a 'Close' column.
            short_window: The number of periods for the short-term EMA.
            long_window: The number of periods for the long-term EMA.
            signal_window: The number of periods for the signal line EMA of the MACD.

        Returns:
            A tuple containing the MACD line (Series) and the Signal line (Series).
        """
        if 'Close' not in data.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")

        # Ensure data has enough points for the longest window
        if len(data) < long_window:
             # Return Series of NaNs if insufficient data for long EMA
             return Series([np.nan] * len(data), index=data.index), Series([np.nan] * len(data), index=data.index)

        # EMA calculations work with both pandas and cuDF Series
        # min_periods can be set to the window size to match standard EMA behavior
        short_ema = data['Close'].ewm(span=short_window, adjust=False, min_periods=short_window).mean()
        long_ema = data['Close'].ewm(span=long_window, adjust=False, min_periods=long_window).mean()

        macd_line = short_ema - long_ema

        # Calculate Signal line EMA on the MACD line
        # min_periods for signal line should be based on when MACD becomes valid
        signal_line = macd_line.ewm(span=signal_window, adjust=False, min_periods=long_window + signal_window - 1).mean()


        return macd_line, signal_line

    def analyze_stock(self, stock_data: StockData) -> dict:
        """
        Analyzes stock data using the MACD Momentum strategy.

        Args:
            stock_data: The StockData object containing historical data.

        Returns:
            A dictionary containing the analysis recommendation and details.
        """
        historical_data = stock_data.get_historical_data()

        if historical_data.empty or len(historical_data) < self.required_data_points:
            return {
                'recommendation': 'WAIT',
                'reasoning': f"Insufficient data ({len(historical_data)} data points) for MACD ({self.short_window},{self.long_window},{self.signal_window}) calculation. Need at least {self.required_data_points}.",
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


        # Calculate MACD and Signal lines using the internal method
        try:
            macd_line, signal_line = self.calculate_macd(
                historical_data,
                short_window=self.short_window,
                long_window=self.long_window,
                signal_window=self.signal_window
            )
            # Ensure we have valid latest and previous values using .iloc and np.nan check
            if macd_line.empty or signal_line.empty or macd_line.iloc[-1] is np.nan or signal_line.iloc[-1] is np.nan:
                 return {
                    'recommendation': 'WAIT',
                    'reasoning': f"MACD or Signal line calculation resulted in no valid latest value.",
                    'confidence': 0.0,
                    'timeframe': timeframe,
                    'trend_direction': 'N/A',
                    'risk_level': 'N/A',
                    'support': 'N/A',
                    'resistance': 'N/A'
                }

            latest_macd = macd_line.iloc[-1]
            latest_signal = signal_line.iloc[-1]
            # Safely get previous values, defaulting to latest if not enough data or NaN
            previous_macd = macd_line.iloc[-2] if len(macd_line) >= 2 and macd_line.iloc[-2] is not np.nan else latest_macd
            previous_signal = signal_line.iloc[-2] if len(signal_line) >= 2 and signal_line.iloc[-2] is not np.nan else latest_signal


        except ValueError as e:
             return {
                'recommendation': 'WAIT',
                'reasoning': f"Could not calculate MACD: {e}",
                'confidence': 0.0,
                'timeframe': timeframe,
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        recommendation = 'WAIT'
        reasoning = "No clear MACD signal."
        confidence = 0.5
        risk_level = 'Medium'
        trend_direction = 'Sideways'

        # Determine the signal based on MACD and Signal line crossovers and zero line crossovers
        # Bullish crossover: MACD crosses above Signal line
        # Comparisons work for both pandas and cuDF Series latest values
        if latest_macd > latest_signal and previous_macd <= previous_signal:
            recommendation = 'BUY'
            reasoning = f"Bullish MACD crossover: MACD ({latest_macd:.4f}) crossed above Signal ({latest_signal:.4f})."
            confidence = 0.7
            risk_level = 'Medium'
            if latest_macd > 0:
                 reasoning += " (Above Zero Line)"
                 confidence = 0.8
                 trend_direction = 'Uptrend'
            else:
                 reasoning += " (Below Zero Line - Potential Reversal)"
                 confidence = 0.6
                 trend_direction = 'Potential Uptrend (from Downtrend)'


        # Bearish crossover: MACD crosses below Signal line
        elif latest_macd < latest_signal and previous_macd >= previous_signal:
            recommendation = 'SELL'
            reasoning = f"Bearish MACD crossover: MACD ({latest_macd:.4f}) crossed below Signal ({latest_signal:.4f})."
            confidence = 0.7
            risk_level = 'Medium'
            if latest_macd < 0:
                 reasoning += " (Below Zero Line)"
                 confidence = 0.8
                 trend_direction = 'Downtrend'
            else:
                 reasoning += " (Above Zero Line - Potential Reversal)"
                 confidence = 0.6
                 trend_direction = 'Potential Downtrend (from Uptrend)'

        # No recent crossover, check position relative to zero line for momentum
        elif latest_macd > 0 and latest_signal > 0:
             recommendation = 'WAIT'
             reasoning = f"MACD ({latest_macd:.4f}) and Signal ({latest_signal:.4f}) are above zero, indicating bullish momentum."
             confidence = 0.6
             risk_level = 'Medium'
             trend_direction = 'Uptrend'

        elif latest_macd < 0 and latest_signal < 0:
             recommendation = 'WAIT'
             reasoning = f"MACD ({latest_macd:.4f}) and Signal ({latest_signal:.4f}) are below zero, indicating bearish momentum."
             confidence = 0.6
             risk_level = 'Medium'
             trend_direction = 'Downtrend'

        else:
             recommendation = 'WAIT'
             reasoning = f"MACD ({latest_macd:.4f}) and Signal ({latest_signal:.4f}) are near zero line or mixed, indicating sideways or uncertain momentum."
             confidence = 0.5
             risk_level = 'Low'
             trend_direction = 'Sideways'


        # Add MACD and Signal values to stock_data for reporting/visualization
        # The add_technical_indicator method in StockData handles type conversion if necessary
        macd_indicator_name = f'MACD_{self.short_window}_{self.long_window}_{self.signal_window}_{timeframe[0]}'
        signal_indicator_name = f'Signal_{self.short_window}_{self.long_window}_{self.signal_window}_{timeframe[0]}'

        stock_data.add_technical_indicator(macd_indicator_name, macd_line)
        stock_data.add_technical_indicator(signal_indicator_name, signal_line)

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
