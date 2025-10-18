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

// Enhanced Allocation Manager
struct AllocationManager {
    last_allocation_time: u64,
    allocation_interval: u64,
    initial_balance: f64,
    profit_threshold: f64,
    stop_loss_threshold: f64,
    momentum_lookback: usize,
    price_history: Vec<f64>,
    volatility_threshold: f64,
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
            initial_balance: 57.94,
            profit_threshold: 0.02,
            stop_loss_threshold: -0.01,
            momentum_lookback: 100,
            price_history: Vec::new(),
            volatility_threshold: 0.02,
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

    fn should_allocate(&self, current_time: u64, momentum: f64, current_portfolio_value: f64, regime: &MarketRegime) -> bool {
        // Check if minimum time has passed (dynamic based on market regime)
        let min_interval = match regime {
            MarketRegime::Volatile => self.allocation_interval / 2,
            MarketRegime::Trending => self.allocation_interval,
            MarketRegime::Ranging => self.allocation_interval * 2,
            MarketRegime::Calm => self.allocation_interval * 3,
        };
        
        let time_elapsed = current_time >= self.last_allocation_time + min_interval;
        
        let volatility = self.calculate_volatility();
        let (vol_threshold, momentum_threshold) = match regime {
            MarketRegime::Volatile => (0.015, 0.0005),
            MarketRegime::Trending => (0.020, 0.0015),
            MarketRegime::Ranging => (0.025, 0.0025),
            MarketRegime::Calm => (0.030, 0.0035),
        };
        
        let volatility_favorable = volatility > vol_threshold;
        let momentum_aligned = momentum.abs() > momentum_threshold;
        
        let current_profit = self.calculate_profit_pct(current_portfolio_value);
        let (profit_target, stop_loss) = match regime {
            MarketRegime::Volatile => (self.profit_threshold * 0.5, self.stop_loss_threshold * 2.0),
            MarketRegime::Trending => (self.profit_threshold, self.stop_loss_threshold),
            MarketRegime::Ranging => (self.profit_threshold * 1.5, self.stop_loss_threshold * 0.5),
            MarketRegime::Calm => (self.profit_threshold * 2.0, self.stop_loss_threshold * 0.3),
        };
        
        let should_reallocate = current_profit < stop_loss || 
                               current_profit > profit_target ||
                               (volatility_favorable && momentum.abs() > momentum_threshold * 3.0);

        time_elapsed && momentum_aligned && should_reallocate
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
        
        if self.allocation_history.len() > 50 {
            self.allocation_history.remove(0);
        }
    }
}

#[derive(Parser)]
#[command(name = "victorychain")]
#[command(about = "Enhanced quantitative trading system")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Run {
        #[arg(long)]
        live: bool,
        #[arg(short, long, default_value = "config.toml")]
        config: String,
        #[arg(long, value_delimiter = ',')]
        symbols: Option<Vec<String>>,
    },
    Test {
        #[arg(short, long, default_value = "config.toml")]
        config: String,
    },
    Balance {
        #[arg(short, long, default_value = "config.toml")]
        config: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let cli = Cli::parse();

    match cli.command {
        Commands::Run { live, config: config_path, symbols } => {
            run_enhanced_trading_system(live, &config_path, symbols).await
        }
        Commands::Test { config: config_path } => {
            test_connection(&config_path).await
        }
        Commands::Balance { config: config_path } => {
            check_balance(&config_path).await
        }
    }
}

async fn run_enhanced_trading_system(live: bool, config_path: &str, symbols: Option<Vec<String>>) -> Result<()> {
    info!("🚀 Starting ENHANCED VictoryChain Trading System");
    
    let cfg = config::Config::from_file(config_path)?;
    let mut router = Router::new(&cfg.exchange).await?;
    let mut risk_mgr = RiskManager::new(&cfg.risk);
    
    let mut strategies: Vec<Box<dyn Strategy>> = vec![
        Box::new(strategy::BasisArb::new(&cfg.basis_arb)),
        Box::new(strategy::ThetaHarvest::new(&cfg.theta)),
        Box::new(strategy::StatArb::new(&cfg.stat_arb)),
        Box::new(strategy::YieldLoop::new(&cfg.yield_loop)),
    ];
    
    info!("💼 Initialized {} strategies with enhanced features:", strategies.len());
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
    
    info!("🎯 Starting ENHANCED trading loop with ML-inspired features...");
    info!("📊 Features: Dynamic sizing, regime detection, portfolio analytics");
    
    loop {
        tick_count += 1;
        
        // Emergency stop check
        if portfolio_analytics.max_drawdown > 0.05 {
            error!("🚨 EMERGENCY STOP: Max drawdown exceeded 5%");
            tokio::time::sleep(Duration::from_secs(60)).await;
            continue;
        }
        
        router.update_market_data();
        let primary_symbol = &cfg.exchange.symbols[0];
        let market = router.get_live_market_data(primary_symbol).await;

        // Update regime detector and get current regime
        regime_detector.update(market.spot_price, market.volume);
        let current_regime = regime_detector.detect_regime();
        
        if current_regime != last_regime {
            info!("📈 Market regime changed: {:?} -> {:?}", last_regime, current_regime);
            last_regime = current_regime.clone();
        }

        let current_time = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        allocation_mgr.update_price_history(market.spot_price);
        let momentum = allocation_mgr.calculate_momentum();
        let volatility = allocation_mgr.calculate_volatility();
        let current_portfolio_value = 57.94 + risk_mgr.calculate_var();
        
        // Enhanced logging
        if tick_count % 10 == 0 {
            let uptime = start_time.elapsed().as_secs();
            info!("\n📊 ENHANCED TRADING STATUS - Tick #{}", tick_count);
            info!("⏰ Uptime: {}s | Regime: {:?}", uptime, current_regime);
            info!("💰 {}: ${:.2} | VaR: ${:.2}", market.symbol, market.spot_price, risk_mgr.calculate_var());
            info!("📈 Momentum: {:.3}% | Volatility: {:.3}%", momentum * 100.0, volatility * 100.0);
            info!("📊 Portfolio: Trades: {} | Win Rate: {:.1}% | PnL: ${:.2}",
                portfolio_analytics.total_trades, portfolio_analytics.get_win_rate() * 100.0,
                portfolio_analytics.total_pnl);
        }

        // Enhanced allocation decision
        if allocation_mgr.should_allocate(current_time, momentum, current_portfolio_value, &current_regime) {
            info!("🎯 ENHANCED ALLOCATION TRIGGERED - Regime: {:?}", current_regime);
            
            for symbol in &cfg.exchange.symbols {
                let symbol_market = router.get_live_market_data(symbol).await;
                
                for strategy in &mut strategies {
                    strategy.on_tick(&symbol_market, &router, &mut risk_mgr).await;
                    
                    // Record activity
                    let trade_record = TradeRecord {
                        timestamp: current_time,
                        symbol: symbol.clone(),
                        side: "AUTO".to_string(),
                        quantity: cfg.exchange.max_position_size,
                        price: symbol_market.spot_price,
                        pnl: 0.0,
                        strategy: strategy.name().to_string(),
                    };
                    
                    portfolio_analytics.record_trade(trade_record);
                }
            }
            
            allocation_mgr.record_allocation(
                cfg.exchange.symbols.clone(),
                vec![cfg.exchange.max_position_size; cfg.exchange.symbols.len()],
                cfg.exchange.symbols.iter()
                    .map(|_| market.spot_price)
                    .collect(),
                momentum,
                volatility,
            );
            
            allocation_mgr.last_allocation_time = current_time;
            
            let next_hours = match current_regime {
                MarketRegime::Volatile => 2.5,
                MarketRegime::Trending => 5.0,
                MarketRegime::Ranging => 10.0,
                MarketRegime::Calm => 15.0,
            };
            
            info!("🔄 Allocation complete. Next in {:.1} hours", next_hours);
        }
        
        // Adaptive polling rate
        let poll_delay = match current_regime {
            MarketRegime::Volatile => Duration::from_millis(500),
            MarketRegime::Trending => Duration::from_millis(1000),
            MarketRegime::Ranging => Duration::from_millis(1500),
            MarketRegime::Calm => Duration::from_millis(2000),
        };
        
        tokio::time::sleep(poll_delay).await;
        
        if !cfg.exchange.live_trading && tick_count >= 100 {
            info!("\n🎯 Enhanced demo completed after {} ticks", tick_count);
            break;
        }
    }
    
    info!("🏁 Enhanced trading system completed");
    Ok(())
}

async fn test_connection(config_path: &str) -> Result<()> {
    info!("🔍 Testing enhanced system connection...");
    let cfg = config::Config::from_file(config_path)?;
    let router = Router::new(&cfg.exchange).await?;
    
    for symbol in &cfg.exchange.symbols {
        let market = router.get_live_market_data(symbol).await;
        info!("✅ {}: ${:.2} (spread: ${:.4})", 
            market.symbol, market.spot_price, market.ask - market.bid);
    }
    
    info!("🎉 Enhanced connection test successful!");
    Ok(())
}

async fn check_balance(config_path: &str) -> Result<()> {
    info!("💰 Checking enhanced account balance...");
    let cfg = config::Config::from_file(config_path)?;
    let router = Router::new(&cfg.exchange).await?;
    
    // This would integrate with actual balance checking
    info!("💼 Account balance check complete (implementation depends on exchange integration)");
    Ok(())
}
