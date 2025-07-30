// technical-indicators.js
class TechnicalIndicators {
    static calculateSMA(data, period) {
        const result = [];
        for (let i = period - 1; i < data.length; i++) {
            const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
            result.push(sum / period);
        }
        return result;
    }

    static calculateEMA(data, period) {
        const result = [];
        const multiplier = 2 / (period + 1);
        result[0] = data[0];
        
        for (let i = 1; i < data.length; i++) {
            result[i] = (data[i] * multiplier) + (result[i - 1] * (1 - multiplier));
        }
        return result;
    }

    static calculateRSI(data, period = 14) {
        const gains = [];
        const losses = [];
        
        for (let i = 1; i < data.length; i++) {
            const change = data[i] - data[i - 1];
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? Math.abs(change) : 0);
        }
        
        const avgGains = this.calculateSMA(gains, period);
        const avgLosses = this.calculateSMA(losses, period);
        
        return avgGains.map((gain, i) => {
            const rs = gain / avgLosses[i];
            return 100 - (100 / (1 + rs));
        });
    }

    static calculateMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const emaFast = this.calculateEMA(data, fastPeriod);
        const emaSlow = this.calculateEMA(data, slowPeriod);
        
        const macd = [];
        for (let i = 0; i < Math.min(emaFast.length, emaSlow.length); i++) {
            macd.push(emaFast[i] - emaSlow[i]);
        }
        
        const signal = this.calculateEMA(macd, signalPeriod);
        const histogram = [];
        
        for (let i = 0; i < Math.min(macd.length, signal.length); i++) {
            histogram.push(macd[i] - signal[i]);
        }
        
        return { macd, signal, histogram };
    }

    static calculateBollingerBands(data, period = 20, stdDev = 2) {
        const sma = this.calculateSMA(data, period);
        const upper = [];
        const lower = [];
        
        for (let i = period - 1; i < data.length; i++) {
            const slice = data.slice(i - period + 1, i + 1);
            const mean = slice.reduce((a, b) => a + b) / period;
            const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
            const std = Math.sqrt(variance);
            
            upper.push(sma[i - period + 1] + (std * stdDev));
            lower.push(sma[i - period + 1] - (std * stdDev));
        }
        
        return { upper, lower, middle: sma };
    }

    static calculateATR(highs, lows, closes, period = 14) {
        const trueRanges = [];
        
        for (let i = 1; i < closes.length; i++) {
            const tr1 = highs[i] - lows[i];
            const tr2 = Math.abs(highs[i] - closes[i - 1]);
            const tr3 = Math.abs(lows[i] - closes[i - 1]);
            trueRanges.push(Math.max(tr1, tr2, tr3));
        }
        
        return this.calculateSMA(trueRanges, period);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = TechnicalIndicators;
}