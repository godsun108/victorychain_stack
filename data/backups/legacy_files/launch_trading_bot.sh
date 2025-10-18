#!/bin/bash

# VictoryChain Trading Bot Launcher
# Comprehensive launcher for all trading strategies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
echo -e "${CYAN}"
cat << "EOF"
██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║
██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ ██║     ███████║███████║██║██╔██╗ ██║
╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  ██║     ██╔══██║██╔══██║██║██║╚██╗██║
 ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   ╚██████╗██║  ██║██║  ██║██║██║ ╚████║
  ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
EOF
echo -e "${NC}"

echo -e "${GREEN}🚀 VictoryChain Trading Bot Launcher${NC}"
echo -e "${BLUE}📊 Advanced AI-Powered Trading Strategies${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: requirements.txt not found. Please run from the project root directory.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found.${NC}"
    echo -e "${YELLOW}   Create .env file with your API keys for live trading.${NC}"
    echo ""
fi

# Function to check Python dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking Python dependencies...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
        exit 1
    fi
    
    # Install/upgrade requirements
    echo -e "${BLUE}📦 Installing/updating Python packages...${NC}"
    pip3 install -r requirements.txt --upgrade --quiet
    
    echo -e "${GREEN}✅ Dependencies checked${NC}"
    echo ""
}

# Function to show bot options
show_bot_menu() {
    echo -e "${CYAN}🤖 Available Trading Bots:${NC}"
    echo ""
    
    echo -e "${GREEN}1.${NC} ${YELLOW}Enhanced Trading Bot${NC} - AI-powered batch analysis with dynamic position sizing"
    echo -e "   ${BLUE}• Features: Claude AI analysis, 5 simultaneous positions, 15-minute scans${NC}"
    echo -e "   ${BLUE}• Best for: Balanced risk/reward with AI insights${NC}"
    echo ""
    
    echo -e "${GREEN}2.${NC} ${YELLOW}Volume-Categorized Bot${NC} - Strategy adaptation based on token volume"
    echo -e "   ${BLUE}• Features: High/Medium/Low/Micro volume strategies, regime-aware trading${NC}"
    echo -e "   ${BLUE}• Best for: Diversified approach across all volume categories${NC}"
    echo ""
    
    echo -e "${GREEN}3.${NC} ${YELLOW}Moonshot Detector${NC} - Specialized for 30-50% opportunities"
    echo -e "   ${BLUE}• Features: Micro-volume focus, breakout detection, extreme profit targets${NC}"
    echo -e "   ${BLUE}• Best for: High-risk, high-reward moonshot hunting${NC}"
    echo ""
    
    echo -e "${GREEN}4.${NC} ${YELLOW}Master Trading Bot${NC} - Combines all strategies with market regime detection"
    echo -e "   ${BLUE}• Features: AI regime detection, adaptive allocation, comprehensive strategy${NC}"
    echo -e "   ${BLUE}• Best for: Sophisticated algorithmic trading with market adaptation${NC}"
    echo ""
    
    echo -e "${GREEN}5.${NC} ${YELLOW}Statistical Analyzer${NC} - Pure statistical momentum analysis"
    echo -e "   ${BLUE}• Features: Standard deviation, probability analysis, statistical significance${NC}"
    echo -e "   ${BLUE}• Best for: Data-driven approach without AI dependencies${NC}"
    echo ""
    
    echo -e "${GREEN}6.${NC} ${YELLOW}Claude Token Predictor${NC} - AI-powered 30-50% gain predictions"
    echo -e "   ${BLUE}• Features: Claude batch analysis, volume categorization, gain predictions${NC}"
    echo -e "   ${BLUE}• Best for: AI-assisted token selection and buy-and-hold strategy${NC}"
    echo ""
    
    echo -e "${GREEN}7.${NC} ${YELLOW}Live Trading Bot${NC} - Original comprehensive live trading system"
    echo -e "   ${BLUE}• Features: Risk management, position tracking, automated trading${NC}"
    echo -e "   ${BLUE}• Best for: Proven live trading with comprehensive features${NC}"
    echo ""
    
    echo -e "${GREEN}8.${NC} ${YELLOW}Demo Mode${NC} - Test any bot without real trading"
    echo -e "   ${BLUE}• Features: All bots run in simulation mode, no real trades${NC}"
    echo -e "   ${BLUE}• Best for: Testing and learning without financial risk${NC}"
    echo ""
    
    echo -e "${GREEN}9.${NC} ${YELLOW}Setup & Configuration${NC} - Initial setup and API key configuration"
    echo -e "   ${BLUE}• Features: .env setup, API key validation, dependency installation${NC}"
    echo -e "   ${BLUE}• Best for: First-time setup and configuration${NC}"
    echo ""
    
    echo -e "${GREEN}0.${NC} ${RED}Exit${NC}"
    echo ""
}

# Function to run enhanced trading bot
run_enhanced_bot() {
    echo -e "${GREEN}🚀 Starting Enhanced Trading Bot...${NC}"
    echo -e "${BLUE}📊 AI-powered batch analysis with dynamic position sizing${NC}"
    echo ""
    python3 enhanced_trading_bot.py
}

# Function to run volume-categorized bot
run_volume_bot() {
    echo -e "${GREEN}🎯 Starting Volume-Categorized Bot...${NC}"
    echo -e "${BLUE}📊 Strategy adaptation based on token volume categories${NC}"
    echo ""
    python3 volume_categorized_bot.py
}

# Function to run moonshot detector
run_moonshot() {
    echo -e "${GREEN}🚀 Starting Moonshot Detector...${NC}"
    echo -e "${BLUE}🎯 Hunting for 30-50% opportunities in micro-volume tokens${NC}"
    echo ""
    python3 moonshot_detector.py
}

# Function to run master bot
run_master_bot() {
    echo -e "${GREEN}🧠 Starting Master Trading Bot...${NC}"
    echo -e "${BLUE}🔄 Market regime detection with adaptive strategy allocation${NC}"
    echo ""
    python3 master_trading_bot.py
}

# Function to run statistical analyzer
run_statistical() {
    echo -e "${GREEN}📊 Starting Statistical Analyzer...${NC}"
    echo -e "${BLUE}📈 Pure statistical momentum analysis${NC}"
    echo ""
    python3 statistical_analyzer.py
}

# Function to run Claude predictor
run_claude_predictor() {
    echo -e "${GREEN}🤖 Starting Claude Token Predictor...${NC}"
    echo -e "${BLUE}🎯 AI-powered 30-50% gain predictions${NC}"
    echo ""
    python3 claude_token_predictor.py
}

# Function to run live trading bot
run_live_bot() {
    echo -e "${GREEN}📈 Starting Live Trading Bot...${NC}"
    echo -e "${BLUE}⚡ Comprehensive live trading system${NC}"
    echo ""
    python3 live_trading_bot.py
}

# Function to run in demo mode
run_demo_mode() {
    echo -e "${YELLOW}📝 Demo Mode Selected${NC}"
    echo -e "${BLUE}All bots will run in simulation mode - no real trades will be executed${NC}"
    echo ""
    
    export DEMO=true
    
    echo -e "${CYAN}Select bot to run in demo mode:${NC}"
    echo "1. Enhanced Trading Bot (Demo)"
    echo "2. Volume-Categorized Bot (Demo)"
    echo "3. Moonshot Detector (Demo)"
    echo "4. Master Trading Bot (Demo)"
    echo "5. Statistical Analyzer (Demo)"
    echo "6. Claude Token Predictor (Demo)"
    echo "7. Live Trading Bot (Demo)"
    echo ""
    
    read -p "Enter choice (1-7): " demo_choice
    
    case $demo_choice in
        1) run_enhanced_bot ;;
        2) run_volume_bot ;;
        3) run_moonshot ;;
        4) run_master_bot ;;
        5) run_statistical ;;
        6) run_claude_predictor ;;
        7) run_live_bot ;;
        *) echo -e "${RED}❌ Invalid choice${NC}" ;;
    esac
}

# Function for setup and configuration
setup_configuration() {
    echo -e "${GREEN}⚙️  Setup & Configuration${NC}"
    echo ""
    
    # Check if .env exists
    if [ -f ".env" ]; then
        echo -e "${GREEN}✅ .env file found${NC}"
        echo -e "${BLUE}Current configuration:${NC}"
        echo ""
        
        # Show current config (without revealing keys)
        if grep -q "BINANCEUS_KEY" .env; then
            echo -e "${GREEN}• Binance API Key: Configured${NC}"
        else
            echo -e "${RED}• Binance API Key: Not configured${NC}"
        fi
        
        if grep -q "BINANCEUS_SECRET" .env; then
            echo -e "${GREEN}• Binance Secret Key: Configured${NC}"
        else
            echo -e "${RED}• Binance Secret Key: Not configured${NC}"
        fi
        
        if grep -q "CLAUDE_API_KEY" .env; then
            echo -e "${GREEN}• Claude API Key: Configured${NC}"
        else
            echo -e "${RED}• Claude API Key: Not configured${NC}"
        fi
        
        echo ""
        echo -e "${YELLOW}1.${NC} Update API keys"
        echo -e "${YELLOW}2.${NC} Test API connections"
        echo -e "${YELLOW}3.${NC} View current .env file"
        echo -e "${YELLOW}4.${NC} Return to main menu"
        echo ""
        
        read -p "Enter choice (1-4): " setup_choice
        
        case $setup_choice in
            1) update_api_keys ;;
            2) test_api_connections ;;
            3) cat .env ;;
            4) return ;;
            *) echo -e "${RED}❌ Invalid choice${NC}" ;;
        esac
    else
        echo -e "${YELLOW}⚠️  .env file not found. Creating new configuration...${NC}"
        create_env_file
    fi
}

# Function to create .env file
create_env_file() {
    echo -e "${BLUE}📝 Creating .env configuration file...${NC}"
    echo ""
    
    # Create .env file with template
    cat > .env << EOF
# Binance US API Configuration
BINANCEUS_KEY=your_BINANCEUS_KEY_here
BINANCEUS_SECRET=your_BINANCEUS_SECRET_here

# Claude AI API Configuration (for AI analysis)
CLAUDE_API_KEY=your_claude_api_key_here

# Trading Configuration
DEMO=true

# Portfolio Configuration
PORTFOLIO_VALUE=10000
MAX_POSITIONS=5
POSITION_SIZE_PCT=0.15

# Risk Management
STOP_LOSS_PCT=0.08
TAKE_PROFIT_PCT=0.15
MAX_HOLD_HOURS=24
EOF
    
    echo -e "${GREEN}✅ .env file created with template${NC}"
    echo -e "${YELLOW}📝 Please edit .env file with your actual API keys${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Get Binance US API keys from: https://www.binance.us/en/usercenter/settings/api-management"
    echo "2. Get Claude API key from: https://console.anthropic.com/"
    echo "3. Edit .env file with your actual keys"
    echo "4. Set DEMO=false when ready for live trading"
    echo ""
}

# Function to update API keys
update_api_keys() {
    echo -e "${BLUE}🔑 Update API Keys${NC}"
    echo ""
    
    echo -e "${YELLOW}Current .env file:${NC}"
    cat .env
    echo ""
    
    echo -e "${BLUE}You can edit the .env file manually or use this interactive updater${NC}"
    echo ""
    
    read -p "Do you want to update Binance API Key? (y/n): " update_binance
    if [ "$update_binance" = "y" ]; then
        read -p "Enter Binance API Key: " binance_key
        sed -i.bak "s/BINANCEUS_KEY=.*/BINANCEUS_KEY=$binance_key/" .env
        echo -e "${GREEN}✅ Binance API Key updated${NC}"
    fi
    
    read -p "Do you want to update Binance Secret Key? (y/n): " update_secret
    if [ "$update_secret" = "y" ]; then
        read -p "Enter Binance Secret Key: " binance_secret
        sed -i.bak "s/BINANCEUS_SECRET=.*/BINANCEUS_SECRET=$binance_secret/" .env
        echo -e "${GREEN}✅ Binance Secret Key updated${NC}"
    fi
    
    read -p "Do you want to update Claude API Key? (y/n): " update_claude
    if [ "$update_claude" = "y" ]; then
        read -p "Enter Claude API Key: " claude_key
        sed -i.bak "s/CLAUDE_API_KEY=.*/CLAUDE_API_KEY=$claude_key/" .env
        echo -e "${GREEN}✅ Claude API Key updated${NC}"
    fi
    
    echo -e "${GREEN}✅ API keys updated${NC}"
}

# Function to test API connections
test_api_connections() {
    echo -e "${BLUE}🔗 Testing API Connections...${NC}"
    echo ""
    
    # Test Binance connection
    echo -e "${BLUE}Testing Binance US API...${NC}"
    python3 -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()

try:
    response = requests.get('https://api.binance.us/api/v3/ping')
    if response.status_code == 200:
        print('✅ Binance US API: Connected')
    else:
        print('❌ Binance US API: Connection failed')
except Exception as e:
    print(f'❌ Binance US API: Error - {e}')
"
    
    # Test Claude API if key is provided
    echo -e "${BLUE}Testing Claude API...${NC}"
    python3 -c "
import requests
import os
from dotenv import load_dotenv

load_dotenv()

claude_key = os.getenv('CLAUDE_API_KEY')
if not claude_key or claude_key == 'your_claude_api_key_here':
    print('⚠️  Claude API: Key not configured')
else:
    try:
        headers = {
            'x-api-key': claude_key,
            'content-type': 'application/json',
        }
        payload = {
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': 'Test'}]
        }
        response = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print('✅ Claude API: Connected')
        else:
            print(f'❌ Claude API: Error {response.status_code}')
    except Exception as e:
        print(f'❌ Claude API: Error - {e}')
"
    
    echo ""
}

# Main menu loop
main_menu() {
    while true; do
        show_bot_menu
        
        echo -e "${CYAN}Select a trading bot or option:${NC}"
        read -p "Enter your choice (0-9): " choice
        echo ""
        
        case $choice in
            1) check_dependencies && run_enhanced_bot ;;
            2) check_dependencies && run_volume_bot ;;
            3) check_dependencies && run_moonshot ;;
            4) check_dependencies && run_master_bot ;;
            5) check_dependencies && run_statistical ;;
            6) check_dependencies && run_claude_predictor ;;
            7) check_dependencies && run_live_bot ;;
            8) check_dependencies && run_demo_mode ;;
            9) setup_configuration ;;
            0) 
                echo -e "${GREEN}👋 Thanks for using VictoryChain Trading Bot!${NC}"
                echo -e "${BLUE}🚀 May your trades be profitable!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please select 0-9.${NC}"
                echo ""
                ;;
        esac
        
        # Wait before showing menu again
        echo ""
        read -p "Press Enter to return to main menu..."
        clear
    done
}

# Start the launcher
clear
main_menu
