# Continue of Code Block 5: Trading Models (Classes for each model)

# Assume StockData, IndicatorCalculationError are defined

class MovingAverageCrossoverModel:
    """
    Analyzes price data using the Moving Average Crossover strategy (SMA 50/200).
    """
    def __init__(self, fast_period: int = 50, slow_period: int = 200):
        self.fast_period: int = fast_period
        self.slow_period: int = slow_period
        self.name: str = f"MA Crossover ({fast_period}/{slow_period})"
        # Define expected indicator column names based on IndicatorCalculator
        # Use SMA for MA Crossover
        self.fast_ma_col: str = f'SMA_{self.fast_period}'
        self.slow_ma_col: str = f'SMA_{self.slow_period}'

    def analyze(self, stock_data: StockData) -> Dict[str, Any]:
        """
        Analyzes price data using the Moving Average Crossover strategy.

        Args:
            stock_data: A StockData object containing price data and calculated indicators.

        Returns:
            A dictionary containing the analysis results, including potential errors.
        """
        df: pd.DataFrame = stock_data.get_dataframe()
        closes: pd.Series = stock_data.closes

        # Ensure sufficient data points for the model logic itself
        required_data_length: int = max(self.fast_period, self.slow_period)
        if len(df) < required_data_length:
            return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "trendDirection": "Insufficient Data",
                "trendStrength": "Unknown",
                "timeframe": "Long-term (3-12 months)",
                "keyLevels": {},
                "technicalData": {},
                "error": f"Insufficient data points ({len(df)} available). Need at least {required_data_length} periods for model logic."
            }

        # Access pre-calculated moving averages from the DataFrame
        try:
            fast_ma_series: pd.Series = df[self.fast_ma_col]
            slow_ma_series: pd.Series = df[self.slow_ma_col]
        except KeyError as e:
             # Catch KeyError if the indicator was not calculated by IndicatorCalculator
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "trendDirection": "Indicator Missing",
                "trendStrength": "Unknown",
                "timeframe": "Long-term (3-12 months)",
                "keyLevels": {},
                "technicalData": {},
                "error": f"Required indicator missing: {e}. Calculation may have failed or been skipped."
            }


        # Ensure the indicator series have enough calculated values at the end for analysis
        # Need at least 2 values for crossover check (current and previous)
        if len(fast_ma_series.dropna()) < 2 or len(slow_ma_series.dropna()) < 2:
             # Find the minimum required periods for the indicator itself
             min_indicator_periods: int = max(self.fast_period, self.slow_period)
             available_valid_fast: int = len(fast_ma_series.dropna())
             available_valid_slow: int = len(slow_ma_series.dropna())

             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "trendDirection": "Insufficient Indicator Data",
                "trendStrength": "Unknown",
                "timeframe": "Long-term (3-12 months)",
                "keyLevels": {},
                 "technicalData": { # Return available technical data
                    self.fast_ma_col: fast_ma_series.tolist() if fast_ma_series is not None else [],
                    self.slow_ma_col: slow_ma_series.tolist() if slow_ma_series is not None else [],
                    "crossoverPoints": []
                },
                "error": f"Insufficient recent calculated moving averages ({available_valid_fast}/{available_valid_slow} valid points available). Need at least 2 valid points for crossover check."
            }


        # Get latest and previous MA values, handling potential NaNs
        current_fast: Union[float, None] = fast_ma_series.iloc[-1] if pd.notna(fast_ma_series.iloc[-1]) else None
        current_slow: Union[float, None] = slow_ma_series.iloc[-1] if pd.notna(slow_ma_series.iloc[-1]) else None
        # Use .iloc[-2] only if the Series has at least 2 elements
        prev_fast: Union[float, None] = fast_ma_series.iloc[-2] if len(fast_ma_series) >= 2 and pd.notna(fast_ma_series.iloc[-2]) else None
        prev_slow: Union[float, None] = slow_ma_series.iloc[-2] if len(slow_ma_series) >= 2 and pd.notna(slow_ma_series.iloc[-2]) else None
        current_price: Union[float, None] = closes.iloc[-1] if not closes.empty and pd.notna(closes.iloc[-1]) else None


        # Determine trend and signals, handling potential None values
        trend_direction: str = "Sideways"
        signal: str = "HOLD"
        confidence: int = 0
        reasoning: List[str] = []

        if current_fast is not None and current_slow is not None:
            # Golden Cross / Death Cross detection
            if prev_fast is not None and prev_slow is not None:
                if current_fast > current_slow and prev_fast <= prev_slow:
                    signal = "BUY"
                    trend_direction = "Golden Cross - Strong Uptrend"
                    confidence = 85
                    reasoning.append("Golden Cross (Fast MA crossed above Slow MA)")
                elif current_fast < current_slow and prev_fast >= prev_slow:
                    signal = "SELL"
                    trend_direction = "Death Cross - Strong Downtrend"
                    confidence = 85
                    reasoning.append("Death Cross (Fast MA crossed below Slow MA)")
                elif current_fast > current_slow:
                    trend_direction = "Uptrend"
                    signal = "BUY" if current_price is not None and current_price > current_fast else "WAIT"
                    confidence = 60
                    reasoning.append("Fast MA is above Slow MA (Uptrend)")
                elif current_fast < current_slow:
                    trend_direction = "Downtrend"
                    signal = "SELL" if current_price is not None and current_price < current_fast else "WAIT"
                    confidence = 60
                    reasoning.append("Fast MA is below Slow MA (Downtrend)")
                else: # current_fast == current_slow (rare, but possible)
                    trend_direction = "Sideways"
                    signal = "HOLD"
                    confidence = 20
                    reasoning.append("Fast MA and Slow MA are converging")
            elif current_fast > current_slow:
                 trend_direction = "Uptrend"
                 signal = "BUY" if current_price is not None and current_price > current_fast else "WAIT"
                 confidence = 50 # Lower confidence if no previous data for crossover check
                 reasoning.append("Fast MA is above Slow MA (Uptrend) - No previous crossover data")
            elif current_fast < current_slow:
                 trend_direction = "Downtrend"
                 signal = "SELL" if current_price is not None and current_price < current_fast else "WAIT"
                 confidence = 50 # Lower confidence if no previous data for crossover check
                 reasoning.append("Fast MA is below Slow MA (Downtrend) - No previous crossover data")
            else:
                 trend_direction = "Sideways"
                 signal = "HOLD"
                 confidence = 20
                 reasoning.append("Fast MA and Slow MA are converging - No previous crossover data")

        else:
             trend_direction = "Undetermined"
             signal = "HOLD"
             confidence = 10 # Low confidence due to missing MA data
             reasoning.append("Insufficient recent MA data for analysis")


        # Calculate trend strength, handling division by zero and NaNs
        ma_separation_pct: Union[float, int] = 0
        if current_slow is not None and pd.notna(current_slow) and current_slow != 0 and current_fast is not None and pd.notna(current_fast):
             ma_separation_pct = abs(current_fast - current_slow) / current_slow * 100


        trend_strength: str = "Weak"
        if ma_separation_pct > 10:
            trend_strength = "Very Strong"
            confidence += 15
            reasoning.append(f"MA separation is Very Strong ({ma_separation_pct:.2f}%)")
        elif ma_separation_pct > 5:
            trend_strength = "Strong"
            confidence += 10
            reasoning.append(f"MA separation is Strong ({ma_separation_pct:.2f}%)")
        elif ma_separation_pct > 2:
            trend_strength = "Moderate"
            confidence += 5
            reasoning.append(f"MA separation is Moderate ({ma_separation_pct:.2f}%)")
        else:
             reasoning.append(f"MA separation is Weak ({ma_separation_pct:.2f}%)")


        # Calculate key levels, handling None values and NaNs
        support: Union[float, None] = None
        resistance: Union[float, None] = None
        if current_fast is not None and pd.notna(current_fast) and current_slow is not None and pd.notna(current_slow):
            support = min(current_fast, current_slow)
            resistance = max(current_fast, current_slow)
            # Simple resistance slightly above the higher MA
            resistance = resistance * 1.02 if resistance is not None and pd.notna(resistance) else None

        support_str: str = f"{support:.2f}" if support is not None and pd.notna(support) else 'N/A'
        resistance_str: str = f"{resistance:.2f}" if resistance is not None and pd.notna(resistance) else 'N/A'


        # Ensure confidence is within bounds
        confidence = max(0, min(confidence, 100))

        # Prepare technical data dictionary, handling potential None series
        technical_data: Dict[str, List[Union[float, None]]] = {
             self.fast_ma_col: fast_ma_series.tolist() if fast_ma_series is not None else [],
             self.slow_ma_col: slow_ma_series.tolist() if slow_ma_series is not None else [],
             "crossoverPoints": self.find_crossovers(fast_ma_series, slow_ma_series)
        }


        return {
            "model": self.name,
            "signal": signal,
            "confidence": confidence,
            "trendDirection": trend_direction,
            "trendStrength": trend_strength,
            "timeframe": "Long-term (3-12 months)",
            "reasoning": reasoning,
            "keyLevels": {
                "fastMA": f"{current_fast:.2f}" if current_fast is not None and pd.notna(current_fast) else 'N/A',
                "slowMA": f"{current_slow:.2f}" if current_slow is not None and pd.notna(current_slow) else 'N/A',
                "support": support_str,
                "resistance": resistance_str,
                "maSeparation": f"{ma_separation_pct:.2f}%" if current_fast is not None and current_slow is not None and current_slow != 0 and pd.notna(ma_separation_pct) else 'N/A'
            },
            "technicalData": technical_data
        }

    def find_crossovers(self, fast_ma_series: pd.Series, slow_ma_series: pd.Series) -> List[Dict[str, str]]:
        """Finds crossover points between two moving average Series."""
        crossovers: List[Dict[str, str]] = []

        if fast_ma_series is None or slow_ma_series is None:
            return []

        # Use pandas shift for efficient comparison
        shifted_fast: pd.Series = fast_ma_series.shift(1)
        shifted_slow: pd.Series = slow_ma_series.shift(1)

        # Find indices where crossover occurred, ignoring NaNs in current or shifted values
        valid_indices: pd.Index = fast_ma_series.index[fast_ma_series.notna() & slow_ma_series.notna() & shifted_fast.notna() & shifted_slow.notna()]

        if valid_indices.empty or len(valid_indices) < 2:
            return [] # Not enough data points to check for crossovers

        bullish_crossovers_indices: pd.Index = valid_indices[(fast_ma_series.loc[valid_indices] > slow_ma_series.loc[valid_indices]) & (shifted_fast.loc[valid_indices] <= shifted_slow.loc[valid_indices])]
        bearish_crossovers_indices: pd.Index = valid_indices[(fast_ma_series.loc[valid_indices] < slow_ma_series.loc[valid_indices]) & (shifted_fast.loc[valid_indices] >= shifted_slow.loc[valid_indices])]


        # Append crossover details, using index as identifier
        for index in bullish_crossovers_indices:
             crossovers.append({"timestamp": index.isoformat(), "type": "Golden Cross"})
        for index in bearish_crossovers_indices:
             crossovers.append({"timestamp": index.isoformat(), "type": "Death Cross"})


        # Sort by timestamp if needed, otherwise order is chronological by index
        # crossovers.sort(key=lambda x: x['timestamp']) # Optional sorting

        # Return only the most recent crossovers (e.g., last 5)
        return crossovers[-5:] if len(crossovers) > 5 else crossovers


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


class MACDMomentumModel:
    """
    Analyzes price data using the MACD Momentum strategy.
    """
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period: int = fast_period
        self.slow_period: int = slow_period
        self.signal_period: int = signal_period
        self.name: str = f"MACD Momentum ({fast_period},{slow_period},{signal_period})"
        # Define expected indicator column names
        self.macd_line_col: str = 'MACD_macd_line'
        self.signal_line_col: str = 'MACD_signal_line'
        self.histogram_col: str = 'MACD_histogram'


    def analyze(self, stock_data: StockData) -> Dict[str, Any]:
        """
        Analyzes price data using the MACD Momentum strategy.

        Args:
            stock_data: A StockData object containing price data and calculated indicators.

        Returns:
            A dictionary containing the analysis results, including potential errors.
        """
        df: pd.DataFrame = stock_data.get_dataframe()

        # Ensure sufficient data points for the model logic itself
        # Need at least enough data for MACD calculation period + some buffer for recent checks
        required_data_length: int = max(self.slow_period, self.fast_period) + self.signal_period - 1 # Approx requirement for MACD calculation
        if len(df) < required_data_length:
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Medium-term (1-3 months)",
                "reasoning": ["Insufficient data points for model logic."],
                "macdAnalysis": {},
                "crossovers": [],
                "technicalData": {},
                "error": f"Insufficient data points ({len(df)} available). Need at least {required_data_length} periods for model logic."
             }


        # Access pre-calculated MACD components from the DataFrame
        try:
            macd_line_series: pd.Series = df[self.macd_line_col]
            signal_line_series: pd.Series = df[self.signal_line_col]
            histogram_series: pd.Series = df[self.histogram_col]
        except KeyError as e:
            # Catch KeyError if the indicator was not calculated by IndicatorCalculator
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Medium-term (1-3 months)",
                "reasoning": ["Indicator Missing."],
                "macdAnalysis": {},
                "crossovers": [],
                "technicalData": {},
                "error": f"Required indicator missing: {e}. Calculation may have failed or been skipped."
            }


        # Ensure required indicator columns have enough calculated values at the end
        # Need at least 2 valid values for MACD/Signal/Histogram for momentum and crossover checks
        if len(macd_line_series.dropna()) < 2 or len(signal_line_series.dropna()) < 2 or len(histogram_series.dropna()) < 2:
            available_valid_macd: int = len(macd_line_series.dropna())
            available_valid_signal: int = len(signal_line_series.dropna())
            available_valid_hist: int = len(histogram_series.dropna())

            return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Medium-term (1-3 months)",
                "reasoning": ["Insufficient recent indicator data."],
                "macdAnalysis": {},
                "crossovers": [],
                "technicalData": {
                     self.macd_line_col: macd_line_series.tolist() if macd_line_series is not None else [],
                     self.signal_line_col: signal_line_series.tolist() if signal_line_series is not None else [],
                     self.histogram_col: histogram_series.tolist() if histogram_series is not None else []
                },
                "error": f"Insufficient recent indicator data for analysis ({available_valid_macd} valid MACD, {available_valid_signal} valid Signal, {available_valid_hist} valid Histogram). Need at least 2 valid points for each."
            }


        # Get latest and previous indicator values, handling potential NaNs at the end
        current_macd: Union[float, None] = macd_line_series.iloc[-1] if pd.notna(macd_line_series.iloc[-1]) else None
        current_signal: Union[float, None] = signal_line_series.iloc[-1] if pd.notna(signal_line_series.iloc[-1]) else None
        current_histogram: Union[float, None] = histogram_series.iloc[-1] if pd.notna(histogram_series.iloc[-1]) else None
        # Use .iloc[-2] only if the Series has at least 2 elements
        prev_macd: Union[float, None] = macd_line_series.iloc[-2] if len(macd_line_series) >= 2 and pd.notna(macd_line_series.iloc[-2]) else None
        prev_signal: Union[float, None] = signal_line_series.iloc[-2] if len(signal_line_series) >= 2 and pd.notna(signal_line_series.iloc[-2]) else None
        prev_histogram: Union[float, None] = histogram_series.iloc[-2] if len(histogram_series) >= 2 and pd.notna(histogram_series.iloc[-2]) else None


        signal: str = "HOLD"
        confidence: int = 0
        reasoning: List[str] = []

        # MACD Line vs Signal Line
        if current_macd is not None and pd.notna(current_macd) and current_signal is not None and pd.notna(current_signal):
            if current_macd > current_signal:
                # Only set BUY signal if not already a strong SELL from another rule (less likely in MACD alone)
                if signal != "SELL":
                    signal = "BUY"
                confidence += 25
                reasoning.append("MACD above signal line (bullish)")
            else:
                # Only set SELL signal if not already a strong BUY
                 if signal != "BUY":
                    signal = "SELL"
                 confidence += 25
                 reasoning.append("MACD below signal line (bearish)")
        else:
             reasoning.append("Current MACD or Signal line not available for comparison.")


        # Histogram analysis (momentum)
        if current_histogram is not None and pd.notna(current_histogram) and prev_histogram is not None and pd.notna(prev_histogram):
            if current_histogram > 0 and current_histogram > prev_histogram:
                confidence += 20
                reasoning.append("MACD histogram expanding (strengthening bullish momentum)")
            elif current_histogram < 0 and current_histogram < prev_histogram:
                confidence += 20
                reasoning.append("MACD histogram expanding (strengthening bearish momentum)")
            elif current_histogram > 0 and current_histogram < prev_histogram:
                confidence -= 10
                reasoning.append("MACD histogram contracting (weakening bullish momentum)")
            elif current_histogram < 0 and current_histogram > prev_histogram:
                confidence -= 10
                reasoning.append("MACD histogram contracting (weakening bearish momentum)")
        else:
             reasoning.append("Current or previous MACD histogram not available for momentum check.")


        # Zero line crossovers
        if current_macd is not None and pd.notna(current_macd) and prev_macd is not None and pd.notna(prev_macd):
            if current_macd > 0 and prev_macd <= 0:
                # Strong signal, potentially override existing HOLD/WAIT, but not necessarily BUY/SELL
                if signal == "HOLD" or signal == "WAIT":
                     signal = "BUY"
                confidence += 30
                reasoning.append("MACD crossed above zero line (strong bullish signal)")
            elif current_macd < 0 and prev_macd >= 0:
                 if signal == "HOLD" or signal == "WAIT":
                    signal = "SELL"
                 confidence += 30
                 reasoning.append("MACD crossed below zero line (strong bearish signal)")
        else:
             reasoning.append("Current or previous MACD not available for zero line crossover check.")


        # Signal line crossovers (using current and previous values for clarity)
        if current_macd is not None and pd.notna(current_macd) and current_signal is not None and pd.notna(current_signal) and \
           prev_macd is not None and pd.notna(prev_macd) and prev_signal is not None and pd.notna(prev_signal):
             if current_macd > current_signal and prev_macd <= prev_signal:
                 # Strong signal, potentially override existing HOLD/WAIT, but not necessarily BUY/SELL
                 if signal == "HOLD" or signal == "WAIT":
                     signal = "BUY"
                 confidence += 25
                 reasoning.append("MACD bullish crossover")
             elif current_macd < current_signal and prev_macd >= prev_signal:
                 if signal == "HOLD" or signal == "WAIT":
                    signal = "SELL"
                 confidence += 25
                 reasoning.append("MACD bearish crossover")
        else:
             reasoning.append("Insufficient recent MACD/Signal data for crossover check.")


        # Ensure confidence is within bounds
        confidence = max(0, min(confidence, 100))

        # Prepare technical data dictionary, handling potential None series
        technical_data: Dict[str, List[Union[float, None]]] = {
             self.macd_line_col: macd_line_series.tolist() if macd_line_series is not None else [],
             self.signal_line_col: signal_line_series.tolist() if signal_line_series is not None else [],
             self.histogram_col: histogram_series.tolist() if histogram_series is not None else []
        }


        return {
            "model": self.name,
            "signal": signal,
            "confidence": confidence,
            "timeframe": "Medium-term (1-3 months)",
            "reasoning": reasoning,
            "macdAnalysis": {
                "macdLine": f"{current_macd:.4f}" if current_macd is not None and pd.notna(current_macd) else 'N/A',
                "signalLine": f"{current_signal:.4f}" if current_signal is not None and pd.notna(current_signal) else 'N/A',
                "histogram": f"{current_histogram:.4f}" if current_histogram is not None and pd.notna(current_histogram) else 'N/A',
                "trend": "Bullish" if current_macd is not None and current_signal is not None and pd.notna(current_macd) and pd.notna(current_signal) and current_macd > current_signal else ("Bearish" if current_macd is not None and current_signal is not None and pd.notna(current_macd) and pd.notna(current_signal) and current_macd < current_signal else "Neutral"),
                "momentum": "Strengthening" if current_histogram is not None and prev_histogram is not None and pd.notna(current_histogram) and pd.notna(prev_histogram) and current_histogram > prev_histogram else ("Weakening" if current_histogram is not None and prev_histogram is not None and pd.notna(current_histogram) and pd.notna(prev_histogram) and current_histogram < prev_histogram else "Stable"),
                "position": "Above Zero" if current_macd is not None and pd.notna(current_macd) and current_macd > 0 else ("Below Zero" if current_macd is not None and pd.notna(current_macd) and current_macd < 0 else "Zero Line")
            },
            "crossovers": self.find_crossovers(macd_line_series, signal_line_series, df.index),
            "technicalData": technical_data
        }

    def find_crossovers(self, macd_line_series: pd.Series, signal_line_series: pd.Series, index: pd.Index) -> List[Dict[str, str]]:
        """Finds recent significant crossover points between MACD and Signal lines, and MACD and Zero line."""
        crossovers: List[Dict[str, str]] = []

        if macd_line_series is None or signal_line_series is None:
            return []

        # Use pandas shift for efficient comparison
        shifted_macd: pd.Series = macd_line_series.shift(1)
        shifted_signal: pd.Series = signal_line_series.shift(1)

        # Ensure we only check where both current and shifted values are not NaNs
        valid_signal_indices: pd.Index = macd_line_series.index[macd_line_series.notna() & signal_line_series.notna() & shifted_macd.notna() & shifted_signal.notna()]
        if valid_signal_indices.empty or len(valid_signal_indices) < 2:
             pass # Not enough valid data for signal crossovers
        else:
            # Signal line crossovers
            bullish_signal_crossovers_indices: pd.Index = valid_signal_indices[(macd_line_series.loc[valid_signal_indices] > signal_line_series.loc[valid_signal_indices]) & (shifted_macd.loc[valid_signal_indices] <= shifted_signal.loc[valid_signal_indices])]
            bearish_signal_crossovers_indices: pd.Index = valid_signal_indices[(macd_line_series.loc[valid_signal_indices] < signal_line_series.loc[valid_signal_indices]) & (shifted_macd.loc[valid_signal_indices] >= shifted_signal.loc[valid_signal_indices])]

            for ts in bullish_signal_crossovers_indices:
                 crossovers.append({"timestamp": ts.isoformat(), "type": "Bullish Signal Crossover"})
            for ts in bearish_signal_crossovers_indices:
                 crossovers.append({"timestamp": ts.isoformat(), "type": "Bearish Signal Crossover"})


        # Zero line crossovers
        valid_zero_indices: pd.Index = macd_line_series.index[macd_line_series.notna() & shifted_macd.notna()]
        if valid_zero_indices.empty or len(valid_zero_indices) < 2:
             pass # Not enough valid data for zero line crossovers
        else:
            bullish_zero_crossovers_indices: pd.Index = valid_zero_indices[(macd_line_series.loc[valid_zero_indices] > 0) & (shifted_macd.loc[valid_zero_indices] <= 0)]
            bearish_zero_crossovers_indices: pd.Index = valid_zero_indices[(macd_line_series.loc[valid_zero_indices] < 0) & (shifted_macd.loc[valid_zero_indices] >= 0)]

            for ts in bullish_zero_crossovers_indices:
                 crossovers.append({"timestamp": ts.isoformat(), "type": "Bullish Zero Crossover"})
            for ts in bearish_zero_crossovers_indices:
                 crossovers.append({"timestamp": ts.isoformat(), "type": "Bearish Zero Crossover"})


        # Return only the most recent crossovers (e.g., last 5)
        # Sort by timestamp first to get the latest
        crossovers.sort(key=lambda x: x['timestamp'])
        return crossovers[-5:] if len(crossovers) > 5 else crossovers


class BollingerBandsModel:
    """
    Analyzes price data using the Bollinger Bands strategy.
    """
    def __init__(self, period: int = 20, std_dev: int = 2):
        self.period: int = period
        self.std_dev: int = std_dev
        self.name: str = f"Bollinger Bands ({period}, {std_dev})"
        # Define expected indicator column names
        self.upper_band_col: str = f'BollingerBands_{self.period}_{self.std_dev}_upper'
        self.middle_band_col: str = f'BollingerBands_{self.period}_{self.std_dev}_middle'
        self.lower_band_col: str = f'BollingerBands_{self.period}_{self.std_dev}_lower'
        self.band_width_history_col: str = f'BollingerBands_BandWidth_{self.period}_{self.std_dev}' # Using a specific name for band width

    def analyze(self, stock_data: StockData) -> Dict[str, Any]:
        """
        Analyzes price data using the Bollinger Bands strategy.

        Args:
            stock_data: A StockData object containing price data and calculated indicators.

        Returns:
            A dictionary containing the analysis results, including potential errors.
        """
        df: pd.DataFrame = stock_data.get_dataframe()
        closes: pd.Series = stock_data.closes
        volumes: pd.Series = stock_data.volumes

        # Ensure sufficient data points for the model logic itself
        required_data_length: int = self.period # Need at least 'period' for the first BB calculation and model logic
        if len(df) < required_data_length:
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-6 weeks)",
                "reasoning": ["Insufficient data points for model logic."],
                "bollingerAnalysis": {},
                "keyLevels": {},
                "technicalData": {},
                "error": f"Insufficient data points ({len(df)} available). Need at least {required_data_length} periods for model logic."
             }

        # Access pre-calculated Bollinger Bands and Volume SMA from the DataFrame
        try:
            upper_band_series: pd.Series = df[self.upper_band_col]
            middle_band_series: pd.Series = df[self.middle_band_col]
            lower_band_series: pd.Series = df[self.lower_band_col]
            volume_sma_series: pd.Series = df['SMA_20'] # Assuming SMA 20 is used for volume confirmation
            # Access the band width history if calculated
            band_width_history_series: Union[pd.Series, None] = df.get(self.band_width_history_col) # Use .get() as it might not always be calculated/needed
        except KeyError as e:
            # Catch KeyError if a required indicator was not calculated by IndicatorCalculator
             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-6 weeks)",
                "reasoning": ["Indicator Missing."],
                "bollingerAnalysis": {},
                "keyLevels": {},
                "technicalData": {},
                "error": f"Required indicator missing: {e}. Calculation may have failed or been skipped."
            }


        # Ensure required indicator columns have at least one calculated value at the end
        if len(upper_band_series.dropna()) < 1 or len(middle_band_series.dropna()) < 1 or len(lower_band_series.dropna()) < 1 or \
           len(volume_sma_series.dropna()) < 1:
             available_valid_upper: int = len(upper_band_series.dropna())
             available_valid_middle: int = len(middle_band_series.dropna())
             available_valid_lower: int = len(lower_band_series.dropna())
             available_valid_vol_sma: int = len(volume_sma_series.dropna())

             return {
                "model": self.name,
                "signal": "HOLD",
                "confidence": 0,
                "timeframe": "Short to Medium-term (2-6 weeks)",
                "reasoning": ["Insufficient recent indicator data."],
                "bollingerAnalysis": {},
                "keyLevels": {},
                "technicalData": {
                     self.upper_band_col: upper_band_series.tolist() if upper_band_series is not None else [],
                     self.middle_band_col: middle_band_series.tolist() if middle_band_series is not None else [],
                     self.lower_band_col: lower_band_series.tolist() if lower_band_series is not None else [],
                     'Volume_SMA_20': volume_sma_series.tolist() if volume_sma_series is not None else []
                },
                "error": f"Insufficient recent indicator data for analysis ({available_valid_upper}/{available_valid_middle}/{available_valid_lower} valid BB, {available_valid_vol_sma} valid VolSMA). Need at least 1 valid point for each."
             }


        # Get latest indicator values, handling potential NaNs at the end
        current_price: Union[float, None] = closes.iloc[-1] if not closes.empty and pd.notna(closes.iloc[-1]) else None
        current_upper: Union[float, None] = upper_band_series.iloc[-1] if pd.notna(upper_band_series.iloc[-1]) else None
        current_lower: Union[float, None] = lower_band_series.iloc[-1] if pd.notna(lower_band_series.iloc[-1]) else None
        current_middle: Union[float, None] = middle_band_series.iloc[-1] if pd.notna(middle_band_series.iloc[-1]) else None
        current_volume: Union[int, None] = volumes.iloc[-1] if not volumes.empty and pd.notna(volumes.iloc[-1]) else None
        avg_volume: Union[float, None] = volume_sma_series.iloc[-1] if pd.notna(volume_sma_series.iloc[-1]) else None


        signal: str = "HOLD"
        confidence: int = 0
        reasoning: List[str] = []

        # Band position analysis
        # Handle potential division by zero if bands are 0 (shouldn't happen with price data, but defensive)
        upper_distance_pct: Union[float, None] = (current_price - current_upper) / current_upper * 100 if current_price is not None and pd.notna(current_price) and current_upper is not None and pd.notna(current_upper) and current_upper != 0 else None
        lower_distance_pct: Union[float, None] = (current_lower - current_price) / current_lower * 100 if current_price is not None and pd.notna(current_price) and current_lower is not None and pd.notna(current_lower) and current_lower != 0 else None
        band_width_pct: Union[float, None] = (current_upper - current_lower) / current_middle * 100 if current_upper is not None and pd.notna(current_upper) and current_lower is not None and pd.notna(current_lower) and current_middle is not None and pd.notna(current_middle) and current_middle != 0 else None


        # Price near bands
        if current_price is not None and pd.notna(current_price) and current_lower is not None and pd.notna(current_lower) and (current_price <= current_lower * 1.02 or (lower_distance_pct is not None and lower_distance_pct <= 2)): # Within 2% of lower band
            signal = "BUY"
            confidence += 35
            reasoning.append(f"Price near lower band ({lower_distance_pct:.1f}% below)" if lower_distance_pct is not None else "Price near lower band")

            # Volume confirmation
            if current_volume is not None and pd.notna(current_volume) and avg_volume is not None and pd.notna(avg_volume) and current_volume > avg_volume * 1.2:
                confidence += 15
                reasoning.append("High volume confirms oversold bounce")
        elif current_price is not None and pd.notna(current_price) and current_upper is not None and pd.notna(current_upper) and (current_price >= current_upper * 0.98 or (upper_distance_pct is not None and upper_distance_pct >= -2)): # Within 2% of upper band
            signal = "SELL"
            confidence += 35
            reasoning.append(f"Price near upper band ({abs(upper_distance_pct):.1f}% above)" if upper_distance_pct is not None else "Price near upper band")

            # Volume confirmation
            if current_volume is not None and pd.notna(current_volume) and avg_volume is not None and pd.notna(avg_volume) and current_volume > avg_volume * 1.2:
                confidence += 15
                reasoning.append("High volume confirms overbought reversal")

        # Band squeeze detection
        # Need band width history to calculate average band width. Accessing it if available.
        avg_band_width: Union[float, None] = band_width_history_series.mean() if band_width_history_series is not None and not band_width_history_series.empty else None

        if band_width_pct is not None and pd.notna(band_width_pct) and avg_band_width is not None and pd.notna(avg_band_width) and band_width_pct < avg_band_width * 0.8:
            reasoning.append("Bollinger Band squeeze detected - breakout expected")
            confidence += 10

        # Middle band (SMA) analysis
        if current_price is not None and pd.notna(current_price) and current_middle is not None and pd.notna(current_middle):
            if current_price > current_middle:
                if signal == "BUY": confidence += 10
                reasoning.append("Price above middle band (bullish bias)")
            else:
                if signal == "SELL": confidence += 10
                reasoning.append("Price below middle band (bearish bias)")

        # Band walk detection - Use recent data from the DataFrame
        band_walk_lookback_period: int = self.period # Use period of BB for band walk check
        recent_closes: pd.Series = closes[-band_walk_lookback_period:] if len(closes) >= band_walk_lookback_period else closes
        recent_upper_band: Union[pd.Series, None] = upper_band_series[-band_walk_lookback_period:] if upper_band_series is not None and len(upper_band_series) >= band_walk_lookback_period else None
        recent_lower_band: Union[pd.Series, None] = lower_band_series[-band_walk_lookback_period:] if lower_band_series is not None and len(lower_band_series) >= band_walk_lookback_period else None


        band_walk: Dict[str, Union[str, int]] = {"type": "None", "strength": 0}
        if recent_closes is not None and not recent_closes.empty and recent_upper_band is not None and recent_lower_band is not None:
             try:
                # Ensure recent data has no NaNs in the relevant series before checking band walk
                aligned_recent_data: pd.DataFrame = pd.DataFrame({
                    'price': recent_closes,
                    'upper': recent_upper_band,
                    'lower': recent_lower_band
                }).dropna()

                if len(aligned_recent_data) >= 5: # Need at least 5 valid points for detection
                    band_walk = self.detect_band_walk(aligned_recent_data['price'], aligned_recent_data['upper'], aligned_recent_data['lower'])
                else:
                     reasoning.append("Insufficient recent valid data for band walk detection.")

             except Exception as e:
                 reasoning.append(f"Error detecting band walk: {e}") # Log error but don't fail model


        if band_walk["type"] != "None":
            reasoning.append(f"{band_walk['type']} band walk detected")
            confidence += band_walk["strength"]

        # Ensure confidence is within bounds
        confidence = max(0, min(confidence, 100))

        # Prepare technical data dictionary
        technical_data: Dict[str, List[Union[float, None]]] = {
             self.upper_band_col: upper_band_series.tolist() if upper_band_series is not None else [],
             self.middle_band_col: middle_band_series.tolist() if middle_band_series is not None else [],
             self.lower_band_col: lower_band_series.tolist() if lower_band_series is not None else [],
             'Volume_SMA_20': volume_sma_series.tolist() if volume_sma_series is not None else [],
             # Include band width history if calculated
             self.band_width_history_col: band_width_history_series.tolist() if band_width_history_series is not None else []
        }


        return {
            "model": self.name,
            "signal": signal,
            "confidence": confidence,
            "timeframe": "Short to Medium-term (2-6 weeks)",
            "reasoning": reasoning,
            "bollingerAnalysis": {
                "currentPrice": f"{current_price:.2f}" if current_price is not None and pd.notna(current_price) else 'N/A',
                "upperBand": f"{current_upper:.2f}" if current_upper is not None and pd.notna(current_upper) else 'N/A',
                "middleBand": f"{current_middle:.2f}" if current_middle is not None and pd.notna(current_middle) else 'N/A',
                "lowerBand": f"{current_lower:.2f}" if current_lower is not None and pd.notna(current_lower) else 'N/A',
                "bandWidth": f"{band_width_pct:.2f}%" if band_width_pct is not None and pd.notna(band_width_pct) else 'N/A',
                "pricePosition": self.get_price_position(current_price, current_upper, current_lower, current_middle),
                "squeeze": band_width_pct is not None and pd.notna(band_width_pct) and avg_band_width is not None and pd.notna(avg_band_width) and band_width_pct < avg_band_width * 0.8,
                "bandWalk": band_walk
            },
            "keyLevels": {
                "resistance": f"{current_upper:.2f}" if current_upper is not None and pd.notna(current_upper) else 'N/A',
                "support": f"{current_lower:.2f}" if current_lower is not None and pd.notna(current_lower) else 'N/A',
                "pivot": f"{current_middle:.2f}" if current_middle is not None and pd.notna(current_middle) else 'N/A'
            },
            "technicalData": technical_data
        }

    def get_price_position(self, price: Union[float, None], upper: Union[float, None], lower: Union[float, None], middle: Union[float, None]) -> str:
        """Determines the price position relative to Bollinger Bands."""
        if price is None or pd.isna(price) or upper is None or pd.isna(upper) or lower is None or pd.isna(lower) or middle is None or pd.isna(middle): return 'N/A'

        if price >= upper: return "Above Upper Band"
        if price <= lower: return "Below Lower Band"
        if price > middle: return "Upper Half"
        return "Lower Half"

    def detect_band_walk(self, prices: pd.Series, upper_band: pd.Series, lower_band: pd.Series) -> Dict[str, Union[str, int]]:
        """Simplified band walk detection on pandas Series."""
        # Ensure enough valid data points for the check
        if len(prices.dropna()) < 5 or len(upper_band.dropna()) < 5 or len(lower_band.dropna()) < 5:
            return {"type": "None", "strength": 0}

        upper_touches: int = 0
        lower_touches: int = 0

        # Check recent periods for touches - Ensure recent slices have enough valid data
        lookback: int = 5
        recent_prices: pd.Series = prices[-lookback:]
        recent_upper: pd.Series = upper_band[-lookback:]
        recent_lower: pd.Series = lower_band[-lookback:]

        # Ensure indices align and data is not NaN in the recent window
        aligned_data: pd.DataFrame = pd.DataFrame({'price': recent_prices, 'upper': recent_upper, 'lower': recent_lower}).dropna()

        if len(aligned_data) < lookback: # Need at least 'lookback' consecutive valid points
             return {"type": "None", "strength": 0}


        for index, row in aligned_data.iterrows():
            if row['price'] >= row['upper'] * 0.98: upper_touches += 1
            if row['price'] <= row['lower'] * 1.02: lower_touches += 1


        if upper_touches >= 3: # Check for at least 3 touches in the last 'lookback' periods
            return {"type": "Upper Band Walk", "strength": 15}
        elif lower_touches >= 3:
            return {"type": "Lower Band Walk", "strength": 15}

        return {"type": "None", "strength": 0}


# Test the updated model analysis methods (Conceptual - requires StockData with indicators)
# Assuming stock_data_obj from previous cells is a valid StockData object with indicators calculated

# if isinstance(stock_data_obj, StockData) and stock_data_obj.has_data():
#     print("\n--- Testing Updated Models with Error Handling ---")
#     try:
#         ma_model = MovingAverageCrossoverModel()
#         ma_result = ma_model.analyze(stock_data_obj)
#         print("\nMA Crossover Analysis Result:")
#         import json
#         print(json.dumps(ma_result, indent=2)) # Check for 'error' key in output

#         rsi_model = RSIMeanReversionModel()
#         rsi_result = rsi_model.analyze(stock_data_obj)
#         print("\nRSI Mean Reversion Analysis Result:")
#         print(json.dumps(rsi_result, indent=2)) # Check for 'error' key in output

#         macd_model = MACDMomentumModel()
#         macd_result = macd_model.analyze(stock_data_obj)
#         print("\nMACD Momentum Analysis Result:")
#         print(json.dumps(macd_result, indent=2)) # Check for 'error' key in output

#         bb_model = BollingerBandsModel()
#         bb_result = bb_model.analyze(stock_data_obj)
#         print("\nBollinger Bands Analysis Result:")
#         print(json.dumps(bb_result, indent=2)) # Check for 'error' key in output

#     except Exception as e:
#         print(f"An unexpected error occurred during model analysis testing: {e}")
# else:
#     print("\nCannot test updated models: stock_data_obj is not a valid StockData object or has no data.")