 // bollinger-bands-model.js
const TechnicalIndicators = require('./technical-indicators');

class BollingerBandsModel {
    constructor(period = 20, stdDev = 2) {
        this.period = period;
        this.stdDev = stdDev;
        this.name = `Bollinger Bands (${period}, ${stdDev})`;
    }

    analyze(priceData) {
        const closes = priceData.map(d => d.close);
        const volumes = priceData.map(d => d.volume || 1000000); // Default volume if not provided
        
        if (closes.length < this.period + 10) {
            throw new Error(`Insufficient data. Need at least ${this.period + 10} periods.`);
        }

        const bb = TechnicalIndicators.calculateBollingerBands(closes, this.period, this.stdDev);
        const volumeSMA = TechnicalIndicators.calculateSMA(volumes, 20);
        
        const currentPrice = closes[closes.length - 1];
        const currentUpper = bb.upper[bb.upper.length - 1];
        const currentLower = bb.lower[bb.lower.length - 1];
        const currentMiddle = bb.middle[bb.middle.length - 1];
        const currentVolume = volumes[volumes.length - 1];
        const avgVolume = volumeSMA[volumeSMA.length - 1];

        let signal = "HOLD";
        let confidence = 0;
        let reasoning = [];

        // Band position analysis
        const upperDistance = (currentPrice - currentUpper) / currentUpper * 100;
        const lowerDistance = (currentLower - currentPrice) / currentLower * 100;
        const bandWidth = (currentUpper - currentLower) / currentMiddle * 100;

        // Price near bands
        if (currentPrice <= currentLower * 1.02) { // Within 2% of lower band
            signal = "BUY";
            confidence += 35;
            reasoning.push(`Price near lower band (${lowerDistance.toFixed(1)}% below)`);
            
            if (currentVolume > avgVolume * 1.2) {
                confidence += 15;
                reasoning.push("High volume confirms oversold bounce");
            }
        } else if (currentPrice >= currentUpper * 0.98) { // Within 2% of upper band
            signal = "SELL";
            confidence += 35;
            reasoning.push(`Price near upper band (${Math.abs(upperDistance).toFixed(1)}% above)`);
            
            if (currentVolume > avgVolume * 1.2) {
                confidence += 15;
                reasoning.push("High volume confirms overbought reversal");
            }
        }

        // Band squeeze detection
        const avgBandWidth = this.calculateAverageBandWidth(bb, 20);
        if (bandWidth < avgBandWidth * 0.8) {
            reasoning.push("Bollinger Band squeeze detected - breakout expected");
            confidence += 10;
        }

        // Middle band (SMA) analysis
        if (currentPrice > currentMiddle) {
            if (signal === "BUY") confidence += 10;
            reasoning.push("Price above middle band (bullish bias)");
        } else {
            if (signal === "SELL") confidence += 10;
            reasoning.push("Price below middle band (bearish bias)");
        }

        return {
            model: this.name,
            signal: signal,
            confidence: Math.min(confidence, 100),
            timeframe: "Short to Medium-term (2-6 weeks)",
            reasoning: reasoning,
            bollingerAnalysis: {
                currentPrice: currentPrice.toFixed(2),
                upperBand: currentUpper.toFixed(2),
                middleBand: currentMiddle.toFixed(2),
                lowerBand: currentLower.toFixed(2),
                bandWidth: bandWidth.toFixed(2) + "%",
                pricePosition: this.getPricePosition(currentPrice, currentUpper, currentLower, currentMiddle),
                squeeze: bandWidth < avgBandWidth * 0.8
            },
            keyLevels: {
                resistance: currentUpper.toFixed(2),
                support: currentLower.toFixed(2),
                pivot: currentMiddle.toFixed(2)
            }
        };
    }

    getPricePosition(price, upper, lower, middle) {
        if (price >= upper) return "Above Upper Band";
        if (price <= lower) return "Below Lower Band";
        if (price > middle) return "Upper Half";
        return "Lower Half";
    }

    calculateAverageBandWidth(bb, periods) {
        const bandWidths = [];
        const startIndex = Math.max(0, bb.upper.length - periods);
        
        for (let i = startIndex; i < bb.upper.length; i++) {
            const width = (bb.upper[i] - bb.lower[i]) / bb.middle[i] * 100;
            bandWidths.push(width);
        }
        
        return bandWidths.reduce((a, b) => a + b, 0) / bandWidths.length;
    }
}

// Usage example
async function testBollingerModel() {
    const model = new BollingerBandsModel(20, 2);
    
    // Sample price data with volatility
    const sampleData = Array.from({length: 50}, (_, i) => ({
        close: 100 + Math.sin(i * 0.2) * 10 + Math.random() * 3,
        volume: 1000000 + Math.random() * 500000
    }));
    
    try {
        const result = model.analyze(sampleData);
        console.log("Bollinger Bands Analysis:", result);
        console.log(`Signal: ${result.signal} (${result.confidence}% confidence)`);
        console.log(`Price: $${result.bollingerAnalysis.currentPrice}`);
        console.log(`Upper Band: $${result.bollingerAnalysis.upperBand}`);
        console.log(`Lower Band: $${result.bollingerAnalysis.lowerBand}`);
        console.log(`Position: ${result.bollingerAnalysis.pricePosition}`);
    } catch (error) {
        console.error("Analysis failed:", error.message);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = BollingerBandsModel;
}
