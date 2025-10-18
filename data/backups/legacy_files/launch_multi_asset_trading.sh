#!/bin/bash

# VictoryChain Multi-Asset Trading Launcher
# Comprehensive trading bot launcher for all portfolio assets

echo "🚀 VictoryChain Multi-Asset Trading System"
echo "=========================================="
echo ""

# Check Python dependencies
echo "Checking dependencies..."
python3 -c "import binance, pandas, numpy, requests, dotenv; print('✅ All dependencies available')" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip3 install python-binance pandas numpy requests python-dotenv anthropic
}

# Check environment
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    exit 1
fi

echo "✅ Environment ready"
echo ""

# Get current portfolio
echo "📊 Current Portfolio:"
python3 check_holdings.py | tail -20
echo ""

echo "🎯 Trading Strategy Options:"
echo ""
echo "1. 📈 Multi-Asset Portfolio Rebalancing"
echo "   - Trades with ALL your assets (not just USDT)"
echo "   - AI-powered momentum analysis"
echo "   - Dynamic rebalancing based on performance"
echo "   - Portfolio value: \$238.75 across 18 assets"
echo ""
echo "2. 🔄 Cross-Asset Arbitrage"
echo "   - Triangular arbitrage between your assets"
echo "   - Momentum arbitrage (high momentum vs low momentum)"
echo "   - Direct trading between asset pairs"
echo ""
echo "3. 🎪 Full Portfolio Trading (Previous Bot)"
echo "   - Legacy full portfolio trading system"
echo "   - All asset support with momentum analysis"
echo ""
echo "4. 🌙 Moonshot Detection"
echo "   - Hunt for micro-volume tokens with high potential"
echo "   - 30-50% gain predictions using AI"
echo ""
echo "5. 📊 Statistical Analysis Only"
echo "   - Run analysis without any trades"
echo "   - Get recommendations and insights"
echo ""
echo "6. 🔍 Live Market Scanner"
echo "   - Real-time momentum scanning"
echo "   - No trades, just monitoring"
echo ""

read -p "Select strategy (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting Multi-Asset Portfolio Rebalancing..."
        echo "This bot will analyze and trade with ALL your current assets:"
        echo "- BTC (\$74.25)"
        echo "- CRV (\$73.52)" 
        echo "- 1000REKT (\$44.62)"
        echo "- USDT (\$42.67)"
        echo "- Plus 14 smaller positions"
        echo ""
        echo "The bot will:"
        echo "1. Analyze momentum for each asset"
        echo "2. Get AI predictions for optimal allocation"
        echo "3. Rebalance portfolio to maximize gains"
        echo "4. Trade between your existing assets"
        echo ""
        
        python3 multi_asset_trading_bot.py
        ;;
        
    2)
        echo ""
        echo "🔄 Starting Cross-Asset Arbitrage Bot..."
        echo "This bot will find arbitrage opportunities between your assets:"
        echo "- Triangular arbitrage (A->B->C->A cycles)"
        echo "- Momentum arbitrage (sell low momentum, buy high momentum)"
        echo "- Direct pair trading when available"
        echo ""
        
        python3 cross_asset_arbitrage_bot.py
        ;;
        
    3)
        echo ""
        echo "🎪 Starting Full Portfolio Trading Bot..."
        echo "Running the comprehensive trading system..."
        echo ""
        
        python3 full_portfolio_trading_bot.py
        ;;
        
    4)
        echo ""
        echo "🌙 Starting Moonshot Detection..."
        echo "Hunting for high-potential micro-volume tokens..."
        echo ""
        
        python3 moonshot_detector.py
        ;;
        
    5)
        echo ""
        echo "📊 Running Statistical Analysis..."
        echo "Analysis mode - no trades will be executed"
        echo ""
        
        echo "Choose analysis type:"
        echo "1. Multi-asset momentum analysis"
        echo "2. Cross-asset arbitrage scan"
        echo "3. Full statistical analysis"
        echo ""
        
        read -p "Select analysis (1-3): " analysis_choice
        
        case $analysis_choice in
            1)
                python3 -c "
from multi_asset_trading_bot import MultiAssetTradingBot
bot = MultiAssetTradingBot()
analysis = bot.analyze_all_assets()
target_allocations = bot.calculate_target_allocations(analysis)
print('\\n📊 RECOMMENDED ALLOCATIONS:')
portfolio = bot.current_holdings
for asset, pct in sorted(target_allocations.items(), key=lambda x: x[1], reverse=True):
    current_pct = portfolio.get(asset, {}).get('allocation_pct', 0)
    print(f'  {asset}: {current_pct:.1f}% → {pct:.1f}%')
"
                ;;
            2)
                python3 -c "
from cross_asset_arbitrage_bot import CrossAssetArbitrageBot
bot = CrossAssetArbitrageBot()
results = bot.scan_opportunities()
print(f'\\n🔍 ARBITRAGE OPPORTUNITIES: {results.get(\"total_opportunities\", 0)}')
"
                ;;
            3)
                python3 statistical_analyzer.py
                ;;
        esac
        ;;
        
    6)
        echo ""
        echo "🔍 Starting Live Market Scanner..."
        echo "Real-time momentum scanning - no trades"
        echo ""
        
        python3 momentum_scanner.py
        ;;
        
    *)
        echo "❌ Invalid choice. Please select 1-6."
        exit 1
        ;;
esac

echo ""
echo "✅ Trading session complete!"
echo ""
echo "📁 Output files saved in current directory:"
ls -la *.json *.log 2>/dev/null | tail -5

echo ""
echo "📊 Check your updated portfolio:"
python3 check_holdings.py | grep "TOTAL\|BTC\|CRV\|1000REKT\|USDT"

echo ""
echo "🔄 Run again? Execute: ./launch_multi_asset_trading.sh"
