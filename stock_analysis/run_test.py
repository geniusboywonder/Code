import sys
import os
from tqdm.auto import tqdm

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up from script_dir)
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))

# Add the project root to sys.path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import modules from the project
from stock_analysis.analysis_orchestration.analysis_orchestrator import AnalysisOrchestrator
from stock_analysis.reporting.report_generator import generate_analysis_report
# Import StockData if needed for type hints or checks, but it's already imported by orchestrator/reporter
# from stock_analysis.data_structures.stock_data import StockData


def run_full_analysis_test(symbol: str, end_date: str):
    """
    Runs a full analysis pipeline test for a given stock symbol and end date.
    """
    print(f"--- Running Full Analysis Test for {symbol} ---")

    orchestrator = AnalysisOrchestrator()

    # The orchestrator now handles determining the start date based on indicator needs
    # Passing None for start_date as orchestrator determines it
    stock_data = orchestrator.run_analysis(symbol, None, end_date)

    if stock_data:
        print(f"\nSuccessfully analyzed data for {stock_data.symbol}.")
        print("\n--- Analysis Report ---")
        report = generate_analysis_report(stock_data)
        print(report)
        print("--- Full Analysis Test Complete ---")
    else:
        print(f"\nFailed to run full analysis for {symbol}.")
        print("--- Full Analysis Test Complete (with Failure) ---")


if __name__ == "__main__":
    # Define the symbol and end date for the test
    # Using a common symbol and a recent date
    test_symbol = 'GOOG'
    test_end_date = '2024-07-31'

    run_full_analysis_test(test_symbol, test_end_date)

    # Example of running test for a symbol that might have less daily data (optional)
    # test_symbol_weekly = 'BRK-A' # Example of a less liquid or differently structured stock
    # print("\n" + "="*50 + "\n") # Separator
    # run_full_analysis_test(test_symbol_weekly, test_end_date)
