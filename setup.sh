#!/bin/bash

# 🏆 VictoryChain Setup Script
# Professional setup for the VictoryChain trading system

set -e  # Exit on any error

echo "🏆 VictoryChain Trading System Setup"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

print_status "Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_info "Creating directory structure..."
mkdir -p data/logs data/backups data/reports
mkdir -p src/web/static/{css,js,img}
mkdir -p config

# (Configuration template copy step removed)

# Set up logging directory
print_info "Setting up logging..."
touch data/logs/victorychain.log
touch data/logs/momentum_trader.log
touch data/logs/web_dashboard.log

# Create __init__.py files for proper package structure
find src -type d -exec touch {}/__init__.py \;

# Make scripts executable
chmod +x main.py
chmod +x update_imports.py
if [ -f "scripts/full_stack_analysis.py" ]; then
    chmod +x scripts/full_stack_analysis.py
fi

# Check if Rust is available (optional)
if command -v cargo &> /dev/null; then
    print_status "Rust found: $(rustc --version)"
    print_info "Building Rust backend (optional)..."
    if [ -f "Cargo.toml" ]; then
        cargo build --release || print_warning "Rust build failed (optional component)"
    fi
else
    print_warning "Rust not found - backend components will not be available"
fi

# Test imports
print_info "Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from core.victorychain_shared import TradingConfig
    from core.victorychain_integration import VictoryChainIntegrationManager
    print('✅ Core imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

print_status "Setup completed successfully!"
echo ""
echo "🚀 Quick Start:"
echo "   python main.py --mode core     # Start core trading engine"
echo "   python main.py --mode web      # Start web dashboard"
echo "   python main.py --mode momentum # Start momentum trader"
echo "   python main.py --mode analyze  # Run token analysis"
echo ""
echo "📚 Documentation:"
echo "   See PROJECT_STRUCTURE.md for detailed information"
echo "   See docs/ directory for comprehensive documentation"
echo ""
echo "⚙️ Configuration:"
echo "   Update .env with your API keys"
echo "   Modify config/victorychain_config.toml for trading settings"
echo ""
print_status "VictoryChain is ready to trade! 🚀"
