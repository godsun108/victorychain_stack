mod binance;
mod config;
mod exchange;
mod math;
mod risk;
mod strategy;
mod ai_analyzer;
mod websocket;
mod dashboard;
mod momentum_predictor;
mod momentum_strategy;
mod statistical_momentum;

use strategy::{Strategy, CapitalGainsMaximizer};
use statistical_momentum::StatisticalMomentumStrategy;
use exchange::Router;
use binance::{BinanceClient, BinanceConfig};
use risk::RiskManager;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use anyhow::Result;
use tokio;
use tracing::{info, warn, error};
use tracing_subscriber;
use clap::{Parser, Subcommand};
use momentum_predictor::MomentumPredictor;
use momentum_strategy::MomentumHoldingStrategy;

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
        if self.total_trades == 0 {
            0.0
        } else {
            self.winning_trades as f64 / self.total_trades as f64
        }
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
            allocation_interval: 30, // 30 seconds for immediate trading
            initial_balance: 57.94,
            profit_threshold: 0.005, // 0.5% profit target
            stop_loss_threshold: -0.005, // 0.5% stop loss
            momentum_lookback: 20, // Shorter for immediate response
            price_history: Vec::new(),
            volatility_threshold: 0.001, // Very low threshold
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
        // Much more aggressive allocation logic
        let min_interval = match regime {
            MarketRegime::Volatile => 10, // 10 seconds
            MarketRegime::Trending => 15, // 15 seconds
            MarketRegime::Ranging => 30,  // 30 seconds
            MarketRegime::Calm => 45,     // 45 seconds
        };
        
        let time_elapsed = current_time >= self.last_allocation_time + min_interval;
        
        let volatility = self.calculate_volatility();
        let (vol_threshold, momentum_threshold) = match regime {
            MarketRegime::Volatile => (0.001, 0.0001),  // Very low thresholds
            MarketRegime::Trending => (0.002, 0.0002),
            MarketRegime::Ranging => (0.003, 0.0003),
            MarketRegime::Calm => (0.005, 0.0005),
        };
        
        // Always trigger on first run or if enough time has passed
        if self.price_history.len() < 5 {
            return true;
        }
        
        let volatility_favorable = volatility > vol_threshold;
        let momentum_aligned = momentum.abs() > momentum_threshold;
        
        let current_profit = self.calculate_profit_pct(current_portfolio_value);
        let (profit_target, stop_loss) = match regime {
            MarketRegime::Volatile => (0.003, -0.003),   // 0.3% targets
            MarketRegime::Trending => (0.005, -0.005),   // 0.5% targets  
            MarketRegime::Ranging => (0.008, -0.002),    // Asymmetric
            MarketRegime::Calm => (0.010, -0.001),       // Patient
        };
        
        let should_reallocate = time_elapsed && (
            current_profit < stop_loss || 
            current_profit > profit_target ||
            (volatility_favorable && momentum_aligned) ||
            momentum.abs() > momentum_threshold * 2.0  // Strong momentum
        );

        should_reallocate
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
    Tokens {
        #[arg(short, long, default_value = "config.toml")]
        config: String,
        #[arg(long, help = "Show only pairs with specific quote asset (e.g., USDT, BTC)")]
        quote: Option<String>,
        #[arg(long, help = "Show detailed token information")]
        detailed: bool,
        #[arg(long, help = "Show current prices")]
        prices: bool,
    },
    Status {
        #[arg(short, long, default_value = "config.toml")]
        config: String,
        #[arg(long, help = "Show rate limiting status")]
        rates: bool,
    },
    Momentum {
        #[arg(short, long, default_value = "config.toml")]
        config: String,
        #[arg(long, help = "Run momentum prediction and trading")]
        predict: bool,
        #[arg(long, help = "Show top momentum opportunities")]
        scan: bool,
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
        Commands::Tokens { config: config_path, quote, detailed, prices } => {
            list_available_tokens(&config_path, quote, detailed, prices).await
        }
        Commands::Status { config: config_path, rates } => {
            show_status(&config_path, rates).await
        }
        Commands::Momentum { config: config_path, predict, scan } => {
            run_momentum_prediction(&config_path, predict, scan).await
        }
    }
}

async fn run_enhanced_trading_system(_live: bool, config_path: &str, _symbols: Option<Vec<String>>) -> Result<()> {
    info!("🚀 Starting ENHANCED VictoryChain Trading System");
    
    let cfg = config::load(config_path);
    let mut router = Router::new(&cfg.exchange);
    router.initialize().await?;
    let mut risk_mgr = RiskManager::new(cfg.risk.clone());
    
    // Select strategy based on AI configuration
    let binance_config = BinanceConfig {
        api_key: cfg.exchange.api_key.clone(),
        secret_key: cfg.exchange.secret_key.clone(),
        testnet: false,
    };
    let binance_client = BinanceClient::new(binance_config);
    
    let mut strategies: Vec<Box<dyn Strategy>> = if cfg.ai.enabled && cfg.ai.primary_strategy == "statistical_momentum" {
        info!("📊 Statistical Momentum Mode ENABLED");
        info!("🎯 Strategy: Standard deviation analysis with probability-based token selection");
        vec![
            Box::new(StatisticalMomentumStrategy::new(binance_client.clone())), // Primary: Statistical analysis
            Box::new(strategy::CapitalGainsMaximizer::new()), // Fallback: Capital gains
        ]
    } else if cfg.ai.enabled && cfg.ai.primary_strategy == "ai_enhanced" {
        info!("💎 Capital Gains Maximizer Mode ENABLED");
        info!("🎯 Strategy: Hold high-momentum tokens for maximum capital appreciation");
        vec![
            Box::new(strategy::CapitalGainsMaximizer::new()), // Primary: Capital gains focused
            Box::new(strategy::AIEnhancedMomentumTrader::new()), // Fallback: AI momentum
        ]
    } else {
        info!("📊 Traditional Trading Mode");
        vec![
            Box::new(strategy::HighestMomentumTrader::new()), // Traditional momentum
        ]
    };
    
    info!("💼 Initialized {} strategy with ALL-IN momentum trading:", strategies.len());
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
        
        // Rate limiting emergency check - very conservative
        if let Some((weight_usage, order_usage)) = router.get_rate_limit_status().await {
            if weight_usage > 500 || order_usage > 25 {
                warn!("🚦 RATE LIMIT WARNING: Weight: {}/720, Orders: {}/35 - Slowing down significantly", 
                    weight_usage, order_usage);
                tokio::time::sleep(Duration::from_secs(10)).await;
            }
            if weight_usage > 600 || order_usage > 30 {
                error!("🚨 RATE LIMIT CRITICAL: Pausing trading for 60 seconds to prevent ban");
                tokio::time::sleep(Duration::from_secs(60)).await;
                continue;
            }
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
            
            // Add rate limiting status with conservative limits
            if let Some(binance_client) = router.get_binance_client() {
                let rate_limiter = binance_client.get_rate_limiter();
                let (weight_usage, order_usage) = rate_limiter.get_usage_stats();
                info!("🚦 Rate Limits (Conservative): Weight: {}/720 | Orders: {}/35", weight_usage, order_usage);
            }
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
        
        // Smart polling that respects rate limits but still aggressive
        let poll_delay = Duration::from_millis(2000); // 2 second intervals
        
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
    let cfg = config::load(config_path);
    let mut router = Router::new(&cfg.exchange);
    router.initialize().await?;
    
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
    let cfg = config::load(config_path);
    let mut router = Router::new(&cfg.exchange);
    router.initialize().await?;
    
    // This would integrate with actual balance checking
    info!("💼 Account balance check complete (implementation depends on exchange integration)");
    Ok(())
}

async fn list_available_tokens(config_path: &str, quote_filter: Option<String>, detailed: bool, show_prices: bool) -> Result<()> {
    info!("🔍 Fetching all available tokens from Binance US...");
    
    let cfg = config::load(config_path);
    let mut router = Router::new(&cfg.exchange);
    router.initialize().await?;
    
    // Get the Binance client from the router to access token information
    use crate::binance::{BinanceClient, BinanceConfig};
    let binance_client = BinanceClient::new(BinanceConfig::default());
    
    // Fetch all active tokens
    let tokens = binance_client.get_all_active_tokens().await?;
    info!("✅ Found {} active trading pairs", tokens.len());
    
    // Filter by quote asset if specified
    let filtered_tokens: Vec<_> = if let Some(quote) = &quote_filter {
        tokens.into_iter()
            .filter(|(_, _, quote_asset)| quote_asset.to_uppercase() == quote.to_uppercase())
            .collect()
    } else {
        tokens
    };
    
    if show_prices {
        info!("📊 Fetching current prices...");
        let all_prices = binance_client.get_all_prices().await?;
        let price_map: std::collections::HashMap<String, f64> = all_prices
            .into_iter()
            .filter_map(|price| price.price.parse::<f64>().ok().map(|p| (price.symbol, p)))
            .collect();
        
        println!("\n🚀 BINANCE US - Available Trading Pairs with Prices:");
        println!("═══════════════════════════════════════════════════");
        
        if detailed {
            println!("{:<15} {:<8} {:<8} {:<15}", "SYMBOL", "BASE", "QUOTE", "PRICE");
            println!("─────────────────────────────────────────────────────────");
            
            for (symbol, base_asset, quote_asset) in &filtered_tokens {
                if let Some(price) = price_map.get(symbol) {
                    println!("{:<15} {:<8} {:<8} ${:<14.6}", 
                        symbol, base_asset, quote_asset, price);
                }
            }
        } else {
            let mut sorted_tokens = filtered_tokens.clone();
            sorted_tokens.sort_by(|a, b| a.0.cmp(&b.0));
            
            for (i, (symbol, _, _)) in sorted_tokens.iter().enumerate() {
                if let Some(price) = price_map.get(symbol) {
                    print!("{:<20} ${:<12.6}", symbol, price);
                    if (i + 1) % 3 == 0 {
                        println!();
                    }
                }
            }
            println!();
        }
    } else {
        println!("\n🚀 BINANCE US - Available Trading Pairs:");
        println!("═══════════════════════════════════════");
        
        if detailed {
            println!("{:<15} {:<8} {:<8}", "SYMBOL", "BASE", "QUOTE");
            println!("─────────────────────────────────────");
            
            for (symbol, base_asset, quote_asset) in &filtered_tokens {
                println!("{:<15} {:<8} {:<8}", symbol, base_asset, quote_asset);
            }
        } else {
            let mut sorted_tokens = filtered_tokens.clone();
            sorted_tokens.sort_by(|a, b| a.0.cmp(&b.0));
            
            for (i, (symbol, _, _)) in sorted_tokens.iter().enumerate() {
                print!("{:<20}", symbol);
                if (i + 1) % 4 == 0 {
                    println!();
                }
            }
            println!();
        }
    }
    
    // Summary statistics
    let quote_assets: std::collections::HashSet<String> = filtered_tokens
        .iter()
        .map(|(_, _, quote)| quote.clone())
        .collect();
    
    let base_assets: std::collections::HashSet<String> = filtered_tokens
        .iter()
        .map(|(_, base, _)| base.clone())
        .collect();
    
    println!("\n📊 SUMMARY:");
    println!("═══════════════════════════════════════");
    println!("Total Trading Pairs: {}", filtered_tokens.len());
    println!("Unique Base Assets: {}", base_assets.len());
    println!("Unique Quote Assets: {}", quote_assets.len());
    
    if quote_filter.is_some() {
        println!("Filter Applied: {} pairs only", quote_filter.unwrap());
    }
    
    println!("\n💡 POPULAR QUOTE ASSETS:");
    let mut quote_counts: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for (_, _, quote) in &filtered_tokens {
        *quote_counts.entry(quote.clone()).or_insert(0) += 1;
    }
    
    let mut sorted_quotes: Vec<_> = quote_counts.into_iter().collect();
    sorted_quotes.sort_by(|a, b| b.1.cmp(&a.1));
    
    for (quote, count) in sorted_quotes.iter().take(10) {
        println!("  {}: {} pairs", quote, count);
    }
    
    println!("\n🎯 USAGE EXAMPLES:");
    println!("  ./target/release/backend tokens --quote USDT --prices    # Show all USDT pairs with prices");
    println!("  ./target/release/backend tokens --detailed               # Show detailed info for all pairs");
    println!("  ./target/release/backend tokens --quote BTC              # Show only BTC pairs");
    
    Ok(())
}

async fn show_status(config_path: &str, show_rates: bool) -> Result<()> {
    let cfg = config::load(config_path);
    let binance_client = BinanceClient::new(BinanceConfig::default());
    
    println!("\n🔍 VICTORYCHAIN SYSTEM STATUS");
    println!("═══════════════════════════════════════");
    
    // Test connection
    match binance_client.get_account_info().await {
        Ok(account_info) => {
            println!("✅ Binance US Connection: ACTIVE");
            println!("📊 Account Status:");
            println!("   Can Trade: {}", account_info.can_trade);
            println!("   Can Withdraw: {}", account_info.can_withdraw);
            println!("   Can Deposit: {}", account_info.can_deposit);
            
            // Show balances
            println!("\n💰 ACCOUNT BALANCES:");
            let mut total_usd_value = 0.0;
            for balance in &account_info.balances {
                let free: f64 = balance.free.parse().unwrap_or(0.0);
                let locked: f64 = balance.locked.parse().unwrap_or(0.0);
                let total = free + locked;
                
                if total > 0.0 {
                    println!("   {}: {:.8} (Free: {:.8}, Locked: {:.8})", 
                        balance.asset, total, free, locked);
                    
                    // Estimate USD value for major assets
                    if balance.asset == "USDT" || balance.asset == "USD" {
                        total_usd_value += total;
                    } else if balance.asset == "BTC" {
                        total_usd_value += total * 65000.0; // Rough estimate
                    } else if balance.asset == "ETH" {
                        total_usd_value += total * 3200.0; // Rough estimate
                    }
                }
            }
            
            println!("   Estimated Total Value: ~${:.2}", total_usd_value);
            
            if show_rates {
                println!("\n🚦 RATE LIMITING STATUS:");
                let rate_limiter = binance_client.get_rate_limiter();
                let (weight_usage, order_usage) = rate_limiter.get_usage_stats();
                
                println!("   Request Weight: {}/720 ({:.1}%) [Conservative: 60% of limit]", 
                    weight_usage, (weight_usage as f64 / 720.0) * 100.0);
                println!("   Order Count: {}/35 ({:.1}%) [Conservative: 70% of limit]", 
                    order_usage, (order_usage as f64 / 35.0) * 100.0);
                
                // Rate limit health check with conservative thresholds
                if weight_usage > 500 || order_usage > 25 {
                    println!("   ⚠️  WARNING: High rate limit usage (conservative thresholds)");
                } else if weight_usage > 400 || order_usage > 20 {
                    println!("   ⚡ MODERATE: Rate limit usage (conservative thresholds)");
                } else {
                    println!("   ✅ HEALTHY: Rate limit usage (conservative thresholds)");
                }
                
                println!("\n📊 CONSERVATIVE RATE LIMIT DETAILS:");
                println!("   • Request Weight Limit: 720/min (60% of 1200 to prevent bans)");
                println!("   • Order Limit: 35 per 10s (70% of 50 to prevent bans)");
                println!("   • Raw Request Limit: 3000 per 5min (50% of 6100 to prevent bans)");
                println!("   • Bot uses ultra-conservative rate limiting for safety");
            }
            
        }
        Err(e) => {
            println!("❌ Binance US Connection: FAILED");
            println!("   Error: {}", e);
            println!("   Check your API credentials in config.toml");
        }
    }
    
    println!("\n🎯 TRADING CONFIGURATION:");
    println!("   Exchange: Binance US");
    println!("   Symbols: {:?}", cfg.exchange.symbols);
    println!("   Max Position Size: {:.2}", cfg.exchange.max_position_size);
    println!("   Fee Rate: {:.4}%", cfg.exchange.fee_rate * 100.0);
    println!("   Live Trading: {}", cfg.exchange.live_trading);
    
    println!("\n💬 USAGE EXAMPLES:");
    println!("   ./target/release/backend run --live          # Start live trading");
    println!("   ./target/release/backend balance             # Check account balance");
    println!("   ./target/release/backend status --rates      # Show rate limiting status");
    println!("   ./target/release/backend tokens --prices     # Show token prices");
    
    Ok(())
}

async fn run_momentum_prediction(config_path: &str, predict: bool, scan: bool) -> Result<()> {
    info!("🔮 Starting Momentum Prediction System");
    
    let cfg = config::Config::from_file(config_path)?;
    
    // Get Claude API key from environment
    let claude_api_key = std::env::var("CLAUDE_API_KEY")
        .map_err(|_| anyhow::anyhow!("CLAUDE_API_KEY environment variable not set"))?;
    
    let mut predictor = MomentumPredictor::new(claude_api_key.clone());
    
    if scan {
        // Just scan and show opportunities
        info!("📊 Scanning for 20-30% momentum opportunities...");
        
        let symbols = vec![
            "BTCUSDT".to_string(), "ETHUSDT".to_string(), "XRPUSDT".to_string(),
            "SOLUSDT".to_string(), "ADAUSDT".to_string(), "DOTUSDT".to_string(),
            "LINKUSDT".to_string(), "AVAXUSDT".to_string(), "MATICUSDT".to_string(),
            "ATOMUSDT".to_string(), "SHIBUSDT".to_string(), "PEPEUSDT".to_string(),
            "FLOKIUSDT".to_string(), "BONKUSDT".to_string(), "ALGOUSDT".to_string(),
        ];
        
        let predictions = predictor.predict_high_momentum_tokens(&symbols).await?;
        
        println!("\n🚀 HIGH MOMENTUM OPPORTUNITIES (20%+ Potential):");
        println!("═══════════════════════════════════════════════════");
        
        if predictions.is_empty() {
            println!("❌ No high-momentum opportunities found at this time");
            println!("   Try scanning again in 10-15 minutes");
        } else {
            for (i, prediction) in predictions.iter().enumerate() {
                println!("\n{}. {} 📈", i + 1, prediction.symbol);
                println!("   Current Price: ${:.6}", prediction.current_price);
                println!("   Target Price:  ${:.6} (+{:.1}%)", 
                         prediction.predicted_price_24h, prediction.predicted_gain_percent);
                println!("   Confidence:    {:.0}% | Risk: {:?}", 
                         prediction.confidence_score, prediction.risk_level);
                println!("   Hold Duration: {:.1} hours", prediction.hold_duration_hours);
                println!("   Entry Rec:     {:?}", prediction.entry_recommendation);
                
                // Show abbreviated AI reasoning
                let reasoning = if prediction.ai_reasoning.len() > 150 {
                    format!("{}...", &prediction.ai_reasoning[..150])
                } else {
                    prediction.ai_reasoning.clone()
                };
                println!("   AI Analysis:   {}", reasoning);
            }
            
            println!("\n💡 NEXT STEPS:");
            println!("   • Use --predict flag to start live momentum trading");
            println!("   • Review AI analysis for each opportunity");
            println!("   • Consider position sizing and risk management");
        }
        
    } else if predict {
        // Run live momentum trading
        info!("🚀 Starting Live Momentum Trading System");
        
        // Initialize trading system
        let binance_config = BinanceConfig {
            api_key: std::env::var("BINANCEUS_KEY").unwrap_or_default(),
            secret_key: std::env::var("BINANCEUS_SECRET").unwrap_or_default(),
            endpoint: cfg.exchange.endpoint.clone(),
            ws_url: "wss://stream.binance.us:9443/ws".to_string(),
            testnet: false,
        };
        
        let client = BinanceClient::new(binance_config);
        let router = Router::new(client, cfg.exchange.fee_rate);
        let mut momentum_strategy = MomentumHoldingStrategy::new(claude_api_key);
        
        info!("✅ Momentum trading system initialized");
        info!("🎯 Strategy: Hold tokens with 20-30% momentum potential");
        info!("📊 Max positions: 3 | Position size: $75 each");
        info!("🛡️ Stop loss: 8% | Scan interval: 10 minutes");
        
        // Main trading loop
        let mut loop_count = 0;
        loop {
            loop_count += 1;
            
            // Create mock market data for strategy tick
            let market_data = MarketData {
                symbol: "MOMENTUM_SCAN".to_string(),
                price: 1.0,
                bid: 1.0,
                ask: 1.0,
                volume: 1000000.0,
                timestamp: chrono::Utc::now().timestamp() as u64,
            };
            
            // Run strategy tick
            if let Err(e) = momentum_strategy.on_tick(&market_data, &router).await {
                error!("Strategy error: {}", e);
            }
            
            // Log status every 10 loops (roughly every 5 minutes with 30s sleep)
            if loop_count % 10 == 0 {
                info!("💼 {}", momentum_strategy.get_position_summary());
                
                let active_positions = momentum_strategy.get_active_positions();
                if !active_positions.is_empty() {
                    info!("📊 Active momentum positions:");
                    for (symbol, position) in active_positions {
                        info!("   {} | Entry: ${:.6} | P&L: {:.2}% | Target: +{:.1}%",
                              symbol, position.entry_price, position.current_pnl_percent, position.predicted_gain);
                    }
                }
            }
            
            // Sleep for 30 seconds between strategy ticks
            tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
        }
        
    } else {
        println!("🔮 Momentum Prediction System");
        println!("Usage:");
        println!("  --scan     Show current 20-30% momentum opportunities");
        println!("  --predict  Start live momentum trading");
        println!("\nExamples:");
        println!("  ./target/release/backend momentum --scan");
        println!("  ./target/release/backend momentum --predict");
    }
    
    Ok(())
}
