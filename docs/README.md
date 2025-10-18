# VictoryChain Advanced Trading Bot System

## 🚀 Overview

VictoryChain is a sophisticated 24/7 cryptocurrency trading bot system designed specifically for Binance US. It combines multiple AI-powered strategies, statistical analysis, and market regime detection to maximize capital gains while maintaining strict risk management.

## ✨ Key Features

### 🧠 AI-Powered Analysis
- **Claude AI Integration**: Advanced token analysis and momentum prediction
- **Statistical Analysis**: Standard deviation, probability, and significance testing
- **Market Regime Detection**: Automatic adaptation to bullish, bearish, sideways, and volatile markets

### 📊 Multiple Trading Strategies
- **Volume-Categorized Trading**: Different strategies for high, medium, low, and micro-volume tokens
- **Moonshot Detection**: Specialized hunting for 30-50% opportunities in micro-volume tokens
- **Master Trading Bot**: Combines all strategies with intelligent allocation based on market conditions
- **Enhanced Trading**: AI-powered batch analysis with dynamic position sizing

### 🛡️ Risk Management
- **Dynamic Stop Losses**: Adaptive based on market regime and token volatility
- **Position Sizing**: Intelligent allocation based on risk level and market conditions
- **Maximum Holdings**: Configurable limits to prevent over-exposure
- **Emergency Stops**: Automatic shutdown mechanisms for extreme market conditions

### 📈 Advanced Analytics
- **Real-time Volume Analysis**: Categorizes all 180+ Binance US USDT pairs by volume
- **Momentum Scoring**: Multi-factor momentum analysis including volume surges
- **Breakout Detection**: Technical pattern recognition for entry timing
- **Performance Tracking**: Comprehensive trade statistics and win rate analysis

## 📊 Architecture

```
├── backend/src/
│   ├── main.rs           # Entry point and orchestration
│   ├── strategy.rs       # Trading strategy implementations
│   ├── math.rs           # Mathematical functions and models
│   ├── exchange.rs       # Market data and order routing
│   ├── risk.rs           # Risk management system
│   └── config.rs         # Configuration management
├── config.toml           # Strategy and system parameters
└── Cargo.toml           # Dependencies and build config
```

## ⚡ Quick Start

1. **Install Rust** (if not already installed):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Clone and run**:
   ```bash
   git clone <repository-url>
   cd victorychain_stack
   cargo run --bin backend
   ```

3. **Configure strategies** by editing `config.toml`:
   ```toml
   [basis_arb]
   min_apr = 0.05                # Minimum APR threshold (5%)
   max_position_size = 50000.0   # Maximum position size
   
   [risk]
   max_drawdown = 0.15           # 15% max drawdown
   var_limit = 5000.0            # VaR limit ($5,000)
   ```

## 🧮 Strategy Equations

### Basis Arbitrage
```
APR = (funding_rate - borrow_rate) × 365
```

### Theta Harvest
```
PnL ≈ -θ + Δ×dS + 0.5×Γ×dS² + Vega×dIV
```

### Statistical Arbitrage
```
Z-score = (spread - μ) / σ
```

### Risk Management
```
VaR₉₅ = z₀.₉₅ × portfolio_std
Health Factor = equity / required_margin
```

## 📈 Performance Monitoring

The system provides real-time monitoring of:
- Strategy P&L and performance metrics
- Risk metrics (VaR, health factor, drawdown)
- Position sizes and exposure
- Market data quality and latency

## 🔧 Configuration

### Strategy Parameters
- **Entry/exit thresholds**: Customize signal sensitivity
- **Position sizing**: Risk-adjusted position limits
- **Rebalancing**: Automated portfolio rebalancing rules

### Risk Controls
- **Drawdown limits**: Circuit breakers for maximum loss
- **VaR limits**: Portfolio-level risk constraints
- **Position limits**: Per-strategy and total exposure caps

## 🛡️ Safety Features

- **Circuit Breaker**: Automatic trading halt on excessive drawdown
- **Health Factor Monitoring**: Margin and liquidity checks
- **Position Size Validation**: Pre-trade risk checks
- **Real-time Risk Metrics**: Continuous portfolio monitoring

## 📚 Dependencies

- **nalgebra**: Linear algebra for portfolio optimization
- **statrs**: Statistical functions and distributions
- **serde/toml**: Configuration management
- **reqwest**: HTTP client for market data (future)
- **tokio**: Async runtime for high-performance execution

## 🔮 Future Enhancements

- [ ] Real exchange API integration (Binance, FTX, etc.)
- [ ] WebSocket market data feeds
- [ ] Advanced ML-based strategies
- [ ] Web dashboard for monitoring
- [ ] Backtesting framework
- [ ] Multi-asset support
- [ ] Cloud deployment scripts

## ⚠️ Disclaimer

This is educational/research software. Trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk.

## 📄 License

MIT Licensed - see LICENSE file for details.
