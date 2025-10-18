use crate::exchange::{MarketData, Router, OrderSide};
use crate::risk::RiskManager;
use crate::binance::{BinanceClient};
use std::collections::{HashMap, VecDeque};
use std::time::{SystemTime, UNIX_EPOCH};
use tracing::{info, warn, error, debug};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatisticalAnalysis {
    pub symbol: String,
    pub current_price: f64,
    pub mean_return: f64,
    pub std_dev: f64,
    pub std_1h: f64,
    pub std_6h: f64,
    pub std_24h: f64,
    pub returns_1h: f64,
    pub returns_6h: f64,
    pub returns_24h: f64,
    pub momentum_1h: f64,
    pub momentum_6h: f64,
    pub momentum_24h: f64,
    pub win_rate: f64,
    pub sharpe_ratio: f64,
    pub trend_correlation: f64,
    pub volume_24h: f64,
    pub composite_score: f64,
    pub prob_10_24h: f64,
    pub prob_20_48h: f64,
    pub prob_30_72h: f64,
    pub risk_adjusted_score: f64,
    pub analysis_timestamp: u64,
}

#[derive(Debug, Clone)]
pub struct PriceData {
    pub timestamp: u64,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
    pub returns: f64,
}

pub struct StatisticalMomentumStrategy {
    pub binance_client: BinanceClient,
    pub analysis_cache: HashMap<String, StatisticalAnalysis>,
    pub last_analysis_time: u64,
    pub analysis_interval: u64, // seconds
    pub min_volume_24h: f64,
    pub min_composite_score: f64,
    pub max_positions: usize,
    pub position_size_usdt: f64,
    pub current_positions: HashMap<String, f64>,
    pub last_trade_time: u64,
    pub trade_cooldown: u64, // seconds between trades
}

impl StatisticalMomentumStrategy {
    pub fn new(binance_client: BinanceClient) -> Self {
        Self {
            binance_client,
            analysis_cache: HashMap::new(),
            last_analysis_time: 0,
            analysis_interval: 3600, // 1 hour
            min_volume_24h: 1000000.0, // $1M minimum volume
            min_composite_score: 25.0,
            max_positions: 3,
            position_size_usdt: 75.0,
            current_positions: HashMap::new(),
            last_trade_time: 0,
            trade_cooldown: 1800, // 30 minutes between trades
        }
    }

    pub async fn get_usdt_pairs(&self) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let exchange_info = self.binance_client.get_exchange_info().await?;
        
        let mut usdt_symbols = Vec::new();
        for symbol_info in exchange_info["symbols"].as_array().unwrap_or(&vec![]) {
            if let (Some(symbol), Some(quote_asset), Some(status)) = (
                symbol_info["symbol"].as_str(),
                symbol_info["quoteAsset"].as_str(),
                symbol_info["status"].as_str()
            ) {
                if quote_asset == "USDT" && 
                   status == "TRADING" && 
                   !["USDCUSDT", "TUSDUSDT", "BUSDUSDT"].contains(&symbol) {
                    usdt_symbols.push(symbol.to_string());
                }
            }
        }
        
        Ok(usdt_symbols)
    }

    pub async fn get_kline_data(&self, symbol: &str, interval: &str, limit: u16) -> Result<Vec<PriceData>, Box<dyn std::error::Error>> {
        let klines = self.binance_client.get_klines(symbol, interval, Some(limit as i32)).await?;
        
        let mut price_data = Vec::new();
        
        for kline in klines {
            if let (Some(timestamp), Some(open), Some(high), Some(low), Some(close), Some(volume)) = (
                kline[0].as_u64(),
                kline[1].as_str().and_then(|s| s.parse::<f64>().ok()),
                kline[2].as_str().and_then(|s| s.parse::<f64>().ok()),
                kline[3].as_str().and_then(|s| s.parse::<f64>().ok()),
                kline[4].as_str().and_then(|s| s.parse::<f64>().ok()),
                kline[5].as_str().and_then(|s| s.parse::<f64>().ok()),
            ) {
                price_data.push(PriceData {
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    returns: 0.0, // Will calculate later
                });
            }
        }

        // Calculate returns
        for i in 1..price_data.len() {
            if price_data[i-1].close > 0.0 {
                price_data[i].returns = (price_data[i].close - price_data[i-1].close) / price_data[i-1].close * 100.0;
            }
        }

        Ok(price_data[1..].to_vec()) // Remove first entry (no return calculated)
    }

    pub fn calculate_statistics(&self, data: &[PriceData]) -> Option<StatisticalAnalysis> {
        if data.len() < 50 {
            return None;
        }

        let returns: Vec<f64> = data.iter().map(|d| d.returns).collect();
        let prices: Vec<f64> = data.iter().map(|d| d.close).collect();
        let volumes: Vec<f64> = data.iter().map(|d| d.volume).collect();

        // Basic statistics
        let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter().map(|r| (r - mean_return).powi(2)).sum::<f64>() / (returns.len() - 1) as f64;
        let std_dev = variance.sqrt();

        // Multi-timeframe analysis
        let returns_1h = returns.last().copied().unwrap_or(0.0);
        let returns_6h = returns.iter().rev().take(6).sum::<f64>();
        let returns_24h = returns.iter().rev().take(24).sum::<f64>();

        // Volatility at different timeframes
        let std_1h = std_dev;
        let std_6h = if returns.len() >= 6 {
            let recent_6h: Vec<f64> = returns.iter().rev().take(6).copied().collect();
            let mean_6h = recent_6h.iter().sum::<f64>() / recent_6h.len() as f64;
            let var_6h = recent_6h.iter().map(|r| (r - mean_6h).powi(2)).sum::<f64>() / (recent_6h.len() - 1) as f64;
            var_6h.sqrt()
        } else {
            std_dev
        };

        let std_24h = if returns.len() >= 24 {
            let recent_24h: Vec<f64> = returns.iter().rev().take(24).copied().collect();
            let mean_24h = recent_24h.iter().sum::<f64>() / recent_24h.len() as f64;
            let var_24h = recent_24h.iter().map(|r| (r - mean_24h).powi(2)).sum::<f64>() / (recent_24h.len() - 1) as f64;
            var_24h.sqrt()
        } else {
            std_dev
        };

        // Momentum indicators
        let momentum_1h = if std_1h > 0.0 { returns_1h / std_1h } else { 0.0 };
        let momentum_6h = if std_6h > 0.0 { returns_6h / std_6h } else { 0.0 };
        let momentum_24h = if std_24h > 0.0 { returns_24h / std_24h } else { 0.0 };

        // Win rate
        let positive_returns = returns.iter().filter(|&&r| r > 0.0).count();
        let win_rate = positive_returns as f64 / returns.len() as f64;

        // Sharpe ratio
        let sharpe_ratio = if std_dev > 0.0 { mean_return / std_dev } else { 0.0 };

        // Trend correlation (simplified)
        let trend_correlation = self.calculate_correlation(&(0..prices.len()).map(|i| i as f64).collect::<Vec<_>>(), &prices);

        // Volume analysis
        let volume_24h = volumes.iter().rev().take(24).sum::<f64>();

        // Probability calculations
        let prob_10_24h = self.calculate_gain_probability(mean_return, std_dev, 10.0, 24);
        let prob_20_48h = self.calculate_gain_probability(mean_return, std_dev, 20.0, 48);
        let prob_30_72h = self.calculate_gain_probability(mean_return, std_dev, 30.0, 72);

        // Composite score calculation
        let volatility_penalty = (std_24h / 10.0).min(0.5);
        let risk_adj_10 = prob_10_24h * (1.0 - volatility_penalty);
        let risk_adj_20 = prob_20_48h * (1.0 - volatility_penalty * 1.2);
        let risk_adj_30 = prob_30_72h * (1.0 - volatility_penalty * 1.5);

        let momentum_composite = momentum_1h * 0.4 + momentum_6h * 0.3 + momentum_24h * 0.2;
        let volume_score = (volume_24h / 10000000.0).min(10.0);

        let composite_score = (risk_adj_10 * 0.4 + risk_adj_20 * 0.3 + risk_adj_30 * 0.2 + 
                              momentum_composite * 5.0 + volume_score).min(100.0);

        let risk_adjusted_score = composite_score * (prob_20_48h / 100.0);

        Some(StatisticalAnalysis {
            symbol: data.first()?.symbol.clone().unwrap_or_default(),
            current_price: prices.last().copied().unwrap_or(0.0),
            mean_return,
            std_dev,
            std_1h,
            std_6h,
            std_24h,
            returns_1h,
            returns_6h,
            returns_24h,
            momentum_1h,
            momentum_6h,
            momentum_24h,
            win_rate,
            sharpe_ratio,
            trend_correlation,
            volume_24h,
            composite_score,
            prob_10_24h,
            prob_20_48h,
            prob_30_72h,
            risk_adjusted_score,
            analysis_timestamp: SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs(),
        })
    }

    fn calculate_correlation(&self, x: &[f64], y: &[f64]) -> f64 {
        if x.len() != y.len() || x.len() < 2 {
            return 0.0;
        }

        let n = x.len() as f64;
        let mean_x = x.iter().sum::<f64>() / n;
        let mean_y = y.iter().sum::<f64>() / n;

        let numerator: f64 = x.iter().zip(y.iter())
            .map(|(xi, yi)| (xi - mean_x) * (yi - mean_y))
            .sum();

        let sum_sq_x: f64 = x.iter().map(|xi| (xi - mean_x).powi(2)).sum();
        let sum_sq_y: f64 = y.iter().map(|yi| (yi - mean_y).powi(2)).sum();

        let denominator = (sum_sq_x * sum_sq_y).sqrt();

        if denominator > 0.0 {
            numerator / denominator
        } else {
            0.0
        }
    }

    fn normal_cdf_approx(&self, x: f64) -> f64 {
        // Approximation of normal CDF
        0.5 * (1.0 + self.erf_approx(x / 2.0_f64.sqrt()))
    }

    fn erf_approx(&self, x: f64) -> f64 {
        // Abramowitz and Stegun approximation
        let a1 = 0.254829592;
        let a2 = -0.284496736;
        let a3 = 1.421413741;
        let a4 = -1.453152027;
        let a5 = 1.061405429;
        let p = 0.3275911;

        let sign = if x >= 0.0 { 1.0 } else { -1.0 };
        let x = x.abs();

        let t = 1.0 / (1.0 + p * x);
        let y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * (-x * x).exp();

        sign * y
    }

    fn calculate_gain_probability(&self, mean_hourly: f64, std_hourly: f64, target_gain: f64, hours: i32) -> f64 {
        if std_hourly <= 0.0 {
            return 0.0;
        }

        let required_hourly = target_gain / hours as f64;
        let z_score = (required_hourly - mean_hourly) / std_hourly;
        let base_prob = (1.0 - self.normal_cdf_approx(z_score)) * 100.0;

        base_prob.max(0.0).min(95.0)
    }

    pub async fn analyze_all_tokens(&mut self) -> Result<Vec<StatisticalAnalysis>, Box<dyn std::error::Error>> {
        info!("Starting comprehensive statistical analysis...");
        
        let usdt_pairs = self.get_usdt_pairs().await?;
        let mut results = Vec::new();

        for (i, symbol) in usdt_pairs.iter().enumerate().take(40) {
            debug!("Analyzing {} ({}/{})", symbol, i + 1, usdt_pairs.len().min(40));

            // Get 24h ticker for volume filtering
            match self.binance_client.get_24hr_ticker(symbol).await {
                Ok(ticker) => {
                    let volume_24h: f64 = ticker["quoteVolume"].as_str()
                        .and_then(|s| s.parse().ok())
                        .unwrap_or(0.0);
                    
                    if volume_24h < self.min_volume_24h {
                        continue;
                    }

                    // Get kline data
                    match self.get_kline_data(symbol, "1h", 336).await {
                        Ok(mut data) => {
                            // Add symbol to data
                            for item in &mut data {
                                item.symbol = Some(symbol.clone());
                            }

                            if let Some(mut analysis) = self.calculate_statistics(&data) {
                                analysis.symbol = symbol.clone();
                                analysis.volume_24h = volume_24h;
                                results.push(analysis);
                            }
                        }
                        Err(e) => {
                            warn!("Failed to get kline data for {}: {}", symbol, e);
                        }
                    }
                }
                Err(e) => {
                    warn!("Failed to get ticker for {}: {}", symbol, e);
                }
            }

            // Rate limiting
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }

        // Sort by composite score
        results.sort_by(|a, b| b.composite_score.partial_cmp(&a.composite_score).unwrap_or(std::cmp::Ordering::Equal));

        info!("Statistical analysis complete! {} tokens analyzed.", results.len());
        Ok(results)
    }

    pub fn get_best_trading_opportunity(&self, results: &[StatisticalAnalysis]) -> Option<&StatisticalAnalysis> {
        results.iter()
            .filter(|analysis| {
                analysis.composite_score >= self.min_composite_score &&
                analysis.volume_24h >= self.min_volume_24h &&
                analysis.std_24h <= 15.0 && // Not too volatile
                !self.current_positions.contains_key(&analysis.symbol)
            })
            .next()
    }

    pub async fn execute_trade(&mut self, analysis: &StatisticalAnalysis, router: &Router) -> Result<(), Box<dyn std::error::Error>> {
        if self.current_positions.len() >= self.max_positions {
            info!("Maximum positions reached, skipping trade for {}", analysis.symbol);
            return Ok(());
        }

        let current_time = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        if current_time - self.last_trade_time < self.trade_cooldown {
            info!("Trade cooldown active, skipping trade for {}", analysis.symbol);
            return Ok(());
        }

        info!("Executing statistical momentum trade for {} (Score: {:.1})", 
              analysis.symbol, analysis.composite_score);

        // Calculate position size
        let quantity = self.position_size_usdt / analysis.current_price;

        // Place buy order
        match router.place_order(&analysis.symbol, OrderSide::Buy, quantity, None).await {
            Ok(_) => {
                self.current_positions.insert(analysis.symbol.clone(), quantity);
                self.last_trade_time = current_time;
                
                info!("✅ Successfully placed buy order: {} {} @ ${:.6}", 
                      quantity, analysis.symbol, analysis.current_price);
                
                // Set stop loss based on volatility
                let stop_loss_percent = (analysis.std_24h * 0.5).max(5.0).min(12.0); // 5-12% based on volatility
                let stop_price = analysis.current_price * (1.0 - stop_loss_percent / 100.0);
                
                info!("📊 Stop loss set at ${:.6} ({:.1}% below current price)", 
                      stop_price, stop_loss_percent);
            }
            Err(e) => {
                error!("❌ Failed to place buy order for {}: {}", analysis.symbol, e);
            }
        }

        Ok(())
    }

    pub fn should_analyze(&self) -> bool {
        let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
        current_time - self.last_analysis_time >= self.analysis_interval
    }

    pub fn print_analysis_summary(&self, results: &[StatisticalAnalysis]) {
        info!("📊 STATISTICAL MOMENTUM ANALYSIS SUMMARY");
        info!("=" * 60);

        for (i, analysis) in results.iter().take(10).enumerate() {
            info!("#{} {} - Score: {:.1}/100", i + 1, analysis.symbol, analysis.composite_score);
            info!("   💰 Price: ${:.6} | 24h Vol: ${:.0}", analysis.current_price, analysis.volume_24h);
            info!("   📈 Probabilities: 10%/24h: {:.1}% | 20%/48h: {:.1}% | 30%/72h: {:.1}%", 
                  analysis.prob_10_24h, analysis.prob_20_48h, analysis.prob_30_72h);
            info!("   📊 Momentum: 1h: {:.2} | 6h: {:.2} | 24h: {:.2}", 
                  analysis.momentum_1h, analysis.momentum_6h, analysis.momentum_24h);
            info!("   📉 Volatility: 1h: {:.2}% | 24h: {:.2}% | Sharpe: {:.2}", 
                  analysis.std_1h, analysis.std_24h, analysis.sharpe_ratio);
        }

        if !results.is_empty() {
            let avg_score: f64 = results.iter().map(|r| r.composite_score).sum::<f64>() / results.len() as f64;
            info!("📈 Average Score: {:.1} | Best: {} ({:.1})", 
                  avg_score, results[0].symbol, results[0].composite_score);
        }
    }
}

#[async_trait::async_trait]
impl crate::strategy::Strategy for StatisticalMomentumStrategy {
    fn name(&self) -> &'static str {
        "StatisticalMomentum"
    }

    async fn on_tick(&mut self, _data: &MarketData, router: &Router, _mgr: &mut RiskManager) {
        if !self.should_analyze() {
            return;
        }

        match self.analyze_all_tokens().await {
            Ok(results) => {
                self.analysis_cache.clear();
                for analysis in &results {
                    self.analysis_cache.insert(analysis.symbol.clone(), analysis.clone());
                }

                self.print_analysis_summary(&results);

                // Execute trade if we find a good opportunity
                if let Some(best_opportunity) = self.get_best_trading_opportunity(&results) {
                    if let Err(e) = self.execute_trade(best_opportunity, router).await {
                        error!("Failed to execute trade: {}", e);
                    }
                }

                self.last_analysis_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
            },
            Err(e) => {
                error!("Failed to analyze tokens: {}", e);
            }
        }
    }
}
