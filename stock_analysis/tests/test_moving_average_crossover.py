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
from stock_analysis.trading_models.moving_average_crossover import MovingAverageCrossoverModel
from stock_analysis.data_structures.stock_data import StockData
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


class TestMovingAverageCrossoverModel(unittest.TestCase):

    def setUp(self):
        # Create a dummy StockData object for testing
        # Need enough data for 200-period SMA
        dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
        # Generate sample price data with a general uptrend
        close_prices = np.linspace(100, 150, 250) + np.random.randn(250) * 5
        data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)
        self.stock_data = StockData(symbol='TEST_MAC', historical_data=data)


        # Create a minimal StockData object for insufficient data tests
        dates_insufficient = pd.date_range(start='2023-01-01', periods=150, freq='D') # Less than 200
        close_prices_insufficient = np.linspace(100, 110, 150)
        data_insufficient = pd.DataFrame({'Close': close_prices_insufficient, 'Open': close_prices_insufficient, 'High': close_prices_insufficient, 'Low': close_prices_insufficient, 'Volume': 100000}, index=dates_insufficient)
        self.stock_data_insufficient = StockData(symbol='TEST_INSUFFICIENT_MAC', historical_data=data_insufficient)

        # Create data with weekly frequency
        dates_weekly = pd.date_range(start='2023-01-01', periods=52, freq='W') # More than 50 for short MA
        close_prices_weekly = np.linspace(100, 130, 52) + np.random.randn(52) * 5
        data_weekly = pd.DataFrame({'Close': close_prices_weekly, 'Open': close_prices_weekly, 'High': close_prices_weekly, 'Low': close_prices_weekly, 'Volume': 100000}, index=dates_weekly)
        self.stock_data_weekly = StockData(symbol='TEST_WEEKLY_MAC', historical_data=data_weekly)


    def test_analyze_stock_sufficient_data(self):
        # Test the analyze_stock method with sufficient data (general case)
        model = MovingAverageCrossoverModel()
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
        # Update expected trend directions based on the model's logic
        self.assertIn(recommendation['trend_direction'], [
            'Uptrend',
            'Downtrend',
            'Sideways',
            'Consolidation (Uptrend bias)',
            'Consolidation (Downtrend bias)'
        ])
        self.assertIn(recommendation['risk_level'], ['Low', 'Medium']) # Update based on model logic


    def test_analyze_stock_insufficient_data(self):
        # Test the analyze_stock method with insufficient data
        model = MovingAverageCrossoverModel()
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
        # Test with data engineered to produce a buy signal
        # (Short MA crosses above Long MA and price is above Short MA)
        dates_buy = pd.date_range(start='2023-01-01', periods=300, freq='D')
        # Create data where price and short MA are initially below long MA, then cross above
        prices_buy = np.concatenate([
            np.linspace(100, 90, 200), # Downtrend
            np.linspace(90, 120, 100) # Strong Uptrend
        ])
        data_buy = pd.DataFrame({'Close': prices_buy, 'Open': prices_buy*0.99, 'High': prices_buy*1.01, 'Low': prices_buy*0.98, 'Volume': 100000}, index=dates_buy)
        stock_data_buy = StockData(symbol='BUY_MAC', historical_data=data_buy)

        model = MovingAverageCrossoverModel()
        recommendation = model.analyze_stock(stock_data_buy)

        self.assertIsInstance(recommendation, dict)
        # Check for BUY signal
        self.assertEqual(recommendation.get('recommendation'), 'BUY')
        self.assertIn('Short-term MA', recommendation.get('reasoning', ''))
        self.assertIn('above long-term MA', recommendation.get('reasoning', ''))
        self.assertIn('price is above short-term MA', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')


    def test_analyze_stock_sell_signal(self):
        # Test with data engineered to produce a sell signal
        # (Short MA crosses below Long MA and price is below Short MA)
        dates_sell = pd.date_range(start='2023-01-01', periods=300, freq='D')
        # Create data where price and short MA are initially above long MA, then cross below
        prices_sell = np.concatenate([
            np.linspace(100, 120, 200), # Uptrend
            np.linspace(120, 90, 100) # Strong Downtrend
        ])
        data_sell = pd.DataFrame({'Close': prices_sell, 'Open': prices_sell*0.99, 'High': prices_sell*1.01, 'Low': prices_sell*0.98, 'Volume': 100000}, index=dates_sell)
        stock_data_sell = StockData(symbol='SELL_MAC', historical_data=data_sell)

        model = MovingAverageCrossoverModel()
        recommendation = model.analyze_stock(stock_data_sell)

        self.assertIsInstance(recommendation, dict)
         # Check for SELL signal
        self.assertEqual(recommendation.get('recommendation'), 'SELL')
        self.assertIn('Short-term MA', recommendation.get('reasoning', ''))
        self.assertIn('below long-term MA', recommendation.get('reasoning', ''))
        self.assertIn('price is below short-term MA', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')

    def test_analyze_stock_weekly_data(self):
        # Test with weekly data
        model = MovingAverageCrossoverModel()
        recommendation = model.analyze_stock(self.stock_data_weekly)

        self.assertIsInstance(recommendation, dict)
        # The recommendation could be BUY, SELL, or WAIT depending on the random data
        self.assertIn(recommendation['recommendation'], ['BUY', 'SELL', 'WAIT'])
        self.assertEqual(recommendation.get('timeframe'), 'Weekly')


if __name__ == '__main__':
    unittest.main()
