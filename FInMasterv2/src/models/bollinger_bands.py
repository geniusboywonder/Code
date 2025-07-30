# Continue of Code Block 5: Trading Models (Classes for each model)

# Assume StockData, IndicatorCalculationError are defined

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