#!/bin/bash
# VictoryChain Trading System Launcher
# Quick launcher for the complete trading system

echo "🎯 VictoryChain Trading System"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "victorychain_control.py" ]; then
    echo "❌ Error: Not in VictoryChain directory"
    echo "   Please navigate to the victorychain_stack folder"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    echo "   Please install Python 3"
    exit 1
fi

echo "✅ Python 3 found"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Creating template .env file..."
    
    cat > .env << EOF
# Binance US API Configuration
BINANCEUS_KEY=your_api_key_here
BINANCEUS_SECRET=your_secret_key_here

# Claude AI API Key (Optional - for enhanced analysis)
CLAUDE_API_KEY=your_claude_api_key_here

# Trading Configuration
DEMO=false
LIVE_TRADING=true
EOF
    
    echo "📝 Please edit .env file with your API keys before trading"
    echo "   You can get Binance US API keys from: https://www.binance.us/en/support/faq/how-to-create-api-keys-on-binance-us"
    echo ""
fi

# Quick setup menu
echo "🚀 Quick Launch Options:"
echo "1. Master Control Center (Full Interface)"
echo "2. Smart Gains-Only Bot (Recommended for beginners)"
echo "3. Ultimate Trading Orchestrator (Advanced)"
echo "4. Trading Dashboard (View performance)"
echo "5. Check Portfolio Balance"
echo "6. Install Dependencies"
echo ""

read -p "Select option (1-6): " choice

case $choice in
    1)
        echo "🎯 Launching Master Control Center..."
        python3 victorychain_control.py
        ;;
    2)
        echo "🛡️  Launching Smart Gains-Only Bot..."
        python3 smart_gains_bot.py
        ;;
    3)
        echo "🚀 Launching Ultimate Trading Orchestrator..."
        python3 ultimate_trading_orchestrator.py
        ;;
    4)
        echo "📊 Launching Trading Dashboard..."
        python3 trading_dashboard.py
        ;;
    5)
        echo "💰 Checking Portfolio Balance..."
        python3 check_holdings.py
        ;;
    6)
        echo "📦 Installing Dependencies..."
        pip3 install python-binance pandas numpy requests python-dotenv scikit-learn anthropic
        echo "✅ Dependencies installed"
        ;;
    *)
        echo "❌ Invalid option"
        echo "   Launching Master Control Center..."
        python3 victorychain_control.py
        ;;
esac
