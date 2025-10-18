#!/bin/bash

# VictoryChain Momentum Trading System
echo "🎯 VictoryChain Momentum Trading System"
echo "======================================"
echo "🔮 AI-Powered 20-30% Momentum Opportunities"
echo "💰 Automated Trading Execution"
echo ""

# Set environment variables
export CLAUDE_API_KEY="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"

echo "✅ AI API configured"
echo ""

if [ "$1" = "scan" ]; then
    echo "🔍 SCANNING FOR MOMENTUM OPPORTUNITIES"
    echo "======================================"
    echo "• Statistical analysis of 40+ high-volume tokens"
    echo "• Standard deviation & probability calculations"
    echo "• Looks for 10-30% gain potential with confidence"
    echo "• Risk-adjusted scoring with volatility penalties"
    echo "• Multi-timeframe momentum analysis"
    echo ""
    
    python3 integrated_momentum_trader.py

elif [ "$1" = "trade" ]; then
    echo "🚀 EXECUTING MOMENTUM TRADES"
    echo "============================"
    echo "⚠️ WARNING: This will execute real trades!"
    echo ""
    echo "Strategy:"
    echo "• $75 position size per opportunity"
    echo "• Max 3 concurrent positions" 
    echo "• 8% stop loss protection"
    echo "• Target: 20-30% gains"
    echo ""
    
    read -p "Press ENTER to scan for opportunities first, or Ctrl+C to cancel: "
    
    echo "🔍 First, scanning for statistical opportunities..."
    python3 integrated_momentum_trader.py
    echo ""
    
    read -p "Proceed with trading the opportunities found above? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "🚀 Executing trades..."
        python3 momentum_trader.py
    else
        echo "❌ Trading cancelled"
    fi

elif [ "$1" = "monitor" ]; then
    echo "📊 MONITORING ACTIVE POSITIONS"
    echo "=============================="
    echo "• Check current P&L on all positions"
    echo "• Identify exit opportunities"
    echo "• Track against targets and stop losses"
    echo ""
    
    echo "⚠️ Note: Full monitoring integration coming soon"
    echo "For now, check your Binance account directly"

elif [ "$1" = "demo" ]; then
    echo "📝 DEMO MODE - SAFE TESTING"
    echo "=========================="
    echo "• Scans real market data"
    echo "• Shows trade recommendations"
    echo "• No real money used"
    echo "• Perfect for testing strategy"
    echo ""
    
    unset BINANCEUS_KEY
    unset BINANCEUS_SECRET
    
    echo "🔍 Scanning for statistical opportunities..."
    python3 integrated_momentum_trader.py
    echo ""
    echo "🎯 Demo trading execution..."
    python3 momentum_trader.py

else
    echo "Usage: ./momentum_system.sh [command]"
    echo ""
    echo "Commands:"
    echo "  scan     🔍 Find 20-30% momentum opportunities"
    echo "  trade    🚀 Execute live momentum trades"
    echo "  monitor  📊 Monitor active positions"
    echo "  demo     📝 Demo mode (safe testing)"
    echo ""
    echo "Examples:"
    echo "  ./momentum_system.sh scan      # Find opportunities"
    echo "  ./momentum_system.sh demo      # Test safely"
    echo "  ./momentum_system.sh trade     # Execute real trades"
    echo ""
    echo "🎯 STRATEGY OVERVIEW:"
    echo "• Statistical analysis of 40+ tokens every run"
    echo "• Standard deviation & probability modeling"
    echo "• Identifies 10-30% gain potential with risk scores"
    echo "• Multi-timeframe momentum (1h, 6h, 24h, 7d)"
    echo "• Executes trades with volatility-based stop losses"
    echo "• Targets 24-72 hour hold periods"
    echo "• $75 position size per opportunity"
    echo "• Max 3 concurrent positions"
    echo ""
    echo "💡 RECOMMENDED WORKFLOW:"
    echo "1. Start with: ./momentum_system.sh demo"
    echo "2. Test strategy: ./momentum_system.sh scan"
    echo "3. When ready: ./momentum_system.sh trade"
    echo "4. Monitor with: ./momentum_system.sh monitor"
fi

echo ""
echo "📈 Current Statistical Analysis Summary:"
echo "• Focus: USDT pairs with >$1M daily volume"
echo "• Method: Standard deviation & probability modeling"
echo "• Target: 10-30% gains in 24-72 hours" 
echo "• Risk management: Volatility-based stop losses"
echo "• Statistical confidence: 65%+ win probabilities"
echo ""
echo "⚠️ Remember: Crypto trading involves significant risk!"
echo "   Only trade with money you can afford to lose."
