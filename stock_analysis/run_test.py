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


def run_full_analysis_test(symbol: str, end_date: str = None):
    """
    Runs a full analysis pipeline test for a given stock symbol and end date.
    If end_date is None, defaults to yesterday.
    """
    end_date_display = end_date if end_date else "yesterday (default)"
    print(f"--- Running Full Analysis Test for {symbol} (end date: {end_date_display}) ---")

    orchestrator = AnalysisOrchestrator()

    # The orchestrator and get_stock_data now handle determining the start date based on work day requirements
    # Passing None for start_date as it's calculated automatically
    stock_data = orchestrator.run_analysis(symbol, None, end_date)

    if stock_data:
        print(f"\nSuccessfully analyzed data for {stock_data.symbol}.")
        if stock_data.note:
            print(f"Data info: {stock_data.note}")
        print("\n--- Analysis Report ---")
        report = generate_analysis_report(stock_data)
        print(report)
        print("--- Full Analysis Test Complete ---")
    else:
        print(f"\nFailed to run full analysis for {symbol}.")
        print("--- Full Analysis Test Complete (with Failure) ---")


if __name__ == "__main__":
    # Define the symbol and end date for the test
    # Using a common symbol and default to yesterday
    test_symbol = 'GOOG'
    test_end_date = None  # Will default to yesterday

    run_full_analysis_test(test_symbol, test_end_date)

    # Example of running test for a symbol that might have less daily data (optional)
    # test_symbol_weekly = 'BRK-A' # Example of a less liquid or differently structured stock
    # print("\n" + "="*50 + "\n") # Separator
    # run_full_analysis_test(test_symbol_weekly, test_end_date)
