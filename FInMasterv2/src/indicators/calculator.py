import pandas as pd
from .technical import TechnicalIndicators
from .base import IndicatorCalculationError

class IndicatorCalculator:
    def __init__(self, stock_data):
        if not stock_data or not stock_data.has_data():
            raise ValueError("Invalid or empty StockData object provided to IndicatorCalculator")
        self._stock_data = stock_data
        self._df = stock_data.get_dataframe()

    def calculate_all_indicators(self):
        closes = self._stock_data.closes
        highs = self._stock_data.highs
        lows = self._stock_data.lows
        num_data_points = self._stock_data.get_num_data_points()

        indicators = {
            'SMA_20': TechnicalIndicators.calculate_sma(closes, 20),
            'EMA_20': TechnicalIndicators.calculate_ema(closes, 20),
            'RSI_14': TechnicalIndicators.calculate_rsi(closes, 14),
            'MACD': TechnicalIndicators.calculate_macd(closes),
            'BollingerBands_20_2': TechnicalIndicators.calculate_bollinger_bands(closes),
            'ATR_14': TechnicalIndicators.calculate_atr(highs, lows, closes, 14)
        }

        for name, result in indicators.items():
            if isinstance(result, pd.Series):
                self._df[name] = result
            elif isinstance(result, pd.DataFrame):
                for col in result.columns:
                    self._df[f"{name}_{col}"] = result[col]
            else:
                raise IndicatorCalculationError(f"Unexpected result type for {name}")
