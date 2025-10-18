use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use anyhow::{Result, anyhow};
use crate::binance::{BinanceClient, BinanceConfig, LiveMarketData};
use crossbeam_channel::Receiver;
use tracing::{info, warn, error};

// Order routing cost equation:
// cost = fee_rate * size + slippage_estimate(size)
// Used by SmartOrderRouter to choose venue.

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub funding_rate: f64,
    pub borrow_rate: f64,
    pub spot_price: f64,
    pub perp_price: f64,
    pub implied_vol: f64,
    pub oracle_price: f64,
    pub timestamp: u64,
    pub spreads: HashMap<String, f64>, // For statistical arbitrage
    pub bid: f64,
    pub ask: f64,
    pub volume: f64,
    pub symbol: String,
}

impl MarketData {
    pub fn from_live_data(live_data: &LiveMarketData) -> Self {
        MarketData {
            funding_rate: 0.0001, // Mock funding rate - would need futures API
            borrow_rate: 0.00005, // Mock borrow rate
            spot_price: live_data.price,
            perp_price: live_data.price * 1.001, // Mock perp premium
            implied_vol: 0.6, // Mock IV
            oracle_price: live_data.price,
            timestamp: live_data.timestamp,
            spreads: HashMap::new(),
            bid: live_data.bid,
            ask: live_data.ask,
            volume: live_data.volume,
            symbol: live_data.symbol.clone(),
        }
    }

    pub fn fetch_all() -> Self {
        // Fallback mock data if live feed fails
        MarketData {
            funding_rate: 0.0001,
            borrow_rate: 0.00005,
            spot_price: 50000.0,
            perp_price: 50050.0,
            implied_vol: 0.6,
            oracle_price: 50025.0,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            spreads: HashMap::new(),
            bid: 49995.0,
            ask: 50005.0,
            volume: 1000.0,
            symbol: "BTCUSDT".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExchangeConfig {
    pub endpoint: String,
    pub fee_rate: f64,
    pub max_position_size: f64,
    pub live_trading: bool,
    pub symbols: Vec<String>,
}

impl Default for ExchangeConfig {
    fn default() -> Self {
        Self {
            endpoint: "https://api.binance.us".to_string(),
            fee_rate: 0.001,
            max_position_size: 10.0,
            live_trading: true,
            symbols: vec!["BTCUSDT".to_string(), "ETHUSDT".to_string()],
        }
    }
}

pub struct Router {
    config: ExchangeConfig,
    binance_client: Option<BinanceClient>,
    pub market_data_receiver: Option<Receiver<LiveMarketData>>,
    latest_market_data: HashMap<String, MarketData>,
}

impl Router {
    pub fn new(config: &ExchangeConfig) -> Self {
        let binance_client = if config.live_trading {
            Some(BinanceClient::new(BinanceConfig::default()))
        } else {
            None
        };

        Self {
            config: config.clone(),
            binance_client,
            market_data_receiver: None,
            latest_market_data: HashMap::new(),
        }
    }

    pub fn set_market_data_receiver(&mut self, receiver: Receiver<LiveMarketData>) {
        self.market_data_receiver = Some(receiver);
    }

    pub async fn initialize(&mut self) -> Result<()> {
        if let Some(client) = &self.binance_client {
            info!("Initializing live trading connection...");
            
            // Test connection
            match client.get_account_info().await {
                Ok(account_info) => {
                    info!("✅ Connected to Binance US successfully");
                    info!("Account can trade: {}", account_info.can_trade);
                    
                    // Log balances
                    for balance in &account_info.balances {
                        let free: f64 = balance.free.parse().unwrap_or(0.0);
                        let locked: f64 = balance.locked.parse().unwrap_or(0.0);
                        if free > 0.0 || locked > 0.0 {
                            info!("Balance {}: Free={:.8}, Locked={:.8}", 
                                balance.asset, free, locked);
                        }
                    }
                }
                Err(e) => {
                    error!("❌ Failed to connect to Binance US: {}", e);
                    return Err(e);
                }
            }
        } else {
            info!("📊 Running in simulation mode");
        }
        
        Ok(())
    }

    pub fn update_market_data(&mut self) {
        // First, try to get data from WebSocket feed
        if let Some(receiver) = &self.market_data_receiver {
            while let Ok(live_data) = receiver.try_recv() {
                let market_data = MarketData::from_live_data(&live_data);
                self.latest_market_data.insert(live_data.symbol.clone(), market_data);
            }
        }
        
        // If no live data available, fetch from REST API
        if self.latest_market_data.is_empty() {
            if let Some(client) = &self.binance_client {
                // Spawn task to fetch live prices for all symbols
                let symbols = self.config.symbols.clone();
                let client_clone = client.clone();
                tokio::spawn(async move {
                    for symbol in symbols {
                        if let Ok(ticker) = client_clone.get_24hr_ticker(&symbol).await {
                            // Update would need to be done through a channel or shared state
                            // For now, we'll handle this in get_market_data method
                        }
                    }
                });
            }
        }
    }

    pub async fn get_live_market_data(&self, symbol: &str) -> MarketData {
        // Try to get cached data first
        if let Some(cached_data) = self.latest_market_data.get(symbol) {
            return cached_data.clone();
        }
        
        // If no cached data and we have a client, fetch live data
        if let Some(client) = &self.binance_client {
            if let Ok(ticker) = client.get_24hr_ticker(symbol).await {
                let price: f64 = ticker.last_price.parse().unwrap_or(50000.0);
                let bid: f64 = ticker.bid_price.parse().unwrap_or(price - 10.0);
                let ask: f64 = ticker.ask_price.parse().unwrap_or(price + 10.0);
                let volume: f64 = ticker.volume.parse().unwrap_or(1000.0);
                
                return MarketData {
                    funding_rate: 0.0001,
                    borrow_rate: 0.00005,
                    spot_price: price,
                    perp_price: price * 1.001,
                    implied_vol: 0.6,
                    oracle_price: price,
                    timestamp: std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap()
                        .as_secs(),
                    spreads: HashMap::new(),
                    bid,
                    ask,
                    volume,
                    symbol: symbol.to_string(),
                };
            }
        }
        
        // Fallback to mock data
        warn!("No live data for {}, using fallback", symbol);
        MarketData::fetch_all()
    }

    pub fn get_market_data(&self, symbol: &str) -> MarketData {
        self.latest_market_data
            .get(symbol)
            .cloned()
            .unwrap_or_else(|| {
                warn!("No live data for {}, using fallback", symbol);
                MarketData::fetch_all()
            })
    }

    /// Calculate total cost including fees and slippage
    pub fn calculate_cost(&self, size: f64) -> f64 {
        let fee_cost = self.config.fee_rate * size;
        let slippage_cost = self.slippage_estimate(size);
        fee_cost + slippage_cost
    }

    /// Estimate slippage based on order size
    fn slippage_estimate(&self, size: f64) -> f64 {
        // Simple square root model for slippage
        0.001 * size.sqrt()
    }

    pub async fn place_order(&self, symbol: &str, side: OrderSide, size: f64, price: Option<f64>) -> Result<OrderResult> {
        if let Some(client) = &self.binance_client {
            // Live trading
            info!("🔄 Placing LIVE order: {} {} {:.8} @ {:?}", 
                side.to_string(), symbol, size, price);

            let binance_side = match side {
                OrderSide::Buy => "BUY",
                OrderSide::Sell => "SELL",
            };

            let binance_order = if let Some(limit_price) = price {
                client.place_limit_order(symbol, binance_side, size, limit_price).await?
            } else {
                client.place_market_order(symbol, binance_side, size).await?
            };

            Ok(OrderResult {
                order_id: binance_order.order_id.to_string(),
                filled_size: binance_order.executed_qty.parse().unwrap_or(0.0),
                avg_price: if binance_order.cumulative_quote_qty.parse::<f64>().unwrap_or(0.0) > 0.0 {
                    binance_order.cumulative_quote_qty.parse::<f64>().unwrap_or(0.0) / 
                    binance_order.executed_qty.parse::<f64>().unwrap_or(1.0)
                } else {
                    price.unwrap_or(0.0)
                },
                status: match binance_order.status.as_str() {
                    "FILLED" => OrderStatus::Filled,
                    "PARTIALLY_FILLED" => OrderStatus::PartiallyFilled,
                    "NEW" => OrderStatus::Pending,
                    "CANCELED" => OrderStatus::Cancelled,
                    _ => OrderStatus::Pending,
                },
            })
        } else {
            // Simulation mode
            info!("📝 Simulating order: {} {} {:.8} @ {:?}", 
                side.to_string(), symbol, size, price);

            Ok(OrderResult {
                order_id: format!("sim_{}", uuid::Uuid::new_v4()),
                filled_size: size,
                avg_price: price.unwrap_or(50000.0),
                status: OrderStatus::Filled,
            })
        }
    }

    pub async fn get_current_price(&self, symbol: &str) -> Result<f64> {
        if let Some(client) = &self.binance_client {
            let ticker = client.get_ticker(symbol).await?;
            Ok(ticker.price.parse()?)
        } else {
            Ok(50000.0) // Mock price
        }
    }

    pub async fn get_price_and_volume(&self, symbol: &str) -> Result<(f64, f64)> {
        if let Some(client) = &self.binance_client {
            match client.get_24hr_ticker(symbol).await {
                Ok(ticker) => {
                    let price: f64 = ticker.last_price.parse()
                        .map_err(|_| anyhow!("Failed to parse price"))?;
                    let volume: f64 = ticker.volume.parse()
                        .map_err(|_| anyhow!("Failed to parse volume"))?;
                    Ok((price, volume))
                }
                Err(e) => {
                    warn!("Failed to get ticker for {}: {}", symbol, e);
                    Err(e)
                }
            }
        } else {
            // Simulation mode - return mock data
            Ok((100.0, 1000.0))
        }
    }

    pub async fn get_order_book(&self, symbol: &str) -> Result<(f64, f64)> {
        if let Some(client) = &self.binance_client {
            // Use ticker data as proxy for bid/ask
            match client.get_24hr_ticker(symbol).await {
                Ok(ticker) => {
                    let price: f64 = ticker.last_price.parse()
                        .map_err(|_| anyhow!("Failed to parse price"))?;
                    
                    // Estimate bid/ask based on last price (typical spread ~0.1%)
                    let spread = price * 0.001; // 0.1% spread estimate
                    let bid = price - spread / 2.0;
                    let ask = price + spread / 2.0;
                    
                    Ok((bid, ask))
                }
                Err(e) => {
                    warn!("Failed to get order book for {}: {}", symbol, e);
                    Err(e)
                }
            }
        } else {
            // Simulation mode
            Ok((99.5, 100.5))
        }
    }

    /// Get access to the Binance client for advanced operations
    pub fn get_binance_client(&self) -> Option<&BinanceClient> {
        self.binance_client.as_ref()
    }

    pub async fn get_rate_limit_status(&self) -> Option<(u32, u32)> {
        if let Some(client) = &self.binance_client {
            let rate_limiter = client.get_rate_limiter();
            Some(rate_limiter.get_usage_stats())
        } else {
            None
        }
    }

    pub async fn emergency_cancel_all_orders(&self, symbol: &str) -> Result<()> {
        if let Some(client) = &self.binance_client {
            match client.emergency_cancel_all_orders(symbol).await {
                Ok(_) => {
                    warn!("🚨 Emergency: Cancelled all orders for {}", symbol);
                    Ok(())
                }
                Err(e) => {
                    error!("Failed to cancel orders for {}: {}", symbol, e);
                    Err(e)
                }
            }
        } else {
            info!("📝 Simulation: Would cancel all orders for {}", symbol);
            Ok(())
        }
    }
}

#[derive(Debug, Clone)]
pub enum OrderSide {
    Buy,
    Sell,
}

impl OrderSide {
    pub fn to_string(&self) -> &str {
        match self {
            OrderSide::Buy => "BUY",
            OrderSide::Sell => "SELL",
        }
    }
}

#[derive(Debug, Clone)]
pub enum OrderStatus {
    Pending,
    Filled,
    PartiallyFilled,
    Cancelled,
}

#[derive(Debug, Clone)]
pub struct OrderResult {
    pub order_id: String,
    pub filled_size: f64,
    pub avg_price: f64,
    pub status: OrderStatus,
}
