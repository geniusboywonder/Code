// summary-table-generator.js
class SummaryTableGenerator {
    
    static generateModelSummaryTable(modelResults) {
        const headers = [
            'Model', 'Signal', 'Confidence', 'Timeframe', 
            'Trend/Level', 'Key Reasoning', 'Support', 'Resistance'
        ];
        
        const rows = [];
        
        modelResults.forEach(result => {
            const reasoning = result.reasoning && result.reasoning.length > 0 
                ? result.reasoning[0].substring(0, 25) + '...'
                : 'Technical analysis';
                
            const trendLevel = result.trendDirection || 
                             result.rsiAnalysis?.level || 
                             result.macdAnalysis?.trend || 
                             result.bollingerAnalysis?.pricePosition || 'N/A';
            
            rows.push([
                result.model || 'Unknown',
                result.signal || 'N/A',
                `${result.confidence || 0}%`,
                result.timeframe || 'N/A',
                trendLevel,
                reasoning,
                result.keyLevels?.support || 'N/A',
                result.keyLevels?.resistance || 'N/A'
            ]);
        });
        
        return this.formatTable(headers, rows);
    }
    
    static generateConsensusSummaryTable(analysisResults) {
        const headers = [
            'Symbol', 'Current Price', 'Consensus Signal', 'Confidence', 
            'Agreement', 'Risk Level', 'Recommendation', 'Position Size'
        ];
        
        const rows = [];
        
        const analyses = Array.isArray(analysisResults) ? analysisResults : [analysisResults];
        
        analyses.forEach(analysis => {
            if (analysis.error) {
                rows.push([
                    analysis.symbol, 'N/A', 'ERROR', 'N/A', 'N/A', 
                    'N/A', analysis.error, 'N/A'
                ]);
            } else {
                const primaryRec = analysis.recommendations?.[0] || {};
                
                rows.push([
                    analysis.symbol,
                    `${analysis.currency} ${analysis.currentPrice?.toFixed(2)}`,
                    analysis.consensus?.signal || 'N/A',
                    `${analysis.consensus?.confidence || 0}%`,
                    analysis.consensus?.agreement || 'N/A',
                    analysis.riskAssessment?.level || 'N/A',
                    primaryRec.action || 'N/A',
                    primaryRec.positionSize || 'N/A'
                ]);
            }
        });
        
        return this.formatTable(headers, rows);
    }
    
    static generatePortfolioSummaryTable(portfolioAnalysis) {
        const headers = [
            'Symbol', 'Signal', 'Confidence', 'Risk', 'Models Bullish', 
            'Models Bearish', 'Primary Timeframe', 'Action', 'Notes'
        ];
        
        const rows = [];
        
        portfolioAnalysis.individualAnalyses.forEach(analysis => {
            if (analysis.error) {
                rows.push([
                    analysis.symbol, 'ERROR', 'N/A', 'N/A', 'N/A', 
                    'N/A', 'N/A', 'SKIP', analysis.error.substring(0, 20) + '...'
                ]);
            } else {
                const signals = analysis.consensus?.signalDistribution || {};
                const bullishCount = (signals.BUY || 0) + (signals.strongBuy || 0);
                const bearishCount = (signals.SELL || 0) + (signals.strongSell || 0);
                
                const notes = this.generatePortfolioNotes(analysis);
                
                rows.push([
                    analysis.symbol,
                    analysis.consensus?.signal || 'N/A',
                    `${analysis.consensus?.confidence || 0}%`,
                    analysis.riskAssessment?.level || 'N/A',
                    `${bullishCount}/${analysis.consensus?.modelCount || 0}`,
                    `${bearishCount}/${analysis.consensus?.modelCount || 0}`,
                    analysis.consensus?.timeframe || 'N/A',
                    analysis.recommendations?.[0]?.action || 'N/A',
                    notes
                ]);
            }
        });
        
        // Add portfolio summary row
        rows.push(['═'.repeat(8), '═'.repeat(8), '═'.repeat(10), '═'.repeat(6), 
                  '═'.repeat(12), '═'.repeat(13), '═'.repeat(15), '═'.repeat(8), '═'.repeat(20)]);
        
        rows.push([
            'PORTFOLIO',
            `${portfolioAnalysis.portfolioSignals.buy + portfolioAnalysis.portfolioSignals.strongBuy} BUY`,
            `${portfolioAnalysis.averageConfidence}%`,
            portfolioAnalysis.portfolioRisk.overall,
            `${portfolioAnalysis.portfolioSignals.buy + portfolioAnalysis.portfolioSignals.strongBuy}`,
            `${portfolioAnalysis.portfolioSignals.sell + portfolioAnalysis.portfolioSignals.strongSell}`,
            'Mixed',
            'REBALANCE',
            portfolioAnalysis.recommendations[0]?.substring(0, 20) + '...' || 'See details'
        ]);
        
        return this.formatTable(headers, rows);
    }
    
    static generatePortfolioNotes(analysis) {
        const notes = [];
        
        if (analysis.vixAnalysis?.buyingOpportunity) {
            notes.push('VIX Opportunity');
        }
        if (analysis.vixAnalysis?.cautionWarranted) {
            notes.push('VIX Caution');
        }
        if (analysis.riskAssessment?.level === 'High') {
            notes.push('High Risk');
        }
        if (analysis.consensus?.confidence > 80) {
            notes.push('High Confidence');
        }
        
        return notes.join(', ') || 'Standard';
    }
    
    static formatTable(headers, rows) {
        // Calculate column widths
        const colWidths = headers.map((header, i) => {
            const maxContentWidth = Math.max(
                header.length,
                ...rows.map(row => String(row[i] || '').length)
            );
            return Math.min(maxContentWidth + 2, 25); // Max width of 25 chars
        });
        
        // Create borders
        const topBorder = '┌' + colWidths.map(width => '─'.repeat(width)).join('┬') + '┐';
        const separator = '├' + colWidths.map(width => '─'.repeat(width)).join('┼') + '┤';
        const bottomBorder = '└' + colWidths.map(width => '─'.repeat(width)).join('┴') + '┘';
        
        // Format header
        const headerRow = '│' + headers.map((header, i) => 
            this.padString(header, colWidths[i])
        ).join('│') + '│';
        
        // Format data rows
        const dataRows = rows.map(row => 
            '│' + row.map((cell, i) => 
                this.padString(String(cell || ''), colWidths[i])
            ).join('│') + '│'
        );
        
        // Combine all parts
        return [
            topBorder,
            headerRow,
            separator,
            ...dataRows,
            bottomBorder
        ].join('\n');
    }
    
    static padString(str, width) {
        if (str.length > width - 2) {
            return ' ' + str.substring(0, width - 4) + '.. ';
        }
        const padding = width - str.length;
        const leftPad = Math.floor(padding / 2);
        const rightPad = padding - leftPad;
        return ' '.repeat(leftPad) + str + ' '.repeat(rightPad);
    }
    
    // Export to CSV format
    static exportToCSV(headers, rows) {
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${String(cell || '')}"`).join(','))
        ].join('\n');
        
        return csvContent;
    }
    
    // Export to JSON format
    static exportToJSON(headers, rows) {
        const jsonData = rows.map(row => {
            const obj = {};
            headers.forEach((header, i) => {
                obj[header] = row[i];
            });
            return obj;
        });
        
        return JSON.stringify(jsonData, null, 2);
    }
    
    // Generate comparison table for multiple symbols
    static generateComparisonTable(multipleAnalyses) {
        const headers = [
            'Symbol', 'MA Signal', 'RSI Signal', 'MACD Signal', 'BB Signal',
            'Consensus', 'Confidence', 'Risk', 'Recommendation'
        ];
        
        const rows = [];
        
        multipleAnalyses.forEach(analysis => {
            if (analysis.error) {
                rows.push([
                    analysis.symbol, 'ERROR', 'ERROR', 'ERROR', 'ERROR',
                    'ERROR', 'N/A', 'N/A', 'SKIP'
                ]);
            } else {
                const models = analysis.modelResults || {};
                
                rows.push([
                    analysis.symbol,
                    models.movingAverage?.signal || 'N/A',
                    models.rsiMeanReversion?.signal || 'N/A',
                    models.macdMomentum?.signal || 'N/A',
                    models.bollingerBands?.signal || 'N/A',
                    analysis.consensus?.signal || 'N/A',
                    `${analysis.consensus?.confidence || 0}%`,
                    analysis.riskAssessment?.level || 'N/A',
                    analysis.recommendations?.[0]?.action || 'N/A'
                ]);
            }
        });
        
        return this.formatTable(headers, rows);
    }
}

// Usage example
function demonstrateSummaryTables() {
    // Sample model results
    const sampleModelResults = [
        {
            model: "MA Crossover (50/200)",
            signal: "BUY",
            confidence: 85,
            timeframe: "Long-term (3-12 months)",
            trendDirection: "Golden Cross - Strong Uptrend",
            reasoning: ["Golden Cross detected", "Strong upward momentum"],
            keyLevels: { support: "145.23", resistance: "148.04" }
        },
        {
            model: "RSI Mean Reversion (14)",
            signal: "BUY",
            confidence: 75,
            timeframe: "Short to Medium-term (2-8 weeks)",
            rsiAnalysis: { level: "Oversold" },
            reasoning: ["RSI oversold (28.4 < 30)", "RSI showing upward momentum"],
            keyLevels: { support: "145.23", resistance: "148.04" }
        },
        {
            model: "MACD Momentum (12,26,9)",
            signal: "BUY",
            confidence: 80,
            timeframe: "Medium-term (1-3 months)",
            macdAnalysis: { trend: "Bullish" },
            reasoning: ["MACD above signal line (bullish)", "MACD histogram expanding"],
            keyLevels: { support: "0.0000", resistance: "0.0456" }
        },
        {
            model: "Bollinger Bands (20, 2)",
            signal: "BUY",
            confidence: 70,
            timeframe: "Short to Medium-term (2-6 weeks)",
            bollingerAnalysis: { pricePosition: "Lower Half" },
            reasoning: ["Price near lower band (2.1% below)", "High volume confirms oversold bounce"],
            keyLevels: { support: "145.79", resistance: "152.45" }
        }
    ];
    
    console.log("=== MODEL SUMMARY TABLE ===");
    console.log(SummaryTableGenerator.generateModelSummaryTable(sampleModelResults));
    
    // Sample consensus analysis
    const sampleConsensusAnalysis = {
        symbol: "AAPL",
        currency: "USD",
        currentPrice: 147.23,
        consensus: {
            signal: "BUY",
            confidence: 78,
            agreement: "Strong Bullish"
        },
        riskAssessment: {
            level: "Medium"
        },
        recommendations: [{
            action: "BUY",
            positionSize: "100-125% of normal"
        }]
    };
    
    console.log("\n=== CONSENSUS SUMMARY TABLE ===");
    console.log(SummaryTableGenerator.generateConsensusSummaryTable(sampleConsensusAnalysis));
    
    // Export to CSV
    const csvData = SummaryTableGenerator.exportToCSV(
        ['Symbol', 'Signal', 'Confidence', 'Action'],
        [
            ['AAPL', 'BUY', '78%', 'BUY'],
            ['GOOGL', 'HOLD', '59%', 'HOLD'],
            ['MSFT', 'BUY', '72%', 'BUY']
        ]
    );
    
    console.log("\n=== CSV EXPORT ===");
    console.log(csvData);
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SummaryTableGenerator;
}