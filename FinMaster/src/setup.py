import requests
import json
import urllib.parse
import pandas as pd
import numpy as np
from typing import Union, Dict, Any, List

class StockDataFetchError(Exception):
    """Custom exception for general stock data fetching failures."""
    pass

class InvalidSymbolError(StockDataFetchError):
    """Custom exception for invalid or not found symbols."""
    pass

class IndicatorCalculationError(Exception):
    """Custom exception for errors during technical indicator calculation."""
    pass