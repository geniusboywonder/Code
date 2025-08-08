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

# Import the health check function
from stock_analysis.health_check.api_checker import check_yahoo_finance_api

# Import DataFrame, Series, pd_module from the setup config
from stock_analysis.setup.config import DataFrame, Series, pd_module, USE_GPU_PANDAS


from stock_analysis.analysis_orchestration.analysis_orchestrator import AnalysisOrchestrator
from stock_analysis.reporting.report_generator import generate_analysis_report

def main():
    """
    Main function to run the stock analysis application.
    """
    # Perform API health check
    if not check_yahoo_finance_api():
        print("Error: Yahoo Finance API health check failed. Cannot proceed with analysis.")
        sys.exit(1)

    # Get user input for stock symbols and date range
    symbols_input = input("Enter stock symbols (comma-separated): ")
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

    if not symbols:
        print("No stock symbols entered. Exiting.")
        return

    # End date defaults to yesterday, start date is calculated automatically
    end_date_input = input("Enter end date (YYYY-MM-DD) or press Enter for yesterday: ").strip()
    end_date = end_date_input if end_date_input else None
    
    # Start date is now calculated automatically to ensure 200+ work days
    start_date = None  # Not used anymore, but kept for compatibility

    orchestrator = AnalysisOrchestrator()

    print("\n--- Running Analysis ---")
    # Wrap the symbols iteration with tqdm for a progress bar
    # The orchestrator handles the data fetching and processing using the configured types
    for symbol in tqdm(symbols, desc="Analyzing Stocks"):
        # The orchestrator is responsible for handling the configured DataFrame/Series types
        stock_data = orchestrator.run_analysis(symbol, start_date, end_date)

        if stock_data:
            # The report generator is responsible for handling the configured DataFrame/Series types
            report = generate_analysis_report(stock_data)
            print(report)
            if stock_data.note:
                print(f"Note: {stock_data.note}")
        else:
            print(f"Could not analyze {symbol}.")

    print("--- Analysis Complete ---")


if __name__ == "__main__":
    main()
