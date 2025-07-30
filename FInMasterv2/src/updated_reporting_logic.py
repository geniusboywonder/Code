
# === Individual Model Summary Table ===
individual_model_rows = []
for model_name, result in analysis_result.get("modelResults", {}).items():
    if result:
        individual_model_rows.append({
            "Symbol": analysis_result.get("symbol", stock_symbol),
            "Model": result.get("model", model_name),
            "Signal": result.get("signal", "N/A"),
            "Confidence": f"{result.get('confidence', 'N/A')}%",
            "Timeframe": result.get("timeframe", "N/A"),
            "Trend Direction": result.get("trendDirection", "N/A"),
            "Risk Level": analysis_result.get("riskAssessment", {}).get("level", "N/A"),
            "Key Reasoning": "; ".join(result.get("reasoning", [])),
            "Support": result.get("keyLevels", {}).get("support", "N/A"),
            "Resistance": result.get("keyLevels", {}).get("resistance", "N/A")
        })

# Add consensus row to individual model table
consensus = analysis_result.get("consensus", {})
individual_model_rows.append({
    "Symbol": analysis_result.get("symbol", stock_symbol),
    "Model": "🎯 CONSENSUS",
    "Signal": consensus.get("signal", "N/A"),
    "Confidence": f"{consensus.get("confidence", "N/A")}%",
    "Timeframe": consensus.get("timeframe", "N/A"),
    "Trend Direction": consensus.get("agreement", "N/A"),
    "Risk Level": analysis_result.get("riskAssessment", {}).get("level", "N/A"),
    "Key Reasoning": "; ".join(consensus.get("reasoning", [])),
    "Support": analysis_result.get("keyLevels", {}).get("keySupport", "N/A"),
    "Resistance": analysis_result.get("keyLevels", {}).get("keyResistance", "N/A")
})

individual_model_df = pd.DataFrame(individual_model_rows)
print("\n=== Individual Model Summary Table ===")
print(individual_model_df.to_string(index=False))

# === Consensus Summary Table ===
consensus_rows = []
symbol = analysis_result.get("symbol", stock_symbol)
consensus_rows.append({
    "Symbol": symbol,
    "Current Price": f"USD {analysis_result.get('currentPrice', 'N/A')}",
    "Consensus Signal": consensus.get("signal", "N/A"),
    "Confidence": f"{consensus.get("confidence", "N/A")}%",
    "Agreement": consensus.get("agreement", "N/A"),
    "Risk Level": analysis_result.get("riskAssessment", {}).get("level", "N/A"),
    "Recommendation": consensus.get("signal", "N/A"),
    "Position Size": analysis_result.get("recommendations", [{}])[0].get("positionSize", "N/A"),
    "Support": analysis_result.get("keyLevels", {}).get("keySupport", "N/A"),
    "Resistance": analysis_result.get("keyLevels", {}).get("keyResistance", "N/A"),
    "Next Review": pd.Timestamp.now().normalize() + pd.Timedelta(days=30)
})

consensus_df = pd.DataFrame(consensus_rows)
print("\n=== Consensus Summary Table ===")
print(consensus_df.to_string(index=False))

# === Portfolio Summary Table ===
portfolio_rows = []
bullish_count = 0
bearish_count = 0
buy_count = 0
for model_name, result in analysis_result.get("modelResults", {}).items():
    if result:
        signal = result.get("signal", "N/A")
        confidence = f"{result.get("confidence", "N/A")}%"
        risk = analysis_result.get("riskAssessment", {}).get("level", "N/A")
        timeframe = result.get("timeframe", "N/A")
        reasoning = "; ".join(result.get("reasoning", []))
        if signal == "BUY":
            bullish_count += 1
            buy_count += 1
        elif signal == "SELL":
            bearish_count += 1
        portfolio_rows.append({
            "Symbol": symbol,
            "Signal": signal,
            "Confidence": confidence,
            "Risk": risk,
            "Models Bullish": f"{bullish_count}/4",
            "Models Bearish": f"{bearish_count}/4",
            "Primary Timeframe": timeframe,
            "Action": signal,
            "Notes": reasoning[:25] + "..." if len(reasoning) > 25 else reasoning
        })

# Add portfolio summary row
portfolio_rows.append({
    "Symbol": "PORTFOLIO",
    "Signal": f"{buy_count} BUY",
    "Confidence": f"{consensus.get("confidence", "N/A")}%",
    "Risk": analysis_result.get("riskAssessment", {}).get("level", "N/A"),
    "Models Bullish": bullish_count,
    "Models Bearish": bearish_count,
    "Primary Timeframe": consensus.get("timeframe", "Mixed"),
    "Action": "REBALANCE",
    "Notes": "Portfolio shows mod.."
})

portfolio_df = pd.DataFrame(portfolio_rows)
print("\n=== Portfolio Summary Table ===")
print(portfolio_df.to_string(index=False))
