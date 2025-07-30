# Continue of Code Block 6: Analysis Orchestration and Execution

# Assume StockData, IndicatorCalculator, InvalidSymbolError, StockDataFetchError, IndicatorCalculationError are defined in previous cells.
# Assume the trading model classes (MovingAverageCrossoverModel, etc.) are defined.
# Assume get_stock_data function is defined.


# Prompt the user for the stock symbol, period, and interval
indicator_calc: Union[IndicatorCalculator, None] = None # Keep a reference to the indicator calculator

try:
    # Step 1: Fetch raw data using the updated get_stock_data function
    print(f"Fetching data for {stock_symbol} period={period} interval={interval}...")
    stock_data_obj = get_stock_data(stock_symbol, period, interval)
    analysis_result["symbol"] = stock_symbol # Set symbol in result once data is fetched

    print(f"Successfully created StockData object with {stock_data_obj.get_num_data_points()} data points.")

    # Update basic metadata from the StockData object if possible
    # Note: Our current get_stock_data doesn't fetch comprehensive metadata like previousClose, marketState etc.
    # A robust solution would fetch this separately or enhance StockData to hold it.
    # For now, we'll rely on what's in the data points or require a separate metadata fetch.
    # Let's get current price from the last data point if available.
    if stock_data_obj.get_num_data_points() > 0:
        last_data_point: pd.Series = stock_data_obj.get_dataframe().iloc[-1]
        analysis_result["currentPrice"] = last_data_point.get('close')
        # Price change calculation is not directly supported by StockData from chart data
        # Needs previous day's close, which is usually in the 'meta' part of the API response.
        # Skipping priceChange for now, unless we make another API call just for meta.
        # Let's add a placeholder or note this limitation.
        analysis_result["priceChange"] = {"absolute": "N/A", "percentage": "N/A"} # Placeholder


    # Populate metadata based on what's available or the initial request parameters
    analysis_result["metadata"]["symbol"] = stock_symbol
    analysis_result["metadata"]["dataPoints"] = stock_data_obj.get_num_data_points()
    analysis_result["metadata"]["period"] = period
    analysis_result["metadata"]["interval"] = interval
    # Additional metadata (currency, exchange, etc.) would need a separate fetch or enhancement
    # of get_stock_data to return more meta info.

    # Step 2: Calculate technical indicators using IndicatorCalculator
    print("Calculating technical indicators...")
    indicator_calc = IndicatorCalculator(stock_data_obj) # Instantiate IndicatorCalculator
    indicator_calc.calculate_all_indicators()
    print("Indicator calculation complete.")


    # Step 3: Run trading models using the StockData object (with indicators)
    models: List[Any] = [
        RSIMeanReversionModel(),
        MACDMomentumModel(),
        BollingerBandsModel(),
        MovingAverageCrossoverModel() # MA Crossover might need SMA50/200
    ]

    for model in models:
        print(f"Running model: {model.name}...")
        try:
            # Pass the StockData object to the analyze method
            model_analysis: Dict[str, Any] = model.analyze(stock_data_obj)

            # Check the returned result dictionary for an 'error' key
            if model_analysis and model_analysis.get("error"):
                # Model reported an error, store it
                analysis_result["modelErrors"][model.name] = model_analysis["error"]
                analysis_result["skippedAnalysis"].append(f"Model: {model.name} ({model_analysis['error']})")
                print(f"Model {model.name} reported an error: {model_analysis['error']}")
                # If the model reported an error, do not add its result to modelResults
            else:
                # Model ran successfully or returned no explicit error
                analysis_result["modelResults"][model.name] = model_analysis
                print(f"Model {model.name} analysis complete.")

        except Exception as e:
            # Catch unexpected errors during model execution that were not caught and
            # reported within the model's analyze method itself.
            analysis_result["overallStatus"] = "partial_success" # Some models might have run
            analysis_result["modelErrors"][model.name] = f"Unexpected error during analysis: {e}"
            analysis_result["skippedAnalysis"].append(f"Model: {model.name} (Unexpected error)")
            print(f"An unexpected error occurred while running model {model.name}: {e}")


    # Step 4: Consolidate results (Consensus, Risk Assessment, Key Levels, Recommendations)
    # This logic needs to be adapted to use the results from analysis_result["modelResults"].

    # Simulate Consensus Calculation
    model_signals: Dict[str, Union[str, None]] = {name: res.get('signal') for name, res in analysis_result["modelResults"].items()}
    buy_count: int = list(model_signals.values()).count("BUY")
    sell_count: int = list(model_signals.values()).count("SELL")
    hold_count: int = list(model_signals.values()).count("HOLD")
    wait_count: int = list(model_signals.values()).count("WAIT")
    total_analyzed_models: int = len(analysis_result["modelResults"])

    consensus_signal: str = "HOLD"
    consensus_confidence: int = 0
    agreement: str = "Mixed"
    reasoning_list: List[str] = []
    timeframe: str = "Mixed Timeframes" # Need to consolidate from models

    # Basic consensus logic based on signal counts
    if total_analyzed_models > 0:
        if buy_count > sell_count and buy_count >= hold_count:
             consensus_signal = "BUY"
             consensus_confidence = int((buy_count / total_analyzed_models) * 100)
             agreement = "Bullish" if consensus_confidence > 50 else "Slightly Bullish"
             if consensus_confidence > 75: agreement = "Strong Bullish"
        elif sell_count > buy_count and sell_count >= hold_count:
             consensus_signal = "SELL"
             consensus_confidence = int((sell_count / total_analyzed_models) * 100)
             agreement = "Bearish" if consensus_confidence > 50 else "Slightly Bearish"
             if consensus_confidence > 75: agreement = "Strong Bearish"
        else:
             consensus_signal = "HOLD"
             # Calculate confidence for HOLD as the maximum of (HOLD count / total) and
             # the difference between the dominant side and the other sides.
             hold_ratio_confidence: int = int((hold_count / total_analyzed_models) * 100)
             dominant_count: int = max(buy_count, sell_count)
             subordinate_count: int = min(buy_count, sell_count)
             # Confidence based on the margin of the dominant side vs the others
             margin_confidence: int = int(((dominant_count - subordinate_count) / total_analyzed_models) * 100) if total_analyzed_models > 0 else 0

             consensus_confidence = max(hold_ratio_confidence, margin_confidence) # Use the higher of the two
             agreement = "Mixed"
             if buy_count > sell_count: agreement = "Slightly Bullish (Mixed)"
             elif sell_count > buy_count: agreement = "Slightly Bearish (Mixed)"


        reasoning_list.append(f"{buy_count}/{total_analyzed_models} models bullish, {sell_count}/{total_analyzed_models} bearish, {hold_count}/{total_analyzed_models} hold")

        # Consolidate timeframes (simplified: just pick the most frequent or report mixed)
        model_timeframes: List[Union[str, None]] = [res.get('timeframe') for res in analysis_result["modelResults"].values() if res.get('timeframe')]
        if model_timeframes:
             from collections import Counter
             timeframe_counts: Counter = Counter(model_timeframes)
             most_common_timeframe: List[tuple[str, int]] = timeframe_counts.most_common(1)
             if most_common_timeframe:
                 timeframe = most_common_timeframe[0][0]
                 if len(timeframe_counts) > 1: timeframe = f"{timeframe} (dominant in mixed)"
             else:
                 timeframe = "Mixed Timeframes"
             reasoning_list.append(f"Contributing timeframes: {', '.join(sorted(set(model_timeframes)))}")
        else:
             timeframe = "Unknown Timeframe"
             reasoning_list.append("No contributing timeframes from successful models.")

    else: # No models ran successfully
        consensus_signal = "N/A"
        consensus_confidence = 0
        agreement = "No Models Run"
        timeframe = "N/A"
        reasoning_list.append("No trading models ran successfully to form a consensus.")

    analysis_result["consensus"] = {
        "signal": consensus_signal,
        "confidence": consensus_confidence,
        "agreement": agreement,
        "signalDistribution": {"BUY": buy_count, "SELL": sell_count, "HOLD": hold_count, "WAIT": wait_count, "ERR": len(analysis_result["modelErrors"])},
        "reasoning": reasoning_list,
        "timeframe": timeframe,
        "modelCount": total_analyzed_models,
        "totalModelAttempted": len(models)
    }

    # Simulate Risk Assessment, Key Levels, Recommendations
    # These still use data from StockData and model results

    # Risk Assessment (simplified)
    # Requires ATR from IndicatorCalculator
    atr_series: Union[pd.Series, None] = stock_data_obj.get_dataframe().get('ATR_14')
    latest_atr: Union[float, None] = atr_series.iloc[-1] if atr_series is not None and not atr_series.empty and pd.notna(atr_series.iloc[-1]) else None
    current_price_for_risk: Union[float, None] = analysis_result["currentPrice"]

    risk_level: str = "Unknown"
    volatility_info: str = "N/A"
    risk_factors: List[str] = ["VIX data not available or not applicable for this symbol."]
    risk_recommendation: str = "Consider your risk profile."

    if latest_atr is not None and pd.notna(latest_atr) and current_price_for_risk is not None and pd.notna(current_price_for_risk) and current_price_for_risk != 0:
        atr_percent: float = (latest_atr / current_price_for_risk) * 100
        volatility_info = f"{atr_percent:.2f}% (based on ATR)"
        if atr_percent < 0.5: risk_level = "Very Low"
        elif atr_percent < 1.5: risk_level = "Low"
        elif atr_percent < 3: risk_level = "Medium"
        elif atr_percent < 5: risk_level = "High"
        else: risk_level = "Very High"

        risk_recommendation = f"Manage position size according to your risk tolerance ({risk_level} volatility)."
    else:
         risk_factors.append("ATR data not available for volatility assessment.")
         risk_recommendation = "Could not assess volatility. Consider your risk profile carefully."


    analysis_result["riskAssessment"] = {
        "level": risk_level,
        "volatility": volatility_info,
        "drawdown": "N/A (Requires historical backtesting analysis)",
        "factors": risk_factors,
        "atr": f"{latest_atr:.2f}" if latest_atr is not None and pd.notna(latest_atr) else 'N/A',
        "recommendation": risk_recommendation
    }

    # Key Levels (simplified)
    # Requires access to BB, SMA/EMA endpoints, recent highs/lows from StockData DataFrame
    df_with_indicators: pd.DataFrame = stock_data_obj.get_dataframe()
    bb_upper: Union[pd.Series, None] = df_with_indicators.get('BollingerBands_20_2_upper')
    bb_lower: Union[pd.Series, None] = df_with_indicators.get('BollingerBands_20_2_lower')
    sma50: Union[pd.Series, None] = df_with_indicators.get('SMA_50')
    sma200: Union[pd.Series, None] = df_with_indicators.get('SMA_200')


    latest_upper: Union[float, None] = bb_upper.iloc[-1] if bb_upper is not None and not bb_upper.empty and pd.notna(bb_upper.iloc[-1]) else None
    latest_lower: Union[float, None] = bb_lower.iloc[-1] if bb_lower is not None and not bb_lower.empty and pd.notna(bb_lower.iloc[-1]) else None
    latest_sma50: Union[float, None] = sma50.iloc[-1] if sma50 is not None and not sma50.empty and pd.notna(sma50.iloc[-1]) else None
    latest_sma200: Union[float, None] = sma200.iloc[-1] if sma200 is not None and not sma200.empty and pd.notna(sma200.iloc[-1]) else None

    current_price_for_levels: Union[float, None] = analysis_result["currentPrice"]

    # Determine support and resistance based on available indicators and recent price action
    key_support_candidates: List[Union[float, None]] = [latest_lower, latest_sma50, latest_sma200]
    key_resistance_candidates: List[Union[float, None]] = [latest_upper, latest_sma50, latest_sma200]

    # Filter out None/NaN values
    valid_support_candidates: List[float] = [val for val in key_support_candidates if val is not None and pd.notna(val)]
    valid_resistance_candidates: List[float] = [val for val in key_resistance_candidates if val is not None and pd.notna(val)]


    # Simple logic: highest valid candidate below current price is support, lowest valid candidate above is resistance
    # Using max() for support candidates below current price to find the closest one from below
    key_support: Union[float, None] = max([val for val in valid_support_candidates if current_price_for_levels is not None and val is not None and pd.notna(val) and val <= current_price_for_levels] or [None])
    # Using min() for resistance candidates above current price to find the closest one from above
    key_resistance: Union[float, None] = min([val for val in valid_resistance_candidates if current_price_for_levels is not None and val is not None and pd.notna(val) and val >= current_price_for_levels] or [None])

    # Fallback support/resistance if no indicators are available: use recent low/high
    recent_high: Union[float, None] = stock_data_obj.highs.max() if stock_data_obj.has_data() else None
    recent_low: Union[float, None] = stock_data_obj.lows.min() if stock_data_obj.has_data() else None

    # Only use recent high/low as fallback if indicator levels are not found
    if key_support is None and recent_low is not None and pd.notna(recent_low):
         key_support = recent_low
    if key_resistance is None and recent_high is not None and pd.notna(recent_high):
         key_resistance = recent_high

    # If still no support/resistance, use the most recent high/low from the last N periods as a weaker fallback
    recent_period_lookback: int = min(stock_data_obj.get_num_data_points(), 20) # Look back up to 20 periods or available data
    recent_high_short: Union[float, None] = stock_data_obj.highs[-recent_period_lookback:].max() if stock_data_obj.has_data() and recent_period_lookback > 0 else None
    recent_low_short: Union[float, None] = stock_data_obj.lows[-recent_period_lookback:].min() if stock_data_obj.has_data() and recent_period_lookback > 0 else None

    if key_support is None and recent_low_short is not None and pd.notna(recent_low_short):
        key_support = recent_low_short
    if key_resistance is None and recent_high_short is not None and pd.notna(recent_high_short):
        key_resistance = recent_high_short


    analysis_result["keyLevels"] = {
        "currentPrice": f"{current_price_for_levels:.2f}" if current_price_for_levels is not None and pd.notna(current_price_for_levels) else 'N/A',
        "recentHigh": f"{recent_high:.2f}" if recent_high is not None and pd.notna(recent_high) else 'N/A', # Overall high
        "recentLow": f"{recent_low:.2f}" if recent_low is not None and pd.notna(recent_low) else 'N/A', # Overall low
        "recentHighShortTerm": f"{recent_high_short:.2f}" if recent_high_short is not None and pd.notna(recent_high_short) else 'N/A',
        "recentLowShortTerm": f"{recent_low_short:.2f}" if recent_low_short is not None and pd.notna(recent_low_short) else 'N/A',
        "keySupport": f"{key_support:.2f}" if key_support is not None and pd.notna(key_support) else 'N/A',
        "keyResistance": f"{key_resistance:.2f}" if key_resistance is not None and pd.notna(key_resistance) else 'N/A',
        "range": f"{(recent_high - recent_low)/recent_low*100:.2f}%" if recent_high is not None and pd.notna(recent_high) and recent_low is not None and pd.notna(recent_low) and recent_low != 0 else 'N/A',
        "indicatorLevels": { # Include some indicator levels for context if available
            "RSI": {"oversold": 30, "overbought": 70, "current": analysis_result["modelResults"].get("RSI Mean Reversion (14)", {}).get("rsiAnalysis", {}).get("current", 'N/A')},
            "Bollinger Bands": {"upper": f"{latest_upper:.2f}" if latest_upper is not None and pd.notna(latest_upper) else 'N/A', "middle": f"{df_with_indicators.get('BollingerBands_20_2_middle', pd.Series()).iloc[-1]:.2f}" if df_with_indicators.get('BollingerBands_20_2_middle', pd.Series()).last_valid_index() is not None else 'N/A', "lower": f"{latest_lower:.2f}" if latest_lower is not None and pd.notna(latest_lower) else 'N/A'}
        },
         "note": "Key levels derived from available data and indicators."
    }

    # Overall Recommendations (simplified based on consensus and risk)
    analysis_result["recommendations"] = [] # Clear previous placeholder recommendations
    consensus_signal: Union[str, None] = analysis_result["consensus"].get("signal")
    risk_level: Union[str, None] = analysis_result["riskAssessment"].get("level")
    consensus_agreement: Union[str, None] = analysis_result["consensus"].get("agreement")
    consensus_timeframe: Union[str, None] = analysis_result["consensus"].get("timeframe")


    if consensus_signal == "BUY":
         analysis_result["recommendations"].append({
            "action": "BUY",
            "positionSize": "Consider a standard position size." if risk_level == "Medium" else ("Consider a slightly larger position size." if risk_level in ["Low", "Very Low"] else "Consider a smaller position size."),
            "reasoning": f"Overall consensus is Bullish ({consensus_agreement}). Technical models show bullish signals. Review key levels for potential entry points."
         })
    elif consensus_signal == "SELL":
         analysis_result["recommendations"].append({
            "action": "SELL",
            "positionSize": "Consider a standard position size." if risk_level == "Medium" else ("Consider a slightly larger position size (for short positions)." if risk_level in ["Low", "Very Low"] else "Consider a smaller position size."),
            "reasoning": f"Overall consensus is Bearish ({consensus_agreement}). Technical models show bearish signals. Review key levels for potential exit points or short entry."
         })
    elif consensus_signal == "HOLD":
         analysis_result["recommendations"].append({
             "action": "HOLD",
             "positionSize": "Maintain current position or wait for clearer signals.",
             "reasoning": f"Overall consensus is Neutral or Mixed ({consensus_agreement}). Technical models provide conflicting or weak signals. Waiting for clearer direction is advised."
         })
    else: # N/A or other unknown signal
        analysis_result["recommendations"].append({
            "action": "UNKNOWN",
            "positionSize": "Exercise caution. Avoid new positions.",
            "reasoning": "Consensus could not be determined, possibly due to data or model errors."
        })


    # Add risk recommendation
    analysis_result["recommendations"].append({
         "action": "RISK FACTORS",
         "positionSize": analysis_result["riskAssessment"].get("recommendation", "Consider your risk profile."),
         "reasoning": f"Risk Level: {risk_level}. Volatility: {analysis_result['riskAssessment'].get('volatility', 'N/A')}. Factors: {'; '.join(analysis_result['riskAssessment'].get('factors', []))}"
    })

    # Add timeframe recommendation
    analysis_result["recommendations"].append({
         "action": "TIMEFRAME",
         "positionSize": "N/A",
         "reasoning": f"Primary signals are relevant for a {consensus_timeframe} timeframe. Review the analysis regularly as conditions change."
    })

    # Final technical indicator values for summary (latest non-NaN values)
    indicators_summary: Dict[str, Any] = {}
    df_with_indicators: pd.DataFrame = stock_data_obj.get_dataframe() # Get the DataFrame with indicators

    if not df_with_indicators.empty:
        latest_row: pd.Series = df_with_indicators.iloc[-1]

        # Get the names of the indicator columns directly from the DataFrame
        # Exclude original OHLCV columns
        original_cols: List[str] = ['open', 'high', 'low', 'close', 'volume']
        indicator_cols_in_df: List[str] = [col for col in df_with_indicators.columns if col not in original_cols]

        for col in indicator_cols_in_df:
            val: Any = latest_row.get(col)
            # Check if the latest value is not NaN
            if pd.notna(val):
                 # Handle complex indicator columns like MACD_macd_line or BollingerBands_20_2_upper
                 parts: List[str] = col.split('_')
                 if parts[0] in ['MACD', 'BollingerBands']:
                     base_name: str = parts[0]
                     if base_name not in indicators_summary:
                         indicators_summary[base_name] = {}
                     # Determine sub-name based on indicator type and parts
                     # MACD: MACD_macd_line, MACD_signal_line, MACD_histogram
                     if base_name == 'MACD' and len(parts) > 1 and parts[1] in ['macd_line', 'signal_line', 'histogram']:
                         sub_name: str = '_'.join(parts[1:])
                     # BollingerBands: BollingerBands_period_std_upper, ..._middle, ..._lower
                     elif base_name == 'BollingerBands' and len(parts) > 3 and parts[3] in ['upper', 'middle', 'lower']:
                         sub_name: str = parts[3]
                     else:
                         sub_name = col # Fallback for unexpected naming

                     # Format numerical values
                     indicators_summary[base_name][sub_name] = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                 else:
                      # Handle simple indicator columns (like SMA, EMA, RSI, ATR)
                      indicators_summary[col] = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
            else:
                 # If latest value is NaN, report as N/A
                 if col.startswith('MACD_') or col.startswith('BollingerBands_'):
                    parts: List[str] = col.split('_')
                    if parts[0] in ['MACD', 'BollingerBands']:
                        base_name: str = parts[0]
                        if base_name not in indicators_summary:
                             indicators_summary[base_name] = {}
                        if base_name == 'MACD' and len(parts) > 1 and parts[1] in ['macd_line', 'signal_line', 'histogram']:
                            sub_name = '_'.join(parts[1:])
                        elif base_name == 'BollingerBands' and len(parts) > 3 and parts[3] in ['upper', 'middle', 'lower']:
                             sub_name = parts[3]
                        else:
                             sub_name = col
                        indicators_summary[base_name][sub_name] = 'N/A'
                    else:
                        indicators_summary[col] = 'N/A'
                 else:
                    indicators_summary[col] = 'N/A'


    analysis_result["technicalIndicators"] = indicators_summary


except (InvalidSymbolError, StockDataFetchError) as e:
    # Handle errors during data fetching
    analysis_result["overallStatus"] = "failure"
    analysis_result["overallError"] = type(e).__name__
    analysis_result["overallMessage"] = str(e)
    analysis_result["skippedAnalysis"].append(f"Data Fetch Failed: {str(e)}")
    print(f"Critical Error during data fetch: {e}")

except IndicatorCalculationError as e:
    # Handle errors during indicator calculation
    analysis_result["overallStatus"] = "failure" # Indicator calculation failure is critical
    analysis_result["overallError"] = type(e).__name__
    analysis_result["overallMessage"] = str(e)
    analysis_result["skippedAnalysis"].append(f"Indicator Calculation Failed: {str(e)}")
    print(f"Critical Error during indicator calculation: {e}")

except Exception as e:
    # Handle any other unexpected critical errors
    analysis_result["overallStatus"] = "failure"
    analysis_result["overallError"] = type(e).__name__
    analysis_result["overallMessage"] = f"An unexpected critical error occurred: {e}"
    analysis_result["skippedAnalysis"].append(f"Critical Error: {str(e)}")
    print(f"An unexpected critical error occurred: {e}")


# --- End of Refactored Orchestration Logic ---


# Display the results based on the analysis_result dictionary

# Prepare data for the table
summary_data: List[Dict[str, Any]] = []

# Add overall error row if applicable
if analysis_result.get('overallStatus') == 'failure':
     summary_data.append({
        "Symbol": analysis_result.get('symbol', stock_symbol), # Use input symbol if result symbol is None
        "Analysis Section": "Overall Error",
        "Signal": "FAILURE",
        "Confidence": "N/A",
        "Timeframe": "N/A",
        "Key Information": f"Error Type: {analysis_result.get('overallError')}",
        "Reasoning/Notes": analysis_result.get('overallMessage', 'See logs for details.'),
        "Recommendation": "Cannot proceed with analysis."
     })
else:
    # Add overall consensus if available and no critical error
    consensus: Union[Dict[str, Any], None] = analysis_result.get('consensus')
    if consensus:
        summary_data.append({
            "Symbol": analysis_result.get('symbol', stock_symbol),
            "Analysis Section": "Consensus",
            "Signal": consensus.get('signal', 'N/A'),
            "Confidence": f"{consensus.get('confidence', 'N/A')}%",
            "Timeframe": consensus.get('timeframe', 'N/A'),
            "Key Information": f"Agreement: {consensus.get('agreement', 'N/A')}",
            "Reasoning/Notes": "; ".join(consensus.get('reasoning', [])),
            "Recommendation": None # Recommendations are handled separately
        })

    # Add individual model results (only successful ones)
    for model_name, result in analysis_result.get('modelResults', {}).items():
        if result: # Only include models that ran successfully
            summary_data.append({
                "Symbol": analysis_result.get('symbol', stock_symbol),
                "Analysis Section": result.get('model', model_name),
                "Signal": result.get('signal', 'N/A'),
                "Confidence": f"{result.get('confidence', 'N/A')}%",
                "Timeframe": result.get('timeframe', 'N/A'),
                # Dynamically add key info based on model result structure
                "Key Information": "; ".join([f"{k}: {v}" for k,v in result.get('keyLevels', {}).items()]) or None,
                "Reasoning/Notes": "; ".join(result.get('reasoning', [])),
                "Recommendation": None
            })

    # Add Risk Assessment if available
    risk_assessment: Union[Dict[str, Any], None] = analysis_result.get('riskAssessment')
    if risk_assessment:
        summary_data.append({
            "Symbol": analysis_result.get('symbol', stock_symbol),
            "Analysis Section": "Risk Assessment",
            "Signal": risk_assessment.get('level', 'N/A'), # Using Risk Level as the 'Signal' for this row
            "Confidence": None,
            "Timeframe": None,
            "Key Information": f"Volatility: {risk_assessment.get('volatility', 'N/A')}, Drawdown: {risk_assessment.get('drawdown', 'N/A')}",
            "Reasoning/Notes": f"Factors: {'; '.join(risk_assessment.get('factors', []))}",
            "Recommendation": risk_assessment.get('recommendation', 'N/A')
        })

    # Add Key Levels Summary if available
    key_levels: Union[Dict[str, Any], None] = analysis_result.get('keyLevels')
    if key_levels:
        summary_data.append({
            "Symbol": analysis_result.get('symbol', stock_symbol),
            "Analysis Section": "Key Levels",
            "Signal": None,
            "Confidence": None,
            "Timeframe": None,
            "Key Information": f"Current Price: {key_levels.get('currentPrice', 'N/A')}, Support: {key_levels.get('keySupport', 'N/A')}, Resistance: {key_levels.get('keyResistance', 'N/A')}",
            "Reasoning/Notes": key_levels.get('note', None), # Include note if available
            "Recommendation": None
        })

    # Add Overall Recommendations
    for rec in analysis_result.get('recommendations', []):
        summary_data.append({
            "Symbol": analysis_result.get('symbol', stock_symbol),
            "Analysis Section": rec.get('action', 'Recommendation'), # Use action as section name
            "Signal": None, # Signal is part of the recommendation text
            "Confidence": None,
            "Timeframe": None, # Timeframe is in the recommendation reasoning
            "Key Information": f"Position Size: {rec.get('positionSize', 'N/A')}",
            "Reasoning/Notes": rec.get('reasoning', 'N/A'),
            "Recommendation": rec.get('action', 'N/A') # Repeat action here for clarity in the Recommendation column
        })

    # Handle skipped analysis sections (due to insufficient data or model errors)
    for skipped in analysis_result.get('skippedAnalysis', []):
         summary_data.append({
            "Symbol": analysis_result.get('symbol', stock_symbol),
            "Analysis Section": "Skipped Analysis",
            "Signal": "N/A",
            "Confidence": "N/A",
            "Timeframe": "N/A",
            "Key Information": None,
            "Reasoning/Notes": skipped,
            "Recommendation": "N/A"
         })


# Create DataFrame
# Check if summary_data is empty before creating DataFrame
if summary_data:
    summary_df: pd.DataFrame = pd.DataFrame(summary_data)

    # Define the desired column order
    desired_order: List[str] = ["Symbol", "Analysis Section", "Signal", "Confidence", "Timeframe", "Key Information", "Reasoning/Notes", "Recommendation"]

    # Reindex the DataFrame to match the desired order, adding missing columns with None
    summary_df = summary_df.reindex(columns=desired_order)

    # Display the table
    print("\n=== Summary Table ===")
    display(summary_df)
else:
    print("\nNo summary data to display (analysis may have failed early).")


# Also print the overall recommendation section separately for clarity
print("\n=== Overall Analysis and Recommendation ===")
symbol: Union[str, None] = analysis_result.get('symbol', stock_symbol)
overall_status: Union[str, None] = analysis_result.get('overallStatus')
overall_error: Union[str, None] = analysis_result.get('overallError')
overall_message: Union[str, None] = analysis_result.get('overallMessage')
consensus_output: Dict[str, Any] = analysis_result.get('consensus', {})
recommendations_output: List[Dict[str, Any]] = analysis_result.get('recommendations', [])
skipped_analysis_output: List[str] = analysis_result.get('skippedAnalysis', [])
model_errors_output: Dict[str, str] = analysis_result.get('modelErrors', {})


if overall_status == 'failure':
    print(f"Analysis failed for {symbol}: {overall_error}")
    if overall_message:
        print(f"Details: {overall_message}")
elif overall_status == 'partial_success':
     print(f"Analysis completed with some issues for {symbol}.")
     # Print details about partial success, like which models failed
     print("\nNote: Some analysis sections were skipped or reported errors:")
     for skipped in skipped_analysis_output:
         print(f"- {skipped}")
     if model_errors_output:
        print("\nModel specific errors:")
        for model_name, error_msg in model_errors_output.items():
            print(f"- {model_name}: {error_msg}")

else: # overallStatus == 'success'
    print(f"\nConsensus Signal for {symbol}:")
    if consensus_output:
        print(f"  Signal: {consensus_output.get('signal', 'N/A')}")
        print(f"  Confidence: {consensus_output.get('confidence', 'N/A')}%")
        print(f"  Agreement: {consensus_output.get('agreement', 'N/A')}")
        print(f"  Timeframe: {consensus_output.get('timeframe', 'N/A')}")
        print("  Reasoning:")
        for reason in consensus_output.get('reasoning', []):
            print(f"    - {reason}")
    else:
        print("  Consensus data not available.")

    print("\nOverall Recommendations:")
    if recommendations_output:
        for i, rec in enumerate(recommendations_output):
            print(f"{i + 1}. Action: {rec.get('action', 'N/A')}")
            print(f"   Position Size: {rec.get('positionSize', 'N/A')}")
            print(f"   Reasoning: {rec.get('reasoning', 'N/A')}")
    else:
        print("  No specific recommendations generated.")

    if skipped_analysis_output:
        print("\nNote: Some analysis sections were skipped due to insufficient data:")
        for skipped in skipped_analysis_output:
             print(f"- {skipped}")

    if model_errors_output:
        print("\nModel specific errors:")
        for model_name, error_msg in model_errors_output.items():
            print(f"- {model_name}: {error_msg}")