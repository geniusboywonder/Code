import sys
import os
# pandas is kept for potential type checks if not using cuDF, but primarily use imported types
import pandas as pd
from tqdm.auto import tqdm

# Add the project root to sys.path to allow importing modules
# This is needed to import modules from the stock_analysis package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import DataFrame, Series, pd_module, and USE_GPU_PANDAS from the setup config
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


from stock_analysis.data_fetching.get_stock_data import get_stock_data
from stock_analysis.technical_indicators.indicator_calculator import IndicatorCalculator
from stock_analysis.trading_models.moving_average_crossover import MovingAverageCrossoverModel
from stock_analysis.trading_models.rsi_mean_reversion import RsiMeanReversionModel
from stock_analysis.trading_models.macd_momentum import MacdMomentumModel
from stock_analysis.trading_models.bollinger_bands import BollingerBandsModel

class AnalysisOrchestrator:
    """
    Orchestrates the stock analysis process and provides a consensus recommendation.
    Uses DataFrame and Series types from setup.config.
    """
    def __init__(self):
        self.indicator_calculator = IndicatorCalculator()
        self.models = [
            MovingAverageCrossoverModel(),
            RsiMeanReversionModel(),
            MacdMomentumModel(),
            BollingerBandsModel()
        ]

    def run_analysis(self, symbol: str, start_date: str, end_date: str):
        """
        Runs the complete analysis for a given stock symbol and date range.

        Args:
            symbol: The stock symbol.
            start_date: The start date for data fetching (Note: get_stock_data determines actual start, can be None).
            end_date: The end date for data fetching (defaults to yesterday if None).

        Returns:
            A StockData object with historical data (as configured DataFrame),
            indicators, and model recommendations, or None if data fetching fails.
        """
        # get_stock_data now returns the configured DataFrame type and handles default end_date
        stock_data = get_stock_data(symbol, end_date)

        if stock_data is None:
            return None

        print("Running Trading Models...")
        # The models themselves handle data of the configured type (DataFrame/Series)
        for model in tqdm(self.models, desc=f"Analyzing {symbol}"):
            model_name = model.__class__.__name__
            try:
                recommendation = model.analyze_stock(stock_data)
                stock_data.add_trading_recommendation(model_name, recommendation)
            except Exception as e:
                print(f"Error running model {model_name} for {symbol}: {e}")
                # Add a default 'WAIT' recommendation if a model fails
                stock_data.add_trading_recommendation(
                    model_name,
                    {
                        'recommendation': 'WAIT',
                        'reasoning': f'Model execution failed: {e}',
                        'confidence': 0.0,
                        'timeframe': 'Error',
                        'trend_direction': 'N/A',
                        'risk_level': 'High',
                        'support': 'N/A',
                        'resistance': 'N/A'
                    }
                )

        # The get_consensus_recommendation method works with the dictionary structure
        # within the StockData object, which contains standard Python types for recommendations.
        self.get_consensus_recommendation(stock_data)

        return stock_data

    def get_consensus_recommendation(self, stock_data):
        """
        Aggregates recommendations from different models to provide a consensus.
        This method operates on the recommendation dictionary within StockData,
        which contains standard Python types (strings, floats, dicts).
        """
        recommendations = stock_data.get_trading_recommendations()
        # Filter out the existing 'Consensus' recommendation if recalculating
        model_recommendations = {k: v for k, v in recommendations.items() if k != 'Consensus'}

        if not model_recommendations:
            stock_data.add_trading_recommendation('Consensus', {'recommendation': 'WAIT', 'reasoning': 'No model recommendations available.', 'confidence': 0.0})
            return

        buy_count = 0
        sell_count = 0
        wait_count = 0
        total_confidence_buy = 0.0
        total_confidence_sell = 0.0

        for rec in model_recommendations.values():
            # Accessing dictionary values which are standard Python types
            rec_type = rec.get('recommendation')
            confidence = rec.get('confidence', 0.0) # Default confidence to 0.0 if missing

            if rec_type == 'BUY':
                buy_count += 1
                total_confidence_buy += confidence
            elif rec_type == 'SELL':
                sell_count += 1
                total_confidence_sell += confidence
            else:
                wait_count += 1

        total_models = len(model_recommendations)

        # Determine consensus based on counts and average confidence
        if total_models == 0: # Handle case where model_recommendations was filtered to empty
             consensus_rec = 'WAIT'
             reasoning = 'No valid model recommendations available after filtering.'
             confidence = 0.0
        elif buy_count > sell_count and buy_count > wait_count:
            consensus_rec = 'BUY'
            reasoning = f"Majority ({buy_count}/{total_models}) models recommend BUY."
            confidence = total_confidence_buy / buy_count if buy_count > 0 else 0.0
        elif sell_count > buy_count and sell_count > wait_count:
            consensus_rec = 'SELL'
            reasoning = f"Majority ({sell_count}/{total_models}) models recommend SELL."
            confidence = total_confidence_sell / sell_count if sell_count > 0 else 0.0
        else:
            consensus_rec = 'WAIT'
            reasoning = f"Mixed signals: BUY({buy_count}), SELL({sell_count}), WAIT({wait_count}). No clear majority."
            # For WAIT consensus, confidence could be the proportion of the majority, or average confidence of the dominant signal if any
            # Using proportion of the largest count for simplicity in mixed case
            confidence = max(buy_count, sell_count, wait_count) / total_models


        # Add or update the 'Consensus' recommendation
        stock_data.add_trading_recommendation('Consensus', {
            'recommendation': consensus_rec,
            'reasoning': reasoning,
            'confidence': round(confidence, 4), # Round confidence for cleaner display
            'timeframe': 'Aggregate', # Consensus is over potentially mixed timeframes
            'trend_direction': 'N/A', # Trend is complex for consensus
            'risk_level': 'N/A', # Risk is complex for consensus
            'support': 'N/A',
            'resistance': 'N/A'
        })
