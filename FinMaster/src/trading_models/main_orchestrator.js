// main-trend-orchestrator.js
const TechnicalIndicators = require('./technical-indicators');
const MovingAverageCrossoverModel = require('./moving-average-crossover-model');
const RSIMeanReversionModel = require('./rsi-mean-reversion-model');
const MACDMomentumModel = require('./macd-momentum-model');
const BollingerBandsModel = require('./bollinger-bands-model');
const SummaryTableGenerator = require('./summary-table-generator');

class MainTrendOrchestrator {
    constructor() {
        this.models = {
            movingAverage: new MovingAverageCrossoverModel(50, 200),
            rsiMeanReversion: new RSIMeanReversionModel(14, 30, 70),
            macdMomentum: new MACDMomentumModel(12, 26, 9),
            bollingerBands: new BollingerBandsModel(20, 2)
        };
    }

    async analyzeSymbol(priceData, symbol = "UNKNOWN") {
        const modelResults = [];
        const modelErrors = {};

        // Run all models
        for (const [modelName, model] of Object.entries(this.models)) {
            try {
                const result = model.analyze(priceData);
                modelResults.push(result);
            } catch (error) {
                modelErrors[modelName] = error.message;
                console.warn(`${modelName} analysis failed:`, error.message);
            }
        }

        // Generate consensus
        const consensus = this.generateConsensus(modelResults);
        
        // Generate summary tables
        const modelSummaryTable = SummaryTableGenerator.generateModelSummaryTable(modelResults);
        
        const analysisResult = {
            symbol: symbol,
            analysisDate: new Date().toISOString().split('T')[0],
            currentPrice: priceData[priceData.length - 1].close,
            modelResults: modelResults,
            modelErrors: modelErrors,
            consensus: consensus,
            summaryTable: modelSummaryTable
        };

        const consensusSummaryTable = SummaryTableGenerator.generateConsensusSummaryTable(analysisResult);

        return {
            ...analysisResult,
            consensusSummaryTable: consensusSummaryTable
        };
    }

    generateConsensus(modelResults) {
        if (modelResults.length === 0) {
            return {
                signal: "HOLD",
                confidence: 0,
                agreement: "No valid signals",
                reasoning: ["Insufficient model data"]
            };
        }

        // Count signals
        const signalCounts = {
            BUY: modelResults.filter(m => m.signal === "BUY").length,
            SELL: modelResults.filter(m => m.signal === "SELL").length,
            HOLD: modelResults.filter(m => m.signal === "HOLD").length,
            WAIT: modelResults.filter(m => m.signal === "WAIT").length
        };

        const totalModels = modelResults.length;
        
        // Determine consensus signal
        let consensusSignal = "HOLD";
        let agreement = "Mixed";
        
        const buySignals = signalCounts.

BUY;
        const sellSignals = signalCounts.

SELL;

        if (buySignals > totalModels * 0.6) {
            consensusSignal = "BUY";
            agreement = "Strong Bullish";
        } else if (sellSignals > totalModels * 0.6) {
            consensusSignal = "SELL";
            agreement = "Strong Bearish";
        } else if (buySignals > sellSignals) {
            consensusSignal = "BUY";
            agreement = "Moderate Bullish";
        } else if (sellSignals > buySignals) {
            consensusSignal = "SELL";
            agreement = "Moderate Bearish";
        }

        // Calculate weighted confidence
        const avgConfidence = modelResults.reduce((sum, model) => sum + model.confidence, 0) / totalModels;

        // Generate reasoning
        const reasoning = [];
        reasoning.push(`${buySignals}/${totalModels} models bullish, ${sellSignals}/${totalModels} bearish`);
        
        modelResults.forEach(model => {
            if (model.confidence > 70) {
                reasoning.push(`${model.model}: ${model.signal} (${model.confidence}% confidence)`);
            }
        });

        return {
            signal: consensusSignal,
            confidence: Math.round(avgConfidence),
            agreement: agreement,
            signalDistribution: signalCounts,
            reasoning: reasoning,
            modelCount: totalModels
        };
    }

    async analyzeMultipleSymbols(symbolDataPairs) {
        const results = [];
        
        for (const { symbol, priceData } of symbolDataPairs) {
            try {
                console.log(`Analyzing ${symbol}...`);
                const analysis = await this.analyzeSymbol(priceData, symbol);
                results.push(analysis);
            } catch (error) {
                console.error(`Failed to analyze ${symbol}:`, error.message);
                results.push({
                    symbol: symbol,
                    error: error.message,
                    analysisDate: new Date().toISOString().split('T')[0]
                });
            }
        }
        
        // Generate comparison table
        const comparisonTable = SummaryTableGenerator.generateComparisonTable(results);
        
        return {
            individualAnalyses: results,
            comparisonTable: comparisonTable,
            summary: this.generatePortfolioSummary(results)
        };
    }

    generatePortfolioSummary(analyses) {
        const validAnalyses = analyses.filter(a => !a.error);
        
        if (validAnalyses.length === 0) {
            return { message: "No valid analyses to summarize" };
        }

        const signalCounts = {
            BUY: validAnalyses.filter(a => a.consensus?.signal === "BUY").length,
            SELL: validAnalyses.filter(a => a.consensus?.signal === "SELL").length,
            HOLD: validAnalyses.filter(a => a.consensus?.signal === "HOLD").length,
            WAIT: validAnalyses.filter(a => a.consensus?.signal === "WAIT").length
        };

        const avgConfidence = validAnalyses.reduce((sum, a) => sum + (a.consensus?.confidence || 0), 0) / validAnalyses.length;

        return {
            totalSymbols: analyses.length,
            validAnalyses: validAnalyses.length,
            signalDistribution: signalCounts,
            averageConfidence: Math.round(avgConfidence),
            recommendation: this.generatePortfolioRecommendation(signalCounts, avgConfidence)
        };
    }

    generatePortfolioRecommendation(signalCounts, avgConfidence) {
        const total = Object.values(signalCounts).reduce((a, b) => a + b, 0);
        const bullishRatio = signalCounts.BUY / total;
        const bearishRatio = signalCounts.

SELL / total;

        if (bullishRatio > 0.6 && avgConfidence > 70) {
            return "Strong portfolio buy signals - consider increasing equity allocation";
        } else if (bullishRatio > 0.4 && avgConfidence > 60) {
            return "Moderate bullish signals - selective position increases recommended";
        } else if (bearishRatio > 0.6) {
            return "Bearish signals dominate - consider reducing risk exposure";
        } else {
            return "Mixed signals - maintain current allocation with selective adjustments";
        }
    }
}

// Usage example
async function demonstrateOrchestrator() {
    const orchestrator = new MainTrendOrchestrator();
    
    // Sample price data (you would replace this with real Yahoo Finance data)
    const samplePriceData = Array.from({length: 252}, (_, i) => ({
        close: 100 + Math.sin(i * 0.02) * 10 + (i * 0.05) + Math.random() * 2,
        volume: 1000000 + Math.random() * 500000
    }));
    
    try {
        // Single symbol analysis
        console.log("=== SINGLE SYMBOL ANALYSIS ===");
        const singleAnalysis = await orchestrator.analyzeSymbol(samplePriceData, "AAPL");
        
        console.log(`\nSymbol: ${singleAnalysis.symbol}`);
        console.log(`Current Price: $${singleAnalysis.currentPrice.toFixed(2)}`);
        console.log(`Consensus: ${singleAnalysis.consensus.signal} (${singleAnalysis.consensus.confidence}% confidence)`);
        console.log(`Agreement: ${singleAnalysis.consensus.agreement}`);
        
        console.log("\n" + singleAnalysis.summaryTable);
        console.log("\n" + singleAnalysis.consensusSummaryTable);
        
        // Multiple symbols analysis
        console.log("\n=== MULTIPLE SYMBOLS ANALYSIS ===");
        const multipleSymbolData = [
            { symbol: "AAPL", priceData: samplePriceData },
            { symbol: "GOOGL", priceData: samplePriceData.map(d => ({...d, close: d.close * 15})) },
            { symbol: "MSFT", priceData: samplePriceData.map(d => ({...d, close: d.close * 2.5})) }
        ];
        
        const multipleAnalysis = await orchestrator.analyzeMultipleSymbols(multipleSymbolData);
        
        console.log("\n" + multipleAnalysis.comparisonTable);
        
        console.log("\n=== PORTFOLIO SUMMARY ===");
        console.log(`Total Symbols: ${multipleAnalysis.summary.totalSymbols}`);
        console.log(`Valid Analyses: ${multipleAnalysis.summary.validAnalyses}`);
        console.log(`Average Confidence: ${multipleAnalysis.summary.averageConfidence}%`);
        console.log(`Recommendation: ${multipleAnalysis.summary.recommendation}`);
        
    } catch (error) {
        console.error("Demonstration failed:", error);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = MainTrendOrchestrator;
}

// Run demonstration
// demonstrateOrchestrator();