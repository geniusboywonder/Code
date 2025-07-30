 // moving-average-crossover-model.js
const TechnicalIndicators = require('./technical-indicators');

class MovingAverageCrossoverModel {
    constructor(fastPeriod = 50, slowPeriod = 200) {
        this.fastPeriod = fastPeriod;
        this.slowPeriod = slowPeriod;
        this.name = `MA Crossover (${fastPeriod}/${slowPeriod})`;
    }

    analyze(priceData) {
        const closes = priceData.map(d => d.close);
        
        if (closes.length < this.slowPeriod) {
            throw new Error(`Insufficient data. Need at least ${this.slowPeriod} periods.`);
        }

        const fastMA = TechnicalIndicators.calculateSMA(closes, this.fastPeriod);
        const slowMA = TechnicalIndicators.calculateSMA(closes, this.slowPeriod);

        const currentFast = fastMA[fastMA.length - 1];
        const currentSlow = slowMA[slowMA.length - 1];
        const prevFast = fastMA[fastMA.length - 2];
        const prevSlow = slowMA[slowMA.length - 2];
        const currentPrice = closes[closes.length - 1];

        let trendDirection = "Sideways";
        let signal = "HOLD";
        let confidence = 0;

        // Golden Cross / Death Cross detection
        if (currentFast > currentSlow && prevFast <= prevSlow) {
            signal = "BUY";
            trendDirection = "Golden Cross - Strong Uptrend";
            confidence = 85;
        } else if (currentFast < currentSlow && prevFast >= prevSlow) {
            signal = "SELL";
            trendDirection = "Death Cross - Strong Downtrend";
            confidence = 85;
        } else if (currentFast > currentSlow) {
            trendDirection = "Uptrend";
            signal = currentPrice > currentFast ? "BUY" : "WAIT";
            confidence = 60;
        } else if (currentFast < currentSlow) {
            trendDirection = "Downtrend";
            signal = currentPrice < currentFast ? "SELL" : "WAIT";
            confidence = 60;
        }

        const maSeparation = Math.abs(currentFast - currentSlow) / currentSlow * 100;
        let trendStrength = "Weak";
        
        if (maSeparation > 10) {
            trendStrength = "Very Strong";
            confidence += 15;
        } else if (maSeparation > 5) {
            trendStrength = "Strong";
            confidence += 10;
        } else if (maSeparation > 2) {
            trendStrength = "Moderate";
            confidence += 5;
        }

        return {
            model: this.name,
            signal: signal,
            confidence: Math.min(confidence, 100),
            trendDirection: trendDirection,
            trendStrength: trendStrength,
            timeframe: "Long-term (3-12 months)",
            keyLevels: {
                fastMA: currentFast.toFixed(2),
                slowMA: currentSlow.toFixed(2),
                support: Math.min(currentFast, currentSlow).toFixed(2),
                resistance: (Math.max(currentFast, currentSlow) * 1.02).toFixed(2),
                maSeparation: maSeparation.toFixed(2) + "%"
            },
            reasoning: [
                `${this.fastPeriod}-day MA: ${currentFast.toFixed(2)}`,
                `${this.slowPeriod}-day MA: ${currentSlow.toFixed(2)}`,
                `Trend: ${trendDirection}`,
                `Strength: ${trendStrength}`
            ]
        };
    }
}

// Usage example
async function testMovingAverageModel() {
    const model = new MovingAverageCrossoverModel(50, 200);
    
    // Sample price data
    const sampleData = [
        {close: 100}, {close: 101}, {close: 102}, {close: 103},
        // ... add more data points (need at least 200)
    ];
    
    try {
        const result = model.analyze(sampleData);
        console.log("Moving Average Analysis:", result);
    } catch (error) {
        console.error("Analysis failed:", error.message);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = MovingAverageCrossoverModel;
}
3. RSI Mean Reversion Model
// rsi-mean-reversion-model.js
const TechnicalIndicators = require('./technical-indicators');

class RSIMeanReversionModel {
    constructor(rsiPeriod = 14, oversoldLevel = 30, overboughtLevel = 70) {
        this.rsiPeriod = rsiPeriod;
        this.oversoldLevel = oversoldLevel;
        this.overboughtLevel = overboughtLevel;
        this.name = `RSI Mean Reversion (${rsiPeriod})`;
    }

    analyze(priceData) {
        const closes = priceData.map(d => d.close);
        
        if (closes.length < this.rsiPeriod + 20) {
            throw new Error(`Insufficient data. Need at least ${this.rsiPeriod + 20} periods.`);
        }

        const rsi = TechnicalIndicators.calculateRSI(closes, this.rsiPeriod);
        const sma20 = TechnicalIndicators.calculateSMA(closes, 20);
        
        const currentRSI = rsi[rsi.length - 1];
        const prevRSI = rsi[rsi.length - 2];
        const currentPrice = closes[closes.length - 1];
        const currentSMA20 = sma20[sma20.length - 1];

        let signal = "HOLD";
        let confidence = 0;
        let reasoning = [];

        // RSI-based signals
        if (currentRSI < this.oversoldLevel) {
            signal = "BUY";
            confidence += 40;
            reasoning.push(`RSI oversold (${currentRSI.toFixed(1)} < ${this.oversoldLevel})`);
            
            if (currentRSI > prevRSI) {
                confidence += 20;
                reasoning.push("RSI showing upward momentum");
            }
        } else if (currentRSI > this.overboughtLevel) {
            signal = "SELL";
            confidence += 40;
            reasoning.push(`RSI overbought (${currentRSI.toFixed(1)} > ${this.overboughtLevel})`);
            
            if (currentRSI < prevRSI) {
                confidence += 20;
                reasoning.push("RSI showing downward momentum");
            }
        }

        // Price vs SMA confirmation
        if (signal === "BUY" && currentPrice > currentSMA20) {
            confidence += 15;
            reasoning.push("Price above 20-day SMA confirms strength");
        } else if (signal === "SELL" && currentPrice < currentSMA20) {
            confidence += 15;
            reasoning.push("Price below 20-day SMA confirms weakness");
        }

        const divergence = this.detectDivergence(closes.slice(-20), rsi.slice(-20));
        if (divergence.type !== "None") {
            confidence += divergence.strength;
            reasoning.push(`${divergence.type} divergence detected`);
        }

        return {
            model: this.name,
            signal: signal,
            confidence: Math.min(confidence, 100),
            timeframe: "Short to Medium-term (2-8 weeks)",
            reasoning: reasoning,
            rsiAnalysis: {
                current: currentRSI.toFixed(2),
                level: this.getRSILevel(currentRSI),
                momentum: currentRSI > prevRSI ? "Rising" : "Falling",
                divergence: divergence
            },
            keyLevels: {
                oversold: this.oversoldLevel,
                overbought: this.overboughtLevel,
                neutral: 50,
                currentLevel: currentRSI.toFixed(2)
            }
        };
    }

    getRSILevel(rsi) {
        if (rsi < 20) return "Extremely Oversold";
        if (rsi < 30) return "Oversold";
        if (rsi < 40) return "Weak";
        if (rsi < 60) return "Neutral";
        if (rsi < 70) return "Strong";
        if (rsi < 80) return "Overbought";
        return "Extremely Overbought";
    }

    detectDivergence(prices, rsiValues) {
        if (prices.length < 10 || rsiValues.length < 10) {
            return { type: "None", strength: 0 };
        }

        const recentPrices = prices.slice(-10);
        const recentRSI = rsiValues.slice(-10);
        
        const priceHigh = Math.max(...recentPrices);
        const priceLow = Math.min(...recentPrices);
        const rsiHigh = Math.max(...recentRSI);
        const rsiLow = Math.min(...recentRSI);
        
        const priceHighIndex = recentPrices.indexOf(priceHigh);
        const priceLowIndex = recentPrices.indexOf(priceLow);
        const rsiHighIndex = recentRSI.indexOf(rsiHigh);
        const rsiLowIndex = recentRSI.indexOf(rsiLow);

        // Bullish divergence
        if (priceLowIndex > rsiLowIndex && recentPrices[priceLowIndex] < recentPrices[rsiLowIndex] && 
            recentRSI[priceLowIndex] > recentRSI[rsiLowIndex]) {
            return { type: "Bullish", strength: 25 };
        }

        // Bearish divergence
        if (priceHighIndex > rsiHighIndex && recentPrices[priceHighIndex] > recentPrices[rsiHighIndex] && 
            recentRSI[priceHighIndex] < recentRSI[rsiHighIndex]) {
            return { type: "Bearish", strength: 25 };
        }

        return { type: "None", strength: 0 };
    }
}

// Usage example
async function testRSIModel() {
    const model = new RSIMeanReversionModel(14, 30, 70);
    
    // Sample price data with RSI oversold condition
    const sampleData = Array.from({length: 50}, (_, i) => ({
        close: 100 - (i * 0.5) + Math.random() * 2 // Declining trend
    }));
    
    try {
        const result = model.analyze(sampleData);
        console.log("RSI Analysis:", result);
        console.log(`Signal: ${result.signal} (${result.confidence}% confidence)`);
        console.log(`RSI Level: ${result.rsiAnalysis.current} (${result.rsiAnalysis.level})`);
    } catch (error) {
        console.error("Analysis failed:", error.message);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = RSIMeanReversionModel;
}
