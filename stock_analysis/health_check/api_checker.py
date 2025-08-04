import yfinance as yf
import pandas as pd

def check_yahoo_finance_api():
    """
    Checks if the Yahoo Finance API is accessible by fetching a small amount of data.
    """
    try:
        # Attempt to fetch 1 day of data for a common symbol like AAPL
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="1d")

        if data.empty:
            print("Yahoo Finance API health check failed: Received empty data.")
            return False
        else:
            print("Yahoo Finance API health check successful.")
            return True

    except Exception as e:
        print(f"Yahoo Finance API health check failed: {e}")
        return False

if __name__ == '__main__':
    check_yahoo_finance_api()
