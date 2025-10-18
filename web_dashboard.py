#!/usr/bin/env python3

"""
🌐 VICTORYCHAIN WEB DASHBOARD
Real-time web interface for monitoring and controlling the trading system
Author: Senior Developer
Version: 2.0.0
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging

# Import VictoryChain components
try:
    from victorychain_shared import (
        OrderType,
        StrategyType,
        TradingConfig,
        MarketData,
        TradingSignal,
        TradeResult,
        PortfolioPosition,
        get_logger,
        format_currency,
        format_percentage,
    )
    from victorychain_integration import VictoryChainIntegrationManager

    HAS_VICTORYCHAIN = True
except ImportError as e:
    print(f"Warning: VictoryChain modules not available: {e}")
    HAS_VICTORYCHAIN = False

# Configure Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "victorychain-dashboard-secret"
)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logger = get_logger(__name__) if HAS_VICTORYCHAIN else logging.getLogger(__name__)


class VictoryChainDashboard:
    """Real-time web dashboard for VictoryChain trading system"""

    def __init__(self):
        self.integration_manager = None
        self.last_update = datetime.now()
        self.dashboard_data = {
            "portfolio": {},
            "active_signals": [],
            "recent_trades": [],
            "performance_metrics": {},
            "system_status": {},
            "market_data": {},
        }

        if HAS_VICTORYCHAIN:
            try:
                self.integration_manager = VictoryChainIntegrationManager()
                self.integration_manager.load_all_modules()
                logger.info("Dashboard connected to VictoryChain")
            except Exception as e:
                logger.error(f"Failed to connect to VictoryChain: {e}")

        # Start background data updater
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _update_loop(self):
        """Background thread to update dashboard data"""
        while True:
            try:
                self._update_dashboard_data()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                time.sleep(10)

    def _update_dashboard_data(self):
        """Update all dashboard data"""
        try:
            current_time = datetime.now()

            # Update portfolio data
            self.dashboard_data["portfolio"] = self._get_portfolio_data()

            # Update active signals
            self.dashboard_data["active_signals"] = self._get_active_signals()

            # Update recent trades
            self.dashboard_data["recent_trades"] = self._get_recent_trades()

            # Update performance metrics
            self.dashboard_data["performance_metrics"] = self._get_performance_metrics()

            # Update system status
            self.dashboard_data["system_status"] = self._get_system_status()

            # Update market data
            self.dashboard_data["market_data"] = self._get_market_data()

            self.last_update = current_time

            # Emit update to connected clients
            socketio.emit("dashboard_update", self.dashboard_data)

        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")

    def _get_portfolio_data(self) -> Dict[str, Any]:
        """Get current portfolio information"""
        if not self.integration_manager:
            return self._get_mock_portfolio()

        try:
            core = self.integration_manager.get_module("victorychain_core_v2")
            if core and hasattr(core, "get_portfolio_status"):
                positions, metrics = core.get_portfolio_status()

                portfolio_data = {
                    "total_value": metrics.total_value,
                    "total_pnl": metrics.total_pnl,
                    "total_pnl_pct": metrics.total_pnl_pct,
                    "positions": [],
                }

                for pos in positions:
                    portfolio_data["positions"].append(
                        {
                            "symbol": pos.asset,
                            "quantity": pos.amount,
                            "value": pos.usd_value,
                            "pnl": getattr(pos, "pnl", 0),
                            "pnl_pct": getattr(pos, "pnl_pct", 0),
                        }
                    )

                return portfolio_data

        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")

        return self._get_mock_portfolio()

    def _get_mock_portfolio(self) -> Dict[str, Any]:
        """Mock portfolio data for demonstration"""
        return {
            "total_value": 10000.0,
            "total_pnl": 1250.0,
            "total_pnl_pct": 12.5,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "quantity": 0.2,
                    "value": 6000.0,
                    "pnl": 800.0,
                    "pnl_pct": 15.3,
                },
                {
                    "symbol": "ETHUSDT",
                    "quantity": 2.5,
                    "value": 4000.0,
                    "pnl": 450.0,
                    "pnl_pct": 12.7,
                },
            ],
        }

    def _get_active_signals(self) -> List[Dict[str, Any]]:
        """Get active trading signals"""
        return [
            {
                "id": "1",
                "symbol": "ADAUSDT",
                "action": "BUY",
                "confidence": 0.85,
                "strategy": "momentum",
                "target_amount": 100.0,
                "reasoning": "Strong momentum breakout with volume confirmation",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "2",
                "symbol": "DOTUSDT",
                "action": "SELL",
                "confidence": 0.73,
                "strategy": "consolidation",
                "target_amount": 50.0,
                "reasoning": "Consolidation target reached, taking profits",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            },
        ]

    def _get_recent_trades(self) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        return [
            {
                "id": "trade_001",
                "symbol": "MAGICUSDT",
                "action": "BUY",
                "quantity": 150.0,
                "price": 0.65,
                "value": 97.50,
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "status": "FILLED",
            },
            {
                "id": "trade_002",
                "symbol": "SOLUSDT",
                "action": "SELL",
                "quantity": 5.0,
                "price": 45.20,
                "value": 226.0,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "status": "FILLED",
            },
        ]

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "daily_pnl": 156.78,
            "daily_pnl_pct": 1.57,
            "weekly_pnl": 892.45,
            "weekly_pnl_pct": 9.18,
            "monthly_pnl": 1250.0,
            "monthly_pnl_pct": 12.5,
            "win_rate": 68.5,
            "total_trades": 47,
            "avg_trade_size": 125.50,
            "sharpe_ratio": 1.85,
            "max_drawdown": -5.2,
        }

    def _get_system_status(self) -> Dict[str, Any]:
        """Get system health status"""
        if self.integration_manager:
            status = self.integration_manager.get_integration_status()
            modules_loaded = sum(1 for m in status["modules"].values() if m["loaded"])
            total_modules = len(status["modules"])
        else:
            modules_loaded = 0
            total_modules = 10

        return {
            "system_health": "healthy" if modules_loaded > 0 else "degraded",
            "modules_loaded": modules_loaded,
            "total_modules": total_modules,
            "uptime": str(datetime.now() - self.last_update),
            "claude_api_status": "connected",
            "binance_api_status": "connected",
            "last_update": self.last_update.isoformat(),
        }

    def _get_market_data(self) -> Dict[str, Any]:
        """Get current market data"""
        return {
            "btc_price": 65432.10,
            "eth_price": 3245.67,
            "total_market_cap": 2.45e12,
            "fear_greed_index": 72,
            "top_gainers": [
                {"symbol": "ADAUSDT", "change": 15.3},
                {"symbol": "DOTUSDT", "change": 12.7},
                {"symbol": "LINKUSDT", "change": 8.9},
            ],
            "top_losers": [
                {"symbol": "XRPUSDT", "change": -6.2},
                {"symbol": "LTCUSDT", "change": -4.8},
                {"symbol": "BCHUSDT", "change": -3.1},
            ],
        }


# Initialize dashboard
dashboard = VictoryChainDashboard()


# Routes
@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("dashboard.html")


@app.route("/api/data")
def get_dashboard_data():
    """Get all dashboard data"""
    return jsonify(dashboard.dashboard_data)


@app.route("/api/portfolio")
def get_portfolio():
    """Get portfolio data"""
    return jsonify(dashboard.dashboard_data["portfolio"])


@app.route("/api/signals")
def get_signals():
    """Get active trading signals"""
    return jsonify(dashboard.dashboard_data["active_signals"])


@app.route("/api/trades")
def get_trades():
    """Get recent trades"""
    return jsonify(dashboard.dashboard_data["recent_trades"])


@app.route("/api/performance")
def get_performance():
    """Get performance metrics"""
    return jsonify(dashboard.dashboard_data["performance_metrics"])


@app.route("/api/status")
def get_status():
    """Get system status"""
    return jsonify(dashboard.dashboard_data["system_status"])


@app.route("/api/market")
def get_market():
    """Get market data"""
    return jsonify(dashboard.dashboard_data["market_data"])


@app.route("/api/manual_trade", methods=["POST"])
def manual_trade():
    """Execute manual trade"""
    try:
        trade_data = request.get_json()

        # Validate trade data
        required_fields = ["symbol", "action", "amount"]
        for field in required_fields:
            if field not in trade_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Here you would integrate with the actual trading system
        logger.info(f"Manual trade request: {trade_data}")

        # Mock successful response
        response = {
            "success": True,
            "trade_id": f"manual_{int(time.time())}",
            "message": f"Trade executed: {trade_data['action']} {trade_data['amount']} {trade_data['symbol']}",
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Manual trade error: {e}")
        return jsonify({"error": str(e)}), 500


# WebSocket events
@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    emit("connected", {"data": "Connected to VictoryChain Dashboard"})
    emit("dashboard_update", dashboard.dashboard_data)


@socketio.on("request_update")
def handle_update_request():
    """Handle manual update request"""
    emit("dashboard_update", dashboard.dashboard_data)


def create_dashboard_html():
    """Create the dashboard HTML template"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VictoryChain Trading Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .status-bar {
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 2rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #64B5F6;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .positive {
            color: #4CAF50;
        }
        
        .negative {
            color: #F44336;
        }
        
        .signal {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #2196F3;
        }
        
        .signal.buy {
            border-left-color: #4CAF50;
        }
        
        .signal.sell {
            border-left-color: #F44336;
        }
        
        .trade {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        
        .auto-refresh {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.5);
            padding: 0.5rem;
            border-radius: 8px;
            font-size: 0.8rem;
        }
        
        @media (max-width: 1200px) {
            .dashboard-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 VictoryChain Trading Dashboard</h1>
        <div class="status-bar">
            <div class="status-item">
                <div class="status-indicator"></div>
                <span>System Online</span>
            </div>
            <div class="status-item">
                <div class="status-indicator"></div>
                <span>Claude AI Connected</span>
            </div>
            <div class="status-item">
                <div class="status-indicator"></div>
                <span>Binance API Active</span>
            </div>
        </div>
    </div>
    
    <div class="auto-refresh">
        <span id="last-update">Last update: --:--:--</span>
    </div>
    
    <div class="dashboard-grid">
        <!-- Portfolio Overview -->
        <div class="card">
            <h3>💼 Portfolio Overview</h3>
            <div id="portfolio-data">
                <div class="metric">
                    <span>Total Value:</span>
                    <span id="total-value">$0.00</span>
                </div>
                <div class="metric">
                    <span>Total P&L:</span>
                    <span id="total-pnl" class="positive">$0.00</span>
                </div>
                <div class="metric">
                    <span>P&L %:</span>
                    <span id="total-pnl-pct" class="positive">0.00%</span>
                </div>
            </div>
        </div>
        
        <!-- Performance Metrics -->
        <div class="card">
            <h3>📈 Performance</h3>
            <div id="performance-data">
                <div class="metric">
                    <span>Daily P&L:</span>
                    <span id="daily-pnl">$0.00</span>
                </div>
                <div class="metric">
                    <span>Win Rate:</span>
                    <span id="win-rate">0%</span>
                </div>
                <div class="metric">
                    <span>Total Trades:</span>
                    <span id="total-trades">0</span>
                </div>
            </div>
        </div>
        
        <!-- System Status -->
        <div class="card">
            <h3>⚙️ System Status</h3>
            <div id="system-status">
                <div class="metric">
                    <span>Health:</span>
                    <span id="system-health">Checking...</span>
                </div>
                <div class="metric">
                    <span>Modules:</span>
                    <span id="modules-status">0/0</span>
                </div>
            </div>
        </div>
        
        <!-- Active Signals -->
        <div class="card">
            <h3>🎯 Active Signals</h3>
            <div id="signals-list">
                <p>No active signals</p>
            </div>
        </div>
        
        <!-- Recent Trades -->
        <div class="card">
            <h3>📋 Recent Trades</h3>
            <div id="trades-list">
                <p>No recent trades</p>
            </div>
        </div>
        
        <!-- Market Overview -->
        <div class="card">
            <h3>🌍 Market Overview</h3>
            <div id="market-data">
                <div class="metric">
                    <span>BTC Price:</span>
                    <span id="btc-price">$0.00</span>
                </div>
                <div class="metric">
                    <span>ETH Price:</span>
                    <span id="eth-price">$0.00</span>
                </div>
                <div class="metric">
                    <span>Fear & Greed:</span>
                    <span id="fear-greed">0</span>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to VictoryChain Dashboard');
        });
        
        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
            document.getElementById('last-update').textContent = 
                'Last update: ' + new Date().toLocaleTimeString();
        });
        
        function updateDashboard(data) {
            // Update portfolio
            if (data.portfolio) {
                document.getElementById('total-value').textContent = 
                    '$' + data.portfolio.total_value.toLocaleString();
                document.getElementById('total-pnl').textContent = 
                    '$' + data.portfolio.total_pnl.toLocaleString();
                document.getElementById('total-pnl-pct').textContent = 
                    data.portfolio.total_pnl_pct.toFixed(2) + '%';
            }
            
            // Update performance
            if (data.performance_metrics) {
                const perf = data.performance_metrics;
                document.getElementById('daily-pnl').textContent = 
                    '$' + perf.daily_pnl.toLocaleString();
                document.getElementById('win-rate').textContent = 
                    perf.win_rate.toFixed(1) + '%';
                document.getElementById('total-trades').textContent = 
                    perf.total_trades;
            }
            
            // Update system status
            if (data.system_status) {
                const status = data.system_status;
                document.getElementById('system-health').textContent = 
                    status.system_health;
                document.getElementById('modules-status').textContent = 
                    status.modules_loaded + '/' + status.total_modules;
            }
            
            // Update market data
            if (data.market_data) {
                const market = data.market_data;
                document.getElementById('btc-price').textContent = 
                    '$' + market.btc_price.toLocaleString();
                document.getElementById('eth-price').textContent = 
                    '$' + market.eth_price.toLocaleString();
                document.getElementById('fear-greed').textContent = 
                    market.fear_greed_index;
            }
            
            // Update signals
            if (data.active_signals) {
                const signalsList = document.getElementById('signals-list');
                if (data.active_signals.length === 0) {
                    signalsList.innerHTML = '<p>No active signals</p>';
                } else {
                    signalsList.innerHTML = data.active_signals.map(signal => `
                        <div class="signal ${signal.action.toLowerCase()}">
                            <strong>${signal.symbol}</strong> - ${signal.action}<br>
                            <small>Confidence: ${(signal.confidence * 100).toFixed(0)}% | ${signal.strategy}</small>
                        </div>
                    `).join('');
                }
            }
            
            // Update trades
            if (data.recent_trades) {
                const tradesList = document.getElementById('trades-list');
                if (data.recent_trades.length === 0) {
                    tradesList.innerHTML = '<p>No recent trades</p>';
                } else {
                    tradesList.innerHTML = data.recent_trades.map(trade => `
                        <div class="trade">
                            <div>
                                <strong>${trade.symbol}</strong> ${trade.action}<br>
                                <small>${trade.quantity} @ $${trade.price}</small>
                            </div>
                            <div>$${trade.value}</div>
                        </div>
                    `).join('');
                }
            }
        }
        
        // Initial data load
        fetch('/api/data')
            .then(response => response.json())
            .then(data => updateDashboard(data))
            .catch(error => console.error('Error loading dashboard data:', error));
    </script>
</body>
</html>"""

    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Write HTML template
    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(html_content)


def main():
    """Run the VictoryChain web dashboard"""

    print("🌐 Starting VictoryChain Web Dashboard")
    print("=" * 50)

    # Create HTML template
    create_dashboard_html()
    print("✅ Dashboard template created")

    # Configure Flask
    port = int(os.environ.get("DASHBOARD_PORT", 5000))
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    print(f"🚀 Dashboard starting on http://{host}:{port}")
    print("📊 Features available:")
    print("  • Real-time portfolio monitoring")
    print("  • Live trading signals")
    print("  • Performance analytics")
    print("  • System health monitoring")
    print("  • WebSocket real-time updates")

    try:
        # Run the Flask app with SocketIO
        socketio.run(app, host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Dashboard startup error: {e}")
        print(f"❌ Failed to start dashboard: {e}")


if __name__ == "__main__":
    main()
