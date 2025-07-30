import pandas as pd
import numpy as np
from typing import List, Union, Dict, Any

# Assume StockData class is defined and imported from a previous cell/module
# Assume StockDataFetchError, InvalidSymbolError are defined

class IndicatorCalculationError(Exception):
    """Custom exception for errors during technical indicator calculation."""
    pass

class TechnicalIndicators:
    """
    Provides static methods for calculating common technical indicators on pandas Series.
    These methods are designed to be called by an IndicatorCalculator or directly
    on pandas Series data.
    """
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Calculates Simple Moving Average (SMA) on a pandas Series."""
        return data.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Calculates Exponential Moving Average (EMA) on a pandas Series."""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculates Relative Strength Index (RSI) on a pandas Series.

        Args:
            data: The pandas Series (typically 'close' prices) to calculate RSI on.
            period: The lookback period for the RSI calculation.

        Returns:
            A pandas Series containing the calculated RSI values.
        """
        delta: pd.Series = data.diff(1)
        gain: pd.Series = delta.where(delta > 0, 0)
        loss: pd.Series = -delta.where(delta < 0, 0)

        avg_gain: pd.Series = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss: pd.Series = loss.ewm(com=period - 1, adjust=False).mean()

        # Handle division by zero or cases where avg_loss is 0
        rs: pd.Series = avg_gain / avg_loss
        rsi: pd.Series = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """
        Calculates Moving Average Convergence Divergence (MACD) on a pandas Series.

        Args:
            data: The pandas Series (typically 'close' prices) to calculate MACD on.
            fast_period: The period for the fast EMA.
            slow_period: The period for the slow EMA.
            signal_period: The period for the signal line EMA of the MACD line.

        Returns:
            A pandas DataFrame containing the MACD line, Signal line, and Histogram.
        """
        ema_fast: pd.Series = TechnicalIndicators.calculate_ema(data, fast_period)
        ema_slow: pd.Series = TechnicalIndicators.calculate_ema(data, slow_period)

        macd_line: pd.Series = ema_fast - ema_slow
        signal_line: pd.Series = TechnicalIndicators.calculate_ema(macd_line, signal_period)
        histogram: pd.Series = macd_line - signal_line

        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        })

    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """
        Calculates Bollinger Bands on a pandas Series.

        Args:
            data: The pandas Series (typically 'close' prices) to calculate Bollinger Bands on.
            period: The period for the middle band (SMA).
            std_dev: The number of standard deviations for the upper and lower bands.

        Returns:
            A pandas DataFrame containing the upper band, middle band (SMA), and lower band.
        """
        middle_band: pd.Series = TechnicalIndicators.calculate_sma(data, period)
        # Calculate rolling standard deviation, handling potential NaNs
        rolling_std: pd.Series = data.rolling(window=period).std(ddof=0) # Use ddof=0 for population std dev, typical in BB

        upper_band: pd.Series = middle_band + (rolling_std * std_dev)
        lower_band: pd.Series = middle_band - (rolling_std * std_dev)

        return pd.DataFrame({
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        })

    @staticmethod
    def calculate_atr(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculates Average True Range (ATR) on pandas Series.

        Args:
            highs: Pandas Series of 'high' prices.
            lows: Pandas Series of 'low' prices.
            closes: Pandas Series of 'close' prices.
            period: The lookback period for the ATR calculation.

        Returns:
            A pandas Series containing the calculated ATR values.
        """
        # Calculate True Range (TR)
        tr1: pd.Series = highs - lows
        tr2: pd.Series = abs(highs - closes.shift(1))
        tr3: pd.Series = abs(lows - closes.shift(1))
        true_range: pd.Series = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR (EMA of TR)
        atr: pd.Series = true_range.ewm(com=period - 1, adjust=False).mean()
        return atr

    # ADX calculation is still complex and requires +DI/-DI, skipping for now as per previous analysis.
    # @staticmethod
    # def calculate_adx(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
    #     """Calculates Average Directional Index (ADX). Requires full implementation."""
    #     print("ADX calculation is not fully implemented.")
    #     return pd.Series([np.nan] * len(closes), index=closes.index)


class IndicatorCalculator:
    """
    Calculates and manages technical indicators for a StockData object.
    Stores calculated indicators as new columns in the StockData's DataFrame.
    Raises IndicatorCalculationError if calculation fails due to insufficient data.
    """
    def __init__(self, stock_data: StockData):
        """
        Initializes the IndicatorCalculator with a StockData object.

        Args:
            stock_data: An instance of the StockData class.

        Raises:
            ValueError: If an invalid or empty StockData object is provided.
        """
        if not isinstance(stock_data, StockData) or not stock_data.has_data():
            raise ValueError("Invalid or empty StockData object provided to IndicatorCalculator")
        self._stock_data: StockData = stock_data
        self._df: pd.DataFrame = stock_data.get_dataframe() # Get reference to the internal DataFrame

    def calculate_all_indicators(self):
        """
        Calculates all supported technical indicators and adds them as columns
        to the internal DataFrame of the associated StockData object.
        Raises IndicatorCalculationError if a required indicator calculation fails
        due to insufficient data or missing series.
        """
        closes: pd.Series = self._stock_data.closes
        highs: pd.Series = self._stock_data.highs
        lows: pd.Series = self._stock_data.lows
        volumes: pd.Series = self._stock_data.volumes
        num_data_points: int = self._stock_data.get_num_data_points()

        print(f"Calculating indicators for {num_data_points} data points...")

        # Define indicators and their minimum required data points
        indicators_to_calculate: Dict[str, tuple] = {
            'SMA_20': (TechnicalIndicators.calculate_sma, 20, [closes], False), # False means not strictly required for all models
            'SMA_50': (TechnicalIndicators.calculate_sma, 50, [closes], False),
            'SMA_200': (TechnicalIndicators.calculate_sma, 200, [closes], True), # MA Crossover might require this, make it required for calc
            'EMA_20': (TechnicalIndicators.calculate_ema, 20, [closes], False),
            'EMA_50': (TechnicalIndicators.calculate_ema, 50, [closes], False),
            'EMA_200': (TechnicalIndicators.calculate_ema, 200, [closes], False),
            'RSI_14': (TechnicalIndicators.calculate_rsi, 14, [closes], True), # Required by RSI model
            'MACD': (TechnicalIndicators.calculate_macd, 26 + 9 - 1, [closes], True), # Approx requirement for MACD (slow_period + signal_period - 1)
            'BollingerBands_20_2': (TechnicalIndicators.calculate_bollinger_bands, 20, [closes], True), # Required by BB model
            'ATR_14': (TechnicalIndicators.calculate_atr, 14, [highs, lows, closes], True), # Required for Risk Assessment
            # 'ADX_14': (TechnicalIndicators.calculate_adx, 14 * 2, [highs, lows, closes], False) # Skipping ADX
        }

        calculated_successfully: Dict[str, bool] = {}

        for indicator_name, (calc_func, min_periods, required_series, is_required) in indicators_to_calculate.items():
            # Check if sufficient data is available for this specific indicator
            has_required_series: bool = all(series is not None and not series.empty for series in required_series)
            sufficient_data: bool = num_data_points >= min_periods and has_required_series

            if sufficient_data:
                try:
                    # Pass the required Series to the calculation function
                    # Note: Some calc functions take 'period' as an explicit arg, some have defaults.
                    # Need to handle this dynamically or pass relevant args explicitly.
                    # For simplicity here, assuming min_periods is the relevant period arg for the function if needed.
                    # A more robust approach might pass args based on function signature or a config.
                    import inspect
                    sig = inspect.signature(calc_func)
                    func_args: List[pd.Series] = [s for s in required_series]
                    if 'period' in sig.parameters:
                         func_args.append(min_periods)
                    elif 'timeperiod' in sig.parameters: # For potential TA-Lib integration later
                         func_args.append(min_periods)

                    result: Union[pd.Series, pd.DataFrame] = calc_func(*func_args)

                    if isinstance(result, pd.Series):
                        self._df[indicator_name] = result
                        print(f" - Calculated {indicator_name}")
                        calculated_successfully[indicator_name] = True
                    elif isinstance(result, pd.DataFrame):
                        # For indicators returning multiple series (like MACD, BB)
                        for col in result.columns:
                            full_col_name: str = f'{indicator_name}_{col}'
                            self._df[full_col_name] = result[col]
                            calculated_successfully[full_col_name] = True # Mark each component as calculated
                        print(f" - Calculated {indicator_name} ({', '.join(result.columns)})")
                    else:
                         print(f" - Warning: Calculation for {indicator_name} returned unexpected type.")
                         if is_required:
                              raise IndicatorCalculationError(f"Calculation for required indicator {indicator_name} returned unexpected type.")


                except Exception as e:
                    error_msg: str = f"Error calculating {indicator_name}: {e}"
                    print(f" - {error_msg}")
                    if is_required:
                        # Raise error for required indicators
                        raise IndicatorCalculationError(error_msg) from e
                    else:
                        # For non-required indicators, add NaN columns and continue
                        try:
                            # Attempt dummy call to get col names/structure
                            dummy_series: pd.Series = pd.Series([1]*max(min_periods, 1), index=pd.to_datetime(range(max(min_periods, 1)), unit='s'))
                            dummy_required_series: List[pd.Series] = [dummy_series] * len(required_series)
                            dummy_args: List[Union[pd.Series, int]] = [s for s in dummy_required_series]
                            if 'period' in sig.parameters:
                                dummy_args.append(min_periods)
                            elif 'timeperiod' in sig.parameters:
                                dummy_args.append(min_periods)

                            dummy_result: Union[pd.Series, pd.DataFrame] = calc_func(*dummy_args)

                            if isinstance(dummy_result, pd.DataFrame):
                                for col in dummy_result.columns:
                                    self._df[f'{indicator_name}_{col}'] = np.nan
                            elif isinstance(dummy_result, pd.Series):
                                self._df[indicator_name] = np.nan
                            else:
                                self._df[indicator_name] = np.nan # Default to Series if structure unknown
                        except Exception:
                            # Fallback if dummy calculation fails
                            self._df[indicator_name] = np.nan # Just add one NaN column as a fallback

            else:
                skip_reason: str = f"Insufficient data ({num_data_points} available, {min_periods} required)" if has_required_series else "Missing required series"
                print(f" - Skipping {indicator_name}: {skip_reason}.")
                if is_required:
                    # Raise error for required indicators if skipped
                    raise IndicatorCalculationError(f"Skipping required indicator {indicator_name} due to {skip_reason}.")
                else:
                    # For non-required indicators, add NaN columns
                    try:
                        # Attempt a dummy calculation to see if it returns DataFrame or Series
                        dummy_series: pd.Series = pd.Series([1]*max(min_periods, 1), index=pd.to_datetime(range(max(min_periods, 1)), unit='s'))
                        dummy_required_series: List[pd.Series] = [dummy_series] * len(required_series)
                        dummy_args: List[Union[pd.Series, int]] = [s for s in dummy_required_series]
                        import inspect
                        sig = inspect.signature(calc_func)
                        if 'period' in sig.parameters:
                            dummy_args.append(min_periods)
                        elif 'timeperiod' in sig.parameters:
                            dummy_args.append(min_periods)


                        dummy_result: Union[pd.Series, pd.DataFrame] = calc_func(*dummy_args)

                        if isinstance(dummy_result, pd.DataFrame):
                             for col in dummy_result.columns:
                                self._df[f'{indicator_name}_{col}'] = np.nan
                        elif isinstance(dummy_result, pd.Series):
                             self._df[indicator_name] = np.nan
                        else:
                             self._df[indicator_name] = np.nan # Default to Series if structure unknown
                    except Exception:
                         # Fallback if dummy calculation fails
                         self._df[indicator_name] = np.nan


        print("Indicator calculation attempt complete. Check DataFrame for calculated columns.")


    def get_indicator_series(self, indicator_name: str) -> pd.Series:
        """Returns a specific indicator series from the DataFrame."""
        if indicator_name in self._df.columns:
            return self._df[indicator_name]
        else:
            # Changed to raise an error if a requested indicator is not found,
            # as models might rely on its existence.
            raise KeyError(f"Indicator series '{indicator_name}' not found in DataFrame. Calculation may have failed or been skipped.")


    def get_indicator_dataframe(self, indicator_name: str) -> pd.DataFrame:
        """Returns a DataFrame for indicators that have multiple components (like MACD, BB)."""
        cols: List[str] = [col for col in self._df.columns if col.startswith(indicator_name + '_')]
        if cols:
            return self._df[cols]
        else:
             # Changed to raise an error if a requested indicator DataFrame is not found.
             raise KeyError(f"Indicator DataFrame for '{indicator_name}' not found. Calculation may have failed or been skipped.")

    def get_all_indicators(self) -> pd.DataFrame:
        """Returns a DataFrame containing all calculated indicator columns."""
        # Return only columns that are NOT the original OHLCV data
        original_cols: List[str] = ['open', 'high', 'low', 'close', 'volume']
        indicator_cols: List[str] = [col for col in self._df.columns if col not in original_cols]
        return self._df[indicator_cols] 
