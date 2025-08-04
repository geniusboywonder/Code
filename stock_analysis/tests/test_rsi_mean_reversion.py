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
from stock_analysis.trading_models.rsi_mean_reversion import RsiMeanReversionModel
from stock_analysis.data_structures.stock_data import StockData
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


class TestRsiMeanReversionModel(unittest.TestCase):

    def setUp(self):
        # Create a dummy StockData object for testing
        # Need enough data for RSI calculation (window=14)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        # Generate sample price data with some variance
        close_prices = np.linspace(100, 110, 100) + np.random.randn(100) * 2
        data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)
        self.stock_data = StockData(symbol='TEST_RSI', historical_data=data)


        # Create data for a clear buy signal (RSI < 30)
        dates_buy_signal = pd.date_range(start='2023-01-01', periods=50, freq='D')
        # Prices drop significantly at the end to create oversold RSI
        prices_buy_signal = np.concatenate([
            np.linspace(100, 105, 40), # Sideways/slight uptrend
            np.linspace(105, 90, 10) # Sharp drop
        ])
        data_buy_signal = pd.DataFrame({'Close': prices_buy_signal, 'Open': prices_buy_signal*0.99, 'High': prices_buy_signal*1.01, 'Low': prices_buy_signal*0.98, 'Volume': 100000}, index=dates_buy_signal)
        self.stock_data_buy_signal = StockData(symbol='BUY_RSI', historical_data=data_buy_signal)


        # Create data for a clear sell signal (RSI > 70)
        dates_sell_signal = pd.date_range(start='2023-01-01', periods=50, freq='D')
        # Prices rise significantly at the end to create overbought RSI
        prices_sell_signal = np.concatenate([
            np.linspace(100, 105, 40), # Sideways/slight uptrend
            np.linspace(105, 120, 10) # Sharp rise
        ])
        data_sell_signal = pd.DataFrame({'Close': prices_sell_signal, 'Open': prices_sell_signal*0.99, 'High': prices_sell_signal*1.01, 'Low': prices_sell_signal*0.98, 'Volume': 100000}, index=dates_sell_signal)
        self.stock_data_sell_signal = StockData(symbol='SELL_RSI', historical_data=data_sell_signal)


        # Create a minimal StockData object for insufficient data tests
        dates_insufficient = pd.date_range(start='2023-01-01', periods=10, freq='D') # Need more than 14 periods for RSI
        close_prices_insufficient = np.linspace(100, 110, 10)
        data_insufficient = pd.DataFrame({'Close': close_prices_insufficient, 'Open': close_prices_insufficient, 'High': close_prices_insufficient, 'Low': close_prices_insufficient, 'Volume': 100000}, index=dates_insufficient)
        self.stock_data_insufficient = StockData(symbol='TEST_INSUFFICIENT_RSI', historical_data=data_insufficient)

        # Create data with weekly frequency
        dates_weekly = pd.date_range(start='2023-01-01', periods=30, freq='W') # More than 14 periods for RSI
        close_prices_weekly = np.linspace(100, 130, 30) + np.random.randn(30) * 5
        data_weekly = pd.DataFrame({'Close': close_prices_weekly, 'Open': close_prices_weekly, 'High': close_prices_weekly, 'Low': close_prices_weekly, 'Volume': 100000}, index=dates_weekly)
        self.stock_data_weekly = StockData(symbol='TEST_WEEKLY_RSI', historical_data=data_weekly)



    def test_calculate_rsi_sufficient_data(self):
        # Test the calculate_rsi method with sufficient data
        model = RsiMeanReversionModel()
        rsi_values = model.calculate_rsi(self.stock_data.get_historical_data(), window=14)

        self.assertIsInstance(rsi_values, Series) # Should return the configured Series type
        self.assertEqual(len(rsi_values), 100)
        # The first `window` (14) values should be NaN, and the 15th should be a number
        self.assertTrue(np.isnan(rsi_values.iloc[13]))
        self.assertFalse(np.isnan(rsi_values.iloc[14]))


    def test_calculate_rsi_insufficient_data(self):
        # Test the calculate_rsi method with insufficient data
        model = RsiMeanReversionModel()
        rsi_values = model.calculate_rsi(self.stock_data_insufficient.get_historical_data(), window=14)

        self.assertIsInstance(rsi_values, Series) # Should return the configured Series type
        self.assertEqual(len(rsi_values), 10)
        # All values should be NaN due to insufficient data
        self.assertTrue(np.all(np.isnan(rsi_values)))

    def test_analyze_stock_sufficient_data(self):
        # Test the analyze_stock method with sufficient data (general case)
        model = RsiMeanReversionModel()
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
            'Potential Uptrend (from Oversold)',
            'Potential Downtrend (from Overbought)'
        ])
        self.assertIn(recommendation['risk_level'], ['Low', 'Medium', 'Medium-High']) # Update based on model logic


    def test_analyze_stock_insufficient_data(self):
        # Test the analyze_stock method with insufficient data
        model = RsiMeanReversionModel()
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

    def test_analyze_stock_buy_signal(self):
        # Test with data designed to produce a buy signal (RSI < 30)
        model = RsiMeanReversionModel()
        recommendation = model.analyze_stock(self.stock_data_buy_signal)

        self.assertIsInstance(recommendation, dict)
        # Check for BUY signal
        self.assertEqual(recommendation.get('recommendation'), 'BUY')
        self.assertIn('below the buy threshold', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')


    def test_analyze_stock_sell_signal(self):
        # Test with data designed to produce a sell signal (RSI > 70)
        model = RsiMeanReversionModel()
        recommendation = model.analyze_stock(self.stock_data_sell_signal)

        self.assertIsInstance(recommendation, dict)
         # Check for SELL signal
        self.assertEqual(recommendation.get('recommendation'), 'SELL')
        self.assertIn('above the sell threshold', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')

    def test_analyze_stock_weekly_data(self):
        # Test with weekly data
        model = RsiMeanReversionModel()
        recommendation = model.analyze_stock(self.stock_data_weekly)

        self.assertIsInstance(recommendation, dict)
        # The recommendation could be BUY, SELL, or WAIT depending on the random data
        self.assertIn(recommendation['recommendation'], ['BUY', 'SELL', 'WAIT'])
        self.assertEqual(recommendation.get('timeframe'), 'Weekly')


if __name__ == '__main__':
    unittest.main()
