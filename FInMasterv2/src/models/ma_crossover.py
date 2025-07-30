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


