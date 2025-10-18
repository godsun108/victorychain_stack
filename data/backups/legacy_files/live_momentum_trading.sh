#!/bin/bash

# Live Momentum Trading Execution
echo "🚀 VictoryChain Live Momentum Trading"
echo "====================================="
echo "⚠️  LIVE TRADING MODE - REAL MONEY AT RISK"
echo ""

# Set environment variables
export CLAUDE_API_KEY="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"
export RUST_LOG=info

echo "📊 Step 1: Checking account balance and status..."
./target/release/backend balance --config config.toml

echo ""
echo "🔍 Step 2: Scanning for high-momentum opportunities..."
python3 momentum_scanner.py --live --min-potential 20 --max-risk medium

echo ""
echo "💰 Step 3: Executing live trades..."
echo "Target allocation: 80% of available USDT"
echo "Expected momentum: 20-30% gains"
echo "Risk management: 8% stop loss, 15% take profit"
echo ""

read -p "⚠️  Confirm live trading execution? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "🎯 Executing live momentum trades..."
    
    # Run the capital gains maximizer with live trading
    ./target/release/backend run --config config.toml --live
else
    echo "❌ Live trading cancelled by user"
    echo "💡 You can run in demo mode with: ./momentum_demo.sh"
fi
