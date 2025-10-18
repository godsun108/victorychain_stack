use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use tracing::{info, warn, error, debug};
use std::collections::HashMap;
use tokio::sync::mpsc;
use anyhow::Result;

#[derive(Debug, Clone)]
pub struct RealtimePriceData {
    pub symbol: String,
    pub price: f64,
    pub price_change: f64,
    pub volume: f64,
    pub timestamp: u64,
}

pub struct BinanceWebSocketManager {
    price_sender: mpsc::UnboundedSender<RealtimePriceData>,
    symbols: Vec<String>,
}

impl BinanceWebSocketManager {
    pub fn new(symbols: Vec<String>) -> (Self, mpsc::UnboundedReceiver<RealtimePriceData>) {
        let (price_sender, price_receiver) = mpsc::unbounded_channel();
        
        (
            Self {
                price_sender,
                symbols,
            },
            price_receiver,
        )
    }

    pub async fn start_realtime_streams(&self) -> Result<()> {
        info!("🔄 Starting real-time WebSocket streams for {} symbols", self.symbols.len());
        
        // Create individual streams for top momentum tokens
        let priority_symbols = [
            "btcusdt", "ethusdt", "xrpusdt", "solusdt", "adausdt",
            "dotusdt", "linkusdt", "avaxusdt", "maticusdt", "atomusdt"
        ];

        // Start ticker stream for all symbols
        let ticker_task = self.start_ticker_stream().await;
        
        // Start individual mini ticker streams for priority tokens
        let mini_ticker_task = self.start_mini_ticker_stream(priority_symbols.to_vec()).await;

        // Wait for both streams
        tokio::try_join!(ticker_task, mini_ticker_task)?;
        
        Ok(())
    }

    async fn start_ticker_stream(&self) -> Result<()> {
        let url = "wss://stream.binance.us:9443/ws/!ticker@arr";
        
        info!("📡 Connecting to Binance US WebSocket: {}", url);
        
        let (ws_stream, _) = connect_async(url).await?;
        let (mut _write, mut read) = ws_stream.split();

        while let Some(message) = read.next().await {
            match message {
                Ok(Message::Text(text)) => {
                    if let Err(e) = self.process_ticker_message(&text).await {
                        debug!("Error processing ticker message: {}", e);
                    }
                }
                Ok(Message::Ping(ping)) => {
                    debug!("Received WebSocket ping: {:?}", ping);
                }
                Ok(Message::Close(_)) => {
                    warn!("WebSocket connection closed");
                    break;
                }
                Err(e) => {
                    error!("WebSocket error: {}", e);
                    break;
                }
                _ => {}
            }
        }

        warn!("Ticker WebSocket stream ended, attempting reconnection...");
        Ok(())
    }

    async fn start_mini_ticker_stream(&self, symbols: Vec<&str>) -> Result<()> {
        let streams: Vec<String> = symbols.iter()
            .map(|s| format!("{}@miniTicker", s))
            .collect();
        
        let stream_param = streams.join("/");
        let url = format!("wss://stream.binance.us:9443/stream?streams={}", stream_param);
        
        info!("📡 Connecting to mini ticker stream: {}", url);
        
        let (ws_stream, _) = connect_async(&url).await?;
        let (mut _write, mut read) = ws_stream.split();

        while let Some(message) = read.next().await {
            match message {
                Ok(Message::Text(text)) => {
                    if let Err(e) = self.process_mini_ticker_message(&text).await {
                        debug!("Error processing mini ticker: {}", e);
                    }
                }
                Ok(Message::Close(_)) => {
                    warn!("Mini ticker WebSocket closed");
                    break;
                }
                Err(e) => {
                    error!("Mini ticker WebSocket error: {}", e);
                    break;
                }
                _ => {}
            }
        }

        Ok(())
    }

    async fn process_ticker_message(&self, text: &str) -> Result<()> {
        let tickers: Vec<Value> = serde_json::from_str(text)?;
        
        for ticker in tickers {
            if let (Some(symbol), Some(price), Some(change), Some(volume)) = (
                ticker["s"].as_str(),
                ticker["c"].as_str(),
                ticker["P"].as_str(),
                ticker["v"].as_str(),
            ) {
                let price: f64 = price.parse().unwrap_or(0.0);
                let change: f64 = change.parse().unwrap_or(0.0);
                let volume: f64 = volume.parse().unwrap_or(0.0);
                
                // Only process USDT pairs with significant volume
                if symbol.ends_with("USDT") && volume > 1000.0 {
                    let price_data = RealtimePriceData {
                        symbol: symbol.to_string(),
                        price,
                        price_change: change,
                        volume,
                        timestamp: chrono::Utc::now().timestamp() as u64,
                    };
                    
                    if let Err(_) = self.price_sender.send(price_data) {
                        warn!("Failed to send price data for {}", symbol);
                    }
                }
            }
        }
        
        Ok(())
    }

    async fn process_mini_ticker_message(&self, text: &str) -> Result<()> {
        let data: Value = serde_json::from_str(text)?;
        
        if let Some(stream_data) = data["data"].as_object() {
            if let (Some(symbol), Some(price), Some(change), Some(volume)) = (
                stream_data["s"].as_str(),
                stream_data["c"].as_str(),
                stream_data["P"].as_str(),
                stream_data["v"].as_str(),
            ) {
                let price: f64 = price.parse().unwrap_or(0.0);
                let change: f64 = change.parse().unwrap_or(0.0);
                let volume: f64 = volume.parse().unwrap_or(0.0);
                
                let price_data = RealtimePriceData {
                    symbol: symbol.to_string(),
                    price,
                    price_change: change,
                    volume,
                    timestamp: chrono::Utc::now().timestamp() as u64,
                };
                
                // Send high-priority updates immediately
                if let Err(_) = self.price_sender.send(price_data) {
                    debug!("Channel closed for {}", symbol);
                }
            }
        }
        
        Ok(())
    }
}

/// Real-time momentum tracker using WebSocket data
pub struct RealtimeMomentumTracker {
    price_history: HashMap<String, Vec<(f64, u64)>>, // symbol -> (price, timestamp)
    volume_history: HashMap<String, Vec<(f64, u64)>>,
    momentum_scores: HashMap<String, f64>,
    lookback_seconds: u64,
}

impl RealtimeMomentumTracker {
    pub fn new(lookback_seconds: u64) -> Self {
        Self {
            price_history: HashMap::new(),
            volume_history: HashMap::new(),
            momentum_scores: HashMap::new(),
            lookback_seconds,
        }
    }

    pub fn update_price_data(&mut self, data: RealtimePriceData) {
        // Update price history
        let price_hist = self.price_history.entry(data.symbol.clone()).or_insert_with(Vec::new);
        price_hist.push((data.price, data.timestamp));
        
        // Update volume history
        let volume_hist = self.volume_history.entry(data.symbol.clone()).or_insert_with(Vec::new);
        volume_hist.push((data.volume, data.timestamp));
        
        // Clean old data
        let cutoff_time = data.timestamp - self.lookback_seconds;
        price_hist.retain(|(_, ts)| *ts >= cutoff_time);
        volume_hist.retain(|(_, ts)| *ts >= cutoff_time);
        
        // Calculate momentum score
        let momentum = self.calculate_momentum(&data.symbol);
        self.momentum_scores.insert(data.symbol.clone(), momentum);
        
        // Log significant momentum changes
        if momentum.abs() > 2.0 {
            info!("🚀 High momentum detected: {} = {:.2}% (Price: ${:.4})", 
                  data.symbol, momentum, data.price);
        }
    }

    fn calculate_momentum(&self, symbol: &str) -> f64 {
        if let Some(price_hist) = self.price_history.get(symbol) {
            if price_hist.len() < 2 {
                return 0.0;
            }
            
            let recent_price = price_hist.last().unwrap().0;
            let old_price = price_hist.first().unwrap().0;
            
            let price_change = (recent_price - old_price) / old_price * 100.0;
            
            // Factor in volume surge
            if let Some(volume_hist) = self.volume_history.get(symbol) {
                if volume_hist.len() >= 2 {
                    let recent_vol = volume_hist.last().unwrap().0;
                    let avg_vol = volume_hist.iter().map(|(v, _)| v).sum::<f64>() / volume_hist.len() as f64;
                    
                    let volume_multiplier = if avg_vol > 0.0 {
                        (recent_vol / avg_vol).min(3.0) // Cap at 3x multiplier
                    } else {
                        1.0
                    };
                    
                    return price_change * volume_multiplier.sqrt();
                }
            }
            
            price_change
        } else {
            0.0
        }
    }

    pub fn get_top_momentum_tokens(&self, count: usize) -> Vec<(String, f64)> {
        let mut tokens: Vec<(String, f64)> = self.momentum_scores
            .iter()
            .map(|(symbol, score)| (symbol.clone(), *score))
            .collect();
        
        tokens.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        tokens.truncate(count);
        
        tokens
    }

    pub fn get_momentum_score(&self, symbol: &str) -> f64 {
        self.momentum_scores.get(symbol).copied().unwrap_or(0.0)
    }
}
