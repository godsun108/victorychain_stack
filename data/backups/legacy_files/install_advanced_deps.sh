#!/bin/bash
"""
Install Advanced Analysis Dependencies
Ensures all required packages are installed for quantum-level trading analysis
"""

echo "🚀 Installing Advanced Trading Analysis Dependencies..."
echo "============================================="

# Core scientific computing
echo "📊 Installing core scientific packages..."
pip install pandas numpy scipy scikit-learn

# Statistical analysis
echo "📈 Installing statistical analysis packages..."
pip install statsmodels

# Additional machine learning
echo "🤖 Installing machine learning packages..."
pip install xgboost lightgbm

# Financial analysis (optional)
echo "💰 Installing financial analysis packages..."
pip install yfinance quantlib-python || echo "⚠️  Some financial packages may not install on all systems"

# Visualization (optional)
echo "📊 Installing visualization packages..."
pip install matplotlib plotly seaborn || echo "⚠️  Visualization packages optional"

# Networking and async
echo "🌐 Installing networking packages..."
pip install aiohttp websockets requests

echo ""
echo "✅ Advanced analysis dependencies installation complete!"
echo ""
echo "🎯 You can now run:"
echo "   python quantum_data_analyst.py"
echo "   python statistical_arbitrage_system.py"
echo "   python market_microstructure_analyzer.py"
echo "   python master_advanced_analysis.py"
echo ""
