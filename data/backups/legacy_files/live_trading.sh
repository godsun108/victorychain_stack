#!/bin/bash

# VictoryChain 24/7 Live Trading System
echo "🚀 VictoryChain 24/7 Live Trading System"
echo "========================================"
echo "📊 Statistical Momentum Analysis"
echo "🤖 Automated Trading Execution"
echo "🛡️ Built-in Risk Management"
echo ""

# Check for API keys
if [ -z "$BINANCE_US_API_KEY" ] || [ -z "$BINANCE_US_SECRET_KEY" ]; then
    echo "⚠️ API keys not found in environment variables"
    echo ""
    echo "Please set your Binance US API keys:"
    echo "export BINANCE_US_API_KEY='your_api_key_here'"
    echo "export BINANCE_US_SECRET_KEY='your_secret_key_here'"
    echo ""
    echo "Or create a .env file with your keys"
fi

if [ "$1" = "start" ]; then
    echo "🚀 STARTING LIVE TRADING BOT"
    echo "============================"
    echo "⚠️ WARNING: This will execute REAL trades with REAL money!"
    echo ""
    echo "Bot Configuration:"
    echo "• Position size: $75 per trade"
    echo "• Max positions: 3 concurrent"
    echo "• Stop loss: 8%"
    echo "• Take profit: 20%"
    echo "• Analysis interval: 30 minutes"
    echo "• Max daily loss: $50"
    echo ""
    
    read -p "Type 'CONFIRM' to start live trading: " confirm
    if [[ $confirm != "CONFIRM" ]]; then
        echo "❌ Live trading cancelled"
        exit 1
    fi
    
    echo "🚀 Starting live trading bot..."
    python3 live_trading_bot.py

elif [ "$1" = "demo" ]; then
    echo "📝 DEMO MODE - SAFE TESTING"
    echo "=========================="
    echo "• Analyzes real market data"
    echo "• Shows trading opportunities"
    echo "• NO REAL MONEY USED"
    echo "• Perfect for testing strategy"
    echo ""
    
    export DEMO=1
    unset BINANCE_US_API_KEY
    unset BINANCE_US_SECRET_KEY
    
    echo "🔍 Running demo trading bot..."
    python3 integrated_momentum_trader.py

elif [ "$1" = "monitor" ]; then
    echo "📊 MONITORING ACTIVE POSITIONS"
    echo "=============================="
    echo "• Check current trades and P&L"
    echo "• View bot status and statistics"
    echo "• Monitor risk levels"
    echo ""
    
    if [ -f "live_trading_bot.log" ]; then
        echo "📋 Recent bot activity:"
        tail -20 live_trading_bot.log
        echo ""
        echo "📊 Live log monitoring (Ctrl+C to stop):"
        tail -f live_trading_bot.log
    else
        echo "❌ No log file found. Bot may not be running."
    fi

elif [ "$1" = "stop" ]; then
    echo "🛑 STOPPING LIVE TRADING BOT"
    echo "==========================="
    
    # Find and kill the bot process
    PID=$(pgrep -f "live_trading_bot.py")
    if [ -n "$PID" ]; then
        echo "🔍 Found bot process: $PID"
        kill $PID
        sleep 2
        
        # Check if still running
        if pgrep -f "live_trading_bot.py" > /dev/null; then
            echo "⚠️ Bot still running, force killing..."
            pkill -f "live_trading_bot.py"
        fi
        
        echo "✅ Bot stopped successfully"
    else
        echo "❌ No running bot found"
    fi

elif [ "$1" = "status" ]; then
    echo "📊 BOT STATUS CHECK"
    echo "=================="
    
    # Check if bot is running
    if pgrep -f "live_trading_bot.py" > /dev/null; then
        PID=$(pgrep -f "live_trading_bot.py")
        echo "✅ Bot is RUNNING (PID: $PID)"
        
        # Show recent activity
        if [ -f "live_trading_bot.log" ]; then
            echo ""
            echo "📋 Recent activity:"
            tail -10 live_trading_bot.log | grep -E "(✅|❌|💰|💸|📊|🚀)"
        fi
    else
        echo "❌ Bot is NOT RUNNING"
        
        # Show last log entries if available
        if [ -f "live_trading_bot.log" ]; then
            echo ""
            echo "📋 Last known activity:"
            tail -5 live_trading_bot.log
        fi
    fi

elif [ "$1" = "deploy" ]; then
    echo "🚀 DEPLOYING LIVE TRADING BOT"
    echo "============================="
    echo "• Sets up systemd service"
    echo "• Configures auto-restart"
    echo "• Creates monitoring scripts"
    echo ""
    
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Deployment requires root privileges"
        echo "Run: sudo ./live_trading.sh deploy"
        exit 1
    fi
    
    ./deploy/deploy-live-bot.sh

elif [ "$1" = "docker" ]; then
    echo "🐳 DOCKER DEPLOYMENT"
    echo "==================="
    echo "• Containerized deployment"
    echo "• Automatic restarts"
    echo "• Resource limits"
    echo "• Easy scaling"
    echo ""
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker first."
        exit 1
    fi
    
    echo "🔧 Building and starting Docker containers..."
    cd deploy/docker
    docker-compose -f docker-compose.live-bot.yml up -d
    
    echo "✅ Docker deployment complete!"
    echo ""
    echo "Commands:"
    echo "• View logs: docker logs -f victorychain-live-trading-bot"
    echo "• Stop: docker-compose -f docker-compose.live-bot.yml down"
    echo "• Status: docker ps"

elif [ "$1" = "test" ]; then
    echo "🧪 TESTING BOT COMPONENTS"
    echo "========================"
    echo "• Test API connection"
    echo "• Validate trading functions"
    echo "• Check statistical analysis"
    echo ""
    
    echo "🔍 Testing API connection..."
    python3 -c "
import requests
import os
try:
    if os.getenv('BINANCE_US_API_KEY'):
        print('✅ API key found')
    else:
        print('❌ API key not found')
    
    response = requests.get('https://api.binance.us/api/v3/ping')
    if response.status_code == 200:
        print('✅ Binance US API reachable')
    else:
        print('❌ API connection failed')
        
    # Test statistical analysis
    from integrated_momentum_trader import IntegratedMomentumTrader
    trader = IntegratedMomentumTrader()
    pairs = trader.get_all_trading_pairs()
    print(f'✅ Found {len(pairs)} trading pairs')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
"

else
    echo "Usage: ./live_trading.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start     🚀 Start live trading bot (REAL MONEY)"
    echo "  demo      📝 Demo mode (safe testing)"
    echo "  monitor   📊 Monitor active positions and logs"
    echo "  stop      🛑 Stop the trading bot"
    echo "  status    📊 Check bot status"
    echo "  deploy    🚀 Deploy as system service"
    echo "  docker    🐳 Deploy with Docker"
    echo "  test      🧪 Test bot components"
    echo ""
    echo "Examples:"
    echo "  ./live_trading.sh demo      # Safe testing"
    echo "  ./live_trading.sh start     # Start live trading"
    echo "  ./live_trading.sh monitor   # Watch bot activity"
    echo "  ./live_trading.sh status    # Check if running"
    echo ""
    echo "🤖 BOT FEATURES:"
    echo "• 24/7 automated trading"
    echo "• Statistical momentum analysis"
    echo "• Multi-timeframe analysis (1h, 6h, 24h)"
    echo "• Risk-adjusted probability scoring"
    echo "• Automatic stop loss (8%) and take profit (20%)"
    echo "• Position size: $75 per trade"
    echo "• Max 3 concurrent positions"
    echo "• Daily loss limit: $50"
    echo "• Analysis every 30 minutes"
    echo "• Trade cooldown: 10 minutes"
    echo ""
    echo "🛡️ RISK MANAGEMENT:"
    echo "• Volatility-based stop losses"
    echo "• Daily loss limits"
    echo "• Position size limits"
    echo "• Volume and liquidity filtering"
    echo "• Statistical significance requirements"
    echo ""
    echo "⚠️ IMPORTANT:"
    echo "• Set BINANCE_US_API_KEY and BINANCE_US_SECRET_KEY"
    echo "• Start with demo mode to test strategy"
    echo "• Monitor logs regularly"
    echo "• Only trade with money you can afford to lose"
fi

echo ""
echo "📈 Statistical Analysis Features:"
echo "• Standard deviation calculations"
echo "• Probability modeling for gains"
echo "• Multi-timeframe momentum detection"
echo "• Risk-adjusted scoring"
echo "• Volume filtering for liquidity"
echo ""
echo "⚠️ Remember: Past performance doesn't guarantee future results!"
