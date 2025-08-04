import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

# Add the project root to sys.path to allow importing modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to be tested
from stock_analysis.health_check.api_checker import check_yahoo_finance_api

class TestHealthCheck(unittest.TestCase):

    @patch('stock_analysis.health_check.api_checker.yf.Ticker')
    def test_check_yahoo_finance_api_success(self, mock_ticker):
        # Configure the mock Ticker object and its history method
        mock_history = MagicMock()
        # Make history() return a non-empty DataFrame
        mock_history.return_value = pd.DataFrame({'Close': [100, 101]})
        mock_ticker.return_value.history = mock_history

        # Call the health check function
        is_healthy = check_yahoo_finance_api()

        # Assert that Ticker and history were called
        mock_ticker.assert_called_once_with('AAPL')
        mock_history.assert_called_once_with(period='1d')
        # Assert that the function returned True
        self.assertTrue(is_healthy)

    @patch('stock_analysis.health_check.api_checker.yf.Ticker')
    def test_check_yahoo_finance_api_empty_data(self, mock_ticker):
        # Configure the mock Ticker object and its history method
        mock_history = MagicMock()
        # Make history() return an empty DataFrame
        mock_history.return_value = pd.DataFrame()
        mock_ticker.return_value.history = mock_history

        # Set up side_effect to return empty data for both daily and weekly attempts
        mock_ticker.return_value.history.side_effect = [pd.DataFrame(), pd.DataFrame()]


        # Call the function
        is_healthy = check_yahoo_finance_api()

        # Assert that Ticker and history were called
        mock_ticker.assert_called_once_with('AAPL')
        mock_history.assert_called_once_with(period='1d')
        # Assert that the function returned False (as empty data indicates a potential issue)
        self.assertFalse(is_healthy)

    @patch('stock_analysis.health_check.api_checker.yf.Ticker')
    def test_check_yahoo_finance_api_exception(self, mock_ticker):
        # Configure the mock Ticker object and its history method to raise an exception
        mock_history = MagicMock()
        mock_history.side_effect = Exception("Simulated API error")
        mock_ticker.return_value.history = mock_history

        # Call the function
        is_healthy = check_yahoo_finance_api()

        # Assertions
        self.assertFalse(is_healthy) # Should return False on exception


if __name__ == '__main__':
    unittest.main()
