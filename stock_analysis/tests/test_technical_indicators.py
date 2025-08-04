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
from stock_analysis.technical_indicators.indicator_calculator import IndicatorCalculator
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


class TestIndicatorCalculator(unittest.TestCase):

    def setUp(self):
        # Create a dummy DataFrame for testing (using pandas initially)
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        close_prices = pd.Series(np.arange(1, 51), index=dates) # Simple increasing sequence
        data = pd.DataFrame({'Close': close_prices})

        # Convert to the configured DataFrame type
        self.data = DataFrame(data)


    def test_calculate_sma(self):
        # Test SMA calculation
        calculator = IndicatorCalculator()
        # Calculate SMA with a window of 10
        sma_values = calculator.calculate_sma(self.data, window=10)

        self.assertIsInstance(sma_values, Series) # Should return the configured Series type
        self.assertEqual(len(sma_values), 50)
        # Check that the first 9 values are NaN
        self.assertTrue(np.all(np.isnan(sma_values.iloc[:9])))
        # Check a known SMA value (SMA of 1 to 10 is 5.5)
        # Need to convert to pandas for direct value comparison if using cuDF
        if USE_GPU_PANDAS:
             self.assertAlmostEqual(sma_values.iloc[9].copy_to_host(), 5.5)
             self.assertAlmostEqual(sma_values.iloc[10].copy_to_host(), 6.5) # SMA of 2 to 11 is 6.5
        else:
             self.assertAlmostEqual(sma_values.iloc[9], 5.5)
             self.assertAlmostEqual(sma_values.iloc[10], 6.5)

        # Test with a smaller window
        sma_values_small = calculator.calculate_sma(self.data, window=3)
        self.assertIsInstance(sma_values_small, Series)
        self.assertEqual(len(sma_values_small), 50)
        self.assertTrue(np.all(np.isnan(sma_values_small.iloc[:2])))
        # SMA of 1, 2, 3 is 2.0
        if USE_GPU_PANDAS:
             self.assertAlmostEqual(sma_values_small.iloc[2].copy_to_host(), 2.0)
        else:
             self.assertAlmostEqual(sma_values_small.iloc[2], 2.0)


    def test_calculate_sma_empty_data(self):
        # Test SMA calculation with empty data
        calculator = IndicatorCalculator()
        empty_data = DataFrame({'Close': []})
        sma_values = calculator.calculate_sma(empty_data, window=10)

        self.assertIsInstance(sma_values, Series)
        self.assertEqual(len(sma_values), 0)


    def test_calculate_sma_insufficient_data(self):
        # Test SMA calculation with insufficient data for the window
        calculator = IndicatorCalculator()
        small_data = DataFrame({'Close': [1, 2, 3]}) # Only 3 data points
        sma_values = calculator.calculate_sma(small_data, window=5)

        self.assertIsInstance(sma_values, Series)
        self.assertEqual(len(sma_values), 3)
        self.assertTrue(np.all(np.isnan(sma_values)))


    def test_calculate_sma_no_close_column(self):
        # Test that ValueError is raised if 'Close' column is missing
        calculator = IndicatorCalculator()
        data_no_close = DataFrame({'Open': [1, 2, 3]})
        with self.assertRaises(ValueError):
            calculator.calculate_sma(data_no_close, window=10)


if __name__ == '__main__':
    unittest.main()
