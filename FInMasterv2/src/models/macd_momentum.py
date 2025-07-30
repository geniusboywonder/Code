# Continue of Code Block 5: Trading Models (Classes for each model)

# Assume StockData, IndicatorCalculationError are defined

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


