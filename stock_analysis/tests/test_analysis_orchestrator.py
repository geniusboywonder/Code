import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
import os

# Add the project root to sys.path to allow importing modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_analysis.analysis_orchestration.analysis_orchestrator import AnalysisOrchestrator
from stock_analysis.data_structures.stock_data import StockData
# Import the actual trading models to be used by the orchestrator test
from stock_analysis.trading_models.moving_average_crossover import MovingAverageCrossoverModel
from stock_analysis.trading_models.rsi_mean_reversion import RsiMeanReversionModel
from stock_analysis.trading_models.macd_momentum import MacdMomentumModel
from stock_analysis.trading_models.bollinger_bands import BollingerBandsModel


class TestAnalysisOrchestrator(unittest.TestCase):

    def setUp(self):
        # Create dummy historical data for testing
        dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
        close_prices = np.linspace(100, 150, 300) + np.random.randn(300) * 2
        self.dummy_data = pd.DataFrame({'Close': close_prices, 'Open': close_prices*0.99, 'High': close_prices*1.01, 'Low': close_prices*0.98, 'Volume': 100000}, index=dates)

        # Create a mock StockData object with the symbol expected by the test
        self.mock_stock_data = StockData(symbol='TEST')
        self.mock_stock_data.add_historical_data(self.dummy_data)

    @patch('stock_analysis.analysis_orchestration.analysis_orchestrator.get_stock_data')
    def test_run_analysis_success(self, mock_get_stock_data):
        # Configure the mock to return our mock StockData object
        mock_get_stock_data.return_value = self.mock_stock_data

        orchestrator = AnalysisOrchestrator()
        # Reduce the number of models for faster testing
        orchestrator.models = [
            MovingAverageCrossoverModel(),
            RsiMeanReversionModel(),
            # Include others if needed, but 2 is sufficient to test the loop
            # MacdMomentumModel(),
            # BollingerBandsModel()
            ]


        stock_data = orchestrator.run_analysis('TEST', '2023-01-01', '2023-12-31')

        self.assertIsNotNone(stock_data)
        self.assertIsInstance(stock_data, StockData)
        self.assertEqual(stock_data.symbol, 'TEST') # Should now pass as mock object has symbol 'TEST'
        self.assertFalse(stock_data.get_historical_data().empty)

        # Check if models added recommendations + Consensus
        recommendations = stock_data.get_trading_recommendations()
        # Expect recommendations from the models run + Consensus
        self.assertGreater(len(recommendations), 0)
        self.assertIn('Consensus', recommendations)
        # Check if model names are in recommendations (based on the reduced list)
        for model in orchestrator.models:
            self.assertIn(model.__class__.__name__, recommendations)

    @patch('stock_analysis.analysis_orchestration.analysis_orchestrator.get_stock_data')
    def test_run_analysis_data_fetch_failure(self, mock_get_stock_data):
        # Configure the mock to return None, simulating data fetch failure
        mock_get_stock_data.return_value = None

        orchestrator = AnalysisOrchestrator()
        stock_data = orchestrator.run_analysis('FAIL_TEST', '2023-01-01', '2023-12-31')

        self.assertIsNone(stock_data)


    def test_get_consensus_recommendation(self):
        orchestrator = AnalysisOrchestrator()
        stock_data_with_recs = StockData(symbol='CONSENSUS_TEST')

        # Test case 1: No model recommendations
        stock_data_no_recs = StockData(symbol='NO_RECS')
        orchestrator.get_consensus_recommendation(stock_data_no_recs)
        recs_no_recs = stock_data_no_recs.get_trading_recommendations()
        self.assertIn('Consensus', recs_no_recs)
        self.assertEqual(recs_no_recs['Consensus']['recommendation'], 'WAIT')
        self.assertIn('No model recommendations', recs_no_recs['Consensus']['reasoning'])
        self.assertEqual(recs_no_recs['Consensus']['confidence'], 0.0)


        # Test case 2: Clear BUY majority
        stock_data_buy_majority = StockData(symbol='BUY_MAJORITY')
        stock_data_buy_majority.add_trading_recommendation('ModelA', {'recommendation': 'BUY', 'confidence': 0.8})
        stock_data_buy_majority.add_trading_recommendation('ModelB', {'recommendation': 'BUY', 'confidence': 0.7})
        stock_data_buy_majority.add_trading_recommendation('ModelC', {'recommendation': 'WAIT', 'confidence': 0.5})
        stock_data_buy_majority.add_trading_recommendation('ModelD', {'recommendation': 'SELL', 'confidence': 0.6})
        orchestrator.get_consensus_recommendation(stock_data_buy_majority)
        recs_buy_majority = stock_data_buy_majority.get_trading_recommendations()
        self.assertIn('Consensus', recs_buy_majority)
        self.assertEqual(recs_buy_majority['Consensus']['recommendation'], 'BUY')
        self.assertIn('models recommend BUY', recs_buy_majority['Consensus']['reasoning'])
        # Check confidence calculation (average of BUY confidences: (0.8 + 0.7)/2 = 0.75)
        self.assertAlmostEqual(recs_buy_majority['Consensus']['confidence'], round((0.8 + 0.7) / 2, 4))


        # Test case 3: Clear SELL majority
        stock_data_sell_majority = StockData(symbol='SELL_MAJORITY')
        stock_data_sell_majority.add_trading_recommendation('ModelA', {'recommendation': 'SELL', 'confidence': 0.9})
        stock_data_sell_majority.add_trading_recommendation('ModelB', {'recommendation': 'SELL', 'confidence': 0.8})
        stock_data_sell_majority.add_trading_recommendation('ModelC', {'recommendation': 'BUY', 'confidence': 0.4})
        stock_data_sell_majority.add_trading_recommendation('ModelD', {'recommendation': 'WAIT', 'confidence': 0.5})
        orchestrator.get_consensus_recommendation(stock_data_sell_majority)
        recs_sell_majority = stock_data_sell_majority.get_trading_recommendations()
        self.assertIn('Consensus', recs_sell_majority)
        self.assertEqual(recs_sell_majority['Consensus']['recommendation'], 'SELL')
        self.assertIn('models recommend SELL', recs_sell_majority['Consensus']['reasoning'])
         # Check confidence calculation (average of SELL confidences: (0.9 + 0.8)/2 = 0.85)
        self.assertAlmostEqual(recs_sell_majority['Consensus']['confidence'], round((0.9 + 0.8) / 2, 4))

        # Test case 4: Mixed recommendations (WAIT)
        stock_data_mixed = StockData(symbol='MIXED_RECS')
        stock_data_mixed.add_trading_recommendation('ModelA', {'recommendation': 'BUY', 'confidence': 0.7})
        stock_data_mixed.add_trading_recommendation('ModelB', {'recommendation': 'SELL', 'confidence': 0.6})
        stock_data_mixed.add_trading_recommendation('ModelC', {'recommendation': 'WAIT', 'confidence': 0.5})
        stock_data_mixed.add_trading_recommendation('ModelD', {'recommendation': 'BUY', 'confidence': 0.8}) # Another BUY
        stock_data_mixed.add_trading_recommendation('ModelE', {'recommendation': 'SELL', 'confidence': 0.7}) # Another SELL
        orchestrator.get_consensus_recommendation(stock_data_mixed)
        recs_mixed = stock_data_mixed.get_trading_recommendations()
        self.assertIn('Consensus', recs_mixed)
        self.assertEqual(recs_mixed['Consensus']['recommendation'], 'WAIT')
        # Corrected expected reasoning string based on orchestrator's output
        self.assertEqual(recs_mixed['Consensus']['reasoning'], 'Mixed signals: BUY(2), SELL(2), WAIT(1). No clear majority.')
        # Check confidence calculation (max(2, 2, 1)/5 = 0.4)
        self.assertAlmostEqual(recs_mixed['Consensus']['confidence'], round(max(2, 2, 1) / 5, 4))

        # Test case 5: All WAIT
        stock_data_all_wait = StockData(symbol='ALL_WAIT')
        stock_data_all_wait.add_trading_recommendation('ModelA', {'recommendation': 'WAIT', 'confidence': 0.5})
        stock_data_all_wait.add_trading_recommendation('ModelB', {'recommendation': 'WAIT', 'confidence': 0.6})
        orchestrator.get_consensus_recommendation(stock_data_all_wait)
        recs_all_wait = stock_data_all_wait.get_trading_recommendations()
        self.assertIn('Consensus', recs_all_wait)
        self.assertEqual(recs_all_wait['Consensus']['recommendation'], 'WAIT')
        self.assertIn('Mixed signals', recs_all_wait['Consensus']['reasoning'])
         # Check confidence calculation (max(0, 0, 2)/2 = 1.0) - logic uses max count / total
        self.assertAlmostEqual(recs_all_wait['Consensus']['confidence'], round(max(0, 0, 2) / 2, 4))

    # Add test for model execution failure within run_analysis
    @patch('stock_analysis.analysis_orchestration.analysis_orchestrator.get_stock_data')
    def test_run_analysis_model_failure(self, mock_get_stock_data):
        mock_get_stock_data.return_value = self.mock_stock_data

        # Mock a model's analyze_stock method to raise an exception
        class FaultyModel:
            def analyze_stock(self, stock_data):
                raise Exception("Simulated Model Error")
            def __class__(self): # Mock __class__ for model_name
                return type('FaultyModel', (object,), {})

        orchestrator = AnalysisOrchestrator()
        orchestrator.models = [FaultyModel()] # Use the faulty model

        stock_data = orchestrator.run_analysis('TEST_MODEL_FAIL', '2023-01-01', '2023-12-31')

        self.assertIsNotNone(stock_data)
        recs = stock_data.get_trading_recommendations()
        self.assertIn('FaultyModel', recs)
        self.assertEqual(recs['FaultyModel']['recommendation'], 'WAIT')
        self.assertIn('Model execution failed', recs['FaultyModel']['reasoning'])
        self.assertEqual(recs['FaultyModel']['confidence'], 0.0)
        self.assertIn('Consensus', recs) # Consensus should still be calculated


if __name__ == '__main__':
    unittest.main()
