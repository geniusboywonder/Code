import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

# Add the project root to sys.path to allow importing modules
import sys
import os
# Assuming the test file is in stock_analysis/tests/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to be tested and configured types
from stock_analysis.data_fetching.get_stock_data import get_stock_data
from stock_analysis.data_structures.stock_data import StockData
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


class TestDataFetching(unittest.TestCase):

    @patch('stock_analysis.data_fetching.get_stock_data.yf.Ticker')
    def test_get_stock_data_success_daily(self, mock_ticker):
        # Configure the mock Ticker and its history method for sufficient daily data
        mock_history = MagicMock()
        # Create a dummy pandas DataFrame with enough daily data
        dates = pd.date_range(end='2024-07-31', periods=250, freq='D')
        dummy_data = pd.DataFrame({'Close': range(250)}, index=dates)
        mock_history.return_value = dummy_data
        mock_ticker.return_value.history = mock_history

        # Call the function
        stock_data = get_stock_data('TEST', '2024-07-31')

        # Assertions
        self.assertIsNotNone(stock_data)
        self.assertIsInstance(stock_data, StockData)
        self.assertEqual(stock_data.symbol, 'TEST')
        historical_data = stock_data.get_historical_data()
        self.assertIsInstance(historical_data, DataFrame) # Should be the configured type
        self.assertEqual(len(historical_data), 250)
        # Verify history was called with expected arguments for daily data
        mock_ticker.assert_called_once_with('TEST')
        # Check if the date range passed to history is correct (approx. 280 days back)
        mock_history.assert_called_once()
        call_args, call_kwargs = mock_history.call_args
        self.assertIn('start', call_kwargs)
        self.assertIn('end', call_kwargs)
        self.assertEqual(call_kwargs['end'], '2024-07-31')
        # Check that the interval is the default ('1d')
        self.assertNotIn('interval', call_kwargs) # Default interval is '1d' if not specified


    @patch('stock_analysis.data_fetching.get_stock_data.yf.Ticker')
    def test_get_stock_data_insufficient_daily_fallback_weekly_success(self, mock_ticker):
        # Configure the mock Ticker and its history method for insufficient daily data
        mock_history_daily = MagicMock()
        # Create a dummy pandas DataFrame with insufficient daily data
        dates_daily = pd.date_range(end='2024-07-31', periods=150, freq='D') # Less than 200
        dummy_data_daily = pd.DataFrame({'Close': range(150)}, index=dates_daily)
        mock_history_daily.return_value = dummy_data_daily

        # Configure the mock history for weekly data (should be called after daily fails)
        mock_history_weekly = MagicMock()
        # Create a dummy pandas DataFrame with sufficient weekly data
        dates_weekly = pd.date_range(end='2024-07-31', periods=50, freq='W') # More than 40
        dummy_data_weekly = pd.DataFrame({'Close': range(50)}, index=dates_weekly)
        mock_history_weekly.return_value = dummy_data_weekly

        # Set up side_effect to return daily data first, then weekly on the second call
        mock_ticker.return_value.history.side_effect = [mock_history_daily.return_value, mock_history_weekly.return_value]

        # Call the function
        stock_data = get_stock_data('TEST_WEEKLY', '2024-07-31')

        # Assertions
        self.assertIsNotNone(stock_data)
        self.assertIsInstance(stock_data, StockData)
        self.assertEqual(stock_data.symbol, 'TEST_WEEKLY')
        historical_data = stock_data.get_historical_data()
        self.assertIsInstance(historical_data, DataFrame) # Should be the configured type
        self.assertEqual(len(historical_data), 50) # Should have weekly data

        # Verify history was called twice: once for daily, once for weekly
        self.assertEqual(mock_ticker.return_value.history.call_count, 2)

        # Check the arguments for the daily call
        daily_call_kwargs = mock_ticker.return_value.history.call_args_list[0][1]
        self.assertIn('start', daily_call_kwargs)
        self.assertIn('end', daily_call_kwargs)
        self.assertEqual(daily_call_kwargs['end'], '2024-07-31')
        self.assertNotIn('interval', daily_call_kwargs) # Default interval is '1d'

        # Check the arguments for the weekly call
        weekly_call_kwargs = mock_ticker.return_value.history.call_args_list[1][1]
        self.assertIn('start', weekly_call_kwargs)
        self.assertIn('end', weekly_call_kwargs)
        self.assertEqual(weekly_call_kwargs['end'], '2024-07-31')
        self.assertEqual(weekly_call_kwargs['interval'], '1wk')

        # Verify that the StockData object has a note about using weekly data
        self.assertIn("weekly interval", stock_data.note)


    @patch('stock_analysis.data_fetching.get_stock_data.yf.Ticker')
    def test_get_stock_data_empty_data(self, mock_ticker):
        # Configure the mock Ticker and its history method to return empty DataFrames
        mock_history = MagicMock()
        mock_history.return_value = pd.DataFrame() # Empty pandas DataFrame
        mock_ticker.return_value.history = mock_history

        # Set up side_effect to return empty data for both daily and weekly attempts
        mock_ticker.return_value.history.side_effect = [pd.DataFrame(), pd.DataFrame()]


        # Call the function
        stock_data = get_stock_data('EMPTY', '2024-07-31')

        # Assertions
        self.assertIsNone(stock_data) # Should return None if data fetching fails

        # Verify history was called twice (daily and weekly attempts)
        self.assertEqual(mock_ticker.return_value.history.call_count, 2)


    @patch('stock_analysis.data_fetching.get_stock_data.yf.Ticker')
    def test_get_stock_data_exception(self, mock_ticker):
        # Configure the mock Ticker and its history method to raise an exception
        mock_history = MagicMock()
        mock_history.side_effect = Exception("Simulated fetch error")
        mock_ticker.return_value.history = mock_history

        # Call the function
        stock_data = get_stock_data('ERROR', '2024-07-31')

        # Assertions
        self.assertIsNone(stock_data) # Should return None on exception

        # Verify history was called (at least once)
        mock_ticker.return_value.history.assert_called()


if __name__ == '__main__':
    unittest.main()
