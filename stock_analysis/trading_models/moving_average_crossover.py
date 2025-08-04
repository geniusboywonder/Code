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


from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS

from ..technical_indicators.indicator_calculator import IndicatorCalculator
from ..data_structures.stock_data import StockData

class MovingAverageCrossoverModel:
    """
    Trading model based on the crossover of short-term and long-term moving averages.
    Uses DataFrame and Series types from setup.config.
    """

    def __init__(self, short_window: int = 50, long_window: int = 200):
        self.indicator_calculator = IndicatorCalculator()
        self.short_window = short_window  # e.g., 50-day or 50-week SMA
        self.long_window = long_window  # e.g., 200-day or 200-week SMA
        self.required_data_points = self.long_window

    def analyze_stock(self, stock_data: StockData) -> dict:
        """
        Analyzes stock data using the Moving Average Crossover strategy.

        Args:
            stock_data: The StockData object containing historical data.

        Returns:
            A dictionary containing the analysis recommendation and details.
        """
        historical_data = stock_data.get_historical_data()

        if historical_data.empty or len(historical_data) < self.required_data_points:
            return {
                'recommendation': 'WAIT',
                'reasoning': f"Insufficient data ({len(historical_data)} data points) for {self.long_window}-period SMA. Need at least {self.required_data_points}.",
                'confidence': 0.0,
                'timeframe': 'N/A',
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        # Determine timeframe based on data frequency
        # Access the index and calculate time differences using the configured Series type
        time_diffs = historical_data.index.to_series().diff().dropna()
        avg_time_diff = time_diffs.mean()

        # Use pd.Timedelta for comparison as cuDF time differences are also handled by pandas TimeDelta logic
        timeframe = 'Weekly' if avg_time_diff > pd.Timedelta(days=1) else 'Daily'


        # Calculate SMAs using the IndicatorCalculator, which uses configured types
        try:
            short_sma = self.indicator_calculator.calculate_sma(historical_data, window=self.short_window)
            long_sma = self.indicator_calculator.calculate_sma(historical_data, window=self.long_window)
        except ValueError as e:
             return {
                'recommendation': 'WAIT',
                'reasoning': f"Could not calculate SMAs: {e}",
                'confidence': 0.0,
                'timeframe': timeframe,
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        # Ensure latest SMA values are not NaN before using them
        if short_sma.empty or long_sma.empty or short_sma.iloc[-1] is np.nan or long_sma.iloc[-1] is np.nan:
             return {
                'recommendation': 'WAIT',
                'reasoning': f"SMA calculation resulted in NaN values at the end.",
                'confidence': 0.0,
                'timeframe': timeframe,
                'trend_direction': 'N/A',
                'risk_level': 'N/A',
                'support': 'N/A',
                'resistance': 'N/A'
            }

        latest_short_sma = short_sma.iloc[-1]
        latest_long_sma = long_sma.iloc[-1]
        latest_close = historical_data['Close'].iloc[-1]


        recommendation = 'WAIT'
        reasoning = "No clear signal."
        trend_direction = 'Sideways'
        confidence = 0.5
        risk_level = 'Medium' # Default risk level

        # Determine the signal based on crossover and current price relative to MAs
        # Comparisons like > and < work for both pandas and cuDF Series latest values
        if latest_short_sma > latest_long_sma and latest_close > latest_short_sma:
            recommendation = 'BUY'
            reasoning = f"Short-term MA ({self.short_window}) is above long-term MA ({self.long_window}), and price is above short-term MA. Potential uptrend."
            trend_direction = 'Uptrend'
            confidence = 0.7
            risk_level = 'Low'
        elif latest_short_sma < latest_long_sma and latest_close < latest_short_sma:
            recommendation = 'SELL'
            reasoning = f"Short-term MA ({self.short_window}) is below long-term MA ({self.long_window}), and price is below short-term MA. Potential downtrend."
            trend_direction = 'Downtrend'
            confidence = 0.7
            risk_level = 'Low'
        elif latest_short_sma > latest_long_sma:
             recommendation = 'WAIT'
             reasoning = f"Short-term MA ({self.short_window}) is above long-term MA ({self.long_window}), but price is below short-term MA. Waiting for confirmation."
             trend_direction = 'Consolidation (Uptrend bias)'
             confidence = 0.4
             risk_level = 'Medium'
        elif latest_short_sma < latest_long_sma:
             recommendation = 'WAIT'
             reasoning = f"Short-term MA ({self.short_window}) is below long-term MA ({self.long_window}), but price is above short-term MA. Waiting for confirmation."
             trend_direction = 'Consolidation (Downtrend bias)'
             confidence = 0.4
             risk_level = 'Medium'
        else:
             recommendation = 'WAIT'
             reasoning = "Short-term and long-term MAs are close, indicating potential sideways movement or indecision."
             trend_direction = 'Sideways'
             confidence = 0.5
             risk_level = 'Medium'

        # Add SMA values to stock_data for reporting/visualization
        # The add_technical_indicator method in StockData handles type conversion if necessary
        stock_data.add_technical_indicator(f'SMA_{self.short_window}_{timeframe[0]}', short_sma)
        stock_data.add_technical_indicator(f'SMA_{self.long_window}_{timeframe[0]}', long_sma)

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
