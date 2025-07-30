import requests
import json
import urllib.parse
from typing import Union

# Assume StockData class is defined in a previous cell/module
# Assume StockDataFetchError, InvalidSymbolError are defined

def get_stock_data(symbol: str, period: str = '1d', interval: str = '1d') -> StockData:
    """
    Fetches and processes stock data for a given symbol, period, and interval
     from Yahoo Finance, returning a StockData object or raising exceptions.

    Args:
        symbol: The stock symbol to fetch data for.
        period: The period for the analysis (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max).
        interval: The interval for the data points (e.g., 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo).

    Returns:
        A StockData object containing the processed stock data.

    Raises:
        InvalidSymbolError: If the symbol is invalid or not found on Yahoo Finance.
        StockDataFetchError: If there's an API error, timeout, or other fetching/processing issue.
    """
    # Validate symbol parameter
    if not symbol or not isinstance(symbol, str) or symbol.strip() == "":
        raise InvalidSymbolError('Symbol parameter is required and must be a non-empty string')

    # Clean symbol without enforcing format
    clean_symbol: str = symbol.strip()
    encoded_symbol: str = urllib.parse.quote_plus(clean_symbol)

    try:
        # Construct the Yahoo Finance API URL with period and interval
        # Using period1=0 and period2=9999999999 with range provides flexibility,
        # but explicitly using range is more direct for period.
        # Let's use range for simplicity as per the original plan.
        yahoo_url: str = f'https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}?range={period}&interval={interval}'
        headers: dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }

        # Use a timeout for the request (15 seconds)
        response: requests.Response = requests.get(yahoo_url, headers=headers, timeout=15)

        if not response.ok:
            # Handle non-200 responses from Yahoo Finance API
            if response.status_code == 404:
                raise InvalidSymbolError(f'Symbol not found on Yahoo Finance: {clean_symbol}')
            else:
                # Include response text in error for debugging
                raise StockDataFetchError(f'Yahoo Finance API error for {clean_symbol}: {response.status_code} {response.reason} - {response.text[:200]}...')

        data: dict = response.json()

        # Check for errors reported within the Yahoo Finance JSON response structure
        if data.get('chart', {}).get('error'):
             error_info: dict = data['chart']['error']
             error_code: str = error_info.get('code', 'N/A')
             error_description: str = error_info.get('description', 'Unknown API error')
             if error_code == 'Bad Request': # Often indicates invalid period/interval combo or symbol issue
                  raise InvalidSymbolError(f'Yahoo Finance API error for {clean_symbol}: Invalid request parameters (period={period}, interval={interval}) or symbol issue. Details: {error_description}')
             else:
                  raise StockDataFetchError(f'Yahoo Finance API error for {clean_symbol}: Code {error_code}, Description: {error_description}')


        # Instantiate StockData object with the chart data
        stock_data_obj: StockData = StockData(data.get('chart'))

        if stock_data_obj.has_data():
            # Return the StockData object directly if it contains data
            return stock_data_obj
        else:
            # If StockData object has no data, it means chart data was missing or malformed
            # This could also happen if the period/interval combination yielded no data points
            raise StockDataFetchError(f'No valid chart data points available for symbol: {clean_symbol} with period={period}, interval={interval}. Check symbol, period, and interval.')

    except requests.exceptions.Timeout:
        raise StockDataFetchError(f'Yahoo Finance API request timed out for {clean_symbol}')
    except requests.exceptions.RequestException as e:
        raise StockDataFetchError(f'Unable to connect to Yahoo Finance API for {clean_symbol}: {e}')
    except InvalidSymbolError:
         # Re-raise the InvalidSymbolError caught from the API response check
         raise
    except StockDataFetchError:
         # Re-raise the StockDataFetchError caught from the API response check or no data points
         raise
    except Exception as e:
        # Catch any other unexpected errors during fetch or initial StockData creation
        raise StockDataFetchError(f'An unexpected error occurred during data fetch or processing for {clean_symbol}: {e}')

# Example Usage block is removed as per instruction #6.
# The testing of this function will be part of the orchestration logic. 
