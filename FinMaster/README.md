# Technical Trading Analysis System

This project is a modular Python-based framework for performing technical analysis on stock data using multiple trading models and indicators.

## 📁 Project Structure

. ├── data/ 
  │ ├── fetching.py # Yahoo Finance data fetcher 
  │ ├── stock_data.py # StockData class for OHLCV and metadata 
  │ ├── exceptions.py # Custom exceptions for data handling 
│ ├── indicators/ 
  │ ├── base.py # IndicatorCalculationError 
  │ ├── technical.py # TechnicalIndicators class (SMA, EMA, RSI, etc.) 
  │ ├── calculator.py # IndicatorCalculator class 
│ ├── models/ 
  │ ├── ma_crossover.py # MovingAverageCrossoverModel 
  │ ├── rsi_mean_reversion.py # RSIMeanReversionModel 
  │ ├── macd_momentum.py # MACDMomentumModel 
  │ ├── bollinger_bands.py # BollingerBandsModel 
│ ├── orchestration/ 
  │ ├── core.py # Main analysis logic 
  │ ├── runner.py # CLI entry point 
  │ ├── utils.py # Helper functions (optional) 
  │ ├── reporting.py # Summary table and print output 
  │ ├── config.py # Constants and model configs (optional) 
