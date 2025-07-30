 // macd-momentum-model.js
const TechnicalIndicators = require('./technical-indicators');

class MACDMomentumModel {
    constructor(fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        this.fastPeriod = fastPeriod;
        this.slowPeriod = slowPeriod;
        this.signalPeriod = signalPeriod;
        this.name = `MACD Momentum (${fastPeriod},${slowPeriod},${signalPeriod})`;
    }

    analyze(priceData) {
        const closes = priceData.map(d => d.close);
        
        if (closes.length < this.slowPeriod + this.signalPeriod + 10) {
            throw new Error(`Insufficient data. Need at least ${this.slowPeriod + this.signalPeriod + 10} periods.`);
        }

        const macdData = TechnicalIndicators.calculateMACD(closes, this.fastPeriod, this.slowPeriod, this.signalPeriod);
        
        const currentMACD = macdData.macd[macdData.macd.length - 1];
        const currentSignal = macdData.signal[macdData.signal.length - 1];
        const currentHistogram = macdData.histogram[macdData.histogram.length - 1];
        const prevHistogram = macdData.histogram[macdData.histogram.length - 2];
        const prevMACD = macdData.macd[macdData.macd.length - 2];
        const prevSignal = macdData.signal[macdData.signal.length - 2];

        let signal = "HOLD";
        let confidence = 0;
        let reasoning = [];

        // MACD Line vs Signal Line
        if (currentMACD > currentSignal) {
            if (signal !== "SELL") signal = "BUY";
            confidence += 25;
            reasoning.push("MACD above signal line (bullish)");
        } else {
            signal = "SELL";
            confidence += 25;
            reasoning.push("MACD below signal line (bearish)");
        }

        // Histogram analysis (momentum)
        if (currentHistogram > 0 && currentHistogram > prevHistogram) {
            confidence += 20;
            reasoning.push("MACD histogram expanding (strengthening bullish momentum)");
        } else if (currentHistogram < 0 && currentHistogram < prevHistogram) {
            confidence += 20;
            reasoning.push("MACD histogram expanding (strengthening bearish momentum)");
        } else if (currentHistogram > 0 && currentHistogram < prevHistogram) {
            confidence -= 10;
            reasoning.push("MACD histogram contracting (weakening bullish momentum)");
        } else if (currentHistogram < 0 && currentHistogram > prevHistogram) {
            confidence -= 10;
            reasoning.push("MACD histogram contracting (weakening bearish momentum)");
        }

        // Zero line crossovers
        if (currentMACD > 0 && prevMACD <= 0) {
            signal = "BUY";
            confidence += 30;
            reasoning.push("MACD crossed above zero line (strong bullish signal)");
        } else if (currentMACD < 0 && prevMACD >= 0) {
            signal = "SELL";
            confidence += 30;
            reasoning.push("MACD crossed below zero line (strong bearish signal)");
        }

        // Signal line crossovers
        if (currentMACD > currentSignal && prevMACD <= prevSignal) {
            if (signal !== "SELL") signal = "BUY";
            confidence += 25;
            reasoning.push("MACD bullish crossover");
        } else if (currentMACD < currentSignal && prevMACD >= prevSignal) {
            signal = "SELL";
            confidence += 25;
            reasoning.push("MACD bearish crossover");
        }

        return {
            model: this.name,
            signal: signal,
            confidence: Math.min(confidence, 100),
            timeframe: "Medium-term (1-3 months)",
            reasoning: reasoning,
            macdAnalysis: {
                macdLine: currentMACD.toFixed(4),
                signalLine: currentSignal.toFixed(4),
                histogram: currentHistogram.toFixed(4),
                trend: currentMACD > currentSignal ? "Bullish" : "Bearish",
                momentum: currentHistogram > prevHistogram ? "Strengthening" : "Weakening",
                position: currentMACD > 0 ? "Above Zero" : "Below Zero"
            },
            keyLevels: {
                support: currentMACD > 0 ? "0.0000" : Math.min(currentMACD, currentSignal).toFixed(4),
                resistance: currentMACD > 0 ? Math.max(currentMACD, currentSignal).toFixed(4) : "0.0000"
            }
        };
    }
}

// Usage example
async function testMACDModel() {
    const model = new MACDMomentumModel(12, 26, 9);
    
    // Sample price data with uptrend
    const sampleData = Array.from({length: 100}, (_, i) => ({
        close: 100 + (i * 0.3) + Math.sin(i * 0.1) * 2 // Uptrend with oscillation
    }));
    
    try {
        const result = model.analyze(sampleData);
        console.log("MACD Analysis:", result);
        console.log(`Signal: ${result.signal} (${result.confidence}% confidence)`);
        console.log(`MACD: ${result.macdAnalysis.macdLine} vs Signal: ${result.macdAnalysis.signalLine}`);
        console.log(`Trend: ${result.macdAnalysis.trend}, Momentum: ${result.macdAnalysis.momentum}`);
    } catch (error) {
        console.error("Analysis failed:", error.message);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = MACDMomentumModel;
}
