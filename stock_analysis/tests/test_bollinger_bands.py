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

# Import the model class
from stock_analysis.trading_models.bollinger_bands import BollingerBandsModel
from stock_analysis.data_structures.stock_data import StockData

class TestBollingerBandsModel(unittest.TestCase):

    def setUp(self):
        # Create a dummy StockData object for testing
        # Need enough data for Bollinger Bands calculation (window=20)
        dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
        # Generate sample price data with some variance
        close_prices = np.linspace(100, 120, 200) + np.random.randn(200) * 2
        data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)
        self.stock_data = StockData(symbol='TEST_BB', historical_data=data)


        # Create data for a clear buy signal (price crossing above lower band)
        dates_buy_signal = pd.date_range(start='2023-01-01', periods=200, freq='D')
        # Prices mostly sideways, then drop significantly towards the end
        # This should push price below the lower band, then maybe a slight bounce back above
        prices_buy_signal = np.concatenate([
            np.linspace(100, 105, 150), # Sideways/slight uptrend
            np.linspace(105, 90, 50) + np.random.randn(50) * 0.5 # Sharp drop
        ])
        # To ensure a cross *above* the lower band at the very end, manually set the last price
        # Bollinger Bands window is 20. Let's calculate bands for the last few points to target the cross.
        data_buy_signal_temp = pd.DataFrame({'Close': prices_buy_signal}, index=dates_buy_signal)
        model_temp = BollingerBandsModel()
        _, _, lower_band_temp = model_temp.calculate_bollinger_bands(data_buy_signal_temp, window=20, num_std_dev=2)
        latest_lower_band = lower_band_temp.iloc[-1] if not lower_band_temp.empty and lower_band_temp.iloc[-1] is not np.nan else 95 # Default if calculation fails

        # Ensure the second to last price is below the band, and the last price is above or equal
        if len(prices_buy_signal) >= 2:
            prices_buy_signal[-2] = latest_lower_band - 1 # Ensure price was below band
            prices_buy_signal[-1] = latest_lower_band + 0.1 # Ensure price crosses above

        data_buy_signal = pd.DataFrame({'Close': prices_buy_signal, 'Open': prices_buy_signal*0.99, 'High': prices_buy_signal*1.01, 'Low': prices_buy_signal*0.98, 'Volume': 100000}, index=dates_buy_signal)
        self.stock_data_buy_signal = StockData(symbol='BUY_BB', historical_data=data_buy_signal)


        # Create data for a clear sell signal (price crossing below upper band)
        dates_sell_signal = pd.date_range(start='2023-01-01', periods=200, freq='D')
        # Prices mostly sideways, then rise significantly towards the end
        # This should push price above the upper band, then maybe a slight drop back below
        prices_sell_signal = np.concatenate([
            np.linspace(100, 105, 150), # Sideways/slight uptrend
            np.linspace(105, 120, 50) + np.random.randn(50) * 0.5 # Sharp rise
        ])
        # To ensure a cross *below* the upper band at the very end, manually set the last price
        data_sell_signal_temp = pd.DataFrame({'Close': prices_sell_signal}, index=dates_sell_signal)
        model_temp = BollingerBandsModel()
        _, upper_band_temp, _ = model_temp.calculate_bollinger_bands(data_sell_signal_temp, window=20, num_std_dev=2)
        latest_upper_band = upper_band_temp.iloc[-1] if not upper_band_temp.empty and upper_band_temp.iloc[-1] is not np.nan else 115 # Default if calculation fails

        # Ensure the second to last price is above the band, and the last price is below or equal
        if len(prices_sell_signal) >= 2:
            prices_sell_signal[-2] = latest_upper_band + 1 # Ensure price was above band
            prices_sell_signal[-1] = latest_upper_band - 0.1 # Ensure price crosses below


        data_sell_signal = pd.DataFrame({'Close': prices_sell_signal, 'Open': prices_sell_signal*0.99, 'High': prices_sell_signal*1.01, 'Low': prices_sell_signal*0.98, 'Volume': 100000}, index=dates_sell_signal)
        self.stock_data_sell_signal = StockData(symbol='SELL_BB', historical_data=data_sell_signal)


        # Create a minimal StockData object for insufficient data tests
        dates_insufficient = pd.date_range(start='2023-01-01', periods=10, freq='D') # Need more than 20 periods for BB
        close_prices_insufficient = np.linspace(100, 110, 10)
        data_insufficient = pd.DataFrame({'Close': close_prices_insufficient, 'Open': close_prices_insufficient, 'High': close_prices_insufficient, 'Low': close_prices_insufficient, 'Volume': 100000}, index=dates_insufficient)
        self.stock_data_insufficient = StockData(symbol='TEST_INSUFFICIENT_BB', historical_data=data_insufficient)

        # Create data with weekly frequency
        dates_weekly = pd.date_range(start='2023-01-01', periods=52, freq='W') # Need more than 20 periods for BB (52 > 20)
        close_prices_weekly = np.linspace(100, 130, 52) + np.random.randn(52) * 5
        data_weekly = pd.DataFrame({'Close': close_prices_weekly, 'Open': close_prices_weekly, 'High': close_prices_weekly, 'Low': close_prices_weekly, 'Volume': 100000}, index=dates_weekly)
        self.stock_data_weekly = StockData(symbol='TEST_WEEKLY_BB', historical_data=data_weekly)


    def test_analyze_stock_sufficient_data(self):
        # Test the analyze_stock method with sufficient data (general case)
        model = BollingerBandsModel()
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
            'Uptrend bias (within Bands)',
            'Downtrend bias (within Bands)',
            'Sideways (within Bands)',
            'Potential Uptrend (from Oversold)',
            'Potential Downtrend (from Overbought)',
            'Strong Uptrend (potentially overextended)',
            'Strong Downtrend (potentially overextended)',
            'Sideways' # Added 'Sideways' as a possibility
        ])
        self.assertIn(recommendation['risk_level'], ['Low', 'Medium', 'Medium-High', 'High']) # Assuming these are the possible risk levels


    def test_analyze_stock_insufficient_data(self):
        # Test the analyze_stock method with insufficient data
        model = BollingerBandsModel()
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
        # Test with data designed to produce a buy signal (price crosses above lower band)
        model = BollingerBandsModel()
        recommendation = model.analyze_stock(self.stock_data_buy_signal)

        self.assertIsInstance(recommendation, dict)
        # Expect BUY signal based on engineered data
        self.assertEqual(recommendation.get('recommendation'), 'BUY')
        self.assertIn('crossed above the Lower Bollinger Band', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily') # Assuming daily data frequency


    def test_analyze_stock_sell_signal(self):
        # Test with data designed to produce a sell signal (price crosses below upper band)
        model = BollingerBandsModel()
        recommendation = model.analyze_stock(self.stock_data_sell_signal)

        self.assertIsInstance(recommendation, dict)
        # Expect SELL signal based on engineered data
        self.assertEqual(recommendation.get('recommendation'), 'SELL')
        self.assertIn('crossed below the Upper Bollinger Band', recommendation.get('reasoning', ''))
        self.assertGreater(recommendation.get('confidence'), 0.5) # Expect higher confidence for a clear signal
        self.assertEqual(recommendation.get('timeframe'), 'Daily')

    def test_analyze_stock_weekly_data(self):
        # Test with weekly data
        model = BollingerBandsModel()
        recommendation = model.analyze_stock(self.stock_data_weekly)

        self.assertIsInstance(recommendation, dict)
        # The recommendation could be BUY, SELL, or WAIT depending on the random data
        self.assertIn(recommendation['recommendation'], ['BUY', 'SELL', 'WAIT'])
        self.assertEqual(recommendation.get('timeframe'), 'Weekly')


if __name__ == '__main__':
    unittest.main()
