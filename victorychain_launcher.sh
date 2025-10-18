#!/bin/bash
# VictoryChain Launcher - Consolidated script for all trading operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check required Python packages
    python3 -c "import binance, requests, dotenv" 2>/dev/null || {
        print_warning "Installing required Python packages..."
        pip3 install python-binance requests python-dotenv
    }
    
    # Check .env file
    if [[ ! -f ".env" ]]; then
        print_error "No .env file found. Please create one with your API keys."
        exit 1
    fi
    
    print_success "All dependencies OK"
}

# Menu system
show_menu() {
    echo ""
    echo -e "${BLUE}🚀 VICTORYCHAIN LAUNCHER${NC}"
    echo "=" * 50
    echo "1. Quick Analysis (Fast market scan)"
    echo "2. Full Analysis (Complete market analysis)"
    echo "3. Live Trading (Execute trades)"
    echo "4. Portfolio Check (Current holdings)"
    echo "5. Monitor Mode (Continuous monitoring)"
    echo "6. Setup/Install (Dependencies and config)"
    echo "7. Exit"
    echo ""
    echo -n "Select option (1-7): "
}

# Quick analysis
quick_analysis() {
    print_status "Running quick market analysis..."
    python3 victorychain_core.py
}

# Full analysis with Claude
full_analysis() {
    print_status "Running full analysis with AI..."
    python3 launch_live_trading.py
}

# Live trading
live_trading() {
    print_warning "LIVE TRADING MODE - REAL MONEY AT RISK"
    echo "This will execute actual trades on Binance US"
    echo -n "Are you sure? Type 'YES' to continue: "
    read confirmation
    
    if [[ "$confirmation" != "YES" ]]; then
        print_error "Live trading cancelled"
        return
    fi
    
    print_status "Starting live trading..."
    python3 -c "
from victorychain_core import VictoryChainCore
vc = VictoryChainCore()
vc.run_analysis(execute_trades=True)
"
}

# Portfolio check
portfolio_check() {
    print_status "Checking portfolio..."
    python3 -c "
from victorychain_core import VictoryChainCore
vc = VictoryChainCore()
account = vc.get_account_info()
if account:
    print(f'Portfolio Value: \${account[\"total_usdt_value\"]:.2f}')
    print(f'Available USDT: \${account[\"usdt_balance\"]:.2f}')
    print('Holdings:')
    for asset, balance in account['balances'].items():
        if balance['total'] > 0:
            print(f'  {asset}: {balance[\"total\"]:.6f}')
"
}

# Monitor mode
monitor_mode() {
    print_status "Starting continuous monitoring..."
    print_warning "Press Ctrl+C to stop"
    
    while true; do
        python3 victorychain_core.py
        print_status "Waiting 5 minutes for next scan..."
        sleep 300  # 5 minutes
    done
}

# Setup/Install
setup_install() {
    print_status "Setting up VictoryChain..."
    
    # Install Python dependencies
    print_status "Installing Python packages..."
    pip3 install python-binance requests python-dotenv anthropic
    
    # Create .env template if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cat > .env << EOF
# Binance US API Configuration
BINANCEUS_KEY=your_api_key_here
BINANCEUS_SECRET=your_secret_key_here

# Claude AI API Key (optional)
CLAUDE_API_KEY=your_claude_key_here

# Trading Configuration
RUST_LOG=info
EOF
        print_success "Created .env template - please add your API keys"
    fi
    
    print_success "Setup complete!"
}

# Main script
main() {
    cd "$(dirname "$0")"
    
    print_status "VictoryChain Trading System"
    check_dependencies
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                quick_analysis
                ;;
            2)
                full_analysis
                ;;
            3)
                live_trading
                ;;
            4)
                portfolio_check
                ;;
            5)
                monitor_mode
                ;;
            6)
                setup_install
                ;;
            7)
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        echo -n "Press Enter to continue..."
        read
    done
}

# Run main function
main "$@"
