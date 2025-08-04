import pandas as pd # Keep for compatibility and .to_string()
import sys
import os

# Add the project root to sys.path to allow importing modules
# This is needed to import modules from the stock_analysis package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import DataFrame, Series, pd_module from the setup config
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS

from ..data_structures.stock_data import StockData

def generate_analysis_report(stock_data: StockData) -> str:
    """
    Generates a formatted report string for the analysis results of a single stock.
    Handles DataFrame/Series types from setup.config by converting to pandas
    for reporting functions like to_string.

    Args:
        stock_data: The StockData object containing analysis results.

    Returns:
        A string containing the formatted report.
    """
    report_lines = [f"--- Analysis Report for {stock_data.symbol} ---", ""]

    # Historical Data Summary (optional, can be too verbose)
    # Access historical data (which is the configured DataFrame type)
    # historical_data = stock_data.get_historical_data()
    # If using cuDF, convert to pandas for .to_string()
    # if USE_GPU_PANDAS:
    #      historical_data = historical_data.to_pandas()
    # report_lines.append("Historical Data Summary:")
    # report_lines.append(historical_data.tail().to_string()) # Displaying last few rows
    # report_lines.append("")

    # Technical Indicators Summary
    report_lines.append("Technical Indicators:")
    technical_indicators = stock_data.get_technical_indicators()
    if technical_indicators:
        scalar_indicators = {}
        series_indicators_present = False
        for indicator_name, value in technical_indicators.items():
            if isinstance(value, pd.Series) or (USE_GPU_PANDAS and isinstance(value, Series)):
                 series_indicators_present = True
                 # If it's a Series (pandas or cuDF), get the latest value for summary
                 if not value.empty:
                     # Access the last element, works for both
                     latest_value = value.iloc[-1]
                     # Ensure latest_value is converted to a standard Python scalar if it's a cuDF scalar
                     if USE_GPU_PANDAS and isinstance(latest_value, pd_module.core.scalar.Scalar):
                         latest_value = latest_value.copy_to_host() # Convert cuDF scalar to host scalar
                     scalar_indicators[indicator_name] = latest_value
                 else:
                      scalar_indicators[indicator_name] = 'Empty Series'
            else:
                # Assume scalar or simple value
                scalar_indicators[indicator_name] = value

        if scalar_indicators:
             for indicator_name, value in scalar_indicators.items():
                 # Format floating point values
                 if isinstance(value, (int, float)):
                     report_lines.append(f"- {indicator_name}: {value:.4f}")
                 else:
                     report_lines.append(f"- {indicator_name}: {value}")


        if series_indicators_present:
            report_lines.append("- (Detailed time-series indicators like SMAs, RSI, MACD, BBands are available but not fully displayed here)")

    else:
        report_lines.append("No technical indicators calculated.")
    report_lines.append("")


    # Trading Model Recommendations Table
    report_lines.append("Individual Model Summary Table:")
    recommendations = stock_data.get_trading_recommendations()
    if recommendations:
        # Exclude Consensus for this table, it will be in the consensus table
        model_recommendations = {k: v for k, v in recommendations.items() if k != 'Consensus'}
        if model_recommendations:
            rec_data = []
            for model_name, rec in model_recommendations.items():
                rec_data.append({
                    'Symbol': stock_data.symbol,
                    'Model': model_name,
                    'Signal': rec.get('recommendation', 'N/A'),
                    'Confidence': f"{rec.get('confidence', 0.0):.2f}", # Format confidence
                    'Timeframe': rec.get('timeframe', 'N/A'),
                    'Trend Direction': rec.get('trend_direction', 'N/A'),
                    'Risk Level': rec.get('risk_level', 'N/A'),
                    'Support': rec.get('support', 'N/A'),
                    'Resistance': rec.get('resistance', 'N/A'),
                    'Key Reasoning': rec.get('reasoning', 'N/A'),
                })
            # Create a pandas DataFrame for reporting functions, regardless of configured type
            rec_df = pd.DataFrame(rec_data)
            # Define the columns to display and their order
            display_columns = [
                'Symbol', 'Model', 'Signal', 'Confidence', 'Timeframe',
                'Trend Direction', 'Risk Level', 'Support', 'Resistance', 'Key Reasoning'
            ]
            # Ensure only available columns are displayed
            display_columns = [col for col in display_columns if col in rec_df.columns]
            # Use to_string for better formatting in the report
            report_lines.append(rec_df[display_columns].to_string(index=False))
        else:
             report_lines.append("No individual model recommendations available.")
    else:
        report_lines.append("No trading model recommendations available.")
    report_lines.append("")

    # Consensus Recommendation Table
    report_lines.append("Consensus Recommendation:")
    consensus_rec = recommendations.get('Consensus')
    if consensus_rec:
        consensus_data = [{
            'Symbol': stock_data.symbol,
            'Consensus Signal': consensus_rec.get('recommendation', 'N/A'),
            'Confidence': f"{consensus_rec.get('confidence', 0.0):.2f}", # Format confidence
            # Note: Current Price, Agreement, Risk Level, Position Size, Support, Resistance, Next Review
            # are placeholders in the consensus logic and need to be implemented if desired.
            'Current Price': 'N/A', # Placeholder
            'Agreement': 'N/A', # Placeholder - could be based on buy/sell/wait counts
            'Risk Level': 'N/A', # Placeholder - could be based on model risk levels or consensus confidence
            'Position Size': 'N/A', # Placeholder
            'Recommendation': consensus_rec.get('recommendation', 'N/A'), # Redundant with Consensus Signal, maybe use for final action?
            'Support': 'N/A', # Placeholder
            'Resistance': 'N/A', # Placeholder
            'Next Review': 'N/A', # Placeholder
            'Reasoning': consensus_rec.get('reasoning', 'N/A') # Add reasoning to consensus table
        }]
        # Create a pandas DataFrame for reporting functions
        consensus_df = pd.DataFrame(consensus_data)
        # Define columns for consensus table
        consensus_columns = [
            'Symbol', 'Current Price', 'Consensus Signal', 'Confidence',
            'Agreement', 'Risk Level', 'Recommendation', 'Position Size',
            'Support', 'Resistance', 'Next Review', 'Reasoning'
        ]
        consensus_columns = [col for col in consensus_columns if col in consensus_df.columns]
        report_lines.append(consensus_df[consensus_columns].to_string(index=False))
    else:
        report_lines.append("Consensus recommendation not available.")
    report_lines.append("")

    report_lines.append("-" * (len(report_lines[0]) if report_lines else 30)) # Separator line

    return "\\n".join(report_lines)

def generate_portfolio_summary_table(list_of_stock_data: list[StockData]) -> str:
    """
    Generates a formatted string for the portfolio summary table.
    Handles StockData objects containing configured DataFrame/Series types.

    Args:
        list_of_stock_data: A list of StockData objects.

    Returns:
        A string containing the formatted portfolio summary table.
    """
    if not list_of_stock_data:
        return "No stock data available for portfolio summary."

    summary_data = []
    for stock_data in list_of_stock_data:
        consensus_rec = stock_data.get_trading_recommendations().get('Consensus', {})
        # Placeholder logic to extract relevant info for the portfolio summary
        summary_data.append({
            'Symbol': stock_data.symbol,
            'Signal': consensus_rec.get('recommendation', 'N/A'),
            'Confidence': f"{consensus_rec.get('confidence', 0.0):.2f}", # Format confidence
            'Risk': 'N/A', # Placeholder (could derive from consensus or individual models)
            'Models Bullish': 'N/A', # Placeholder (could count models recommending BUY)
            'Models Bearish': 'N/A', # Placeholder (could count models recommending SELL)
            'Primary Timeframe': 'N/A', # Placeholder (could be based on consensus or most frequent model timeframe)
            'Action': consensus_rec.get('recommendation', 'N/A'), # Using consensus recommendation as action for now
            'Notes': consensus_rec.get('reasoning', 'N/A') # Using consensus reasoning as notes for now
        })

    # Create a pandas DataFrame for reporting functions
    summary_df = pd.DataFrame(summary_data)
    # Define columns for portfolio summary table
    summary_columns = [
        'Symbol', 'Signal', 'Confidence', 'Risk', 'Models Bullish',
        'Models Bearish', 'Primary Timeframe', 'Action', 'Notes'
    ]
     # Ensure only available columns are displayed
    summary_columns = [col for col in summary_columns if col in summary_df.columns]
    # Use to_string for formatting in the report
    return summary_df[summary_columns].to_string(index=False)


# You can add more reporting functions here, e.g., for multiple stocks
# def generate_summary_table(list_of_stock_data: list[StockData]) -> pd.DataFrame:
#     pass
