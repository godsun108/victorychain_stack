#!/bin/bash

# VictoryChain Statistical Momentum Trading System
echo "📊 VictoryChain Statistical Momentum System"
echo "==========================================="
echo "🧮 Standard Deviation & Probability Analysis"
echo "📈 Multi-timeframe Momentum Detection"
echo "🎯 Risk-Adjusted Token Selection"
echo ""

# Set environment variables
export CLAUDE_API_KEY="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"

echo "✅ Environment configured for statistical analysis"
echo ""

if [ "$1" = "analyze" ]; then
    echo "🔍 STATISTICAL MOMENTUM ANALYSIS"
    echo "================================"
    echo "• Analyzes 40+ high-volume USDT pairs"
    echo "• Calculates standard deviation across timeframes"
    echo "• Estimates gain probabilities (10%, 20%, 30%)"
    echo "• Risk-adjusted scoring with volatility penalties"
    echo "• Multi-timeframe momentum (1h, 6h, 24h, 7d)"
    echo ""
    
    python3 integrated_momentum_trader.py

elif [ "$1" = "simple" ]; then
    echo "🔍 SIMPLIFIED STATISTICAL ANALYSIS"
    echo "=================================="
    echo "• Uses only standard Python libraries"
    echo "• Standard deviation calculations"
    echo "• Probability-based token selection"
    echo "• Compatible with any Python environment"
    echo ""
    
    python3 simplified_statistical_analyzer.py

elif [ "$1" = "enhanced" ]; then
    echo "🔍 ENHANCED STATISTICAL ANALYSIS"
    echo "==============================="
    echo "• Advanced scipy/numpy calculations"
    echo "• GARCH volatility estimation"
    echo "• Market regime detection"
    echo "• Advanced probability distributions"
    echo ""
    
    echo "⚠️ Requires scipy and numpy installation"
    read -p "Continue? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        python3 enhanced_statistical_analyzer.py
    else
        echo "❌ Enhanced analysis cancelled"
    fi

elif [ "$1" = "rust" ]; then
    echo "🦀 RUST STATISTICAL MOMENTUM BOT"
    echo "==============================="
    echo "• Native Rust implementation"
    echo "• Integrated with Binance API"
    echo "• Live trading capabilities"
    echo "• Statistical analysis built-in"
    echo ""
    
    echo "🔧 Building Rust bot with statistical momentum..."
    cargo build --release
    
    if [ $? -eq 0 ]; then
        echo "🚀 Starting statistical momentum bot..."
        ./target/release/victorychain-bot run --live --config config.toml
    else
        echo "❌ Build failed. Check Rust code for errors."
    fi

elif [ "$1" = "demo" ]; then
    echo "📝 DEMO MODE - STATISTICAL ANALYSIS"
    echo "=================================="
    echo "• Analyzes real market data"
    echo "• Shows statistical probabilities"
    echo "• No real trading executed"
    echo "• Perfect for testing methodology"
    echo ""
    
    unset BINANCE_US_API_KEY
    unset BINANCE_US_SECRET_KEY
    
    echo "🔍 Running statistical analysis demo..."
    python3 integrated_momentum_trader.py
    echo ""
    echo "📊 Demo Results Summary:"
    echo "The analysis above shows probability-based rankings"
    echo "Use scores >25 for potential trading opportunities"
    echo "Higher volatility = higher risk but higher rewards"

elif [ "$1" = "compare" ]; then
    echo "⚖️ COMPARISON MODE"
    echo "=================="
    echo "• Runs both simple and integrated analyzers"
    echo "• Compares results and recommendations"
    echo "• Helps validate statistical consistency"
    echo ""
    
    echo "🔍 Running integrated analyzer..."
    python3 integrated_momentum_trader.py > integrated_results.tmp
    echo ""
    echo "🔍 Running simplified analyzer..."
    python3 simplified_statistical_analyzer.py > simplified_results.tmp
    echo ""
    echo "📊 COMPARISON RESULTS:"
    echo "====================="
    echo ""
    echo "INTEGRATED ANALYZER TOP 3:"
    grep "^#[1-3]" integrated_results.tmp || echo "No results found"
    echo ""
    echo "SIMPLIFIED ANALYZER TOP 3:"
    grep "^#[1-3]" simplified_results.tmp || echo "No results found"
    
    rm -f integrated_results.tmp simplified_results.tmp

else
    echo "Usage: ./statistical_momentum.sh [command]"
    echo ""
    echo "Commands:"
    echo "  analyze   🔍 Run integrated statistical analysis"
    echo "  simple    📊 Run simplified analysis (no dependencies)"
    echo "  enhanced  🧮 Run advanced analysis (requires scipy/numpy)"
    echo "  rust      🦀 Run Rust bot with statistical momentum"
    echo "  demo      📝 Demo mode (safe testing)"
    echo "  compare   ⚖️ Compare different analyzers"
    echo ""
    echo "Examples:"
    echo "  ./statistical_momentum.sh analyze    # Best overall"
    echo "  ./statistical_momentum.sh simple     # No dependencies"
    echo "  ./statistical_momentum.sh demo       # Safe testing"
    echo "  ./statistical_momentum.sh rust       # Live trading"
    echo ""
    echo "🧮 STATISTICAL METHODOLOGY:"
    echo "• Standard deviation analysis across multiple timeframes"
    echo "• Normal distribution probability calculations"
    echo "• Risk-adjusted scoring with volatility penalties"
    echo "• Multi-timeframe momentum indicators"
    echo "• Volume and liquidity filtering"
    echo "• Statistical significance testing"
    echo ""
    echo "📊 KEY METRICS EXPLAINED:"
    echo "• Composite Score: Overall probability-based ranking (0-100)"
    echo "• Gain Probabilities: Chance of X% gain in Y hours"
    echo "• Risk-Adjusted: Probabilities after volatility penalty"
    echo "• Momentum Scores: Return/volatility ratios"
    echo "• Sharpe Ratio: Risk-adjusted return measure"
    echo "• Win Rate: Historical percentage of positive returns"
    echo ""
fi

echo ""
echo "📈 Statistical Analysis Focus:"
echo "• Standard deviation calculations for risk assessment"
echo "• Probability modeling for gain estimation"
echo "• Multi-timeframe analysis (1h, 6h, 24h, 7d)"
echo "• Risk-adjusted scoring with volatility integration"
echo "• Volume filtering for liquidity assurance"
echo ""
echo "⚠️ Remember: Statistics are based on historical data"
echo "   Past performance doesn't guarantee future results!"
