import pandas as pd
from typing import Dict, Any, List, Union

class StockData:
    """
    Encapsulates stock price data, using a pandas DataFrame internally.
    Provides easy access to key data series like open, high, low, close, volume, and timestamp.
    Can also store calculated technical indicators.
    """
    def __init__(self, chart_data: Dict[str, Any]):
        """
        Initializes StockData object from raw Yahoo Finance chart data.

        Args:
            chart_data: The 'chart' dictionary from the Yahoo Finance API response.
                        Expected structure: {'result': [{'timestamp': [...], 'indicators': {'quote': [{'open': [...], 'high': [...], 'low': [...], 'close': [...], 'volume': [...]}]}}]}
        """
        self.df: pd.DataFrame = pd.DataFrame()
        self._has_data: bool = False
        self._metadata: Dict[str, Any] = {} # To store potential metadata if available

        if chart_data and chart_data.get('result') and chart_data['result'][0]:
            result: Dict[str, Any] = chart_data['result'][0]
            timestamps: List[Union[int, None]] = result.get('timestamp', [])
            indicators: Dict[str, Any] = result.get('indicators', {})
            quote: List[Dict[str, List[Union[float, int, None]]]] = indicators.get('quote', [])
            meta: Dict[str, Any] = result.get('meta', {}) # Capture metadata if present in chart result

            if timestamps and quote and quote[0]:
                quote_data: Dict[str, List[Union[float, int, None]]] = quote[0]
                data: Dict[str, List[Union[float, int, None]]] = {
                    'timestamp': timestamps,
                    'open': quote_data.get('open', []),
                    'high': quote_data.get('high', []),
                    'low': quote_data.get('low', []),
                    'close': quote_data.get('close', []),
                    'volume': quote_data.get('volume', [])
                }

                # Ensure all lists have the same length before creating DataFrame
                # And filter out None values that might appear in lists
                first_key: Union[str, None] = list(data.keys())[0] if data else None
                if first_key and all(len(data.get(key, [])) == len(data[first_key]) for key in data):
                    # Filter out None values that might appear in lists before creating DataFrame
                    # This ensures columns have consistent types if possible, but NaNs will be pd.NA or np.nan
                    processed_data: Dict[str, List[Union[float, int, pd.NAType]]] = {k: [v if v is not None else pd.NA for v in lst] for k, lst in data.items()}

                    self.df = pd.DataFrame(processed_data)
                    # Convert timestamp from Unix to datetime and set as index
                    self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='s')
                    self.df.set_index('timestamp', inplace=True)

                    # Convert columns to appropriate dtypes, coercing errors
                    for col in ['open', 'high', 'low', 'close']:
                        # Use float64 to handle potential NaNs from coercion
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce').astype('float64')
                    # Fill NaN volumes with 0 and convert to int64
                    self.df['volume'] = pd.to_numeric(self.df['volume'], errors='coerce').fillna(0).astype('int64')

                    if not self.df.empty:
                        self._has_data = True
                        # Store any relevant metadata
                        self._metadata = {
                            "symbol": meta.get("symbol"),
                            "currency": meta.get("currency"),
                            "exchangeName": meta.get("exchangeName"),
                            "instrumentType": meta.get("instrumentType"),
                            "firstTradeDate": pd.to_datetime(meta.get("firstTradeDate"), unit='s', errors='coerce'),
                            "regularMarketPrice": meta.get("regularMarketPrice"),
                            "chartPreviousClose": meta.get("chartPreviousClose"),
                            "dataGranularity": meta.get("dataGranularity"),
                            "range": meta.get("range"),
                            "validRanges": meta.get("validRanges")
                            # Add other relevant meta fields as needed
                        }

                else:
                    print("Warning: Mismatch in data list lengths or empty data. DataFrame not created.") # Or raise an error


    @property
    def timestamps(self) -> pd.DatetimeIndex:
        """Returns the timestamp index."""
        return self.df.index if self._has_data else pd.DatetimeIndex([])

    @property
    def opens(self) -> pd.Series:
        """Returns the 'open' series."""
        return self.df['open'] if self._has_data and 'open' in self.df.columns else pd.Series([], dtype='float64')

    @property
    def highs(self) -> pd.Series:
        """Returns the 'high' series."""
        return self.df['high'] if self._has_data and 'high' in self.df.columns else pd.Series([], dtype='float64')

    @property
    def lows(self) -> pd.Series:
        """Returns the 'low' series."""
        return self.df['low'] if self._has_data and 'low' in self.df.columns else pd.Series([], dtype='float64')

    @property
    def closes(self) -> pd.Series:
        """Returns the 'close' series."""
        return self.df['close'] if self._has_data and 'close' in self.df.columns else pd.Series([], dtype='float64')

    @property
    def volumes(self) -> pd.Series:
        """Returns the 'volume' series."""
        return self.df['volume'] if self._has_data and 'volume' in self.df.columns else pd.Series([], dtype='int64')

    def get_dataframe(self) -> pd.DataFrame:
        """Returns the internal pandas DataFrame."""
        return self.df

    def get_num_data_points(self) -> int:
        """Returns the number of data points (rows) in the DataFrame."""
        return len(self.df)

    def has_data(self) -> bool:
        """Returns True if the StockData object contains valid data."""
        return self._has_data

    def get_metadata(self) -> Dict[str, Any]:
        """Returns the stored metadata."""
        return self._metadata

    def add_indicator(self, indicator_name: str, indicator_series: pd.Series):
        """Adds a calculated indicator series as a new column to the DataFrame."""
        if isinstance(indicator_series, pd.Series) and indicator_series.index.equals(self.df.index):
            self.df[indicator_name] = indicator_series
        else:
            print(f"Warning: Could not add indicator '{indicator_name}'. Provided data is not a pandas Series or index does not match.")
            # Optionally raise an error here depending on desired strictness.

    def add_indicator_dataframe(self, indicator_name: str, indicator_df: pd.DataFrame):
        """Adds multiple calculated indicator series from a DataFrame to the internal DataFrame."""
        if isinstance(indicator_df, pd.DataFrame) and indicator_df.index.equals(self.df.index):
            # Add each column from the indicator_df to the main DataFrame
            for col in indicator_df.columns:
                self.df[f'{indicator_name}_{col}'] = indicator_df[col]
        else:
            print(f"Warning: Could not add indicator DataFrame for '{indicator_name}'. Provided data is not a pandas DataFrame or index does not match.")
            # Optionally raise an error here.

    def get_indicator_series(self, indicator_name: str) -> pd.Series:
        """Returns a specific indicator series from the DataFrame."""
        if indicator_name in self.df.columns:
            return self.df[indicator_name]
        else:
            # Changed to raise an error if a requested indicator is not found,
            # as models might rely on its existence.
            raise KeyError(f"Indicator series '{indicator_name}' not found in DataFrame. Calculation may have failed or been skipped.")


    def get_indicator_dataframe(self, indicator_name: str) -> pd.DataFrame:
        """Returns a DataFrame for indicators that have multiple components (like MACD, BB)."""
        cols: List[str] = [col for col in self.df.columns if col.startswith(indicator_name + '_')]
        if cols:
            return self.df[cols]
        else:
             # Changed to raise an error if a requested indicator DataFrame is not found.
             raise KeyError(f"Indicator DataFrame for '{indicator_name}' not found. Calculation may have failed or been skipped.")
