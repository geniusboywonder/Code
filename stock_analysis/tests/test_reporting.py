import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the project root to sys.path to allow importing modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_analysis.reporting.report_generator import generate_analysis_report, generate_portfolio_summary_table
from stock_analysis.data_structures.stock_data import StockData
# Import DataFrame, Series from setup.config if needed for creating mock data
# from stock_analysis.setup.config import DataFrame, Series, pd_module

class TestReporting(unittest.TestCase):

    def setUp(self):
        # Create a mock StockData object with sample data, indicators, and recommendations
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        close_prices = np.linspace(100, 110, 50)
        mock_historical_data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)

        self.mock_stock_data = StockData(symbol='TEST_REPORT')
        self.mock_stock_data.add_historical_data(mock_historical_data) # StockData handles potential conversion

        # Add some mock technical indicators (scalar and Series)
        self.mock_stock_data.add_technical_indicator('Latest_Close', mock_historical_data['Close'].iloc[-1])
        self.mock_stock_data.add_technical_indicator('Volume_Avg_50D', mock_historical_data['Volume'].rolling(window=50).mean().iloc[-1])
        # Add a mock Series indicator (SMA_20)
        mock_sma_20 = mock_historical_data['Close'].rolling(window=20).mean()
        self.mock_stock_data.add_technical_indicator('SMA_20_D', mock_sma_20)


        # Add some mock trading recommendations
        self.mock_stock_data.add_trading_recommendation('MovingAverageCrossoverModel', {
            'recommendation': 'BUY',
            'reasoning': 'Short MA above Long MA.',
            'confidence': 0.75,
            'timeframe': 'Daily',
            'trend_direction': 'Uptrend',
            'risk_level': 'Low',
            'support': '105.0',
            'resistance': '115.0'
        })
        self.mock_stock_data.add_trading_recommendation('RsiMeanReversionModel', {
            'recommendation': 'WAIT',
            'reasoning': 'RSI in neutral zone.',
            'confidence': 0.5,
            'timeframe': 'Daily',
            'trend_direction': 'Sideways',
            'risk_level': 'Medium',
            'support': 'N/A',
            'resistance': 'N/A'
        })
        self.mock_stock_data.add_trading_recommendation('BollingerBandsModel', {
            'recommendation': 'SELL',
            'reasoning': 'Price touched upper band.',
            'confidence': 0.6,
            'timeframe': 'Weekly',
            'trend_direction': 'Potential Downtrend (from Overbought)',
            'risk_level': 'Medium-High',
            'support': 'N/A',
            'resistance': 'N/A'
        })

        # Add a mock Consensus recommendation
        self.mock_stock_data.add_trading_recommendation('Consensus', {
            'recommendation': 'WAIT',
            'reasoning': 'Mixed signals.',
            'confidence': 0.6,
            'timeframe': 'Aggregate',
            'trend_direction': 'N/A',
            'risk_level': 'N/A',
            'support': 'N/A',
            'resistance': 'N/A' # Placeholder fields
        })


        # Create a list of mock StockData objects for portfolio summary testing
        self.list_of_mock_stock_data = [
            self.mock_stock_data,
            StockData(symbol='AAPL'), # Add another mock StockData
            StockData(symbol='MSFT')  # Add a third mock StockData
        ]
        # Add dummy recommendations to the other mock stocks
        self.list_of_mock_stock_data[1].add_trading_recommendation('Consensus', {'recommendation': 'BUY', 'confidence': 0.8})
        self.list_of_mock_stock_data[2].add_trading_recommendation('Consensus', {'recommendation': 'SELL', 'confidence': 0.7})


    def test_generate_analysis_report(self):
        # Test the generate_analysis_report function
        report = generate_analysis_report(self.mock_stock_data)

        self.assertIsInstance(report, str)
        self.assertIn("--- Analysis Report for TEST_REPORT ---", report)
        self.assertIn("Technical Indicators:", report)
        self.assertIn("Individual Model Summary Table:", report)
        self.assertIn("Consensus Recommendation:", report)

        # Check for presence of model names and recommendations
        self.assertIn("MovingAverageCrossoverModel", report)
        self.assertIn("RsiMeanReversionModel", report)
        self.assertIn("BollingerBandsModel", report)
        self.assertIn("BUY", report)
        self.assertIn("WAIT", report)
        self.assertIn("SELL", report)

        # Check for presence of detailed fields in the individual model table
        self.assertIn("Timeframe", report)
        self.assertIn("Trend Direction", report)
        self.assertIn("Risk Level", report)
        self.assertIn("Support", report)
        self.assertIn("Resistance", report)
        self.assertIn("Key Reasoning", report)

        # Check for presence of Consensus details
        self.assertIn("Consensus Signal", report)
        self.assertIn("Confidence", report)
        self.assertIn("Mixed signals.", report) # Check for reasoning in consensus


    def test_generate_portfolio_summary_table(self):
        # Test the generate_portfolio_summary_table function
        summary_table = generate_portfolio_summary_table(self.list_of_mock_stock_data)

        self.assertIsInstance(summary_table, str)
        self.assertIn("Symbol", summary_table)
        self.assertIn("Signal", summary_table)
        self.assertIn("Confidence", summary_table)
        self.assertIn("Risk", summary_table) # Check for placeholder columns
        self.assertIn("Action", summary_table)
        self.assertIn("Notes", summary_table) # Check for placeholder columns

        # Check for presence of symbols and consensus signals
        self.assertIn("TEST_REPORT", summary_table)
        self.assertIn("AAPL", summary_table)
        self.assertIn("MSFT", summary_table)
        self.assertIn("WAIT", summary_table)
        self.assertIn("BUY", summary_table)
        self.assertIn("SELL", summary_table)


if __name__ == '__main__':
    unittest.main()
