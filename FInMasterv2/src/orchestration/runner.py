stock_symbol: str = input("Enter Stock Symbol (e.g., AAPL, TSLA): ")
period: str = input("Enter Analysis Period (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max): ")
interval: str = input("Enter Analysis Interval (e.g., 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo): ")


# --- Start of Refactored Orchestration Logic ---

analysis_result: Dict[str, Any] = {
    "symbol": None,
    "analysisDate": pd.Timestamp.now().isoformat(),
    "currentPrice": None,
    "priceChange": None,
    "metadata": {},
    "modelResults": {}, # Store results from successfully run models
    "modelErrors": {}, # Store errors reported by individual models' analyze method
    "consensus": None,
    "vixAnalysis": None, # Placeholder, VIX analysis not yet implemented
    "riskAssessment": None,
    "keyLevels": None,
    "recommendations": [],
    "marketContext": {}, # Placeholder, market context not yet implemented
    "technicalIndicators": {}, # Placeholder for final indicator values summary
    "skippedAnalysis": [], # List of analysis sections/models that were skipped or failed
    "overallStatus": "success", # Overall status: success, failure, or partial_success
    "overallError": None, # Store critical errors that halted processing
    "overallMessage": None
}

stock_data_obj: Union[StockData, None] = None