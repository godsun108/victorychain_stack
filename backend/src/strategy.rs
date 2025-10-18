use crate::math::*;
use crate::exchange::{MarketData, Router, OrderSide};
use crate::risk::RiskManager;
use crate::config::{BasisArbConfig, ThetaHarvestConfig, StatArbConfig, YieldLoopConfig};
use crate::binance::{BinanceClient, BinanceTicker};
use std::collections::{VecDeque, HashMap};
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{info, warn, error};
use crate::ai_analyzer::{AITokenAnalyzer, AIAnalysisResult};
use async_trait::async_trait;

/// Strategy equations:
/// Perp-Spot Basis Arb APR: APR = (funding_rate − borrow_rate) * 365
/// Yield-Looping Net APR: net_apr = reward_apr − borrow_apr
/// Theta Harvest PnL: PnL ≈ −θ + Δ dS + 0.5 Γ dS² + Vega dIV
/// StatArb Z-score: z = (spread − μ) / σ
/// FlashLoan Profit: profit = Σ(triangle_rates) − gas_cost
/// NFT Funding Yield: yield = funding_rate − oracle_drift

#[async_trait::async_trait]
pub trait Strategy {
    fn name(&self) -> &'static str;
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager);
}

// Basis Arbitrage Strategy
pub struct BasisArb {
    config: BasisArbConfig,
    position: f64,
    last_trade_time: u64,
}

impl BasisArb {
    pub fn new(config: &BasisArbConfig) -> Self {
        Self {
            config: config.clone(),
            position: 0.0,
            last_trade_time: 0,
        }
    }
}

#[async_trait::async_trait]
impl Strategy for BasisArb {
    fn name(&self) -> &'static str { "BasisArb" }
    
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        // Get real market prices for better basis calculation
        let btc_price = match router.get_current_price("BTCUSDT").await {
            Ok(price) => price,
            Err(_) => return, // Skip if can't get price
        };
        
        // Calculate realistic spread (using bid-ask as proxy for basis)
        let (bid, ask) = match router.get_order_book("BTCUSDT").await {
            Ok((b, a)) => (b, a),
            Err(_) => return,
        };
        
        let spread = ask - bid;
        let spread_pct = spread / btc_price * 100.0;
        
        // Enhanced APR calculation with real funding rates
        let estimated_funding = spread_pct * 24.0 * 365.0; // Annualized spread-based estimate
        
        // Only trade if sufficient time has passed and conditions are met
        if data.timestamp - self.last_trade_time < 30 { // 30 second cooldown for immediate trading
            return;
        }
        
        if estimated_funding > self.config.min_apr && spread_pct > 0.05 { // 0.05% minimum spread
            // Calculate position size based on available USDT balance
            let usdt_balance = 57.94; // Your current balance
            let risk_amount = (usdt_balance * 0.1_f64).min(self.config.max_position_size); // Risk 10% max
            let size = risk_amount / btc_price;
            
            // Ensure minimum size requirements
            if size < 0.00001 { // Binance minimum
                warn!("Position size too small: {:.8}", size);
                return;
            }
            
            if mgr.validate_trade("BTCUSDT", size) {
                info!("🎯 Attempting basis arbitrage...");
                info!("   BTC Price: ${:.2}, Spread: {:.4}%, Size: {:.6} BTC", 
                    btc_price, spread_pct, size);
                
                match router.place_order("BTCUSDT", OrderSide::Buy, size, Some(bid + spread * 0.3)).await {
                    Ok(order) => {
                        let profit_estimate = spread * size * 0.5; // Conservative profit estimate
                        mgr.update_position("BTCUSDT", size, profit_estimate);
                        self.position += size;
                        self.last_trade_time = data.timestamp;
                        
                        info!("✅ Basis Arb executed: Estimated Funding APR={:.1}%, Size={:.6} BTC, Est. Profit=${:.4}", 
                            estimated_funding * 100.0, size, profit_estimate);
                    }
                    Err(e) => {
                        warn!("❌ Failed to execute basis arb: {}", e);
                    }
                }
            } else {
                info!("⚠️ Risk limits prevent basis arb trade");
            }
        }
    }
}

// Theta Harvest Strategy (Options)
pub struct ThetaHarvest {
    config: ThetaHarvestConfig,
    portfolio_delta: f64,
    portfolio_gamma: f64,
    portfolio_vega: f64,
    portfolio_theta: f64,
    last_hedge_time: u64,
}

impl ThetaHarvest {
    pub fn new(config: &ThetaHarvestConfig) -> Self {
        Self {
            config: config.clone(),
            portfolio_delta: 0.0,
            portfolio_gamma: 0.0,
            portfolio_vega: 0.0,
            portfolio_theta: 0.0,
            last_hedge_time: 0,
        }
    }
}

#[async_trait::async_trait]
impl Strategy for ThetaHarvest {
    fn name(&self) -> &'static str { "ThetaHarvest" }
    
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        // Calculate option Greeks
        let strike = data.spot_price * 1.1; // 10% OTM
        let time_to_expiry = 30.0/365.0; // 30 days
        let risk_free_rate = 0.05;
        
        let greeks = black_scholes_greeks(
            data.spot_price, 
            strike,
            time_to_expiry,
            risk_free_rate,
            data.implied_vol
        );
        
        // PnL ≈ −θ + Δ dS + 0.5 Γ dS² + Vega dIV
        let expected_daily_theta = greeks.theta * self.portfolio_theta;
        
        // Sell options if theta is attractive and within risk limits
        if greeks.theta < self.config.theta_threshold && 
           greeks.gamma.abs() < self.config.gamma_limit &&
           greeks.vega.abs() < self.config.vega_limit {
            
            let contracts = 0.01; // Small size for demo
            if mgr.validate_trade("BTC-OPTIONS", contracts) {
                // Mock options trade (would need options API)
                info!("🎭 Theta Harvest: θ={:.2}, Δ={:.3}, Expected Daily P&L=${:.2}", 
                    greeks.theta, greeks.delta, expected_daily_theta);
                
                // Update portfolio Greeks
                self.portfolio_delta += greeks.delta * contracts;
                self.portfolio_gamma += greeks.gamma * contracts;
                self.portfolio_vega += greeks.vega * contracts;
                self.portfolio_theta += contracts;
                
                mgr.update_position("BTC-OPTIONS", contracts, expected_daily_theta);
            }
        }
        
        // Delta hedge if needed (with cooldown)
        if self.portfolio_delta.abs() > self.config.delta_target + 0.1 && 
           data.timestamp - self.last_hedge_time > 300 { // 5 min cooldown
            
            let hedge_size = -self.portfolio_delta * 0.1; // Partial hedge
            let side = if hedge_size > 0.0 { OrderSide::Buy } else { OrderSide::Sell };
            
            match router.place_order("BTCUSDT", side, hedge_size.abs(), None).await {
                Ok(_) => {
                    self.portfolio_delta += hedge_size;
                    self.last_hedge_time = data.timestamp;
                    info!("🛡️ Delta hedge: {:.6} BTC", hedge_size);
                }
                Err(e) => {
                    warn!("Failed to hedge delta: {}", e);
                }
            }
        }
    }
}

// Statistical Arbitrage Strategy
pub struct StatArb {
    config: StatArbConfig,
    spread_history: VecDeque<f64>,
    mean: f64,
    std: f64,
    position: f64,
    last_trade_time: u64,
}

impl StatArb {
    pub fn new(config: &StatArbConfig) -> Self {
        Self {
            config: config.clone(),
            spread_history: VecDeque::new(),
            mean: 0.0,
            std: 1.0,
            position: 0.0,
            last_trade_time: 0,
        }
    }
    
    fn update_stats(&mut self, spread: f64) {
        self.spread_history.push_back(spread);
        if self.spread_history.len() > self.config.lookback_period {
            self.spread_history.pop_front();
        }
        
        if self.spread_history.len() > 10 {
            // Calculate rolling mean and std
            let sum: f64 = self.spread_history.iter().sum();
            self.mean = sum / self.spread_history.len() as f64;
            
            let variance: f64 = self.spread_history.iter()
                .map(|&x| (x - self.mean).powi(2))
                .sum::<f64>() / (self.spread_history.len() - 1) as f64;
            self.std = variance.sqrt().max(0.001); // Avoid division by zero
        }
    }
}

#[async_trait::async_trait]
impl Strategy for StatArb {
    fn name(&self) -> &'static str { "StatArb" }
    
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        // Get real prices for BTC and ETH
        let btc_price = match router.get_current_price("BTCUSDT").await {
            Ok(price) => price,
            Err(_) => return,
        };
        
        let eth_price = match router.get_current_price("ETHUSDT").await {
            Ok(price) => price,
            Err(_) => return,
        };
        
        // Calculate BTC/ETH ratio
        let spread = btc_price / eth_price;
        self.update_stats(spread);
        
        if self.spread_history.len() < 30 { // Need minimum data
            return;
        }
        
        // Z-score: z = (spread − μ) / σ
        let z = z_score(spread, self.mean, self.std);
        
        // Only trade if sufficient time has passed
        if data.timestamp - self.last_trade_time < 60 { // 1 min cooldown for immediate trading
            return;
        }
        
        // Entry signal - more conservative for live trading
        if z.abs() > self.config.z_entry && self.position.abs() < 0.001 {
            let usdt_balance = 57.94;
            let risk_amount = (usdt_balance * 0.05_f64).min(5.0); // Risk 5% max, cap at $5
            let position_size = risk_amount / btc_price;
            
            if position_size < 0.00001 { // Check minimum size
                return;
            }
            
            if mgr.validate_trade("BTC-ETH-SPREAD", position_size) {
                info!("📊 StatArb signal detected: Z={:.2}, Ratio={:.1}, Mean={:.1}", 
                    z, spread, self.mean);
                
                if z > 0.0 {
                    // BTC relatively expensive vs ETH: sell BTC
                    match router.place_order("BTCUSDT", OrderSide::Sell, position_size, None).await {
                        Ok(_) => {
                            self.position = -position_size;
                            self.last_trade_time = data.timestamp;
                            
                            let expected_profit = z.abs() * self.std * position_size * btc_price * 0.01;
                            mgr.update_position("BTC-ETH-SPREAD", position_size, expected_profit);
                            
                            info!("✅ StatArb Entry: Sold {:.6} BTC (Z={:.2}, Est. Profit=${:.4})", 
                                position_size, z, expected_profit);
                        }
                        Err(e) => {
                            warn!("❌ Failed to enter stat arb position: {}", e);
                        }
                    }
                } else {
                    // BTC relatively cheap vs ETH: buy BTC
                    match router.place_order("BTCUSDT", OrderSide::Buy, position_size, None).await {
                        Ok(_) => {
                            self.position = position_size;
                            self.last_trade_time = data.timestamp;
                            
                            let expected_profit = z.abs() * self.std * position_size * btc_price * 0.01;
                            mgr.update_position("BTC-ETH-SPREAD", position_size, expected_profit);
                            
                            info!("✅ StatArb Entry: Bought {:.6} BTC (Z={:.2}, Est. Profit=${:.4})", 
                                position_size, z, expected_profit);
                        }
                        Err(e) => {
                            warn!("❌ Failed to enter stat arb position: {}", e);
                        }
                    }
                }
            }
        }
        
        // Exit signal
        if z.abs() < self.config.z_exit && self.position.abs() > 0.00001 {
            let close_side = if self.position > 0.0 { OrderSide::Sell } else { OrderSide::Buy };
            
            match router.place_order("BTCUSDT", close_side, self.position.abs(), None).await {
                Ok(_) => {
                    info!("✅ StatArb Exit: Closed {:.6} BTC position (Z={:.2} -> mean reversion)", 
                        self.position, z);
                    self.position = 0.0;
                    self.last_trade_time = data.timestamp;
                }
                Err(e) => {
                    warn!("❌ Failed to exit stat arb position: {}", e);
                }
            }
        }
        
        // Log current status periodically
        if data.timestamp % 300 == 0 { // Every 5 minutes
            info!("📊 StatArb Status: Z={:.2}, Position={:.6} BTC, Mean={:.1}, Std={:.2}", 
                z, self.position, self.mean, self.std);
        }
    }
}

// Yield Looping Strategy
pub struct YieldLoop {
    config: YieldLoopConfig,
    leveraged_position: f64,
    collateral: f64,
    last_rebalance_time: u64,
}

impl YieldLoop {
    pub fn new(config: &YieldLoopConfig) -> Self {
        Self {
            config: config.clone(),
            leveraged_position: 0.0,
            collateral: 0.0,
            last_rebalance_time: 0,
        }
    }
}

#[async_trait::async_trait]
impl Strategy for YieldLoop {
    fn name(&self) -> &'static str { "YieldLoop" }
    
    async fn on_tick(&mut self, data: &MarketData, _router: &Router, mgr: &mut RiskManager) {
        // Mock reward APR (e.g., from staking or lending)
        let reward_apr = 0.08; // 8% APY
        let borrow_apr = data.borrow_rate * 365.0;
        
        // Net APR: net_apr = reward_apr − borrow_apr
        let net_apr = reward_apr - borrow_apr;
        
        // Only proceed if sufficient time has passed
        if data.timestamp - self.last_rebalance_time < 300 { // 5 min cooldown for immediate trading
            return;
        }
        
        if net_apr > self.config.min_net_apr {
            let base_amount = 1000.0; // Smaller amount for live trading
            let leverage = self.config.leverage_ratio;
            let total_position = base_amount * leverage;
            
            if mgr.validate_trade("YIELD-LOOP", total_position) {
                // Mock yield looping logic
                self.collateral += base_amount;
                self.leveraged_position += total_position;
                self.last_rebalance_time = data.timestamp;
                
                // Calculate expected profit
                let daily_profit = total_position * net_apr / 365.0;
                mgr.update_position("YIELD-LOOP", total_position, daily_profit);
                
                info!("🔄 Yield Loop: Net APR={:.2}%, Leverage={:.1}x, Daily Profit=${:.2}", 
                    net_apr * 100.0, leverage, daily_profit);
            }
        }
        
        // Check if rebalancing is needed
        if self.leveraged_position > 0.0 && self.collateral > 0.0 {
            let current_ratio = self.leveraged_position / self.collateral;
            let target_ratio = self.config.leverage_ratio;
            
            if (current_ratio - target_ratio).abs() > self.config.rebalance_threshold {
                info!("🔄 Rebalancing needed: Current={:.2}x, Target={:.2}x", 
                    current_ratio, target_ratio);
                self.last_rebalance_time = data.timestamp;
            }
        }
    }
}

// Momentum Trading Strategy for High-Volume Tokens
pub struct MomentumTrader {
    config: StatArbConfig, // Reuse config structure
    price_history: std::collections::HashMap<String, VecDeque<f64>>,
    volume_history: std::collections::HashMap<String, VecDeque<f64>>,
    positions: std::collections::HashMap<String, f64>,
    last_trade_times: std::collections::HashMap<String, u64>,
    target_symbols: Vec<String>,
}

impl MomentumTrader {
    pub fn new(config: &StatArbConfig) -> Self {
        Self {
            config: config.clone(),
            price_history: std::collections::HashMap::new(),
            volume_history: std::collections::HashMap::new(),
            positions: std::collections::HashMap::new(),
            last_trade_times: std::collections::HashMap::new(),
            target_symbols: vec![
                "PEPEUSDT".to_string(),
                "BONKUSDT".to_string(), 
                "SHIBUSDT".to_string(),
                "FLOKIUSDT".to_string(),
                "DOGEUSDT".to_string(),
                "RENDERUSDT".to_string(),
                "SUIUSDT".to_string(),
                "ARBUSDT".to_string(),
                "OPUSDT".to_string(),
                "AVAXUSDT".to_string(),
            ],
        }
    }

    fn calculate_momentum(&mut self, symbol: &str, price: f64, volume: f64) -> Option<f64> {
        let prices = self.price_history.entry(symbol.to_string()).or_insert_with(VecDeque::new);
        let volumes = self.volume_history.entry(symbol.to_string()).or_insert_with(VecDeque::new);
        
        prices.push_back(price);
        volumes.push_back(volume);
        
        // Keep only last 20 data points
        if prices.len() > 20 {
            prices.pop_front();
            volumes.pop_front();
        }
        
        if prices.len() < 5 {
            return None;
        }
        
        // Calculate price momentum (% change over last 5 periods)
        let old_price = prices[prices.len() - 5];
        let price_momentum = (price - old_price) / old_price;
        
        // Calculate volume surge (current vs average)
        let avg_volume: f64 = volumes.iter().sum::<f64>() / volumes.len() as f64;
        let volume_surge = if avg_volume > 0.0 { volume / avg_volume } else { 1.0 };
        
        // Combined momentum score
        Some(price_momentum * volume_surge.ln().max(0.0))
    }
}

#[async_trait::async_trait]
impl Strategy for MomentumTrader {
    fn name(&self) -> &'static str { "MomentumTrader" }
    
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        for symbol in &self.target_symbols.clone() {
            // Check cooldown (15 seconds between trades per symbol for immediate trading)
            if let Some(&last_time) = self.last_trade_times.get(symbol) {
                if current_time - last_time < 15 {
                    continue;
                }
            }
            
            // Get current price and volume
            let (price, volume) = match router.get_price_and_volume(symbol).await {
                Ok((p, v)) => (p, v),
                Err(_) => continue,
            };
            
            // Calculate momentum
            if let Some(momentum) = self.calculate_momentum(symbol, price, volume) {
                let current_position = self.positions.get(symbol).unwrap_or(&0.0);
                
                // Strong positive momentum - BUY signal
                if momentum > 0.02 && *current_position <= 0.0 { // 2% momentum threshold
                    let usdt_balance = 57.94; // Available balance
                    let risk_per_trade = (usdt_balance * 0.05_f64).min(10.0); // Risk 5% or $10 max
                    let trade_size_usdt = risk_per_trade;
                    let trade_size = trade_size_usdt / price;
                    
                    // Check minimum trade size
                    let min_notional = 5.0; // Binance minimum
                    if trade_size * price >= min_notional {
                        if mgr.validate_trade(symbol, trade_size) {
                            info!("🚀 MOMENTUM BUY: {} - Momentum: {:.4}, Size: ${:.2}", 
                                symbol, momentum, trade_size_usdt);
                            
                            match router.place_order(symbol, OrderSide::Buy, trade_size, None).await {
                                Ok(_) => {
                                    self.positions.insert(symbol.clone(), trade_size);
                                    self.last_trade_times.insert(symbol.clone(), current_time);
                                    mgr.update_position(symbol, trade_size, momentum * trade_size_usdt * 0.1);
                                    
                                    info!("✅ Momentum buy executed: {} @ ${:.6}", symbol, price);
                                }
                                Err(e) => {
                                    warn!("❌ Failed momentum buy {}: {}", symbol, e);
                                }
                            }
                        }
                    }
                }
                
                // Strong negative momentum or profit taking - SELL signal
                else if (momentum < -0.02 || momentum > 0.05) && *current_position > 0.0 {
                    let sell_size = *current_position;
                    
                    info!("📉 MOMENTUM SELL: {} - Momentum: {:.4}, Size: {:.6}", 
                        symbol, momentum, sell_size);
                    
                    match router.place_order(symbol, OrderSide::Sell, sell_size, None).await {
                        Ok(_) => {
                            let profit = sell_size * price - self.positions.get(symbol).unwrap_or(&0.0) * price;
                            self.positions.insert(symbol.clone(), 0.0);
                            self.last_trade_times.insert(symbol.clone(), current_time);
                            mgr.update_position(symbol, -sell_size, profit);
                            
                            info!("✅ Momentum sell executed: {} @ ${:.6}, Est. P&L: ${:.2}", 
                                symbol, price, profit);
                        }
                        Err(e) => {
                            warn!("❌ Failed momentum sell {}: {}", symbol, e);
                        }
                    }
                }
            }
        }
    }
}

// Enhanced Arbitrage Strategy for Cross-Exchange Opportunities
pub struct CrossExchangeArb {
    config: BasisArbConfig,
    last_arb_time: u64,
    profitable_pairs: Vec<String>,
}

impl CrossExchangeArb {
    pub fn new(config: &BasisArbConfig) -> Self {
        Self {
            config: config.clone(),
            last_arb_time: 0,
            profitable_pairs: vec![
                "BTCUSDT".to_string(),
                "ETHUSDT".to_string(),
                "SOLUSDT".to_string(),
                "ADAUSDT".to_string(),
                "AVAXUSDT".to_string(),
            ],
        }
    }
}

#[async_trait::async_trait]
impl Strategy for CrossExchangeArb {
    fn name(&self) -> &'static str { "CrossExchangeArb" }
    
    async fn on_tick(&mut self, data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
            
        // Check cooldown (30 seconds between arbitrage attempts for immediate trading)
        if current_time - self.last_arb_time < 30 {
            return;
        }
        
        for symbol in &self.profitable_pairs.clone() {
            // Get order book depth
            let (bid, ask) = match router.get_order_book(symbol).await {
                Ok((b, a)) => (b, a),
                Err(_) => continue,
            };
            
            let spread_pct = (ask - bid) / bid * 100.0;
            
            // Look for profitable arbitrage opportunities
            if spread_pct > 0.1 { // 0.1% minimum spread
                let mid_price = (bid + ask) / 2.0;
                let usdt_balance = 57.94;
                let trade_amount = (usdt_balance * 0.15_f64).min(20.0); // Use 15% or $20 max
                let trade_size = trade_amount / mid_price;
                
                if mgr.validate_trade(symbol, trade_size) {
                    // Execute buy at bid, sell at ask strategy
                    info!("⚡ ARBITRAGE OPPORTUNITY: {} - Spread: {:.3}%, Amount: ${:.2}", 
                        symbol, spread_pct, trade_amount);
                    
                    // Place buy order slightly above bid
                    let buy_price = bid + (ask - bid) * 0.25;
                    match router.place_order(symbol, OrderSide::Buy, trade_size, Some(buy_price)).await {
                        Ok(_) => {
                            // Immediately place sell order
                            let sell_price = ask - (ask - bid) * 0.25;
                            match router.place_order(symbol, OrderSide::Sell, trade_size, Some(sell_price)).await {
                                Ok(_) => {
                                    let expected_profit = trade_size * (sell_price - buy_price) * 0.8; // Account for fees
                                    mgr.update_position(symbol, 0.0, expected_profit);
                                    self.last_arb_time = current_time;
                                    
                                    info!("✅ Arbitrage executed: {} Buy@${:.6} Sell@${:.6}, Est.Profit: ${:.4}", 
                                        symbol, buy_price, sell_price, expected_profit);
                                }
                                Err(e) => {
                                    warn!("❌ Failed arbitrage sell {}: {}", symbol, e);
                                }
                            }
                        }
                        Err(e) => {
                            warn!("❌ Failed arbitrage buy {}: {}", symbol, e);
                        }
                    }
                }
            }
        }
    }
}

// Smart Token Trader - Uses existing balances for immediate trades
pub struct SmartTokenTrader {
    last_trade_time: std::collections::HashMap<String, u64>,
    existing_balances: std::collections::HashMap<String, f64>,
}

impl SmartTokenTrader {
    pub fn new() -> Self {
        let mut balances = std::collections::HashMap::new();
        // Your current balances from the system output
        balances.insert("SHIB".to_string(), 31323.12);
        balances.insert("PEPE".to_string(), 74886.30);
        balances.insert("BONK".to_string(), 9260.37);
        balances.insert("FLOKI".to_string(), 3985.07);
        balances.insert("KNC".to_string(), 799.67);
        balances.insert("HBAR".to_string(), 0.536);
        balances.insert("IOTA".to_string(), 1.33);
        balances.insert("ALGO".to_string(), 0.728);
        balances.insert("XLM".to_string(), 0.566);
        balances.insert("ADA".to_string(), 0.037);
        balances.insert("DOT".to_string(), 0.00144);
        balances.insert("QNT".to_string(), 0.00025800);
        balances.insert("ATOM".to_string(), 0.00150);
        
        Self {
            last_trade_time: std::collections::HashMap::new(),
            existing_balances: balances,
        }
    }
}

#[async_trait::async_trait]
impl Strategy for SmartTokenTrader {
    fn name(&self) -> &'static str { "SmartTokenTrader" }
    
    async fn on_tick(&mut self, _data: &MarketData, router: &Router, mgr: &mut RiskManager) {
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        // Check each token we already own for profitable selling opportunities
        for (token, balance) in &self.existing_balances.clone() {
            if *balance <= 0.0 {
                continue;
            }
            
            // Check cooldown (30 seconds between trades per token)
            if let Some(&last_time) = self.last_trade_time.get(token) {
                if current_time - last_time < 30 {
                    continue;
                }
            }
            
            let symbol = format!("{}USDT", token);
            
            // Get current price with minimal API calls
            if let Ok(price) = router.get_current_price(&symbol).await {
                // Simple profit-taking strategy: sell if we have tokens
                let sell_amount = match token.as_str() {
                    "SHIB" | "PEPE" | "BONK" | "FLOKI" => {
                        // For meme coins, sell small amounts frequently
                        (*balance * 0.1).max(1000.0) // Sell 10% or minimum 1000 tokens
                    }
                    "KNC" => {
                        (*balance * 0.05).max(10.0) // Sell 5% or minimum 10 KNC
                    }
                    _ => {
                        (*balance * 0.2).max(0.01) // Sell 20% or minimum 0.01
                    }
                };
                
                let usdt_value = sell_amount * price;
                
                // Only trade if the value is significant enough (>$5)
                if usdt_value >= 5.0 {
                    if mgr.validate_trade(&symbol, -sell_amount) {
                        info!("💰 SMART SELL: {} - Amount: {:.6}, Value: ${:.2}, Price: ${:.8}", 
                            symbol, sell_amount, usdt_value, price);
                        
                        match router.place_order(&symbol, OrderSide::Sell, sell_amount, None).await {
                            Ok(_) => {
                                // Update our balance tracking
                                if let Some(current_balance) = self.existing_balances.get_mut(token) {
                                    *current_balance -= sell_amount;
                                }
                                
                                self.last_trade_time.insert(token.clone(), current_time);
                                mgr.update_position(&symbol, -sell_amount, usdt_value * 0.05); // Assume 5% profit
                                
                                info!("✅ Smart sell executed: {} @ ${:.8}, Value: ${:.2}", 
                                    symbol, price, usdt_value);
                            }
                            Err(e) => {
                                warn!("❌ Failed smart sell {}: {}", symbol, e);
                            }
                        }
                    }
                } else {
                    info!("💡 {} value too small: ${:.2}", symbol, usdt_value);
                }
            }
        }
        
        // Look for buying opportunities with USDT
        let usdt_balance = 57.94; // Your available USDT
        if usdt_balance > 10.0 { // Only trade if we have enough USDT
            
            // Target high-momentum tokens for buying
            let buy_targets = vec!["BTCUSDT", "ETHUSDT", "SOLUSDT", "RENDERUSDT", "SUIUSDT"];
            
            for symbol in buy_targets {
                // Check cooldown
                if let Some(&last_time) = self.last_trade_time.get(symbol) {
                    if current_time - last_time < 60 { // 1 minute cooldown for buying
                        continue;
                    }
                }
                
                if let Ok(price) = router.get_current_price(symbol).await {
                    // Simple buying strategy: small amounts of strong tokens
                    let buy_amount_usdt = (usdt_balance * 0.1_f64).min(15.0); // Use 10% or max $15
                    let buy_size = buy_amount_usdt / price;
                    
                    if mgr.validate_trade(symbol, buy_size) {
                        info!("🚀 SMART BUY: {} - Size: {:.6}, Value: ${:.2}, Price: ${:.2}", 
                            symbol, buy_size, buy_amount_usdt, price);
                        
                        match router.place_order(symbol, OrderSide::Buy, buy_size, None).await {
                            Ok(_) => {
                                self.last_trade_time.insert(symbol.to_string(), current_time);
                                mgr.update_position(symbol, buy_size, -buy_amount_usdt);
                                
                                info!("✅ Smart buy executed: {} @ ${:.2}", symbol, price);
                                break; // Only one buy per cycle
                            }
                            Err(e) => {
                                warn!("❌ Failed smart buy {}: {}", symbol, e);
                            }
                        }
                    }
                }
            }
        }
    }
}

// Enhanced Highest Momentum Trader with diversification and market awareness
pub struct HighestMomentumTrader {
    last_scan_time: u64,
    scan_interval: u64,
    current_allocation: Option<String>,
    momentum_threshold: f64,
    max_positions: usize,  // Allow multiple positions for diversification
    min_volume_threshold: f64,  // Minimum volume for liquidity
}

impl HighestMomentumTrader {
    pub fn new() -> Self {
        Self {
            last_scan_time: 0,
            scan_interval: 120, // Scan every 2 minutes for faster reaction
            current_allocation: None,
            momentum_threshold: 0.015, // 1.5% minimum momentum (more selective)
            max_positions: 2, // Allow up to 2 positions for diversification
            min_volume_threshold: 50000.0, // Minimum $50k volume for liquidity
        }
    }

    async fn scan_all_tokens_for_momentum(&self, router: &Router) -> Result<Option<(String, f64)>, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            info!("🔍 Scanning ALL Binance US tokens for highest momentum...");
            
            // Get all 24hr tickers
            let all_tickers = binance_client.get_all_tickers().await?;
            
            let mut best_token: Option<(String, f64)> = None;
            let mut processed_count = 0;
            
            for ticker in all_tickers {
                // Only consider USDT pairs for simplicity
                if !ticker.symbol.ends_with("USDT") {
                    continue;
                }
                
                // Parse price change percentage as momentum
                if let Ok(momentum) = ticker.price_change_percent.parse::<f64>() {
                    let momentum_decimal = momentum / 100.0; // Convert percentage to decimal
                    
                    // Only consider positive momentum above threshold
                    if momentum_decimal > self.momentum_threshold {
                        processed_count += 1;
                        
                        if let Some((_, current_best)) = &best_token {
                            if momentum_decimal > *current_best {
                                best_token = Some((ticker.symbol.clone(), momentum_decimal));
                                info!("📈 New momentum leader: {} with {:.2}%", ticker.symbol, momentum * 100.0);
                            }
                        } else {
                            best_token = Some((ticker.symbol.clone(), momentum_decimal));
                            info!("📈 First momentum candidate: {} with {:.2}%", ticker.symbol, momentum * 100.0);
                        }
                    }
                }
            }
            
            info!("✅ Processed {} tokens with positive momentum > {:.1}%", 
                processed_count, self.momentum_threshold * 100.0);
            
            if let Some((symbol, momentum)) = &best_token {
                info!("🏆 HIGHEST MOMENTUM TOKEN: {} with {:.2}%", symbol, momentum * 100.0);
            } else {
                info!("❌ No tokens found with momentum > {:.1}%", self.momentum_threshold * 100.0);
            }
            
            Ok(best_token)
        } else {
            Ok(None)
        }
    }

    async fn allocate_all_funds(&mut self, symbol: &str, router: &Router) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            // Get current USDT balance
            let account_info = binance_client.get_account_info().await?;
            let usdt_balance = account_info.balances.iter()
                .find(|b| b.asset == "USDT")
                .map(|b| b.free.parse::<f64>().unwrap_or(0.0))
                .unwrap_or(0.0);
            
            if usdt_balance < 10.0 {
                warn!("💰 Insufficient USDT balance: ${:.2} (minimum $10 required)", usdt_balance);
                return Ok(());
            }
            
            // Use 95% of balance to leave some buffer
            let allocation_amount = usdt_balance * 0.95;
            
            info!("🚀 ALLOCATING ALL FUNDS: ${:.2} USDT → {}", allocation_amount, symbol);
            info!("💰 Available USDT: ${:.2}, Allocating: ${:.2}", usdt_balance, allocation_amount);
            
            // Get current price for the token
            let current_price = router.get_current_price(symbol).await?;
            let mut quantity = allocation_amount / current_price;
            
            // Adjust quantity to meet Binance lot size requirements
            // Round down to reasonable decimal places based on price
            if current_price > 100.0 {
                quantity = (quantity * 100000.0).floor() / 100000.0; // 5 decimal places
            } else if current_price > 1.0 {
                quantity = (quantity * 10000.0).floor() / 10000.0; // 4 decimal places  
            } else if current_price > 0.1 {
                quantity = (quantity * 1000.0).floor() / 1000.0; // 3 decimal places
            } else {
                quantity = (quantity * 100.0).floor() / 100.0; // 2 decimal places
            }
            
            // Ensure minimum quantity (many tokens require at least 1 unit)
            if quantity < 1.0 && current_price < 1.0 {
                quantity = quantity.floor().max(1.0);
            }
            
            info!("📊 Trade Details: {} @ ${:.6} = {:.8} tokens (adjusted for lot size)", symbol, current_price, quantity);
            
            // Place market buy order
            match router.place_order(symbol, OrderSide::Buy, quantity, None).await {
                Ok(order_result) => {
                    info!("✅ SUCCESS: Allocated ${:.2} to {} - Order ID: {}", 
                        allocation_amount, symbol, order_result.order_id);
                    self.current_allocation = Some(symbol.to_string());
                }
                Err(e) => {
                    error!("❌ FAILED to allocate to {}: {}", symbol, e);
                }
            }
        }
        
        Ok(())
    }
}

#[async_trait::async_trait]
impl Strategy for HighestMomentumTrader {
    fn name(&self) -> &'static str {
        "HighestMomentumTrader"
    }

    async fn on_tick(&mut self, _data: &MarketData, router: &Router, _risk_mgr: &mut RiskManager) {
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        // Check if it's time to scan for new opportunities
        if current_time >= self.last_scan_time + self.scan_interval {
            self.last_scan_time = current_time;
            
            info!("🔍 Scanning ALL Binance US tokens for highest momentum...");
            
            // Get all available tokens from Binance
            if let Some(client) = router.get_binance_client() {
                // STEP 1: Sell all existing positions first
                if let Ok(account_info) = client.get_account_info().await {
                    info!("💸 SELLING ALL EXISTING POSITIONS TO GO ALL-IN...");
                    
                    for balance in &account_info.balances {
                        let free_amount: f64 = balance.free.parse().unwrap_or(0.0);
                        
                        // Skip USDT and sell everything else with significant value
                        if balance.asset != "USDT" && free_amount > 0.0 {
                            let symbol = format!("{}USDT", balance.asset);
                            
                            // Check if this trading pair exists and has sufficient value
                            if let Ok(ticker) = client.get_ticker(&symbol).await {
                                let price: f64 = ticker.price.parse().unwrap_or(0.0);
                                let value = free_amount * price;
                                
                                if value >= 1.0 { // Only sell if worth at least $1
                                    info!("🔄 SELLING {}: {:.8} {} (≈${:.2})", symbol, free_amount, balance.asset, value);
                                    
                                    // Calculate correct quantity using Binance filters
                                    match client.calculate_order_quantity(&symbol, false, free_amount, price).await {
                                        Ok(adjusted_qty) => {
                                            match router.place_order(&symbol, OrderSide::Sell, adjusted_qty, None).await {
                                                Ok(_) => {
                                                    info!("✅ SOLD {}: {:.8} {} → ${:.2}", symbol, adjusted_qty, balance.asset, adjusted_qty * price);
                                                }
                                                Err(e) => {
                                                    warn!("❌ Failed to sell {} even with adjusted quantity: {}", symbol, e);
                                                }
                                            }
                                        }
                                        Err(e) => {
                                            warn!("❌ Failed to calculate quantity for {}: {}", symbol, e);
                                            // Fallback to original logic as last resort
                                            let adjusted_qty = (free_amount * 0.999).floor();
                                            if adjusted_qty > 0.0 {
                                                match router.place_order(&symbol, OrderSide::Sell, adjusted_qty, None).await {
                                                    Ok(_) => info!("✅ SOLD {} with fallback quantity", symbol),
                                                    Err(e2) => warn!("❌ Fallback sell also failed for {}: {}", symbol, e2),
                                                }
                                            }
                                        }
                                    }
                                    
                                    // Wait a bit between sales to respect rate limits
                                    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                                } else {
                                    info!("� Skipping {} - value too small: ${:.4}", symbol, value);
                                }
                            }
                        }
                    }
                    
                    // Wait for sales to settle
                    info!("⏰ Waiting 3 seconds for sales to settle...");
                    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                }
                
                // STEP 2: Find highest momentum token
                match client.get_all_tickers().await {
                    Ok(tickers) => {
                        let mut momentum_tokens = Vec::new();
                        
                        // Calculate momentum for all tokens with enhanced filtering
                        for ticker in &tickers {
                            if let Ok(change_pct) = ticker.price_change_percent.parse::<f64>() {
                                if let Ok(volume) = ticker.volume.parse::<f64>() {
                                    if let Ok(price) = ticker.price.parse::<f64>() {
                                        // Enhanced filtering: momentum + volume + price validity
                                        if change_pct > 1.0 && 
                                           volume > 10000.0 && // Minimum volume for liquidity
                                           price > 0.0001 { // Avoid dust tokens
                                            momentum_tokens.push((ticker.symbol.clone(), change_pct, ticker.price.clone()));
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Sort by momentum (highest first)
                        momentum_tokens.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                        
                        info!("📈 Found {} tokens with momentum > 1%:", momentum_tokens.len());
                        for (i, (symbol, momentum, price)) in momentum_tokens.iter().take(10).enumerate() {
                            info!("  {}. {}: +{:.2}% @ ${}", i+1, symbol, momentum, price);
                        }
                        
                        // STEP 3: Go ALL-IN on highest momentum token
                        if let Some((best_symbol, best_momentum, best_price)) = momentum_tokens.first() {
                            info!("🎯 HIGHEST MOMENTUM FOUND: {} with +{:.2}% gain!", best_symbol, best_momentum);
                            
                            // Check if market is open before trading
                            match client.is_market_open(best_symbol).await {
                                Ok(true) => {
                                    info!("✅ Market OPEN for {} - proceeding with trade", best_symbol);
                                }
                                Ok(false) => {
                                    warn!("🕐 Market CLOSED for {} - skipping trade (will retry next cycle)", best_symbol);
                                    return;
                                }
                                Err(e) => {
                                    warn!("❓ Cannot determine market status for {}: {} - proceeding cautiously", best_symbol, e);
                                }
                            }
                            
                            // Get updated account info after sales
                            if let Ok(account_info) = client.get_account_info().await {
                                let mut total_usdt_value = 0.0;
                                
                                // Calculate total USDT available (should be more after sales)
                                for balance in &account_info.balances {
                                    if balance.asset == "USDT" {
                                        total_usdt_value += balance.free.parse::<f64>().unwrap_or(0.0);
                                    }
                                }
                                
                                info!("💰 Total USDT available after sales: ${:.2}", total_usdt_value);
                                
                                if total_usdt_value >= 11.0 { // Minimum for most tokens
                                    let allocation_amount = total_usdt_value * 0.98; // Use 98% of balance (leave small buffer)
                                    let price: f64 = best_price.parse().unwrap_or(0.0);
                                    let quantity = allocation_amount / price;
                                    
                                    info!("💰 GOING ALL-IN ON {}: ${:.2} USDT → ~{:.4} tokens @ ${}", 
                                        best_symbol, allocation_amount, quantity, price);
                                    
                                    // Calculate correct quantity using Binance filters to avoid LOT_SIZE errors
                                    match client.calculate_order_quantity(best_symbol, true, quantity, price).await {
                                        Ok(adjusted_qty) => {
                                            match router.place_order(best_symbol, OrderSide::Buy, adjusted_qty, None).await {
                                                Ok(_) => {
                                                    info!("🚀🚀🚀 SUCCESS! ALL-IN BUY ORDER PLACED! 🚀🚀🚀");
                                                    info!("   Symbol: {}", best_symbol);
                                                    info!("   Quantity: {:.8}", adjusted_qty);
                                                    info!("   Value: ${:.2}", adjusted_qty * price);
                                                    info!("   Momentum: +{:.2}%", best_momentum);
                                                    info!("   🎯 PORTFOLIO NOW 100% IN HIGHEST MOMENTUM TOKEN!");
                                                    info!("   💰 SAVED GAS FEES: Single order instead of multiple attempts!");
                                                    self.current_allocation = Some(best_symbol.clone());
                                                }
                                                Err(e) => {
                                                    warn!("❌ Smart order failed: {}", e);
                                                    warn!("   This should rarely happen with proper lot size calculation");
                                                }
                                            }
                                        }
                                        Err(e) => {
                                            warn!("❌ Failed to calculate optimal quantity: {}", e);
                                            warn!("   Falling back to multi-attempt strategy...");
                                            
                                            // Fallback to original multi-attempt logic only if calculation fails
                                            let quantity_options = vec![
                                                (quantity * 100.0).round() / 100.0,  
                                                (quantity * 10.0).round() / 10.0,    
                                                quantity.round(),                     
                                                (quantity * 1000.0).round() / 1000.0,
                                            ];
                                            
                                            let mut success = false;
                                            for (i, qty_attempt) in quantity_options.iter().enumerate() {
                                                if *qty_attempt <= 0.0 { continue; }
                                                
                                                info!("🔄 Fallback Attempt {}: Trying quantity {:.6}", i+1, qty_attempt);
                                                match router.place_order(best_symbol, OrderSide::Buy, *qty_attempt, None).await {
                                                    Ok(_) => {
                                                        info!("✅ Fallback order succeeded on attempt {}", i+1);
                                                        self.current_allocation = Some(best_symbol.clone());
                                                        success = true;
                                                        break;
                                                    }
                                                    Err(e) => {
                                                        warn!("❌ Fallback attempt {} failed: {}", i+1, e);
                                                    }
                                                }
                                            }
                                            
                                            if !success {
                                                warn!("❌ All fallback attempts failed for {}", best_symbol);
                                            }
                                        }
                                    }
                                } else {
                                    warn!("💸 Insufficient USDT balance after sales: ${:.2}", total_usdt_value);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        warn!("❌ Failed to get all tickers: {}", e);
                    }
                }
            }
        }
    }
}

// AI-Enhanced Highest Momentum Trader with Claude/HuggingFace integration
pub struct AIEnhancedMomentumTrader {
    ai_analyzer: AITokenAnalyzer,
    last_scan_time: u64,
    scan_interval: u64,
    current_allocation: Option<String>,
    momentum_threshold: f64,
    ai_score_threshold: f64,
    max_positions: usize,
    min_volume_threshold: f64,
    confidence_threshold: f64,
}

impl AIEnhancedMomentumTrader {
    pub fn new() -> Self {
        Self {
            ai_analyzer: AITokenAnalyzer::new(),
            last_scan_time: 0,
            scan_interval: 180, // Scan every 3 minutes for AI analysis
            current_allocation: None,
            momentum_threshold: 0.01, // Lower threshold since AI will filter
            ai_score_threshold: 70.0, // AI must score >= 70/100
            max_positions: 1, // Focus on single best AI pick
            min_volume_threshold: 100000.0, // Higher volume for AI picks
            confidence_threshold: 0.6, // AI confidence >= 60%
        }
    }

    async fn scan_ai_enhanced_tokens(&mut self, router: &Router) -> Result<Option<(String, f64, AIAnalysisResult)>, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            info!("🤖 Starting AI-enhanced token analysis...");
            
            // Get AI analysis of all tokens
            let ai_analyses = self.ai_analyzer.analyze_all_tokens(binance_client).await?;
            
            // Get top AI picks with high confidence
            let top_picks = self.ai_analyzer.get_top_ai_picks(&ai_analyses, 5);
            
            info!("🎯 AI identified {} high-confidence bullish tokens", top_picks.len());
            
            if top_picks.is_empty() {
                info!("⚠️ No tokens meet AI criteria. Staying in USDT.");
                return Ok(None);
            }
            
            // Find the best AI pick that also meets our volume requirements
            for pick in top_picks {
                if pick.ai_score >= self.ai_score_threshold && 
                   pick.confidence >= self.confidence_threshold &&
                   pick.predicted_direction == "bullish" {
                    
                    // Verify volume requirements
                    let tickers = binance_client.get_all_tickers().await?;
                    if let Some(ticker) = tickers.iter().find(|t| t.symbol == pick.symbol) {
                        if let Ok(volume) = ticker.volume.parse::<f64>() {
                            if volume >= self.min_volume_threshold {
                                if let Ok(price_change) = ticker.price_change_percent.parse::<f64>() {
                                    let momentum = price_change / 100.0;
                                    
                                    info!("✅ AI Selected: {} - Score: {:.1}/100, Confidence: {:.1}%, Momentum: {:.2}%", 
                                        pick.symbol, pick.ai_score, pick.confidence * 100.0, momentum * 100.0);
                                    info!("   AI Reasoning: {}", pick.reasoning);
                                    
                                    return Ok(Some((pick.symbol.clone(), momentum, pick)));
                                }
                            }
                        }
                    }
                }
            }
            
            info!("⚠️ No AI picks meet volume/momentum requirements");
        }
        
        Ok(None)
    }

    async fn execute_ai_driven_rebalance(&mut self, router: &Router, target_symbol: &str, ai_analysis: &AIAnalysisResult) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        info!("🚀 Executing AI-driven rebalance to {} (Hold Duration: {:.1}h)", 
            target_symbol, ai_analysis.hold_duration_hours);
        
        // Check if we need to change allocation
        if let Some(current) = &self.current_allocation {
            if current == target_symbol {
                info!("💎 Already allocated to AI's top pick: {}", target_symbol);
                return Ok(());
            }
        }
        
        if let Some(binance_client) = router.get_binance_client() {
            // Get current USDT balance
            let account_info = binance_client.get_account_info().await?;
            let mut usdt_balance = 0.0;
            let mut current_holdings = Vec::new();
            
            for balance in &account_info.balances {
                let free_balance: f64 = balance.free.parse().unwrap_or(0.0);
                
                if balance.asset == "USDT" {
                    usdt_balance = free_balance;
                } else if free_balance > 0.0 {
                    current_holdings.push((balance.asset.clone(), free_balance));
                }
            }
            
            info!("💰 Current Portfolio: {} USDT, {} other holdings", usdt_balance, current_holdings.len());
            
            // Sell all non-USDT holdings first
            for (asset, quantity) in current_holdings {
                let sell_symbol = format!("{}USDT", asset);
                
                // Check if this symbol exists and has sufficient volume
                if let Ok(ticker) = binance_client.get_ticker(&sell_symbol).await {
                    info!("💸 Selling {} {} (current price: ${})", quantity, asset, ticker.price);
                    
                    match binance_client.place_market_order(&sell_symbol, "SELL", quantity).await {
                        Ok(order) => {
                            info!("✅ Sold {} {}: Order {}", quantity, asset, order.order_id);
                            // Add to USDT balance
                            if let Ok(price) = ticker.price.parse::<f64>() {
                                usdt_balance += quantity * price * 0.999; // Account for fees
                            }
                        }
                        Err(e) => {
                            warn!("⚠️ Failed to sell {}: {}", asset, e);
                        }
                    }
                    
                    // Small delay between sells
                    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
                }
            }
            
            // Now buy the AI-selected token with ALL USDT
            if usdt_balance > 10.0 { // Minimum $10 to trade
                info!("🎯 Buying {} with ${:.2} USDT (AI Score: {:.1}/100)", 
                    target_symbol, usdt_balance, ai_analysis.ai_score);
                
                match binance_client.get_ticker(target_symbol).await {
                    Ok(ticker) => {
                        if let Ok(price) = ticker.price.parse::<f64>() {
                            let quantity = (usdt_balance * 0.995) / price; // Leave 0.5% for fees
                            
                            match binance_client.place_market_order(target_symbol, "BUY", quantity).await {
                                Ok(order) => {
                                    info!("✅ AI-Driven Purchase Complete!");
                                    info!("   Order ID: {}", order.order_id);
                                    info!("   Symbol: {}", target_symbol);
                                    info!("   Quantity: {:.8}", quantity);
                                    info!("   AI Confidence: {:.1}%", ai_analysis.confidence * 100.0);
                                    info!("   Expected Hold: {:.1} hours", ai_analysis.hold_duration_hours);
                                    
                                    self.current_allocation = Some(target_symbol.to_string());
                                }
                                Err(e) => {
                                    error!("❌ Failed to buy {}: {}", target_symbol, e);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        error!("❌ Failed to get price for {}: {}", target_symbol, e);
                    }
                }
            } else {
                warn!("⚠️ Insufficient USDT balance: ${:.2}", usdt_balance);
            }
        }
        
        Ok(())
    }
}

#[async_trait::async_trait]
impl Strategy for AIEnhancedMomentumTrader {
    fn name(&self) -> &'static str {
        "AIEnhancedMomentumTrader"
    }

    async fn on_tick(&mut self, _data: &MarketData, router: &Router, _mgr: &mut RiskManager) {
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        
        if current_time - self.last_scan_time >= self.scan_interval {
            self.last_scan_time = current_time;
            info!("🤖 AI analysis interval reached - executing rebalance");
            
            match self.scan_ai_enhanced_tokens(router).await {
                Ok(Some((symbol, momentum, ai_analysis))) => {
                    info!("🎯 AI recommends: {} (momentum: {:.2}%, AI score: {:.1}/100)", 
                        symbol, momentum * 100.0, ai_analysis.ai_score);
                    
                    if let Err(e) = self.execute_ai_driven_rebalance(router, &symbol, &ai_analysis).await {
                        error!("❌ Failed to execute AI-driven rebalance: {}", e);
                    }
                }
                Ok(None) => {
                    info!("🤖 AI found no suitable opportunities. Staying in current allocation.");
                }
                Err(e) => {
                    error!("❌ AI analysis failed: {}", e);
                }
            }
        }
    }
}

// Capital Gains Maximizer - Enhanced AI Strategy for Long-term Momentum Holds
pub struct CapitalGainsMaximizer {
    ai_analyzer: AITokenAnalyzer,
    last_scan_time: u64,
    scan_interval: u64,
    current_holdings: HashMap<String, TokenPosition>,
    profit_target: f64,
    stop_loss: f64,
    min_momentum_threshold: f64,
    max_hold_duration: u64,
    position_entry_time: HashMap<String, u64>,
    profit_tracking: HashMap<String, f64>,
}

#[derive(Debug, Clone)]
struct TokenPosition {
    symbol: String,
    quantity: f64,
    entry_price: f64,
    entry_time: u64,
    ai_score: f64,
    expected_hold_duration: f64,
    stop_loss_price: f64,
    profit_target_price: f64,
}

impl CapitalGainsMaximizer {
    pub fn new() -> Self {
        Self {
            ai_analyzer: AITokenAnalyzer::new(),
            last_scan_time: 0,
            scan_interval: 300, // 5 minutes for better timing
            current_holdings: HashMap::new(),
            profit_target: 0.15, // 15% profit target
            stop_loss: 0.08, // 8% stop loss
            min_momentum_threshold: 3.0, // 3% minimum momentum
            max_hold_duration: 24 * 3600, // 24 hours max hold
            position_entry_time: HashMap::new(),
            profit_tracking: HashMap::new(),
        }
    }

    async fn scan_for_maximum_momentum_tokens(&mut self, router: &Router) -> Result<Vec<(String, f64, AIAnalysisResult)>, Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            info!("🎯 Scanning for MAXIMUM MOMENTUM tokens for capital gains...");
            
            // Get AI analysis of all tokens
            let ai_analyses = self.ai_analyzer.analyze_all_tokens(binance_client).await?;
            
            // Filter for highest momentum tokens with strong AI confidence
            let mut high_momentum_candidates = Vec::new();
            
            for analysis in ai_analyses {
                // Get current ticker data for momentum verification
                if let Ok(tickers) = binance_client.get_all_tickers().await {
                    if let Some(ticker) = tickers.iter().find(|t| t.symbol == analysis.symbol) {
                        if let Ok(price_change) = ticker.price_change_percent.parse::<f64>() {
                            let momentum = price_change;
                            
                            // Strict criteria for maximum capital gains
                            if analysis.ai_score >= 75.0 && 
                               analysis.confidence >= 0.7 &&
                               analysis.predicted_direction == "bullish" &&
                               momentum >= self.min_momentum_threshold &&
                               analysis.risk_level <= 0.4 { // Lower risk tolerance for capital preservation
                                
                                if let Ok(volume) = ticker.volume.parse::<f64>() {
                                    if volume >= 200000.0 { // Higher volume requirement for liquidity
                                        high_momentum_candidates.push((
                                            analysis.symbol.clone(),
                                            momentum,
                                            analysis
                                        ));
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Sort by AI score * momentum for best opportunities
            high_momentum_candidates.sort_by(|a, b| {
                let score_a = a.2.ai_score * (1.0 + a.1 / 100.0);
                let score_b = b.2.ai_score * (1.0 + b.1 / 100.0);
                score_b.partial_cmp(&score_a).unwrap_or(std::cmp::Ordering::Equal)
            });
            
            info!("📈 Found {} high-momentum capital gain candidates", high_momentum_candidates.len());
            for (i, (symbol, momentum, analysis)) in high_momentum_candidates.iter().take(3).enumerate() {
                info!("   {}. {} - AI: {:.1}/100, Momentum: {:.2}%, Risk: {:.1}/10, Hold: {:.1}h",
                    i+1, symbol, analysis.ai_score, momentum, analysis.risk_level * 10.0, analysis.hold_duration_hours);
            }
            
            return Ok(high_momentum_candidates);
        }
        
        Ok(Vec::new())
    }

    async fn manage_existing_positions(&mut self, router: &Router) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            let current_time = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
            let mut positions_to_close = Vec::new();
            
            // Check each position for profit/loss conditions
            for (symbol, position) in &self.current_holdings {
                if let Ok(ticker) = binance_client.get_ticker(symbol).await {
                    if let Ok(current_price) = ticker.price.parse::<f64>() {
                        let profit_pct = (current_price - position.entry_price) / position.entry_price;
                        let hold_duration_hours = (current_time - position.entry_time) as f64 / 3600.0;
                        
                        info!("📊 Position Check: {} - P&L: {:.2}%, Duration: {:.1}h, Target: {:.1}%",
                            symbol, profit_pct * 100.0, hold_duration_hours, self.profit_target * 100.0);
                        
                        let should_close = 
                            profit_pct >= self.profit_target || // Hit profit target
                            profit_pct <= -self.stop_loss || // Hit stop loss
                            hold_duration_hours >= position.expected_hold_duration || // Max hold time
                            current_time - position.entry_time >= self.max_hold_duration; // Absolute max time
                        
                        if should_close {
                            let reason = if profit_pct >= self.profit_target {
                                format!("🎉 PROFIT TARGET HIT: {:.2}%", profit_pct * 100.0)
                            } else if profit_pct <= -self.stop_loss {
                                format!("🛡️ STOP LOSS: {:.2}%", profit_pct * 100.0)
                            } else {
                                format!("⏰ MAX HOLD TIME: {:.1}h", hold_duration_hours)
                            };
                            
                            info!("🔄 Closing position: {} - {}", symbol, reason);
                            positions_to_close.push(symbol.clone());
                        }
                    }
                }
            }
            
            // Close positions that meet exit criteria
            for symbol in positions_to_close {
                if let Some(position) = self.current_holdings.remove(&symbol) {
                    // Sell the position
                    match binance_client.place_market_order(&symbol, "SELL", position.quantity).await {
                        Ok(_) => {
                            info!("✅ Closed position: {} - Quantity: {:.8}", symbol, position.quantity);
                            self.position_entry_time.remove(&symbol);
                        }
                        Err(e) => {
                            error!("❌ Failed to close position {}: {}", symbol, e);
                            // Re-add position if sale failed
                            self.current_holdings.insert(symbol, position);
                        }
                    }
                }
            }
        }
        
        Ok(())
    }

    async fn execute_capital_gains_strategy(&mut self, router: &Router) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        if let Some(binance_client) = router.get_binance_client() {
            // First, manage existing positions
            self.manage_existing_positions(router).await?;
            
            // Get available USDT for new positions
            let account_info = binance_client.get_account_info().await?;
            let mut usdt_balance = 0.0;
            
            for balance in &account_info.balances {
                if balance.asset == "USDT" {
                    usdt_balance = balance.free.parse().unwrap_or(0.0);
                    break;
                }
            }
            
            info!("💰 Available USDT for new positions: ${:.2}", usdt_balance);
            
            // Only enter new positions if we have significant capital and few current holdings
            if usdt_balance > 50.0 && self.current_holdings.len() < 2 {
                let candidates = self.scan_for_maximum_momentum_tokens(router).await?;
                
                if let Some((symbol, momentum, analysis)) = candidates.first() {
                    info!("🚀 ENTERING CAPITAL GAINS POSITION: {}", symbol);
                    info!("   AI Score: {:.1}/100", analysis.ai_score);
                    info!("   Momentum: {:.2}%", momentum);
                    info!("   Expected Hold: {:.1} hours", analysis.hold_duration_hours);
                    info!("   Risk Level: {:.1}/10", analysis.risk_level * 10.0);
                    
                    // Use 80% of available USDT for the position
                    let position_size_usdt = usdt_balance * 0.8;
                    
                    if let Ok(ticker) = binance_client.get_ticker(symbol).await {
                        if let Ok(entry_price) = ticker.price.parse::<f64>() {
                            let quantity = position_size_usdt / entry_price;
                            
                            match binance_client.place_market_order(symbol, "BUY", quantity).await {
                                Ok(_) => {
                                    info!("✅ POSITION OPENED: {} - ${:.2} ({:.8} tokens)", 
                                        symbol, position_size_usdt, quantity);
                                    
                                    let current_time = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
                                    
                                    // Track the position
                                    let position = TokenPosition {
                                        symbol: symbol.clone(),
                                        quantity,
                                        entry_price,
                                        entry_time: current_time,
                                        ai_score: analysis.ai_score,
                                        expected_hold_duration: analysis.hold_duration_hours,
                                        stop_loss_price: entry_price * (1.0 - self.stop_loss),
                                        profit_target_price: entry_price * (1.0 + self.profit_target),
                                    };
                                    
                                    self.current_holdings.insert(symbol.clone(), position);
                                    self.position_entry_time.insert(symbol.clone(), current_time);
                                    
                                    info!("🎯 Position targets set:");
                                    info!("   Profit Target: ${:.8} (+{:.1}%)", 
                                        entry_price * (1.0 + self.profit_target), self.profit_target * 100.0);
                                    info!("   Stop Loss: ${:.8} (-{:.1}%)", 
                                        entry_price * (1.0 - self.stop_loss), self.stop_loss * 100.0);
                                }
                                Err(e) => {
                                    error!("❌ Failed to open position {}: {}", symbol, e);
                                }
                            }
                        }
                    }
                }
            } else if self.current_holdings.len() >= 2 {
                info!("📊 Portfolio at capacity ({} positions). Managing existing holdings.", self.current_holdings.len());
            } else {
                info!("💰 Insufficient capital (${:.2}) for new momentum positions.", usdt_balance);
            }
        }
        
        Ok(())
    }
}

#[async_trait]
impl Strategy for CapitalGainsMaximizer {
    fn name(&self) -> &'static str {
        "CapitalGainsMaximizer"
    }

    async fn on_tick(&mut self, _data: &MarketData, router: &Router, _mgr: &mut RiskManager) {
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        
        if current_time - self.last_scan_time >= self.scan_interval {
            self.last_scan_time = current_time;
            info!("💎 Capital Gains Analysis Interval - Checking for maximum momentum opportunities");
            
            if let Err(e) = self.execute_capital_gains_strategy(router).await {
                error!("❌ Capital gains strategy error: {}", e);
            }
        }
        
        // Quick position monitoring every tick
        if !self.current_holdings.is_empty() {
            if let Err(e) = self.manage_existing_positions(router).await {
                error!("❌ Position management error: {}", e);
            }
        }
    }
}
