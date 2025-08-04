import sys
import os
import warnings
from typing import Tuple, Optional, Dict, Any

# The following lines are removed because __file__ is not defined in notebooks
# # Add the project root to sys.path to allow importing modules
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# Import DataFrame and Series from the setup config
# Assumes stock_analysis is reachable via sys.path (e.g., added at notebook start)
try:
    from stock_analysis.setup.config import DataFrame, Series
except ImportError:
    # Fallback import if stock_analysis is not in sys.path
    # This might indicate an issue with notebook setup
    print("Warning: Could not import stock_analysis.setup.config directly. Ensure project root is in sys.path.")
    import pandas as pd
    DataFrame = pd.DataFrame
    Series = pd.Series


class IndicatorCalculator:
    """
    A class to calculate various technical indicators with adaptive window sizing
    for datasets with limited historical data.
    """

    # Default window configurations for different data lengths
    WINDOW_CONFIGS = {
        'short': {  # For datasets with 20-60 days
            'sma_short': 5,
            'sma_medium': 10,
            'sma_long': 20,
            'rsi': 14,
            'macd_fast': 8,
            'macd_slow': 17,
            'macd_signal': 9,
            'bb_period': 10,
            'bb_std': 2
        },
        'medium': {  # For datasets with 60-150 days
            'sma_short': 10,
            'sma_medium': 20,
            'sma_long': 50,
            'rsi': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2
        },
        'long': {  # For datasets with 150+ days
            'sma_short': 20,
            'sma_medium': 50,
            'sma_long': 200,
            'rsi': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2
        }
    }

    def __init__(self):
        """Initialize the IndicatorCalculator."""
        self._last_data_length = None
        self._current_config = None

    def _validate_data(self, data: DataFrame, required_columns: list = None) -> None:
        """
        Validate input data structure.

        Args:
            data: Input DataFrame
            required_columns: List of required column names

        Raises:
            ValueError: If data validation fails
        """
        if data is None or data.empty:
            raise ValueError("Data cannot be None or empty.")

        if required_columns is None:
            required_columns = ['Close']

        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")

    def _determine_data_regime(self, data_length: int) -> str:
        """
        Determine the appropriate parameter regime based on data length.

        Args:
            data_length: Number of data points available

        Returns:
            String indicating the regime ('short', 'medium', 'long')
        """
        if data_length < 60:
            return 'short'
        elif data_length < 150:
            return 'medium'
        else:
            return 'long'

    def _get_adaptive_window(self, data_length: int, requested_window: int,
                           indicator_type: str = 'sma_long') -> int:
        """
        Get an adaptive window size based on available data.

        Args:
            data_length: Available data points
            requested_window: Originally requested window size
            indicator_type: Type of indicator for fallback defaults

        Returns:
            Adjusted window size
        """
        regime = self._determine_data_regime(data_length)
        config = self.WINDOW_CONFIGS[regime]

        # If requested window is reasonable for the data length, use it
        if requested_window <= data_length * 0.3:  # Use max 30% of available data
            return requested_window

        # Otherwise, fall back to regime-appropriate defaults
        fallback_window = config.get(indicator_type, min(requested_window, data_length // 4))

        if fallback_window > data_length:
            fallback_window = max(2, data_length // 4)  # Minimum window of 2

        if fallback_window != requested_window:
            warnings.warn(
                f"Requested window {requested_window} too large for data length {data_length}. "
                f"Using adaptive window {fallback_window} instead.",
                UserWarning
            )

        return fallback_window

    def get_current_config(self, data_length: int) -> Dict[str, Any]:
        """
        Get the current configuration parameters based on data length.

        Args:
            data_length: Number of data points available

        Returns:
            Dictionary of current configuration parameters
        """
        regime = self._determine_data_regime(data_length)
        return self.WINDOW_CONFIGS[regime].copy()

    def calculate_sma(self, data: DataFrame, window: int = None,
                     adaptive: bool = True) -> Series:
        """
        Calculates the Simple Moving Average (SMA) for a given window.

        Args:
            data: pandas or cuDF DataFrame with a 'Close' column.
            window: The number of periods to include in the SMA calculation.
                   If None, uses adaptive default based on data length.
            adaptive: Whether to adapt window size to available data.

        Returns:
            A pandas or cuDF Series containing the SMA values.
        """
        self._validate_data(data, ['Close'])

        data_length = len(data)

        if window is None:
            # Use adaptive default
            regime = self._determine_data_regime(data_length)
            window = self.WINDOW_CONFIGS[regime]['sma_long']

        if adaptive:
            window = self._get_adaptive_window(data_length, window, 'sma_long')
        elif window > data_length:
            raise ValueError(f"Window size {window} exceeds data length {data_length}")

        return data['Close'].rolling(window=window, min_periods=1).mean()

    def calculate_rsi(self, data: DataFrame, window: int = None,
                     adaptive: bool = True) -> Series:
        """
        Calculate the Relative Strength Index (RSI).

        Args:
            data: DataFrame with 'Close' column
            window: Period for RSI calculation (default: adaptive based on data length)
            adaptive: Whether to adapt window size to available data

        Returns:
            Series containing RSI values
        """
        self._validate_data(data, ['Close'])

        data_length = len(data)

        if window is None:
            regime = self._determine_data_regime(data_length)
            window = self.WINDOW_CONFIGS[regime]['rsi']

        if adaptive:
            window = self._get_adaptive_window(data_length, window, 'rsi')
        elif window > data_length:
            raise ValueError(f"Window size {window} exceeds data length {data_length}")

        # Calculate price changes
        delta = data['Close'].diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=window, min_periods=1).mean()
        avg_losses = losses.rolling(window=window, min_periods=1).mean()

        # Calculate RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(self, data: DataFrame, fast_window: int = None,
                      slow_window: int = None, signal_window: int = None,
                      adaptive: bool = True) -> Tuple[Series, Series, Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: DataFrame with 'Close' column
            fast_window: Fast EMA period
            slow_window: Slow EMA period
            signal_window: Signal line EMA period
            adaptive: Whether to adapt window sizes to available data

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        self._validate_data(data, ['Close'])

        data_length = len(data)
        regime = self._determine_data_regime(data_length)
        config = self.WINDOW_CONFIGS[regime]

        if fast_window is None:
            fast_window = config['macd_fast']
        if slow_window is None:
            slow_window = config['macd_slow'] # Fixed: Should be macd_slow
        if signal_window is None:
            signal_window = config['macd_signal']

        if adaptive:
            fast_window = self._get_adaptive_window(data_length, fast_window, 'macd_fast')
            slow_window = self._get_adaptive_window(data_length, slow_window, 'macd_slow')
            signal_window = self._get_adaptive_window(data_length, signal_window, 'macd_signal')

        # Ensure fast < slow
        if fast_window >= slow_window:
            fast_window = max(1, slow_window - 1)

        # Calculate EMAs
        ema_fast = data['Close'].ewm(span=fast_window, min_periods=1).mean()
        ema_slow = data['Close'].ewm(span=slow_window, min_periods=1).mean()

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_window, min_periods=1).mean()

        # Calculate histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def calculate_bollinger_bands(self, data: DataFrame, window: int = None,
                                 num_std: float = None, adaptive: bool = True) -> Tuple[Series, Series, Series]:
        """
        Calculate Bollinger Bands.

        Args:
            data: DataFrame with 'Close' column
            window: Period for moving average and standard deviation
            num_std: Number of standard deviations for bands
            adaptive: Whether to adapt window size to available data

        Returns:
            Tuple of (Upper Band, Middle Band/SMA, Lower Band)
        """
        self._validate_data(data, ['Close'])

        data_length = len(data)
        regime = self._determine_data_regime(data_length)
        config = self.WINDOW_CONFIGS[regime]

        if window is None:
            window = config['bb_period']
        if num_std is None:
            num_std = config['bb_std']

        if adaptive:
            window = self._get_adaptive_window(data_length, window, 'bb_period')

        # Calculate middle band (SMA)
        middle_band = data['Close'].rolling(window=window, min_periods=1).mean()

        # Calculate standard deviation
        std_dev = data['Close'].rolling(window=window, min_periods=1).std()

        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * num_std)
        lower_band = middle_band - (std_dev * num_std)

        return upper_band, middle_band, lower_band

    def get_data_summary(self, data: DataFrame) -> Dict[str, Any]:
        """
        Get a summary of the data and recommended parameters.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary containing data summary and recommendations
        """
        self._validate_data(data)

        data_length = len(data)
        regime = self._determine_data_regime(data_length)
        config = self.WINDOW_CONFIGS[regime]

        return {
            'data_length': data_length,
            'regime': regime,
            'recommended_config': config,
            'data_start': data.index[0] if hasattr(data.index, '__getitem__') else 'N/A',
            'data_end': data.index[-1] if hasattr(data.index, '__getitem__') else 'N/A'
        }
