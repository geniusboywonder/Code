import unittest
import pandas as pd
import numpy as np

# Add the project root to sys.path to allow importing modules
import sys
import os
# Assuming the test file is in stock_analysis/tests/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the module to be tested and configured types
from stock_analysis.data_structures.stock_data import StockData
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


class TestStockData(unittest.TestCase):

    def setUp(self):
        # Setup any necessary test data or objects
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        # Create a pandas DataFrame initially
        self.pandas_data = pd.DataFrame({'Close': np.random.rand(100)}, index=dates)

        # Create a StockData instance with initial data
        self.stock_data = StockData(symbol='TEST')
        self.stock_data.add_historical_data(self.pandas_data) # This should handle internal conversion

    def test_add_historical_data(self):
        # Test adding historical data and verify the type
        historical_data = self.stock_data.get_historical_data()
        self.assertIsInstance(historical_data, DataFrame)
        self.assertEqual(len(historical_data), 100)
        self.assertTrue('Close' in historical_data.columns)
        self.assertIsInstance(historical_data.index, pd.DatetimeIndex) # Index should be pandas DatetimeIndex


    def test_add_technical_indicator_scalar(self):
        # Test adding a scalar technical indicator
        indicator_name = 'SMA_50_Latest'
        indicator_value = 105.5
        self.stock_data.add_technical_indicator(indicator_name, indicator_value)
        indicators = self.stock_data.get_technical_indicators()
        self.assertIn(indicator_name, indicators)
        self.assertEqual(indicators[indicator_name], indicator_value)
        # Ensure the type remains standard Python or numpy scalar
        self.assertNotIsInstance(indicators[indicator_name], Series)


    def test_add_technical_indicator_series(self):
        # Test adding a Series technical indicator
        indicator_name = 'RSI_14'
        # Create a dummy Series (initially pandas)
        dummy_rsi_series = pd.Series(np.random.rand(100) * 100, index=self.pandas_data.index)
        self.stock_data.add_technical_indicator(indicator_name, dummy_rsi_series)

        indicators = self.stock_data.get_technical_indicators()
        self.assertIn(indicator_name, indicators)
        # Verify the type is the configured Series type
        self.assertIsInstance(indicators[indicator_name], Series)
        self.assertEqual(len(indicators[indicator_name]), 100)
        self.assertTrue(np.allclose(indicators[indicator_name].to_pandas(), dummy_rsi_series)) # Compare values after converting back to pandas


    def test_add_trading_recommendation(self):
        # Test adding a trading recommendation
        model_name = 'TestModel'
        recommendation = {
            'recommendation': 'BUY',
            'reasoning': 'Test reason',
            'confidence': 0.9
        }
        self.stock_data.add_trading_recommendation(model_name, recommendation)
        recommendations = self.stock_data.get_trading_recommendations()
        self.assertIn(model_name, recommendations)
        self.assertEqual(recommendations[model_name], recommendation)
        # Ensure the recommendation data remains a standard dictionary
        self.assertIsInstance(recommendations[model_name], dict)


    def test_get_methods(self):
        # Test the getter methods
        self.assertIsInstance(self.stock_data.get_historical_data(), DataFrame)
        self.assertIsInstance(self.stock_data.get_technical_indicators(), dict)
        self.assertIsInstance(self.stock_data.get_trading_recommendations(), dict)
        self.assertEqual(self.stock_data.symbol, 'TEST')

    def test_initialization_with_data(self):
        # Test initializing StockData directly with a DataFrame
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        data = pd.DataFrame({'Close': np.random.rand(50)}, index=dates)
        # Convert to configured DataFrame type for initialization
        initial_df = DataFrame(data)
        stock_data_init = StockData(symbol='INIT_TEST', historical_data=initial_df)
        self.assertIsInstance(stock_data_init.get_historical_data(), DataFrame)
        self.assertEqual(stock_data_init.symbol, 'INIT_TEST')
        self.assertEqual(len(stock_data_init.get_historical_data()), 50)
        self.assertDictEqual(stock_data_init.get_technical_indicators(), {})
        self.assertDictEqual(stock_data_init.get_trading_recommendations(), {})


if __name__ == '__main__':
    unittest.main()
