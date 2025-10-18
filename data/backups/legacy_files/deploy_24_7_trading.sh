#!/bin/bash

# VictoryChain 24/7 Live Trading Deployment Script
# Sets up production-ready 24/7 trading with monitoring and auto-restart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 VictoryChain 24/7 Live Trading Deployment${NC}"
echo "==============================================="

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}📱 Detected macOS - Using launchd for 24/7 operation${NC}"
    SYSTEM_TYPE="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${YELLOW}🐧 Detected Linux - Using systemd for 24/7 operation${NC}"
    SYSTEM_TYPE="linux"
else
    echo -e "${RED}❌ Unsupported operating system${NC}"
    exit 1
fi

# Verify we're in the right directory
if [ ! -f "live_24_7_trading_bot.py" ]; then
    echo -e "${RED}❌ Error: live_24_7_trading_bot.py not found. Run from project directory.${NC}"
    exit 1
fi

# Check Python installation
echo -e "${BLUE}🐍 Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

PYTHON_PATH=$(which python3)
echo -e "${GREEN}✅ Python found: $PYTHON_PATH${NC}"

# Install/update dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Check API keys
echo -e "${BLUE}🔑 Checking API configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create it with your API keys.${NC}"
    exit 1
fi

# Verify API keys are set
if ! grep -q "BINANCEUS_KEY=" .env || ! grep -q "BINANCEUS_SECRET=" .env; then
    echo -e "${RED}❌ Binance API keys not found in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API keys configured${NC}"

# Create logs directory
echo -e "${BLUE}📝 Setting up logging...${NC}"
mkdir -p logs
chmod 755 logs

# Test API connectivity
echo -e "${BLUE}🔗 Testing API connectivity...${NC}"
python3 -c "
import os
from dotenv import load_dotenv
import requests
import hmac
import hashlib
import time

load_dotenv()

api_key = os.getenv('BINANCEUS_KEY')
secret_key = os.getenv('BINANCEUS_SECRET')

try:
    timestamp = int(time.time() * 1000)
    query_string = f'timestamp={timestamp}'
    signature = hmac.new(secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    
    headers = {'X-MBX-APIKEY': api_key}
    url = f'https://api.binance.us/api/v3/account?{query_string}&signature={signature}'
    
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        print('✅ Binance API: Connected')
    else:
        print(f'❌ Binance API Error: {response.status_code}')
        exit(1)
except Exception as e:
    print(f'❌ API Test Failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ API connectivity test failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API connectivity verified${NC}"

# System-specific deployment
if [ "$SYSTEM_TYPE" == "macos" ]; then
    echo -e "${BLUE}🍏 Setting up macOS launchd service...${NC}"
    
    # Create launchd plist
    cat > ~/Library/LaunchAgents/com.victorychain.trading.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.victorychain.trading</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$(pwd)/live_24_7_trading_bot.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    
    <key>ThrottleInterval</key>
    <integer>60</integer>
    
    <key>StandardOutPath</key>
    <string>$(pwd)/logs/launchd_trading.log</string>
    
    <key>StandardErrorPath</key>
    <string>$(pwd)/logs/launchd_trading.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONPATH</key>
        <string>$(pwd)</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF
    
    echo -e "${GREEN}✅ Launchd service created${NC}"
    
    # Load the service
    launchctl unload ~/Library/LaunchAgents/com.victorychain.trading.plist 2>/dev/null || true
    launchctl load ~/Library/LaunchAgents/com.victorychain.trading.plist
    
    echo -e "${GREEN}✅ Service loaded and will start automatically${NC}"
    
    # Show management commands
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo "  Start:   launchctl start com.victorychain.trading"
    echo "  Stop:    launchctl stop com.victorychain.trading"
    echo "  Status:  launchctl list | grep victorychain"
    echo "  Logs:    tail -f logs/launchd_trading.log"
    
elif [ "$SYSTEM_TYPE" == "linux" ]; then
    echo -e "${BLUE}🐧 Setting up systemd service...${NC}"
    
    # Update systemd service file with correct paths
    sed -i.bak "s|/Users/nicholaskramer/Downloads/victorychain_stack|$(pwd)|g" victorychain-24-7.service
    sed -i.bak "s|User=nicholaskramer|User=$USER|g" victorychain-24-7.service
    sed -i.bak "s|/opt/homebrew/Cellar/python@3.13/3.13.5/Frameworks/Python.framework/Versions/3.13/bin/python3|$PYTHON_PATH|g" victorychain-24-7.service
    
    # Install systemd service
    sudo cp victorychain-24-7.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable victorychain-24-7.service
    
    echo -e "${GREEN}✅ Systemd service installed and enabled${NC}"
    
    # Show management commands
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo "  Start:   sudo systemctl start victorychain-24-7"
    echo "  Stop:    sudo systemctl stop victorychain-24-7"
    echo "  Status:  sudo systemctl status victorychain-24-7"
    echo "  Logs:    sudo journalctl -u victorychain-24-7 -f"
fi

# Create monitoring script
echo -e "${BLUE}📊 Creating monitoring script...${NC}"
cat > monitor_trading.sh << 'EOF'
#!/bin/bash

# VictoryChain 24/7 Trading Monitor
# Shows real-time status and performance

echo "🚀 VictoryChain 24/7 Trading Monitor"
echo "===================================="

# Check if bot is running
if pgrep -f "live_24_7_trading_bot.py" > /dev/null; then
    echo "✅ Trading Bot: RUNNING"
    PID=$(pgrep -f "live_24_7_trading_bot.py")
    echo "   Process ID: $PID"
    
    # Show resource usage
    if command -v ps &> /dev/null; then
        CPU_MEM=$(ps -p $PID -o %cpu,%mem --no-headers 2>/dev/null)
        if [ ! -z "$CPU_MEM" ]; then
            echo "   CPU/Memory: $CPU_MEM"
        fi
    fi
else
    echo "❌ Trading Bot: NOT RUNNING"
fi

echo ""
echo "📊 Recent Performance:"

# Show recent log entries
if [ -f "logs/launchd_trading.log" ]; then
    echo "📝 Recent Activity (launchd):"
    tail -n 10 logs/launchd_trading.log | grep -E "(LIVE|✅|❌|P&L|HEALTH CHECK)"
elif [ -f "logs/systemd_24_7_trading.log" ]; then
    echo "📝 Recent Activity (systemd):"
    tail -n 10 logs/systemd_24_7_trading.log | grep -E "(LIVE|✅|❌|P&L|HEALTH CHECK)"
fi

# Show latest trading log
LATEST_LOG=$(ls -t live_24_7_trading_*.log 2>/dev/null | head -n 1)
if [ ! -z "$LATEST_LOG" ]; then
    echo ""
    echo "📈 Latest Trading Activity:"
    tail -n 5 "$LATEST_LOG" | grep -E "(BUY ORDER|SELL ORDER|P&L|HEALTH CHECK)"
fi

echo ""
echo "🔧 Management Commands:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   Start:   launchctl start com.victorychain.trading"
    echo "   Stop:    launchctl stop com.victorychain.trading"
    echo "   Logs:    tail -f logs/launchd_trading.log"
else
    echo "   Start:   sudo systemctl start victorychain-24-7"
    echo "   Stop:    sudo systemctl stop victorychain-24-7"
    echo "   Logs:    sudo journalctl -u victorychain-24-7 -f"
fi
EOF

chmod +x monitor_trading.sh

echo -e "${GREEN}✅ Monitoring script created: ./monitor_trading.sh${NC}"

# Final summary
echo ""
echo -e "${GREEN}🎉 24/7 Live Trading Deployment Complete!${NC}"
echo "========================================="
echo -e "${BLUE}📊 Configuration Summary:${NC}"
echo "   • Portfolio: \$50 starting balance"
echo "   • Position Size: 25% per trade (\$12.50)"
echo "   • Stop Loss: 6%"
echo "   • Take Profit: 12%"
echo "   • Max Positions: 3"
echo "   • Scan Interval: 15 minutes"
echo ""
echo -e "${BLUE}🔧 Management:${NC}"
echo "   • Monitor: ./monitor_trading.sh"
echo "   • Logs: logs/ directory"
echo "   • Service: Auto-restart enabled"
echo ""
echo -e "${YELLOW}⚠️  Important Reminders:${NC}"
echo "   • Monitor regularly, especially first 24 hours"
echo "   • Check logs for any errors or unusual activity"
echo "   • The bot will trade with real money 24/7"
echo "   • Emergency stop at 20% portfolio loss"
echo ""

# Ask if user wants to start immediately
read -p "🚀 Start 24/7 live trading now? (y/N): " start_now

if [[ $start_now =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 Starting 24/7 live trading...${NC}"
    
    if [ "$SYSTEM_TYPE" == "macos" ]; then
        launchctl start com.victorychain.trading
        echo -e "${GREEN}✅ Trading bot started via launchd${NC}"
        echo "📊 Monitor with: ./monitor_trading.sh"
        echo "📝 View logs: tail -f logs/launchd_trading.log"
    else
        sudo systemctl start victorychain-24-7
        echo -e "${GREEN}✅ Trading bot started via systemd${NC}"
        echo "📊 Monitor with: sudo systemctl status victorychain-24-7"
        echo "📝 View logs: sudo journalctl -u victorychain-24-7 -f"
    fi
    
    echo ""
    echo -e "${YELLOW}🎯 The bot is now running 24/7 and will trade with real money!${NC}"
    echo -e "${YELLOW}📊 Monitor closely for the first few hours.${NC}"
else
    echo -e "${BLUE}✅ Deployment complete. You can start trading later with the management commands shown above.${NC}"
fi

echo ""
echo -e "${GREEN}🚀 Happy Trading! May your algorithms be profitable! 💰${NC}"
