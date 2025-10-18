#!/bin/bash

# VictoryChain Momentum Predictor
echo "🔮 VictoryChain 20-30% Momentum Predictor"
echo "=========================================="
echo "🎯 AI-Powered Token Momentum Analysis"
echo "📈 Identifies tokens with 20-30% upside potential"
echo "⚡ Real-time scanning and live trading execution"
echo ""

# Set environment variables
export CLAUDE_API_KEY="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"
export RUST_LOG=info

echo "✅ Configuration loaded"
echo ""

if [ "$1" = "scan" ]; then
    echo "🔍 SCANNING MODE - Finding momentum opportunities..."
    echo "Expected output:"
    echo "• Top tokens with 20-30% momentum potential"
    echo "• AI confidence scores and analysis"
    echo "• Entry recommendations and price targets"
    echo "• Risk assessments and hold durations"
    echo ""
    echo "Starting scan..."
    echo ""
    
    ./target/release/backend momentum --scan --config config.toml

elif [ "$1" = "trade" ]; then
    echo "🚀 LIVE TRADING MODE - Executing momentum trades..."
    echo "Strategy Details:"
    echo "• Max 3 concurrent positions ($75 each)"
    echo "• 20%+ predicted gains required"
    echo "• 70%+ AI confidence required"
    echo "• 8% stop loss protection"
    echo "• Hold duration: 12-48 hours"
    echo ""
    echo "⚠️  WARNING: This will execute real trades with real money!"
    echo "Press Ctrl+C within 5 seconds to cancel..."
    echo ""
    
    sleep 5
    
    echo "Starting live momentum trading..."
    echo ""
    
    ./target/release/backend momentum --predict --config config.toml

else
    echo "Usage:"
    echo "  ./run_momentum.sh scan    # Scan for momentum opportunities"
    echo "  ./run_momentum.sh trade   # Start live momentum trading"
    echo ""
    echo "Examples:"
    echo "  🔍 Find opportunities:     ./run_momentum.sh scan"
    echo "  🚀 Execute trades:         ./run_momentum.sh trade"
    echo ""
    echo "What to expect:"
    echo "• SCAN mode shows you the best 20-30% opportunities"
    echo "• TRADE mode automatically enters and manages positions"
    echo "• AI analyzes 50+ tokens every 10 minutes"
    echo "• Only highest confidence opportunities are selected"
    echo "• Smart position management with stop losses"
fi
