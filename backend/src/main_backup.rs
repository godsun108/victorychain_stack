mod binance;
mod config;
mod exchange;
mod math;
mod risk;
mod strategy;

use strategy::Strategy;
use exchange::{Router, MarketData, OrderSide};
use risk::RiskManager;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use anyhow::Result;
use tokio;
use tracing::{info, warn, error};
use tracing_subscriber;
use crossbeam_channel;
use clap::{Parser, Subcommand};

// Bulk allocation state tracking with enhanced features
struct AllocationManager {
    last_allocation_time: u64,
    allocation_interval: u64, // 5 hours in seconds
    initial_balance: f64,
    profit_threshold: f64,
    stop_loss_threshold: f64,
    momentum_lookback: usize,
    price_history: Vec<f64>,
    volatility_threshold: f64,
    correlation_threshold: f64,
    allocation_history: Vec<AllocationRecord>,
}

#[derive(Debug, Clone)]
struct AllocationRecord {
    timestamp: u64,
    symbols: Vec<String>,
    amounts: Vec<f64>,
    prices: Vec<f64>,
    momentum: f64,
    volatility: f64,
}

impl AllocationManager {
    fn new() -> Self {
        Self {
            last_allocation_time: 0,
            allocation_interval: 5 * 60 * 60, // 5 hours
            initial_balance: 57.94, // Starting balance
            profit_threshold: 0.02, // 2% profit target
            stop_loss_threshold: -0.01, // 1% stop loss
            momentum_lookback: 100, // Look back 100 ticks for momentum
            price_history: Vec::new(),
            volatility_threshold: 0.02, // 2% volatility threshold
            correlation_threshold: 0.7, // 70% correlation threshold
            allocation_history: Vec::new(),
        }
    }

    fn update_price_history(&mut self, price: f64) {
        self.price_history.push(price);
        if self.price_history.len() > self.momentum_lookback {
            self.price_history.remove(0);
        }
    }

    fn calculate_momentum(&self) -> f64 {
        if self.price_history.len() < 20 {
            return 0.0;
        }
        
        let recent_avg = self.price_history.iter()
            .rev()
            .take(10)
            .sum::<f64>() / 10.0;
            
        let older_avg = self.price_history.iter()
            .rev()
            .skip(10)
            .take(10)
            .sum::<f64>() / 10.0;
            
        (recent_avg - older_avg) / older_avg
    }

    fn calculate_volatility(&self) -> f64 {
        if self.price_history.len() < 20 {
            return 0.0;
        }
        
        let returns: Vec<f64> = self.price_history
            .windows(2)
            .map(|w| (w[1] - w[0]) / w[0])
            .collect();
            
        let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean_return).powi(2))
            .sum::<f64>() / returns.len() as f64;
            
        variance.sqrt()
    }

    fn calculate_profit_pct(&self, current_portfolio_value: f64) -> f64 {
        (current_portfolio_value - self.initial_balance) / self.initial_balance
    }

    // Dynamic position sizing based on market conditions and confidence
    fn calculate_position_size(&self, base_size: f64, regime: &MarketRegime, confidence: f64, volatility: f64) -> f64 {
        let regime_multiplier = match regime {
            MarketRegime::Volatile => 0.5,  // Smaller positions in volatile markets
            MarketRegime::Trending => 1.0,  // Normal size in trending markets
            MarketRegime::Ranging => 0.8,   // Slightly smaller in ranging markets
            MarketRegime::Calm => 1.2,      // Larger positions in calm markets
        };
        
        // Volatility adjustment (inverse relationship)
        let vol_multiplier = if volatility > 0.03 {
            0.6  // Much smaller if high volatility
        } else if volatility > 0.02 {
            0.8  // Smaller if moderate volatility
        } else {
            1.1  // Slightly larger if low volatility
        };
        
        // Confidence multiplier (0.5 to 1.5 range)
        let confidence_multiplier = (confidence * 1.0 + 0.5).min(1.5);
        
        // Historical performance adjustment
        let performance_multiplier = if self.allocation_history.len() > 3 {
            let recent_success = self.allocation_history.iter()
                .rev()
                .take(3)
                .map(|a| if a.momentum.abs() > 0.001 { 1.0 } else { 0.0 })
                .sum::<f64>() / 3.0;
            
            0.7 + (recent_success * 0.6) // Range: 0.7 to 1.3
        } else {
            1.0
        };
        
        let final_size = base_size * regime_multiplier * vol_multiplier * confidence_multiplier * performance_multiplier;
        
        // Safety bounds
        final_size.max(base_size * 0.2).min(base_size * 2.0)
    }

    // Advanced ML-inspired allocation decision with multiple factors
    fn should_allocate(&self, current_time: u64, momentum: f64, current_portfolio_value: f64, regime: &MarketRegime) -> bool {
        // Check if minimum time has passed (dynamic based on market regime)
        let min_interval = match regime {
            MarketRegime::Volatile => self.allocation_interval / 2, // More frequent in volatile markets
            MarketRegime::Trending => self.allocation_interval,     // Normal frequency
            MarketRegime::Ranging => self.allocation_interval * 2,   // Less frequent in ranging markets
            MarketRegime::Calm => self.allocation_interval * 3,      // Least frequent in calm markets
        };
        
        let time_elapsed = current_time >= self.last_allocation_time + min_interval;
        
        // Calculate volatility for better timing
        let volatility = self.calculate_volatility();
        
        // Regime-adjusted thresholds
        let (vol_threshold, momentum_threshold) = match regime {
            MarketRegime::Volatile => (0.015, 0.0005), // Lower thresholds for high volatility
            MarketRegime::Trending => (0.020, 0.0015), // Standard thresholds
            MarketRegime::Ranging => (0.025, 0.0025),  // Higher thresholds for ranging
            MarketRegime::Calm => (0.030, 0.0035),     // Highest thresholds for calm
        };
        
        let volatility_favorable = volatility > vol_threshold;
        let momentum_aligned = momentum.abs() > momentum_threshold;
        
        // Calculate current profit with regime adjustment
        let current_profit = self.calculate_profit_pct(current_portfolio_value);
        
        // Dynamic profit/loss thresholds based on market regime
        let (profit_target, stop_loss) = match regime {
            MarketRegime::Volatile => (self.profit_threshold * 0.5, self.stop_loss_threshold * 2.0), // Tighter stops
            MarketRegime::Trending => (self.profit_threshold, self.stop_loss_threshold),
            MarketRegime::Ranging => (self.profit_threshold * 1.5, self.stop_loss_threshold * 0.5), // Wider targets
            MarketRegime::Calm => (self.profit_threshold * 2.0, self.stop_loss_threshold * 0.3),
        };
        
        let should_reallocate = current_profit < stop_loss || 
                               current_profit > profit_target ||
                               (volatility_favorable && momentum.abs() > momentum_threshold * 3.0); // Strong override
        
        // Multi-factor risk score with regime weighting
        let risk_score = volatility * momentum.abs() * match regime {
            MarketRegime::Volatile => 1.5, // Higher weight in volatile markets
            MarketRegime::Trending => 1.0,
            MarketRegime::Ranging => 0.7,
            MarketRegime::Calm => 0.5,
        };
        
        let risk_favorable = risk_score > 0.00005 && risk_score < 0.02;
        
        // Historical performance weighting
        let historical_success_rate = if self.allocation_history.len() > 5 {
            let recent_allocations = self.allocation_history.iter().rev().take(5);
            let successful = recent_allocations.filter(|a| a.momentum * momentum > 0.0).count();
            successful as f64 / 5.0
        } else {
            0.5 // Default neutral
        };
        
        let confidence_multiplier = if historical_success_rate > 0.6 { 1.2 } else { 0.8 };
        
        // Final decision with confidence weighting
        let base_decision = time_elapsed && momentum_aligned && should_reallocate && risk_favorable;
        let confidence_adjusted = (risk_score * confidence_multiplier) > 0.0001;
        
        base_decision && confidence_adjusted
    }

    fn record_allocation(&mut self, symbols: Vec<String>, amounts: Vec<f64>, prices: Vec<f64>, momentum: f64, volatility: f64) {
        let record = AllocationRecord {
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            symbols,
            amounts,
            prices,
            momentum,
            volatility,
        };
        
        self.allocation_history.push(record);
        
        // Keep only last 50 allocations
        if self.allocation_history.len() > 50 {
            self.allocation_history.remove(0);
        }
    }
}

#[derive(Parser)]
#[command(name = "victorychain")]
#[command(about = "A sophisticated quantitative trading system")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run the trading system
    Run {
        /// Enable live trading (default: simulation)
        #[arg(long)]
        live: bool,
        /// Configuration file path
        #[arg(short, long, default_value = "config.toml")]
        config: String,
        /// Trading symbols to monitor
        #[arg(long, value_delimiter = ',')]
        symbols: Option<Vec<String>>,
    },
    /// Test connection to exchange
    Test {
        /// Configuration file path
        #[arg(short, long, default_value = "config.toml")]
        config: String,
    },
    /// Check account balance
    Balance {
        /// Configuration file path
        #[arg(short, long, default_value = "config.toml")]
        config: String,
    },
}

// Enhanced portfolio analytics and performance tracking
#[derive(Debug, Clone)]
struct PortfolioAnalytics {
    total_trades: u64,
    winning_trades: u64,
    total_pnl: f64,
    max_drawdown: f64,
    sharpe_ratio: f64,
    daily_returns: Vec<f64>,
    trade_history: Vec<TradeRecord>,
    risk_adjusted_return: f64,
    var_95: f64,
    beta: f64,
}

#[derive(Debug, Clone)]
struct TradeRecord {
    timestamp: u64,
    symbol: String,
    side: String,
    quantity: f64,
    price: f64,
    pnl: f64,
    strategy: String,
}

impl PortfolioAnalytics {
    fn new() -> Self {
        Self {
            total_trades: 0,
            winning_trades: 0,
            total_pnl: 0.0,
            max_drawdown: 0.0,
            sharpe_ratio: 0.0,
            daily_returns: Vec::new(),
            trade_history: Vec::new(),
            risk_adjusted_return: 0.0,
            var_95: 0.0,
            beta: 0.0,
        }
    }

    fn record_trade(&mut self, trade: TradeRecord) {
        self.total_trades += 1;
        if trade.pnl > 0.0 {
            self.winning_trades += 1;
        }
        self.total_pnl += trade.pnl;
        self.trade_history.push(trade);
        
        // Keep only last 1000 trades
        if self.trade_history.len() > 1000 {
            self.trade_history.remove(0);
        }
        
        self.update_metrics();
    }

    fn update_metrics(&mut self) {
        if self.trade_history.is_empty() {
            return;
        }

        // Calculate win rate
        let win_rate = self.winning_trades as f64 / self.total_trades as f64;
        
        // Calculate Sharpe ratio (simplified)
        if !self.daily_returns.is_empty() {
            let mean_return = self.daily_returns.iter().sum::<f64>() / self.daily_returns.len() as f64;
            let return_std = {
                let variance = self.daily_returns.iter()
                    .map(|r| (r - mean_return).powi(2))
                    .sum::<f64>() / self.daily_returns.len() as f64;
                variance.sqrt()
            };
            
            if return_std > 0.0 {
                self.sharpe_ratio = (mean_return - 0.01 / 365.0) / return_std; // Risk-free rate adjusted
            }
        }

        // Calculate max drawdown
        let mut peak = 0.0;
        let mut current_drawdown = 0.0;
        for trade in &self.trade_history {
            let running_pnl: f64 = self.trade_history.iter()
                .take_while(|t| t.timestamp <= trade.timestamp)
                .map(|t| t.pnl)
                .sum();
            
            if running_pnl > peak {
                peak = running_pnl;
            }
            
            let drawdown = (peak - running_pnl) / peak.max(1.0);
            if drawdown > current_drawdown {
                current_drawdown = drawdown;
            }
        }
        self.max_drawdown = current_drawdown;
    }

    fn get_win_rate(&self) -> f64 {
        if self.total_trades == 0 { 0.0 } else { self.winning_trades as f64 / self.total_trades as f64 }
    }

    fn get_avg_trade_pnl(&self) -> f64 {
        if self.total_trades == 0 { 0.0 } else { self.total_pnl / self.total_trades as f64 }
    }
}

// Advanced market regime detection
#[derive(Debug, Clone, PartialEq)]
enum MarketRegime {
    Trending,
    Ranging,
    Volatile,
    Calm,
}

struct MarketRegimeDetector {
    price_history: Vec<f64>,
    volume_history: Vec<f64>,
    lookback_period: usize,
}

impl MarketRegimeDetector {
    fn new(lookback_period: usize) -> Self {
        Self {
            price_history: Vec::new(),
            volume_history: Vec::new(),
            lookback_period,
        }
    }

    fn update(&mut self, price: f64, volume: f64) {
        self.price_history.push(price);
        self.volume_history.push(volume);
        
        if self.price_history.len() > self.lookback_period {
            self.price_history.remove(0);
            self.volume_history.remove(0);
        }
    }

    fn detect_regime(&self) -> MarketRegime {
        if self.price_history.len() < 20 {
            return MarketRegime::Calm;
        }

        let volatility = self.calculate_volatility();
        let trend_strength = self.calculate_trend_strength();
        
        if volatility > 0.03 && trend_strength > 0.5 {
            MarketRegime::Volatile
        } else if trend_strength > 0.3 {
            MarketRegime::Trending
        } else if volatility < 0.01 {
            MarketRegime::Calm
        } else {
            MarketRegime::Ranging
        }
    }

    fn calculate_volatility(&self) -> f64 {
        if self.price_history.len() < 2 {
            return 0.0;
        }
        
        let returns: Vec<f64> = self.price_history
            .windows(2)
            .map(|w| (w[1] - w[0]) / w[0])
            .collect();
            
        let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean_return).powi(2))
            .sum::<f64>() / returns.len() as f64;
            
        variance.sqrt()
    }

    fn calculate_trend_strength(&self) -> f64 {
        if self.price_history.len() < 10 {
            return 0.0;
        }
        
        let first_half = &self.price_history[..self.price_history.len()/2];
        let second_half = &self.price_history[self.price_history.len()/2..];
        
        let first_avg = first_half.iter().sum::<f64>() / first_half.len() as f64;
        let second_avg = second_half.iter().sum::<f64>() / second_half.len() as f64;
        
        ((second_avg - first_avg) / first_avg).abs()
    }
}

// Entry point: orchestrates strategies
#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let cli = Cli::parse();

    match cli.command {
        Commands::Run { live, config: config_path, symbols } => {
            run_trading_system(live, &config_path, symbols).await
        }
        Commands::Test { config: config_path } => {
            test_connection(&config_path).await
        }
        Commands::Balance { config: config_path } => {
            check_balance(&config_path).await
        }
    }
}

async fn run_trading_system(live_trading: bool, config_path: &str, symbols_override: Option<Vec<String>>) -> Result<()> {
    info!("🚀 VictoryChain Stack Starting...");
    
    let mut cfg = config::load(config_path);
    cfg.exchange.live_trading = live_trading;
    
    if let Some(symbols) = symbols_override {
        cfg.exchange.symbols = symbols;
    }
    
    info!("📋 Config loaded: poll_ms={}, risk_free_rate={:.2}%, live_trading={}", 
        cfg.poll_ms, cfg.risk_free_rate * 100.0, cfg.exchange.live_trading);
    
    // Initialize router for exchange connections
    let mut router = Router::new(&cfg.exchange);
    let mut risk_mgr = RiskManager::new(cfg.risk.clone());
    
    // Connect and start data feeds
    if cfg.exchange.live_trading {
        info!("🔌 Starting WebSocket market data feed...");
        let (sender, receiver) = crossbeam_channel::unbounded();
        router.market_data_receiver = Some(receiver);
        
        let symbols = cfg.exchange.symbols.clone();
        tokio::spawn(async move {
            // Note: WebSocket functionality needs to be implemented in binance.rs
            tokio::time::sleep(Duration::from_secs(10)).await;
        });
        
        tokio::time::sleep(Duration::from_secs(2)).await;
    }
    
    // Instantiate strategies
    let mut strategies: Vec<Box<dyn Strategy>> = vec![
        Box::new(strategy::BasisArb::new(&cfg.basis_arb)),
        Box::new(strategy::ThetaHarvest::new(&cfg.theta)),
        Box::new(strategy::StatArb::new(&cfg.stat_arb)),
        Box::new(strategy::YieldLoop::new(&cfg.yield_loop)),
    ];
    
    info!("💼 Initialized {} strategies:", strategies.len());
    for strategy in &strategies {
        info!("  - {}", strategy.name());
    }
    
    // Initialize enhanced systems
    let mut allocation_mgr = AllocationManager::new();
    let mut portfolio_analytics = PortfolioAnalytics::new();
    let mut regime_detector = MarketRegimeDetector::new(50);
    let mut tick_count = 0;
    let start_time = std::time::Instant::now();
    let mut last_regime = MarketRegime::Calm;
    let mut emergency_stop = false;
    
    info!("🎯 Starting ENHANCED trading loop with ML-inspired features...");
    info!("📊 Features: Dynamic sizing, regime detection, portfolio analytics, emergency stops");
    
    loop {
        tick_count += 1;
        
        // Emergency stop check
        if portfolio_analytics.max_drawdown > 0.05 { // 5% max drawdown emergency stop
            if !emergency_stop {
                error!("🚨 EMERGENCY STOP: Max drawdown exceeded 5%");
                emergency_stop = true;
            }
            tokio::time::sleep(Duration::from_secs(60)).await; // Wait 1 minute before continuing
            continue;
        } else if emergency_stop {
            info!("✅ Emergency stop lifted - resuming normal operations");
            emergency_stop = false;
        }
        
        // Update market data from live feed
        router.update_market_data();
        
        // Get primary symbol market data with live fetching
        let primary_symbol = &cfg.exchange.symbols[0];
        let market = router.get_live_market_data(primary_symbol).await;

        // Update regime detector and get current regime
        regime_detector.update(market.spot_price, market.volume);
        let current_regime = regime_detector.detect_regime();
        
        // Log regime changes
        if current_regime != last_regime {
            info!("📈 Market regime changed: {:?} -> {:?}", last_regime, current_regime);
            last_regime = current_regime.clone();
        }

        // Calculate enhanced market analytics
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        allocation_mgr.update_price_history(market.spot_price);
        let momentum = allocation_mgr.calculate_momentum();
        let volatility = allocation_mgr.calculate_volatility();
        let current_portfolio_value = 57.94 + risk_mgr.calculate_var();
        
        // Enhanced logging with regime and analytics
        if tick_count % 10 == 0 {
            let uptime = start_time.elapsed().as_secs();
            let momentum_pct = momentum * 100.0;
            let volatility_pct = volatility * 100.0;
            let risk_score = volatility * momentum.abs();
            let time_to_next_allocation = if current_time > allocation_mgr.last_allocation_time {
                let elapsed = current_time - allocation_mgr.last_allocation_time;
                let min_interval = match current_regime {
                    MarketRegime::Volatile => allocation_mgr.allocation_interval / 2,
                    MarketRegime::Trending => allocation_mgr.allocation_interval,
                    MarketRegime::Ranging => allocation_mgr.allocation_interval * 2,
                    MarketRegime::Calm => allocation_mgr.allocation_interval * 3,
                };
                (min_interval.saturating_sub(elapsed)) / 3600
            } else {
                allocation_mgr.allocation_interval / 3600
            };
            
            info!("\n📊 ENHANCED TRADING STATUS - Tick #{}", tick_count);
            info!("⏰ Uptime: {}s | Regime: {:?} | Next allocation: {:.1}h", uptime, current_regime, time_to_next_allocation as f64);
            info!("💰 {}: ${:.2} | Spread: ${:.2} | VaR: ${:.2}", 
                market.symbol, market.spot_price, market.ask - market.bid, risk_mgr.calculate_var());
            info!("📈 Momentum: {:.3}% | Volatility: {:.3}% | Risk Score: {:.6}", 
                momentum_pct, volatility_pct, risk_score);
            info!("📊 Portfolio: Trades: {} | Win Rate: {:.1}% | PnL: ${:.2} | Sharpe: {:.2} | Max DD: {:.2}%",
                portfolio_analytics.total_trades, portfolio_analytics.get_win_rate() * 100.0,
                portfolio_analytics.total_pnl, portfolio_analytics.sharpe_ratio, portfolio_analytics.max_drawdown * 100.0);
        }

        // Enhanced allocation decision with regime awareness
        if allocation_mgr.should_allocate(current_time, momentum, current_portfolio_value, &current_regime) {
            info!("🎯 ENHANCED ALLOCATION TRIGGERED - Regime: {:?}", current_regime);
            info!("📊 Momentum: {:.4}% | Volatility: {:.4}% | Portfolio Value: ${:.2}", 
                momentum * 100.0, volatility * 100.0, current_portfolio_value);
            
            let confidence = (momentum.abs() + volatility).min(1.0);
            
            // Enhanced multi-symbol allocation with dynamic sizing
            for (i, symbol) in cfg.exchange.symbols.iter().enumerate() {
                let symbol_market = router.get_live_market_data(symbol).await;
                let base_position_size = cfg.exchange.max_position_size;
                
                // Calculate dynamic position size
                let position_size = allocation_mgr.calculate_position_size(
                    base_position_size, &current_regime, confidence, volatility
                );
                
                info!("📈 {} Analysis: Price=${:.2} | Position Size=${:.2} (base: ${:.2})", 
                    symbol, symbol_market.spot_price, position_size, base_position_size);
                
                // Enhanced strategy execution with regime-aware logic
                for strategy in &mut strategies {
                    // Skip strategies based on market regime
                    let should_run = match (strategy.name().as_str(), &current_regime) {
                        ("BasisArb", MarketRegime::Volatile) => true,     // Good for volatility
                        ("StatArb", MarketRegime::Ranging) => true,       // Good for mean reversion
                        ("ThetaHarvest", MarketRegime::Calm) => true,     // Good for low vol
                        ("YieldLoop", MarketRegime::Trending) => true,    // Good for trends
                        _ => confidence > 0.3, // Only run others if confident
                    };
                    
                    if !should_run {
                        continue;
                    }
                    
                    if let Some(signal) = strategy.generate_signal(&symbol_market, &market, &mut risk_mgr) {
                        let regime_adjusted_size = match current_regime {
                            MarketRegime::Volatile => position_size * 0.7, // More conservative
                            _ => position_size,
                        };
                        
                        info!("� Signal from {}: {} ${:.2} at ${:.2} (regime adjusted)", 
                            strategy.name(), 
                            if signal.quantity > 0.0 { "BUY" } else { "SELL" },
                            regime_adjusted_size,
                            signal.price
                        );
                        
                        // Execute trade with enhanced analytics
                        if let Ok(executed) = router.execute_order(symbol, signal.quantity.signum(), regime_adjusted_size, &market).await {
                            let trade_record = TradeRecord {
                                timestamp: current_time,
                                symbol: symbol.clone(),
                                side: if signal.quantity > 0.0 { "BUY".to_string() } else { "SELL".to_string() },
                                quantity: regime_adjusted_size,
                                price: signal.price,
                                pnl: executed.pnl.unwrap_or(0.0),
                                strategy: strategy.name(),
                            };
                            
                            portfolio_analytics.record_trade(trade_record);
                            
                            info!("✅ TRADE EXECUTED: {} {} ${:.2} @ ${:.2} | PnL: ${:.4}", 
                                if signal.quantity > 0.0 { "BOUGHT" } else { "SOLD" },
                                symbol, regime_adjusted_size, signal.price,
                                executed.pnl.unwrap_or(0.0)
                            );
                        }
                        
                        // Cooldown between trades (regime-adjusted)
                        let cooldown = match current_regime {
                            MarketRegime::Volatile => Duration::from_millis(500),  // Faster in volatile
                            MarketRegime::Trending => Duration::from_secs(1),     // Normal
                            MarketRegime::Ranging => Duration::from_secs(2),      // Slower in ranging
                            MarketRegime::Calm => Duration::from_secs(3),         // Slowest in calm
                        };
                        tokio::time::sleep(cooldown).await;
                    }
                }
            }
            
            // Record the enhanced allocation
            allocation_mgr.record_allocation(
                cfg.exchange.symbols.clone(),
                vec![allocation_mgr.calculate_position_size(cfg.exchange.max_position_size, &current_regime, confidence, volatility); cfg.exchange.symbols.len()],
                cfg.exchange.symbols.iter().map(|s| router.get_live_market_data(s)).collect::<Vec<_>>().await.into_iter().map(|m| m.spot_price).collect(),
                momentum,
                volatility,
            );
            
            allocation_mgr.last_allocation_time = current_time;
            info!("🔄 Allocation cycle complete. Next allocation in {:.1} hours based on {:?} regime", 
                match current_regime {
                    MarketRegime::Volatile => 2.5,
                    MarketRegime::Trending => 5.0,
                    MarketRegime::Ranging => 10.0,
                    MarketRegime::Calm => 15.0,
                }, current_regime);
        }
        
        // Check if trading is halted
        if risk_mgr.is_trading_halted() {
            warn!("🛑 Trading halted due to risk limits");
            tokio::time::sleep(Duration::from_millis(cfg.poll_ms * 10)).await;
            continue;
        }
        
        // Adaptive polling rate based on market regime
        let poll_delay = match current_regime {
            MarketRegime::Volatile => Duration::from_millis(500),  // Very fast
            MarketRegime::Trending => Duration::from_millis(1000), // Normal
            MarketRegime::Ranging => Duration::from_millis(1500),  // Slower
            MarketRegime::Calm => Duration::from_millis(2000),     // Slowest
        };
        
        tokio::time::sleep(poll_delay).await;
        
        // Stop after 1000 ticks for demo (remove in production)
        if !cfg.exchange.live_trading && tick_count >= 100 {
            info!("\n🎯 Demo completed after {} ticks", tick_count);
            break;
        }
    }
    
    print_final_stats(&risk_mgr, start_time.elapsed().as_secs());
    Ok(())
}

async fn execute_enhanced_allocation(
    router: &Router, 
    risk_mgr: &mut RiskManager, 
    _market: &MarketData,
    cfg: &config::Config,
    allocation_mgr: &mut AllocationManager,
    momentum: f64,
    volatility: f64
) -> Result<()> {
    info!("� Executing ENHANCED bulk allocation with smart position sizing...");
    
    // Get live account balance
    let account_balance = 57.94; // Your current USDT balance
    
    // Dynamic allocation percentage based on market conditions
    let base_allocation = 0.8; // 80% base
    let volatility_adjustment = (volatility * 10.0).min(0.2); // Up to 20% more in high vol
    let momentum_adjustment = (momentum.abs() * 5.0).min(0.1); // Up to 10% more on strong momentum
    
    let dynamic_allocation_pct = (base_allocation + volatility_adjustment + momentum_adjustment).min(0.95); // Max 95%
    let total_allocation = account_balance * dynamic_allocation_pct;
    
    info!("💰 Dynamic allocation: {:.1}% of balance (${:.2} total)", 
        dynamic_allocation_pct * 100.0, total_allocation);
    
    // Smart position sizing based on individual asset momentum and correlation
    let symbols = &cfg.exchange.symbols;
    let mut symbol_weights = Vec::new();
    let mut symbol_prices = Vec::new();
    let mut total_weight = 0.0;
    
    // Calculate individual weights based on momentum and volatility
    for symbol in symbols {
        let current_price = match router.get_current_price(symbol).await {
            Ok(price) => price,
            Err(_) => {
                warn!("❌ Failed to get price for {} - using default weight", symbol);
                symbol_prices.push(50000.0);
                symbol_weights.push(1.0);
                total_weight += 1.0;
                continue;
            }
        };
        
        symbol_prices.push(current_price);
        
        // Weight based on momentum direction and volatility
        let base_weight = 1.0;
        let momentum_weight = if momentum > 0.0 { 1.2 } else { 0.8 }; // Favor direction of momentum
        let volatility_weight = (1.0 + volatility * 2.0).min(1.5); // Higher weight for more volatile assets
        
        let final_weight = base_weight * momentum_weight * volatility_weight;
        symbol_weights.push(final_weight);
        total_weight += final_weight;
    }
    
    // Normalize weights and execute orders
    let mut allocation_amounts = Vec::new();
    
    for (i, symbol) in symbols.iter().enumerate() {
        let weight = symbol_weights[i] / total_weight;
        let allocation_amount = total_allocation * weight;
        let current_price = symbol_prices[i];
        
        if !risk_mgr.validate_trade(symbol, allocation_amount) {
            warn!("❌ Risk validation failed for {} - skipping", symbol);
            allocation_amounts.push(0.0);
            continue;
        }
        
        let quantity = allocation_amount / current_price;
        
        // Place buy order with smart position sizing
        match router.place_order(symbol, OrderSide::Buy, quantity, None).await {
            Ok(_) => {
                info!("✅ Smart allocation: {} @ ${:.2} | Weight: {:.1}% | Amount: ${:.2} | Qty: {:.6}", 
                    symbol, current_price, weight * 100.0, allocation_amount, quantity);
                allocation_amounts.push(allocation_amount);
            }
            Err(e) => {
                warn!("❌ Failed to place enhanced order for {}: {}", symbol, e);
                allocation_amounts.push(0.0);
            }
        }
        
        // Rate limiting between orders
        tokio::time::sleep(Duration::from_millis(150)).await;
    }
    
    // Record this allocation for future analysis
    allocation_mgr.record_allocation(
        symbols.clone(),
        allocation_amounts,
        symbol_prices,
        momentum,
        volatility
    );
    
    info!("🎯 Enhanced allocation complete - Total deployed: ${:.2} ({:.1}% of balance)", 
        total_allocation, dynamic_allocation_pct * 100.0);
    info!("📈 Portfolio now positioned for momentum: {:.3}% | volatility: {:.3}%", 
        momentum * 100.0, volatility * 100.0);
    
    Ok(())
}

async fn test_connection(config_path: &str) -> Result<()> {
    info!("🔍 Testing exchange connection...");
    
    let _cfg = config::load(config_path);
    let binance_config = binance::BinanceConfig::default();
    let client = binance::BinanceClient::new(binance_config);
    
    match client.get_account_info().await {
        Ok(account_info) => {
            info!("✅ Connection successful!");
            info!("Can trade: {}", account_info.can_trade);
            info!("Can withdraw: {}", account_info.can_withdraw);
            info!("Can deposit: {}", account_info.can_deposit);
            
            info!("\n💰 Account Balances:");
            for balance in &account_info.balances {
                let free: f64 = balance.free.parse().unwrap_or(0.0);
                let locked: f64 = balance.locked.parse().unwrap_or(0.0);
                if free > 0.0 || locked > 0.0 {
                    info!("  {}: Free={:.8}, Locked={:.8}", balance.asset, free, locked);
                }
            }
        }
        Err(e) => {
            error!("❌ Connection failed: {}", e);
        }
    }
    
    Ok(())
}

async fn check_balance(config_path: &str) -> Result<()> {
    info!("💰 Checking account balance...");
    
    let _cfg = config::load(config_path);
    let binance_config = binance::BinanceConfig::default();
    let client = binance::BinanceClient::new(binance_config);
    
    match client.get_account_info().await {
        Ok(account_info) => {
            info!("✅ Account balances retrieved:");
            let mut total_usdt = 0.0;
            
            for balance in &account_info.balances {
                let free: f64 = balance.free.parse().unwrap_or(0.0);
                let locked: f64 = balance.locked.parse().unwrap_or(0.0);
                if free > 0.0 || locked > 0.0 {
                    info!("  {}: Free={:.8}, Locked={:.8}", balance.asset, free, locked);
                    if balance.asset == "USDT" {
                        total_usdt = free + locked;
                    }
                }
            }
            
            info!("\n📊 Total USDT available for trading: ${:.2}", total_usdt);
        }
        Err(e) => {
            error!("❌ Failed to get balance: {}", e);
        }
    }
    
    Ok(())
}

fn print_final_stats(risk_mgr: &RiskManager, uptime_secs: u64) {
    let hours = uptime_secs / 3600;
    let minutes = (uptime_secs % 3600) / 60;
    let seconds = uptime_secs % 60;
    
    info!("\n🏁 Trading session completed!");
    info!("⏱️  Total uptime: {}h {}m {}s", hours, minutes, seconds);
    info!("📊 Final VaR: ${:.2}", risk_mgr.calculate_var());
    info!("🎯 Thanks for using VictoryChain Stack!");
}

