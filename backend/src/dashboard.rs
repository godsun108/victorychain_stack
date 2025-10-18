use axum::{
    extract::State,
    http::StatusCode,
    response::{Html, Json},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::Arc};
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tracing::{info, error};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DashboardMetrics {
    pub total_balance_usdt: f64,
    pub current_positions: Vec<PositionInfo>,
    pub daily_pnl: f64,
    pub total_trades: u64,
    pub win_rate: f64,
    pub top_gainers: Vec<TokenPerformance>,
    pub bot_status: String,
    pub last_trade_time: u64,
    pub ai_analysis_status: String,
    pub rate_limit_status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionInfo {
    pub symbol: String,
    pub quantity: f64,
    pub entry_price: f64,
    pub current_price: f64,
    pub pnl_percent: f64,
    pub pnl_usdt: f64,
    pub hold_duration_hours: f64,
    pub ai_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenPerformance {
    pub symbol: String,
    pub price_change_24h: f64,
    pub volume_change: f64,
    pub momentum_score: f64,
    pub ai_score: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingCommand {
    pub action: String, // "start", "stop", "emergency_stop", "rebalance"
    pub symbol: Option<String>,
    pub amount: Option<f64>,
}

pub struct DashboardState {
    metrics: Arc<RwLock<DashboardMetrics>>,
    is_trading_active: Arc<RwLock<bool>>,
}

impl DashboardState {
    pub fn new() -> Self {
        Self {
            metrics: Arc::new(RwLock::new(DashboardMetrics {
                total_balance_usdt: 0.0,
                current_positions: Vec::new(),
                daily_pnl: 0.0,
                total_trades: 0,
                win_rate: 0.0,
                top_gainers: Vec::new(),
                bot_status: "Initializing".to_string(),
                last_trade_time: 0,
                ai_analysis_status: "Connecting".to_string(),
                rate_limit_status: "Normal".to_string(),
            })),
            is_trading_active: Arc::new(RwLock::new(false)),
        }
    }

    pub async fn update_metrics(&self, new_metrics: DashboardMetrics) {
        let mut metrics = self.metrics.write().await;
        *metrics = new_metrics;
    }

    pub async fn set_trading_status(&self, active: bool) {
        let mut status = self.is_trading_active.write().await;
        *status = active;
    }
}

pub async fn start_dashboard_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    let state = DashboardState::new();
    
    let app = Router::new()
        .route("/", get(dashboard_home))
        .route("/api/metrics", get(get_metrics))
        .route("/api/status", get(get_status))
        .route("/api/command", post(execute_command))
        .route("/api/positions", get(get_positions))
        .route("/api/performance", get(get_performance_stats))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind(format!("127.0.0.1:{}", port)).await?;
    
    info!("🌐 Dashboard server starting on http://127.0.0.1:{}", port);
    info!("📊 Access your trading dashboard at: http://127.0.0.1:{}", port);
    
    axum::serve(listener, app).await?;
    
    Ok(())
}

async fn dashboard_home() -> Html<&'static str> {
    Html(r#"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VictoryChain Trading Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .status-bar { 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .metric { text-align: center; margin-bottom: 15px; }
        .metric-value { font-size: 2rem; font-weight: bold; margin-bottom: 5px; }
        .metric-label { opacity: 0.8; font-size: 0.9rem; }
        .positive { color: #4CAF50; }
        .negative { color: #f44336; }
        .neutral { color: #ff9800; }
        .btn { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 5px;
        }
        .btn:hover { background: #45a049; }
        .btn.danger { background: #f44336; }
        .btn.danger:hover { background: #da190b; }
        .positions-table { width: 100%; border-collapse: collapse; }
        .positions-table th, .positions-table td { 
            padding: 10px; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.2); 
        }
        .auto-refresh { margin-top: 20px; text-align: center; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 VictoryChain Trading Dashboard</h1>
            <p>AI-Powered Capital Gains Maximizer</p>
        </div>
        
        <div class="status-bar">
            <div>
                <strong>Bot Status:</strong> <span id="bot-status">Loading...</span>
            </div>
            <div>
                <strong>AI Analysis:</strong> <span id="ai-status">Loading...</span>
            </div>
            <div>
                <strong>Rate Limits:</strong> <span id="rate-status">Loading...</span>
            </div>
            <div>
                <button class="btn" onclick="toggleTrading()">Start/Stop Trading</button>
                <button class="btn danger" onclick="emergencyStop()">Emergency Stop</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Portfolio Overview</h3>
                <div class="metric">
                    <div class="metric-value" id="total-balance">$0.00</div>
                    <div class="metric-label">Total Balance (USDT)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="daily-pnl">$0.00</div>
                    <div class="metric-label">Daily P&L</div>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Trading Stats</h3>
                <div class="metric">
                    <div class="metric-value" id="total-trades">0</div>
                    <div class="metric-label">Total Trades</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="win-rate">0%</div>
                    <div class="metric-label">Win Rate</div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Current Positions</h3>
                <div id="positions-container">
                    <p>No active positions</p>
                </div>
            </div>
            
            <div class="card">
                <h3>🚀 Top Momentum Tokens</h3>
                <div id="top-gainers-container">
                    <p>Loading...</p>
                </div>
            </div>
        </div>
        
        <div class="auto-refresh">
            <p>Auto-refreshing every 5 seconds • Last updated: <span id="last-update">Never</span></p>
        </div>
    </div>

    <script>
        let isTrading = false;
        
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
            }
        }
        
        function updateDashboard(data) {
            document.getElementById('bot-status').textContent = data.bot_status;
            document.getElementById('ai-status').textContent = data.ai_analysis_status;
            document.getElementById('rate-status').textContent = data.rate_limit_status;
            document.getElementById('total-balance').textContent = `$${data.total_balance_usdt.toFixed(2)}`;
            
            const pnlElement = document.getElementById('daily-pnl');
            pnlElement.textContent = `$${data.daily_pnl.toFixed(2)}`;
            pnlElement.className = `metric-value ${data.daily_pnl >= 0 ? 'positive' : 'negative'}`;
            
            document.getElementById('total-trades').textContent = data.total_trades;
            document.getElementById('win-rate').textContent = `${(data.win_rate * 100).toFixed(1)}%`;
            
            // Update positions
            const positionsContainer = document.getElementById('positions-container');
            if (data.current_positions.length === 0) {
                positionsContainer.innerHTML = '<p>No active positions</p>';
            } else {
                let positionsHtml = '<table class="positions-table"><tr><th>Symbol</th><th>Qty</th><th>P&L</th><th>Hold Time</th></tr>';
                data.current_positions.forEach(pos => {
                    const pnlClass = pos.pnl_percent >= 0 ? 'positive' : 'negative';
                    positionsHtml += `<tr>
                        <td>${pos.symbol}</td>
                        <td>${pos.quantity.toFixed(4)}</td>
                        <td class="${pnlClass}">${pos.pnl_percent.toFixed(2)}%</td>
                        <td>${pos.hold_duration_hours.toFixed(1)}h</td>
                    </tr>`;
                });
                positionsHtml += '</table>';
                positionsContainer.innerHTML = positionsHtml;
            }
            
            // Update top gainers
            const gainersContainer = document.getElementById('top-gainers-container');
            if (data.top_gainers.length === 0) {
                gainersContainer.innerHTML = '<p>No data available</p>';
            } else {
                let gainersHtml = '';
                data.top_gainers.slice(0, 5).forEach(token => {
                    const changeClass = token.price_change_24h >= 0 ? 'positive' : 'negative';
                    gainersHtml += `<div>
                        <strong>${token.symbol}</strong>: 
                        <span class="${changeClass}">${token.price_change_24h.toFixed(2)}%</span>
                        ${token.ai_score ? ` (AI: ${token.ai_score.toFixed(0)}/100)` : ''}
                    </div>`;
                });
                gainersContainer.innerHTML = gainersHtml;
            }
            
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }
        
        async function toggleTrading() {
            try {
                const action = isTrading ? 'stop' : 'start';
                await fetch('/api/command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                isTrading = !isTrading;
            } catch (error) {
                console.error('Failed to toggle trading:', error);
            }
        }
        
        async function emergencyStop() {
            if (confirm('Are you sure you want to execute an emergency stop? This will cancel all orders and halt trading.')) {
                try {
                    await fetch('/api/command', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'emergency_stop' })
                    });
                    alert('Emergency stop executed!');
                } catch (error) {
                    console.error('Failed to execute emergency stop:', error);
                }
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(fetchMetrics, 5000);
        fetchMetrics(); // Initial load
    </script>
</body>
</html>
    "#)
}

async fn get_metrics(State(state): State<DashboardState>) -> Json<DashboardMetrics> {
    let metrics = state.metrics.read().await;
    Json(metrics.clone())
}

async fn get_status(State(state): State<DashboardState>) -> Json<HashMap<String, bool>> {
    let is_active = state.is_trading_active.read().await;
    let mut status = HashMap::new();
    status.insert("is_trading_active".to_string(), *is_active);
    Json(status)
}

async fn execute_command(
    State(state): State<DashboardState>,
    Json(command): Json<TradingCommand>,
) -> Result<Json<HashMap<String, String>>, StatusCode> {
    info!("📡 Received dashboard command: {:?}", command);
    
    let mut response = HashMap::new();
    
    match command.action.as_str() {
        "start" => {
            state.set_trading_status(true).await;
            response.insert("status".to_string(), "Trading started".to_string());
        }
        "stop" => {
            state.set_trading_status(false).await;
            response.insert("status".to_string(), "Trading stopped".to_string());
        }
        "emergency_stop" => {
            state.set_trading_status(false).await;
            response.insert("status".to_string(), "Emergency stop executed".to_string());
            // Here you would trigger emergency stop logic
        }
        "rebalance" => {
            response.insert("status".to_string(), "Rebalance triggered".to_string());
            // Here you would trigger rebalancing logic
        }
        _ => {
            return Err(StatusCode::BAD_REQUEST);
        }
    }
    
    Ok(Json(response))
}

async fn get_positions(State(state): State<DashboardState>) -> Json<Vec<PositionInfo>> {
    let metrics = state.metrics.read().await;
    Json(metrics.current_positions.clone())
}

async fn get_performance_stats(State(state): State<DashboardState>) -> Json<HashMap<String, f64>> {
    let metrics = state.metrics.read().await;
    let mut stats = HashMap::new();
    
    stats.insert("total_balance".to_string(), metrics.total_balance_usdt);
    stats.insert("daily_pnl".to_string(), metrics.daily_pnl);
    stats.insert("win_rate".to_string(), metrics.win_rate);
    stats.insert("total_trades".to_string(), metrics.total_trades as f64);
    
    Json(stats)
}
