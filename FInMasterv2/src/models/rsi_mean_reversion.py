# Continue of Code Block 5: Trading Models (Classes for each model)

# Assume StockData, IndicatorCalculationError are defined

class RSIMeanReversionModel:
    """
    Analyzes price data using the RSI Mean Reversion strategy.
    """
    def __init__(self, rsi_period: int = 14, oversold_level: int = 30, overbought_level: int = 70):
        self.rsi_period: int = rsi_period
        self.oversold_level: int = oversold_level
        self.overbought_level: int = overbought_level
        self.name: str = f"RSI Mean Reversion ({rsi_period})"
        # Define expected indicator column names
        self.rsi_col: str = f'RSI_{self.rsi_period}'
        self.sma20_col: str = 'SMA_20' # Assuming SMA 20 is needed for confirmation

    def analyze(self, stock_data: StockData) -> Dict[str, Any]:
        """
        Analyzes price data using the RSI Mean Reversion strategy.

        Args:
            stock_data: A StockData object containing price data and calculated indicators.

        Returns:
            A dictionary containing the analysis results, including potential errors.
        """
        df: pd.DataFrame = stock_data.get_dataframe()
        closes: pd.Series = stock_data.closes

        # Ensure sufficient data points for the model logic itself
        # Need at least enough data for RSI calculation period + some buffer for recent checks
        required_data_length: int = self.rsi_period + 1 # Need period + 1 for diff in RSI calculation, and 2 for current/prev check
        if len(df) < required_data_length:
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-8 weeks)",
                "reasoning": ["Insufficient data points for model logic."],
                "rsiAnalysis": {},
                "keyLevels": {},
                "technicalData": {},
                "error": f"Insufficient data points ({len(df)} available). Need at least {required_data_length} periods for model logic."
            }


        # Access pre-calculated indicators from the DataFrame
        try:
            rsi_series: pd.Series = df[self.rsi_col]
            sma20_series: pd.Series = df[self.sma20_col]
        except KeyError as e:
            # Catch KeyError if the indicator was not calculated by IndicatorCalculator
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-8 weeks)",
                "reasoning": ["Indicator Missing."],
                "rsiAnalysis": {},
                "keyLevels": {},
                "technicalData": {},
                "error": f"Required indicator missing: {e}. Calculation may have failed or been skipped."
            }


        # Ensure required indicator columns have enough calculated values at the end for analysis
        # Need at least 2 valid RSI values for momentum check, and 1 valid SMA20 for price comparison
        if len(rsi_series.dropna()) < 2 or len(sma20_series.dropna()) < 1:
             available_valid_rsi: int = len(rsi_series.dropna())
             available_valid_sma20: int = len(sma20_series.dropna())
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-8 weeks)",
                "reasoning": ["Insufficient recent indicator data."],
                "rsiAnalysis": {},
                "keyLevels": {},
                "technicalData": {
                     self.rsi_col: rsi_series.tolist() if rsi_series is not None else [],
                     self.sma20_col: sma20_series.tolist() if sma20_series is not None else []
                },
                "error": f"Insufficient recent indicator data for analysis ({available_valid_rsi} valid RSI, {available_valid_sma20} valid SMA20). Need at least 2 valid RSI and 1 valid SMA20."
             }


        # Get latest and previous indicator values, handling potential NaNs at the end
        current_rsi: Union[float, None] = rsi_series.iloc[-1] if pd.notna(rsi_series.iloc[-1]) else None
        # Use .iloc[-2] only if the Series has at least 2 elements
        prev_rsi: Union[float, None] = rsi_series.iloc[-2] if len(rsi_series) >= 2 and pd.notna(rsi_series.iloc[-2]) else None
        current_price: Union[float, None] = closes.iloc[-1] if not closes.empty and pd.notna(closes.iloc[-1]) else None
        current_sma20: Union[float, None] = sma20_series.iloc[-1] if pd.notna(sma20_series.iloc[-1]) else None


        signal: str = "HOLD"
        confidence: int = 0
        reasoning: List[str] = []

        # RSI-based signals
        if current_rsi is not None and pd.notna(current_rsi):
            reasoning.append(f"Current RSI: {current_rsi:.2f}")
            if current_rsi < self.oversold_level:
                signal = "BUY"
                confidence += 40
                reasoning.append(f"RSI oversold ({current_rsi:.1f} < {self.oversold_level})")

                # Extra confidence if RSI is turning up
                if prev_rsi is not None and pd.notna(prev_rsi) and current_rsi > prev_rsi:
                    confidence += 20
                    reasoning.append("RSI showing upward momentum")
                elif prev_rsi is not None and pd.notna(prev_rsi) and current_rsi < prev_rsi:
                     reasoning.append("RSI still falling (caution)")


            elif current_rsi > self.overbought_level:
                signal = "SELL"
                confidence += 40
                reasoning.append(f"RSI overbought ({current_rsi:.1f} > {self.overbought_level})")

                # Extra confidence if RSI is turning down
                if prev_rsi is not None and pd.notna(prev_rsi) and current_rsi < prev_rsi:
                    confidence += 20
                    reasoning.append("RSI showing downward momentum")
                elif prev_rsi is not None and pd.notna(prev_rsi) and current_rsi > prev_rsi:
                     reasoning.append("RSI still rising (caution)")

            elif current_rsi >= 40 and current_rsi <= 60:
                 confidence += 10
                 reasoning.append("RSI Neutral Zone")
            elif current_rsi > 60:
                 reasoning.append("RSI in bullish territory")
            elif current_rsi < 40:
                 reasoning.append("RSI in bearish territory")
        else:
             reasoning.append("Current RSI is not available.")


        # Price vs SMA confirmation
        if current_price is not None and pd.notna(current_price) and current_sma20 is not None and pd.notna(current_sma20):
            if current_price > current_sma20:
                if signal == "BUY": confidence += 15
                reasoning.append("Price above 20-day SMA (bullish bias)")
            else:
                if signal == "SELL": confidence += 15
                reasoning.append("Price below 20-day SMA (bearish bias)")
        else:
             reasoning.append("Current price or SMA20 not available for confirmation.")


        # RSI divergence detection (simplified check for recent data)
        # Use pandas slicing for recent data - need enough data points for the rolling window min/max
        divergence_lookback_period: int = max(self.rsi_period, 20) # Use a lookback period relevant to RSI and SMA
        recent_closes: pd.Series = closes[-divergence_lookback_period:] if len(closes) >= divergence_lookback_period else closes
        recent_rsi: Union[pd.Series, None] = rsi_series[-divergence_lookback_period:] if rsi_series is not None and len(rsi_series) >= divergence_lookback_period else None


        divergence: Dict[str, Any] = {"type": "None", "strength": 0}
        if recent_closes is not None and recent_rsi is not None and not recent_closes.empty and not recent_rsi.empty:
            try:
                # Filter out NaNs from recent data before passing to divergence detection
                valid_recent_closes: pd.Series = recent_closes.dropna()
                valid_recent_rsi: pd.Series = recent_rsi.dropna()
                if len(valid_recent_closes) >= 5 and len(valid_recent_rsi) >= 5: # Need at least 5 valid points for detection
                     divergence = self.detect_divergence(valid_recent_closes, valid_recent_rsi)
                else:
                     reasoning.append("Insufficient recent valid data for divergence detection.")

            except Exception as e:
                reasoning.append(f"Error detecting divergence: {e}") # Log error but don't fail model


        if divergence["type"] != "None":
            confidence += divergence["strength"]
            reasoning.append(f"{divergence['type']} divergence detected")
            # Adjust signal based on strong divergence (strength > 20 implies significant confidence boost)
            if divergence["type"] == "Bullish" and signal != "SELL" and divergence["strength"] > 15: # Use 15 as strength from detection
                 signal = "BUY"
                 reasoning.append("Signal reinforced by bullish divergence.")
            if divergence["type"] == "Bearish" and signal != "BUY" and divergence["strength"] > 15:
                 signal = "SELL"
                 reasoning.append("Signal reinforced by bearish divergence.")


        # Ensure confidence is within bounds
        confidence = max(0, min(confidence, 100))

        # Prepare technical data dictionary, handling potential None series
        technical_data: Dict[str, List[Union[float, None]]] = {
             self.rsi_col: rsi_series.tolist() if rsi_series is not None else [],
             self.sma20_col: sma20_series.tolist() if sma20_series is not None else []
        }


        return {
            "model": self.name,
            "signal": signal,
            "confidence": confidence,
            "timeframe": "Short to Medium-term (2-8 weeks)",
            "reasoning": reasoning,
            "rsiAnalysis": {
                "current": f"{current_rsi:.2f}" if current_rsi is not None and pd.notna(current_rsi) else 'N/A',
                "level": self.get_rsi_level(current_rsi),
                "momentum": "Rising" if current_rsi is not None and prev_rsi is not None and pd.notna(current_rsi) and pd.notna(prev_rsi) and current_rsi > prev_rsi else ("Falling" if current_rsi is not None and prev_rsi is not None and pd.notna(current_rsi) and pd.notna(prev_rsi) and current_rsi < prev_rsi else "Stable"),
                "divergence": divergence
            },
            "keyLevels": {
                "oversold": self.oversold_level,
                "overbought": self.overbought_level,
                "neutral": 50,
                "currentLevel": f"{current_rsi:.2f}" if current_rsi is not None and pd.notna(current_rsi) else 'N/A'
            },
            "technicalData": technical_data
        }

    def get_rsi_level(self, rsi: Union[float, None]) -> str:
        """Determines the RSI level description."""
        if rsi is None or pd.isna(rsi): return "N/A"
        if rsi < 20: return "Extremely Oversold"
        if rsi < 30: return "Oversold"
        if rsi < 40: return "Weak"
        if rsi < 60: return "Neutral"
        if rsi < 70: return "Strong"
        if rsi < 80: return "Overbought"
        return "Extremely Overbought"

    def detect_divergence(self, prices: pd.Series, rsi_values: pd.Series) -> Dict[str, Union[str, int]]:
        """Simplified divergence detection on pandas Series."""
        # Ensure enough data points after dropping NaNs for rolling window
        if len(prices.dropna()) < 5 or len(rsi_values.dropna()) < 5:
            return {"type": "None", "strength": 0}

        # Check for potential bullish divergence (lower low in price, higher low in RSI)
        # Find indices of recent significant lows using rolling window min
        price_lows_indices: pd.Index = prices[prices == prices.rolling(window=3, center=True).min()].index
        rsi_lows_indices: pd.Index = rsi_values[rsi_values == rsi_values.rolling(window=3, center=True).min()].index

        # Filter out NaNs from indices before looking up values
        price_lows_indices = price_lows_indices[prices.loc[price_lows_indices].notna()]
        rsi_lows_indices = rsi_lows_indices[rsi_values.loc[rsi_lows_indices].notna()]


        # Look for the last two significant lows in price and RSI that are not NaN
        if len(price_lows_indices) >= 2 and len(rsi_lows_indices) >= 2:
            last_price_low_idx = price_lows_indices[-1]
            second_last_price_low_idx = price_lows_indices[-2]
            last_rsi_low_idx = rsi_lows_indices[-1]
            second_last_rsi_low_idx = rsi_lows_indices[-2]

            # Ensure indices are in correct order (second last occurs before last)
            # And check if price made a lower low and RSI made a higher low, using .loc to get values by index
            if second_last_price_low_idx < last_price_low_idx and second_last_rsi_low_idx < last_rsi_low_idx:
                 if prices.loc[last_price_low_idx] < prices.loc[second_last_price_low_idx] and rsi_values.loc[last_rsi_low_idx] > rsi_values.loc[second_last_rsi_low_idx]:
                     return {"type": "Potential Bullish", "strength": 15}


        # Check for potential bearish divergence (higher high in price, lower high in RSI)
        # Find indices of recent significant highs using rolling window max
        price_highs_indices: pd.Index = prices[prices == prices.rolling(window=3, center=True).max()].index
        rsi_highs_indices: pd.Index = rsi_values[rsi_values == rsi_values.rolling(window=3, center=True).max()].index

        # Filter out NaNs from indices before looking up values
        price_highs_indices = price_highs_indices[prices.loc[price_highs_indices].notna()]
        rsi_highs_indices = rsi_highs_indices[rsi_values.loc[rsi_highs_indices].notna()]


        # Look for the last two significant highs in price and RSI that are not NaN
        if len(price_highs_indices) >= 2 and len(rsi_highs_indices) >= 2:
            last_price_high_idx = price_highs_indices[-1]
            second_last_price_high_idx = price_highs_indices[-2]
            last_rsi_high_idx = rsi_highs_indices[-1]
            second_last_rsi_high_idx = rsi_highs_indices[-2]

            # Ensure indices are in correct order (second last occurs before last)
            # And check if price made a higher high and RSI made a lower high, using .loc to get values by index
            if second_last_price_high_idx < last_price_high_idx and second_last_rsi_high_idx < last_rsi_high_idx:
                 if prices.loc[last_price_high_idx] > prices.loc[second_last_price_high_idx] and rsi_values.loc[last_rsi_high_idx] < rsi_values.loc[second_last_rsi_high_idx]:
                     return {"type": "Potential Bearish", "strength": 15}

        return {"type": "None", "strength": 0}


