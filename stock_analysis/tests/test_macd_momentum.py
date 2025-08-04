import unittest
import pandas as pd
import numpy as np

# Add the project root to sys.path to allow importing modules
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the module to be tested and configured types
from stock_analysis.trading_models.macd_momentum import MacdMomentumModel
from stock_analysis.data_structures.stock_data import StockData
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS

class TestMacdMomentumModel(unittest.TestCase):

    def setUp(self):
        # Create a dummy StockData object for testing
        # Need enough data for MACD (12, 26, 9) -> 26 + 9 - 1 = 34 data points minimum
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        # Generate sample price data
        close_prices = np.linspace(100, 110, 100) + np.random.randn(100) * 2
        data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)
        self.stock_data = StockData(symbol='TEST_MACD', historical_data=data)

        # Create data for a clear bullish crossover signal (MACD crosses above Signal)
        dates_bullish = pd.date_range(start='2023-01-01', periods=50, freq='D')
        # Prices engineered to create a bullish crossover towards the end
        prices_bullish = np.concatenate([
            np.linspace(100, 105, 30), # Sideways/slight uptrend
            np.linspace(105, 115, 20) # Stronger uptrend to induce crossover
        ])
        data_bullish = pd.DataFrame({'Close': prices_bullish, 'Open': prices_bullish*0.99, 'High': prices_bullish*1.01, 'Low': prices_bullish*0.98, 'Volume': 100000}, index=dates_bullish)
        self.stock_data_bullish = StockData(symbol='BULLISH_MACD', historical_data=data_bullish)


        # Create data for a clear bearish crossover signal (MACD crosses below Signal)
        dates_bearish = pd.date_range(start='2023-01-01', periods=50, freq='D')
        # Prices engineered to create a bearish crossover towards the end
        prices_bearish = np.concatenate([
            np.linspace(110, 105, 30), # Sideways/slight downtrend
            np.linspace(105, 95, 20) # Stronger downtrend to induce crossover
        ])
        data_bearish = pd.DataFrame({'Close': prices_bearish, 'Open': prices_bearish*0.99, 'High': prices_bearish*1.01, 'Low': prices_bearish*0.98, 'Volume': 100000}, index=dates_bearish)
        self.stock_data_bearish = StockData(symbol='BEARISH_MACD', historical_data=data_bearish)


        # Create data for a clear bullish momentum signal (MACD and Signal > 0)
        dates_bullish_momentum = pd.date_range(start='2023-01-01', periods=60, freq='D')
        # Prices engineered to keep MACD and Signal above zero
        prices_bullish_momentum = np.linspace(100, 130, 60) # Consistent Uptrend
        data_bullish_momentum = pd.DataFrame({'Close': prices_bullish_momentum, 'Open': prices_bullish_momentum*0.99, 'High': prices_bullish_momentum*1.01, 'Low': prices_bullish_momentum*0.98, 'Volume': 100000}, index=dates_bullish_momentum)
        self.stock_data_bullish_momentum = StockData(symbol='BULLISH_MOMENTUM_MACD', historical_data=data_bullish_momentum)

        # Create data for a clear bearish momentum signal (MACD and Signal < 0)
        dates_bearish_momentum = pd.date_range(start='2023-01-01', periods=60, freq='D')
        # Prices engineered to keep MACD and Signal below zero
        prices_bearish_momentum = np.linspace(130, 100, 60) # Consistent Downtrend
        data_bearish_momentum = pd.DataFrame({'Close': prices_bearish_momentum, 'Open': prices_bearish_momentum*0.99, 'High': prices_bearish_momentum*1.01, 'Low': prices_bearish_momentum*0.98, 'Volume': 100000}, index=dates_bearish_momentum)
        self.stock_data_bearish_momentum = StockData(symbol='BEARISH_MOMENTUM_MACD', historical_data=data_bearish_momentum)


        # Create a minimal StockData object for insufficient data tests
        dates_insufficient = pd.date_range(start='2023-01-01', periods=30, freq='D') # Less than 34
        close_prices_insufficient = np.linspace(100, 110, 30)
        data_insufficient = pd.DataFrame({'Close': close_prices_insufficient, 'Open': close_prices_insufficient, 'High': close_prices_insufficient, 'Low': close_prices_insufficient, 'Volume': 100000}, index=dates_insufficient)
        self.stock_data_insufficient = StockData(symbol='TEST_INSUFFICIENT_MACD', historical_data=data_insufficient)

        # Create data with weekly frequency
        dates_weekly = pd.date_range(start='2023-01-01', periods=40, freq='W') # More than 34 periods for MACD
        close_prices_weekly = np.linspace(100, 130, 40) + np.random.randn(40) * 5
        data_weekly = pd.DataFrame({'Close': close_prices_weekly, 'Open': close_prices_weekly, 'High': close_prices_weekly, 'Low': close_prices_weekly, 'Volume': 100000}, index=dates_weekly)
        self.stock_data_weekly = StockData(symbol='TEST_WEEKLY_MACD', historical_data=data_weekly)


    def test_calculate_macd_sufficient_data(self):
        # Test the calculate_macd method with sufficient data
        model = MacdMomentumModel()
        macd_line, signal_line = model.calculate_macd(self.stock_data.get_historical_data(), short_window=12, long_window=26, signal_window=9)

        self.assertIsInstance(macd_line, Series) # Should return the configured Series type
        self.assertIsInstance(signal_line, Series) # Should return the configured Series type
        self.assertEqual(len(macd_line), 100)
        self.assertEqual(len(signal_line), 100)
        # The first `long_window + signal_window - 1` (34) values of signal_line should be NaN
        self.assertTrue(np.isnan(signal_line.iloc[33]))
        self.assertFalse(np.isnan(signal_line.iloc[34]))


    def test_calculate_macd_insufficient_data(self):
        # Test the calculate_macd method with insufficient data
        model = MacdMomentumModel()
        macd_line, signal_line = model.calculate_macd(self.stock_data_insufficient.get_historical_data(), short_window=12, long_window=26, signal_window=9)

        self.assertIsInstance(macd_line, Series) # Should return the configured Series type
        self.assertIsInstance(signal_line, Series) # Should return the configured Series type
        self.assertEqual(len(macd_line), 30)
        self.assertEqual(len(signal_line), 30)
        # All values should be NaN due to insufficient data
        self.assertTrue(np.all(np.isnan(macd_line)))
        self.assertTrue(np.all(np.isnan(signal_line)))

    def test_analyze_stock_sufficient_data(self):
        # Test the analyze_stock method with sufficient data (general case)
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data)

        self.assertIsInstance(recommendation, dict)
        self.assertIn('recommendation', recommendation)
        self.assertIn('reasoning', recommendation)
        self.assertIn('confidence', recommendation)
        self.assertIn('timeframe', recommendation)
        self.assertIn('trend_direction', recommendation)
        self.assertIn('risk_level', recommendation)
        self.assertIn('support', recommendation)
        self.assertIn('resistance', recommendation)

        self.assertIn(recommendation['recommendation'], ['BUY', 'SELL', 'WAIT'])
        self.assertGreaterEqual(recommendation['confidence'], 0.0)
        self.assertLessEqual(recommendation['confidence'], 1.0)
        self.assertIn(recommendation['timeframe'], ['Daily', 'Weekly'])
        self.assertIn(recommendation['trend_direction'], [
             'Sideways',
             'Uptrend',
             'Downtrend',
             'Potential Uptrend (from Downtrend)',
             'Potential Downtrend (from Uptrend)'
        ])
        self.assertIn(recommendation['risk_level'], ['Low', 'Medium']) # Update based on model logic


    def test_analyze_stock_insufficient_data(self):
        # Test the analyze_stock method with insufficient data
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_insufficient)

        self.assertIsInstance(recommendation, dict)
        self.assertEqual(recommendation.get('recommendation'), 'WAIT')
        self.assertIn('Insufficient data', recommendation.get('reasoning', ''))
        self.assertEqual(recommendation.get('confidence'), 0.0)
        self.assertEqual(recommendation.get('timeframe'), 'N/A')
        self.assertEqual(recommendation.get('trend_direction'), 'N/A')
        self.assertEqual(recommendation.get('risk_level'), 'N/A')
        self.assertEqual(recommendation.get('support'), 'N/A')
        self.assertEqual(recommendation.get('resistance'), 'N/A')


    def test_analyze_stock_bullish_crossover(self):
        # Test with data designed to produce a bullish crossover (MACD crosses above Signal)
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_bullish)

        self.assertIsInstance(recommendation, dict)
        # Check for BUY signal
        self.assertEqual(recommendation.get('recommendation'), 'BUY')
        self.assertIn('Bullish MACD crossover', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')

    def test_analyze_stock_bearish_crossover(self):
        # Test with data designed to produce a bearish crossover (MACD crosses below Signal)
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_bearish)

        self.assertIsInstance(recommendation, dict)
         # Check for SELL signal
        self.assertEqual(recommendation.get('recommendation'), 'SELL')
        self.assertIn('Bearish MACD crossover', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')

    def test_analyze_stock_bullish_momentum(self):
        # Test with data designed to produce bullish momentum (MACD and Signal > 0)
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_bullish_momentum)

        self.assertIsInstance(recommendation, dict)
        self.assertEqual(recommendation.get('recommendation'), 'WAIT')
        self.assertIn('above zero, indicating bullish momentum', recommendation.get('reasoning', ''))
        self.assertGreaterEqual(recommendation.get('confidence'), 0.5) # Expect at least neutral confidence, potentially higher
        self.assertEqual(recommendation.get('timeframe'), 'Daily')
        self.assertEqual(recommendation.get('trend_direction'), 'Uptrend')


    def test_analyze_stock_bearish_momentum(self):
        # Test with data designed to produce bearish momentum (MACD and Signal < 0)
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_bearish_momentum)

        self.assertIsInstance(recommendation, dict)
        self.assertEqual(recommendation.get('recommendation'), 'WAIT')
        self.assertIn('below zero, indicating bearish momentum', recommendation.get('reasoning', ''))
        self.assertGreaterEqual(recommendation.get('confidence'), 0.5) # Expect at least neutral confidence, potentially higher
        self.assertEqual(recommendation.get('timeframe'), 'Daily')
        self.assertEqual(recommendation.get('trend_direction'), 'Downtrend')


    def test_analyze_stock_weekly_data(self):
        # Test with weekly data
        model = MacdMomentumModel()
        recommendation = model.analyze_stock(self.stock_data_weekly)

        self.assertIsInstance(recommendation, dict)
        # The recommendation could be BUY, SELL, or WAIT depending on the data
        self.assertIn(recommendation['recommendation'], ['BUY', 'SELL', 'WAIT'])
        self.assertEqual(recommendation.get('timeframe'), 'Weekly')


if __name__ == '__main__':
    unittest.main()
