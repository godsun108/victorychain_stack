use crate::momentum_predictor::{MomentumPredictor, MomentumPrediction, EntryRecommendation};
use crate::strategy::Strategy;
use crate::exchange::{Router, MarketData, OrderResult};
use crate::binance::BinanceClient;
use async_trait::async_trait;
use anyhow::Result;
use tracing::{info, warn, error};
use std::collections::HashMap;
use chrono::Utc;

pub struct MomentumHoldingStrategy {
    predictor: MomentumPredictor,
    active_positions: HashMap<String, MomentumPosition>,
    target_gain_threshold: f64, // 20-30%
    min_confidence_score: f64,   // 70%+
    max_positions: usize,        // Limit concurrent positions
    position_size_usdt: f64,     // Size per position
    stop_loss_percent: f64,      // 8% stop loss
    last_scan_time: u64,
    scan_interval_seconds: u64,
}

#[derive(Debug, Clone)]
struct MomentumPosition {
    symbol: String,
    entry_price: f64,
    quantity: f64,
    entry_time: u64,
    target_price: f64,
    stop_loss_price: f64,
    predicted_gain: f64,
    confidence_score: f64,
    hold_duration_hours: f64,
    current_pnl_percent: f64,
}

impl MomentumHoldingStrategy {
    pub fn new(claude_api_key: String) -> Self {
        Self {
            predictor: MomentumPredictor::new(claude_api_key),
            active_positions: HashMap::new(),
            target_gain_threshold: 20.0,  // Look for 20%+ opportunities
            min_confidence_score: 70.0,   // High confidence required
            max_positions: 3,             // Max 3 concurrent positions
            position_size_usdt: 75.0,     // $75 per position
            stop_loss_percent: 8.0,       // 8% stop loss
            last_scan_time: 0,
            scan_interval_seconds: 600,   // Scan every 10 minutes
        }
    }

    async fn scan_for_momentum_opportunities(&mut self, router: &Router) -> Result<Vec<MomentumPrediction>> {
        let current_time = Utc::now().timestamp() as u64;
        
        // Only scan if enough time has passed
        if current_time - self.last_scan_time < self.scan_interval_seconds {
            return Ok(Vec::new());
        }
        
        info!("🔍 Scanning for 20-30% momentum opportunities...");
        
        // Get all USDT trading pairs
        let all_symbols = self.get_all_usdt_pairs(router).await?;
        
        // Filter for high-volume, active tokens
        let filtered_symbols = self.filter_active_tokens(&all_symbols, router).await?;
        
        info!("📊 Analyzing {} high-volume tokens for momentum", filtered_symbols.len());
        
        // Get AI predictions for momentum
        let predictions = self.predictor.predict_high_momentum_tokens(&filtered_symbols).await?;
        
        // Filter for our criteria (20%+ gain, 70%+ confidence)
        let qualified_predictions: Vec<MomentumPrediction> = predictions
            .into_iter()
            .filter(|p| {
                p.predicted_gain_percent >= self.target_gain_threshold 
                && p.confidence_score >= self.min_confidence_score
                && matches!(p.entry_recommendation, EntryRecommendation::StrongBuy | EntryRecommendation::Buy)
            })
            .collect();
        
        if !qualified_predictions.is_empty() {
            info!("🚀 Found {} tokens with 20%+ momentum potential:", qualified_predictions.len());
            for prediction in &qualified_predictions {
                info!("   {} -> {:.1}% gain potential (confidence: {:.0}%)", 
                      prediction.symbol, prediction.predicted_gain_percent, prediction.confidence_score);
            }
        }
        
        self.last_scan_time = current_time;
        Ok(qualified_predictions)
    }

    async fn execute_momentum_trades(&mut self, predictions: Vec<MomentumPrediction>, router: &Router) -> Result<()> {
        // Check if we have room for more positions
        let available_slots = self.max_positions.saturating_sub(self.active_positions.len());
        if available_slots == 0 {
            info!("📊 All position slots occupied ({}), waiting for exits", self.max_positions);
            return Ok(());
        }
        
        // Sort predictions by score (gain * confidence)
        let mut sorted_predictions = predictions;
        sorted_predictions.sort_by(|a, b| {
            let score_a = a.predicted_gain_percent * (a.confidence_score / 100.0);
            let score_b = b.predicted_gain_percent * (b.confidence_score / 100.0);
            score_b.partial_cmp(&score_a).unwrap()
        });
        
        // Take the top opportunities that fit our available slots
        let selected_predictions = sorted_predictions.into_iter().take(available_slots);
        
        for prediction in selected_predictions {
            if let Err(e) = self.enter_momentum_position(&prediction, router).await {
                error!("Failed to enter position for {}: {}", prediction.symbol, e);
            }
        }
        
        Ok(())
    }

    async fn enter_momentum_position(&mut self, prediction: &MomentumPrediction, router: &Router) -> Result<()> {
        info!("🎯 Entering momentum position: {} (target: +{:.1}%)", 
              prediction.symbol, prediction.predicted_gain_percent);
        
        let current_price = prediction.current_price;
        let quantity = self.position_size_usdt / current_price;
        
        // Calculate target and stop loss prices
        let target_price = current_price * (1.0 + prediction.predicted_gain_percent / 100.0);
        let stop_loss_price = current_price * (1.0 - self.stop_loss_percent / 100.0);
        
        // Execute buy order
        match router.market_buy(&prediction.symbol, quantity).await {
            Ok(order_result) => {
                let position = MomentumPosition {
                    symbol: prediction.symbol.clone(),
                    entry_price: current_price,
                    quantity,
                    entry_time: Utc::now().timestamp() as u64,
                    target_price,
                    stop_loss_price,
                    predicted_gain: prediction.predicted_gain_percent,
                    confidence_score: prediction.confidence_score,
                    hold_duration_hours: prediction.hold_duration_hours,
                    current_pnl_percent: 0.0,
                };
                
                self.active_positions.insert(prediction.symbol.clone(), position);
                
                info!("✅ Momentum position entered: {} @ ${:.6} (qty: {:.4})", 
                      prediction.symbol, current_price, quantity);
                info!("   🎯 Target: ${:.6} (+{:.1}%) | 🛡️ Stop: ${:.6} (-{:.1}%)",
                      target_price, prediction.predicted_gain_percent, stop_loss_price, self.stop_loss_percent);
            }
            Err(e) => {
                error!("Failed to enter momentum position for {}: {}", prediction.symbol, e);
            }
        }
        
        Ok(())
    }

    async fn manage_existing_positions(&mut self, router: &Router) -> Result<()> {
        if self.active_positions.is_empty() {
            return Ok(());
        }
        
        let current_time = Utc::now().timestamp() as u64;
        let mut positions_to_close = Vec::new();
        
        for (symbol, position) in &mut self.active_positions {
            // Update current P&L
            if let Ok(current_price) = self.get_current_price(symbol, router).await {
                let pnl_percent = (current_price - position.entry_price) / position.entry_price * 100.0;
                position.current_pnl_percent = pnl_percent;
                
                let hold_time_hours = (current_time - position.entry_time) as f64 / 3600.0;
                
                // Check exit conditions
                let should_exit = self.should_exit_position(position, current_price, hold_time_hours);
                
                if should_exit.0 {
                    positions_to_close.push((symbol.clone(), should_exit.1));
                }
                
                // Log position status
                if pnl_percent.abs() > 5.0 || hold_time_hours > 12.0 {
                    info!("📊 {} position: {:.2}% P&L, {:.1}h held (target: +{:.1}%)", 
                          symbol, pnl_percent, hold_time_hours, position.predicted_gain);
                }
            }
        }
        
        // Close positions that need to be closed
        for (symbol, reason) in positions_to_close {
            self.close_momentum_position(&symbol, &reason, router).await?;
        }
        
        Ok(())
    }

    fn should_exit_position(&self, position: &MomentumPosition, current_price: f64, hold_time_hours: f64) -> (bool, String) {
        // Hit target price
        if current_price >= position.target_price {
            return (true, format!("TARGET_HIT: Gained {:.1}%", position.current_pnl_percent));
        }
        
        // Hit stop loss
        if current_price <= position.stop_loss_price {
            return (true, format!("STOP_LOSS: Lost {:.1}%", position.current_pnl_percent));
        }
        
        // Exceeded hold duration
        if hold_time_hours >= position.hold_duration_hours {
            return (true, format!("TIME_EXIT: Held {:.1}h, P&L: {:.1}%", hold_time_hours, position.current_pnl_percent));
        }
        
        // Momentum turned negative after being positive
        if position.current_pnl_percent < -5.0 && hold_time_hours > 2.0 {
            return (true, format!("MOMENTUM_LOSS: {:.1}% decline", position.current_pnl_percent));
        }
        
        // Take profits on strong gains even before target
        if position.current_pnl_percent >= 25.0 && hold_time_hours > 6.0 {
            return (true, format!("EARLY_PROFIT: Strong {:.1}% gain", position.current_pnl_percent));
        }
        
        (false, String::new())
    }

    async fn close_momentum_position(&mut self, symbol: &str, reason: &str, router: &Router) -> Result<()> {
        if let Some(position) = self.active_positions.remove(symbol) {
            info!("🔄 Closing momentum position: {} | Reason: {}", symbol, reason);
            
            // Execute sell order
            match router.market_sell(symbol, position.quantity).await {
                Ok(_) => {
                    let hold_time_hours = (Utc::now().timestamp() as u64 - position.entry_time) as f64 / 3600.0;
                    
                    info!("✅ Position closed: {} | P&L: {:.2}% | Held: {:.1}h", 
                          symbol, position.current_pnl_percent, hold_time_hours);
                    
                    // Log performance metrics
                    if position.current_pnl_percent >= 15.0 {
                        info!("🎉 MOMENTUM SUCCESS: {} achieved {:.1}% gain in {:.1}h!", 
                              symbol, position.current_pnl_percent, hold_time_hours);
                    }
                }
                Err(e) => {
                    error!("Failed to close position for {}: {}", symbol, e);
                    // Re-add position back if sell failed
                    self.active_positions.insert(symbol.to_string(), position);
                }
            }
        }
        
        Ok(())
    }

    async fn get_all_usdt_pairs(&self, router: &Router) -> Result<Vec<String>> {
        // This would integrate with your existing token listing functionality
        // Return top volume USDT pairs
        Ok(vec![
            "BTCUSDT".to_string(), "ETHUSDT".to_string(), "XRPUSDT".to_string(),
            "SOLUSDT".to_string(), "ADAUSDT".to_string(), "DOTUSDT".to_string(),
            "LINKUSDT".to_string(), "AVAXUSDT".to_string(), "MATICUSDT".to_string(),
            "ATOMUSDT".to_string(), "NEARUSDT".to_string(), "ALGOUSDT".to_string(),
            "IOTAUSDT".to_string(), "XLMUSDT".to_string(), "HBARUSDT".to_string(),
            "SHIBUSDT".to_string(), "PEPEUSDT".to_string(), "FLOKIUSDT".to_string(),
        ])
    }

    async fn filter_active_tokens(&self, symbols: &[String], router: &Router) -> Result<Vec<String>> {
        // Filter for tokens with good volume and volatility
        let mut active_tokens = Vec::new();
        
        for symbol in symbols {
            // This would check 24h volume > $1M and price change > 2%
            active_tokens.push(symbol.clone());
        }
        
        // Return top 50 most active
        active_tokens.truncate(50);
        Ok(active_tokens)
    }

    async fn get_current_price(&self, symbol: &str, router: &Router) -> Result<f64> {
        // This would get current price from router/binance client
        Ok(100.0) // Mock price
    }

    pub fn get_active_positions(&self) -> &HashMap<String, MomentumPosition> {
        &self.active_positions
    }

    pub fn get_position_summary(&self) -> String {
        if self.active_positions.is_empty() {
            "No active momentum positions".to_string()
        } else {
            let total_pnl: f64 = self.active_positions.values().map(|p| p.current_pnl_percent).sum();
            let avg_pnl = total_pnl / self.active_positions.len() as f64;
            
            format!("{} active positions | Avg P&L: {:.2}% | Available slots: {}", 
                    self.active_positions.len(), avg_pnl, 
                    self.max_positions - self.active_positions.len())
        }
    }
}

#[async_trait]
impl Strategy for MomentumHoldingStrategy {
    async fn on_tick(&mut self, data: &MarketData, router: &Router) -> Result<()> {
        // Manage existing positions first
        self.manage_existing_positions(router).await?;
        
        // Look for new momentum opportunities
        let predictions = self.scan_for_momentum_opportunities(router).await?;
        
        if !predictions.is_empty() {
            self.execute_momentum_trades(predictions, router).await?;
        }
        
        // Log status every few ticks
        if self.last_scan_time % 1800 == 0 { // Every 30 minutes
            info!("💼 Momentum Strategy Status: {}", self.get_position_summary());
        }
        
        Ok(())
    }
}
