use serde::{Deserialize, Serialize};
use reqwest::Client;
use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::time::{SystemTime, UNIX_EPOCH, Duration, Instant};
use anyhow::{Result, anyhow};
use tokio_tungstenite::{connect_async, tungstenite::Message};
use futures_util::StreamExt;
use crossbeam_channel::Sender;
use tracing::{info, warn, error, debug};
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;
use tokio::time::sleep;

type HmacSha256 = Hmac<Sha256>;

// Rate limiting structures
#[derive(Debug, Clone)]
pub struct RateLimitBucket {
    pub requests: VecDeque<Instant>,
    pub max_requests: u32,
    pub window_duration: Duration,
}

impl RateLimitBucket {
    pub fn new(max_requests: u32, window_duration: Duration) -> Self {
        Self {
            requests: VecDeque::new(),
            max_requests,
            window_duration,
        }
    }

    pub fn can_make_request(&mut self) -> bool {
        let now = Instant::now();
        
        // Remove old requests outside the window
        while let Some(&front_time) = self.requests.front() {
            if now.duration_since(front_time) > self.window_duration {
                self.requests.pop_front();
            } else {
                break;
            }
        }

        self.requests.len() < self.max_requests as usize
    }

    pub fn add_request(&mut self) {
        self.requests.push_back(Instant::now());
    }

    pub fn time_until_next_request(&self) -> Option<Duration> {
        if self.requests.len() < self.max_requests as usize {
            return None;
        }

        if let Some(&oldest_request) = self.requests.front() {
            let elapsed = Instant::now().duration_since(oldest_request);
            if elapsed < self.window_duration {
                Some(self.window_duration - elapsed)
            } else {
                None
            }
        } else {
            None
        }
    }
}

#[derive(Debug)]
pub struct RateLimiter {
    // Request weight limit: 1200 per minute
    pub weight_bucket: Arc<Mutex<RateLimitBucket>>,
    // Order limit: 50 per 10 seconds
    pub order_bucket: Arc<Mutex<RateLimitBucket>>,
    // Raw requests: 6100 per 5 minutes
    pub raw_request_bucket: Arc<Mutex<RateLimitBucket>>,
    // Track current usage from headers
    pub current_weight_usage: Arc<Mutex<u32>>,
    pub current_order_usage: Arc<Mutex<u32>>,
}

impl RateLimiter {
    pub fn new() -> Self {
        // Use much more conservative limits to prevent bans
        Self {
            // Use only 60% of weight limit (720 instead of 1200)
            weight_bucket: Arc::new(Mutex::new(RateLimitBucket::new(720, Duration::from_secs(60)))),
            // Use only 70% of order limit (35 instead of 50)
            order_bucket: Arc::new(Mutex::new(RateLimitBucket::new(35, Duration::from_secs(10)))),
            // Use only 50% of raw request limit (3000 instead of 6100)
            raw_request_bucket: Arc::new(Mutex::new(RateLimitBucket::new(3000, Duration::from_secs(300)))),
            current_weight_usage: Arc::new(Mutex::new(0)),
            current_order_usage: Arc::new(Mutex::new(0)),
        }
    }

    pub async fn wait_for_request(&self, weight: u32, is_order: bool) -> Result<()> {
        loop {
            let can_make_request = {
                let mut weight_bucket = self.weight_bucket.lock().unwrap();
                let mut raw_bucket = self.raw_request_bucket.lock().unwrap();
                
                // Check weight limit
                let weight_ok = weight_bucket.can_make_request();
                let raw_ok = raw_bucket.can_make_request();
                
                if is_order {
                    let mut order_bucket = self.order_bucket.lock().unwrap();
                    let order_ok = order_bucket.can_make_request();
                    
                    if weight_ok && raw_ok && order_ok {
                        // Add requests to all relevant buckets
                        for _ in 0..weight {
                            weight_bucket.add_request();
                        }
                        raw_bucket.add_request();
                        order_bucket.add_request();
                        true
                    } else {
                        false
                    }
                } else {
                    if weight_ok && raw_ok {
                        // Add requests to relevant buckets
                        for _ in 0..weight {
                            weight_bucket.add_request();
                        }
                        raw_bucket.add_request();
                        true
                    } else {
                        false
                    }
                }
            };

            if can_make_request {
                break;
            }

            // Calculate wait time with extra safety margin
            let wait_time = {
                let weight_bucket = self.weight_bucket.lock().unwrap();
                let raw_bucket = self.raw_request_bucket.lock().unwrap();
                
                // Start with minimum wait of 500ms for safety
                let mut max_wait = Duration::from_millis(500);
                
                if let Some(weight_wait) = weight_bucket.time_until_next_request() {
                    max_wait = max_wait.max(weight_wait + Duration::from_millis(100));
                }
                
                if let Some(raw_wait) = raw_bucket.time_until_next_request() {
                    max_wait = max_wait.max(raw_wait + Duration::from_millis(100));
                }
                
                if is_order {
                    let order_bucket = self.order_bucket.lock().unwrap();
                    if let Some(order_wait) = order_bucket.time_until_next_request() {
                        max_wait = max_wait.max(order_wait + Duration::from_millis(200));
                    }
                }
                
                max_wait
            };

            debug!("Rate limit reached, waiting {:?}", wait_time);
            sleep(wait_time).await;
        }

        Ok(())
    }

    pub fn update_from_headers(&self, headers: &reqwest::header::HeaderMap) {
        // Update current usage from response headers
        if let Some(weight_header) = headers.get("X-MBX-USED-WEIGHT-1M") {
            if let Ok(weight_str) = weight_header.to_str() {
                if let Ok(weight) = weight_str.parse::<u32>() {
                    *self.current_weight_usage.lock().unwrap() = weight;
                    debug!("Current weight usage: {}/1200", weight);
                }
            }
        }

        if let Some(order_header) = headers.get("X-MBX-ORDER-COUNT-10S") {
            if let Ok(order_str) = order_header.to_str() {
                if let Ok(orders) = order_str.parse::<u32>() {
                    *self.current_order_usage.lock().unwrap() = orders;
                    debug!("Current order usage: {}/50", orders);
                }
            }
        }
    }

    pub fn get_usage_stats(&self) -> (u32, u32) {
        let weight_usage = *self.current_weight_usage.lock().unwrap();
        let order_usage = *self.current_order_usage.lock().unwrap();
        (weight_usage, order_usage)
    }
}

#[derive(Debug, Clone)]
pub struct BinanceConfig {
    pub api_key: String,
    pub secret_key: String,
    pub base_url: String,
    pub ws_url: String,
    pub testnet: bool,
}

impl Default for BinanceConfig {
    fn default() -> Self {
        Self {
            api_key: "o0KEblMxyczeSMETOFC5Kp7wheZJVVk0JQ5tfGv5TGiLXX909VqcR59ofWFoytVX".to_string(),
            secret_key: "bjzQ1ZB3qoxE62r5uofcrPSLUYsYqqFyfzZaAdgjOBNHSZlnNiBXXm2zKBM8PMYg".to_string(),
            base_url: "https://api.binance.us".to_string(),
            ws_url: "wss://stream.binance.us:9443/ws".to_string(),
            testnet: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceTicker {
    #[serde(rename = "symbol", alias = "s")]
    pub symbol: String,
    #[serde(rename = "lastPrice", alias = "c")]
    pub price: String,
    #[serde(rename = "priceChangePercent", alias = "P", default = "default_change")]
    pub price_change_percent: String,
    #[serde(rename = "volume", alias = "v", default = "default_volume")]
    pub volume: String,
}

fn default_change() -> String {
    "0.00".to_string()
}

fn default_volume() -> String {
    "0.0".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceOrderBook {
    pub bids: Vec<[String; 2]>,
    pub asks: Vec<[String; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceOrder {
    #[serde(rename = "orderId")]
    pub order_id: u64,
    pub symbol: String,
    pub status: String,
    #[serde(rename = "executedQty")]
    pub executed_qty: String,
    #[serde(rename = "cummulativeQuoteQty")]
    pub cumulative_quote_qty: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceBalance {
    pub asset: String,
    pub free: String,
    pub locked: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceAccountInfo {
    pub balances: Vec<BinanceBalance>,
    #[serde(rename = "canTrade")]
    pub can_trade: bool,
    #[serde(rename = "canWithdraw")]
    pub can_withdraw: bool,
    #[serde(rename = "canDeposit")]
    pub can_deposit: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Binance24hrTicker {
    pub symbol: String,
    #[serde(rename = "lastPrice")]
    pub last_price: String,
    #[serde(rename = "bidPrice")]
    pub bid_price: String,
    #[serde(rename = "askPrice")]
    pub ask_price: String,
    pub volume: String,
    #[serde(rename = "priceChange")]
    pub price_change: String,
    #[serde(rename = "priceChangePercent")]
    pub price_change_percent: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceExchangeInfo {
    pub timezone: String,
    #[serde(rename = "serverTime")]
    pub server_time: u64,
    pub symbols: Vec<BinanceSymbol>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceSymbol {
    pub symbol: String,
    pub status: String,
    #[serde(rename = "baseAsset")]
    pub base_asset: String,
    #[serde(rename = "quoteAsset")]
    pub quote_asset: String,
    #[serde(rename = "baseAssetPrecision")]
    pub base_asset_precision: u32,
    #[serde(rename = "quotePrecision")]
    pub quote_precision: u32,
    #[serde(rename = "orderTypes")]
    pub order_types: Vec<String>,
    #[serde(rename = "icebergAllowed")]
    pub iceberg_allowed: bool,
    #[serde(rename = "ocoAllowed")]
    pub oco_allowed: bool,
    #[serde(rename = "isSpotTradingAllowed")]
    pub is_spot_trading_allowed: bool,
    #[serde(rename = "isMarginTradingAllowed")]
    pub is_margin_trading_allowed: bool,
    pub permissions: Vec<String>,
    pub filters: Vec<BinanceFilter>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceAllTickers {
    pub tickers: Vec<BinanceTicker>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinanceFilter {
    #[serde(rename = "filterType")]
    pub filter_type: String,
    #[serde(rename = "minQty")]
    pub min_qty: Option<String>,
    #[serde(rename = "maxQty")]
    pub max_qty: Option<String>,
    #[serde(rename = "stepSize")]
    pub step_size: Option<String>,
    #[serde(rename = "minPrice")]
    pub min_price: Option<String>,
    #[serde(rename = "maxPrice")]
    pub max_price: Option<String>,
    #[serde(rename = "tickSize")]
    pub tick_size: Option<String>,
    #[serde(rename = "minNotional")]
    pub min_notional: Option<String>,
}

#[derive(Clone)]
pub struct BinanceClient {
    client: Client,
    config: BinanceConfig,
    rate_limiter: Arc<RateLimiter>,
}

impl BinanceClient {
    pub fn new(config: BinanceConfig) -> Self {
        let client = Client::new();
        let rate_limiter = Arc::new(RateLimiter::new());
        Self { client, config, rate_limiter }
    }

    pub fn get_rate_limiter(&self) -> Arc<RateLimiter> {
        self.rate_limiter.clone()
    }

    async fn make_rate_limited_request(
        &self,
        request_builder: reqwest::RequestBuilder,
        weight: u32,
        is_order: bool,
    ) -> Result<reqwest::Response> {
        // Wait for rate limit
        self.rate_limiter.wait_for_request(weight, is_order).await?;

        // Additional safety delay to prevent rapid-fire requests
        sleep(Duration::from_millis(200)).await;

        // Make the request
        let response = request_builder.send().await?;

        // Update rate limiter with response headers
        self.rate_limiter.update_from_headers(response.headers());

        // Check for rate limit errors
        if response.status() == 429 {
            // Extract retry-after header if present
            let retry_after = response.headers().get("Retry-After").cloned();
            let error_text = response.text().await?;
            warn!("Rate limit exceeded: {}", error_text);
            
            if let Some(retry_after) = retry_after {
                if let Ok(retry_str) = retry_after.to_str() {
                    if let Ok(retry_seconds) = retry_str.parse::<u64>() {
                        warn!("Waiting {} seconds before retry", retry_seconds);
                        sleep(Duration::from_secs(retry_seconds)).await;
                    }
                }
            }
            
            return Err(anyhow!("Rate limit exceeded: {}", error_text));
        }

        if response.status() == 418 {
            let error_text = response.text().await?;
            error!("IP banned: {}", error_text);
            return Err(anyhow!("IP banned: {}", error_text));
        }

        Ok(response)
    }

    fn sign_request(&self, query_string: &str) -> String {
        let mut mac = HmacSha256::new_from_slice(self.config.secret_key.as_bytes())
            .expect("HMAC can take key of any size");
        mac.update(query_string.as_bytes());
        hex::encode(mac.finalize().into_bytes())
    }

    fn get_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }

    pub async fn get_account_info(&self) -> Result<BinanceAccountInfo> {
        let timestamp = Self::get_timestamp();
        let query_string = format!("timestamp={}", timestamp);
        let signature = self.sign_request(&query_string);
        let url = format!("{}/api/v3/account?{}&signature={}", 
            self.config.base_url, query_string, signature);

        let request = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key);

        let response = self.make_rate_limited_request(request, 20, false).await?;

        if response.status().is_success() {
            let account_info: BinanceAccountInfo = response.json().await?;
            Ok(account_info)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get account info: {}", error_text))
        }
    }

    pub async fn get_ticker(&self, symbol: &str) -> Result<BinanceTicker> {
        let url = format!("{}/api/v3/ticker/24hr?symbol={}", self.config.base_url, symbol);
        
        let request = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key);

        let response = self.make_rate_limited_request(request, 2, false).await?;

        if response.status().is_success() {
            let ticker: BinanceTicker = response.json().await?;
            Ok(ticker)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get ticker for {}: {}", symbol, error_text))
        }
    }

    pub async fn get_24hr_ticker(&self, symbol: &str) -> Result<Binance24hrTicker> {
        let url = format!("{}/api/v3/ticker/24hr?symbol={}", self.config.base_url, symbol);
        
        let request = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key);

        let response = self.make_rate_limited_request(request, 2, false).await?;

        if response.status().is_success() {
            let ticker: Binance24hrTicker = response.json().await?;
            Ok(ticker)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get 24hr ticker for {}: {}", symbol, error_text))
        }
    }

    pub async fn get_order_book(&self, symbol: &str, limit: u16) -> Result<BinanceOrderBook> {
        let url = format!("{}/api/v3/depth?symbol={}&limit={}", 
            self.config.base_url, symbol, limit);
        
        // Weight varies by limit: 1-100=5, 101-500=25, 501-1000=50, 1001-5000=250
        let weight = match limit {
            1..=100 => 5,
            101..=500 => 25,
            501..=1000 => 50,
            1001..=5000 => 250,
            _ => 5,
        };

        let request = self.client
            .get(&url)
            .header("X-MBX-APIKEY", &self.config.api_key);

        let response = self.make_rate_limited_request(request, weight, false).await?;

        if response.status().is_success() {
            let order_book: BinanceOrderBook = response.json().await?;
            Ok(order_book)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get order book for {}: {}", symbol, error_text))
        }
    }

    pub async fn place_market_order(&self, symbol: &str, side: &str, quantity: f64) -> Result<BinanceOrder> {
        let timestamp = Self::get_timestamp();
        let query_string = format!(
            "symbol={}&side={}&type=MARKET&quantity={:.8}&timestamp={}",
            symbol, side, quantity, timestamp
        );
        let signature = self.sign_request(&query_string);
        let url = format!("{}/api/v3/order", self.config.base_url);

        let request = self.client
            .post(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .body(format!("{}&signature={}", query_string, signature));

        let response = self.make_rate_limited_request(request, 1, true).await?;

        if response.status().is_success() {
            let order: BinanceOrder = response.json().await?;
            info!("Order placed successfully: {:?}", order);
            Ok(order)
        } else {
            let error_text = response.text().await?;
            error!("Failed to place order: {}", error_text);
            Err(anyhow!("Failed to place order: {}", error_text))
        }
    }

    pub async fn place_limit_order(&self, symbol: &str, side: &str, quantity: f64, price: f64) -> Result<BinanceOrder> {
        let timestamp = Self::get_timestamp();
        let query_string = format!(
            "symbol={}&side={}&type=LIMIT&timeInForce=GTC&quantity={:.8}&price={:.8}&timestamp={}",
            symbol, side, quantity, price, timestamp
        );
        let signature = self.sign_request(&query_string);
        let url = format!("{}/api/v3/order", self.config.base_url);

        let request = self.client
            .post(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .body(format!("{}&signature={}", query_string, signature));

        let response = self.make_rate_limited_request(request, 1, true).await?;

        if response.status().is_success() {
            let order: BinanceOrder = response.json().await?;
            info!("Limit order placed successfully: {:?}", order);
            Ok(order)
        } else {
            let error_text = response.text().await?;
            error!("Failed to place limit order: {}", error_text);
            Err(anyhow!("Failed to place limit order: {}", error_text))
        }
    }

    pub async fn cancel_order(&self, symbol: &str, order_id: u64) -> Result<()> {
        let timestamp = Self::get_timestamp();
        let query_string = format!("symbol={}&orderId={}&timestamp={}", symbol, order_id, timestamp);
        let signature = self.sign_request(&query_string);
        let url = format!("{}/api/v3/order", self.config.base_url);

        let request = self.client
            .delete(&url)
            .header("X-MBX-APIKEY", &self.config.api_key)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .body(format!("{}&signature={}", query_string, signature));

        let response = self.make_rate_limited_request(request, 1, false).await?;

        if response.status().is_success() {
            info!("Order {} cancelled successfully", order_id);
            Ok(())
        } else {
            let error_text = response.text().await?;
            error!("Failed to cancel order {}: {}", order_id, error_text);
            Err(anyhow!("Failed to cancel order {}: {}", order_id, error_text))
        }
    }

    pub async fn get_exchange_info(&self) -> Result<BinanceExchangeInfo> {
        let url = format!("{}/api/v3/exchangeInfo", self.config.base_url);

        let request = self.client.get(&url);
        let response = self.make_rate_limited_request(request, 20, false).await?;

        if response.status().is_success() {
            let exchange_info: BinanceExchangeInfo = response.json().await?;
            Ok(exchange_info)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get exchange info: {}", error_text))
        }
    }

    pub async fn get_all_tickers(&self) -> Result<Vec<BinanceTicker>> {
        let url = format!("{}/api/v3/ticker/24hr", self.config.base_url);

        let request = self.client.get(&url);
        let response = self.make_rate_limited_request(request, 80, false).await?;

        if response.status().is_success() {
            let tickers: Vec<BinanceTicker> = response.json().await?;
            Ok(tickers)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get all tickers: {}", error_text))
        }
    }

    pub async fn get_all_prices(&self) -> Result<Vec<BinancePrice>> {
        let url = format!("{}/api/v3/ticker/price", self.config.base_url);

        let request = self.client.get(&url);
        let response = self.make_rate_limited_request(request, 4, false).await?;

        if response.status().is_success() {
            let prices: Vec<BinancePrice> = response.json().await?;
            Ok(prices)
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to get all prices: {}", error_text))
        }
    }

    pub async fn get_available_trading_pairs(&self) -> Result<Vec<String>> {
        let exchange_info = self.get_exchange_info().await?;
        
        let active_symbols: Vec<String> = exchange_info.symbols
            .into_iter()
            .filter(|symbol| symbol.status == "TRADING" && symbol.is_spot_trading_allowed)
            .map(|symbol| symbol.symbol)
            .collect();
            
        Ok(active_symbols)
    }

    pub async fn get_all_active_tokens(&self) -> Result<Vec<(String, String, String)>> {
        let exchange_info = self.get_exchange_info().await?;
        
        let tokens: Vec<(String, String, String)> = exchange_info.symbols
            .into_iter()
            .filter(|symbol| symbol.status == "TRADING" && symbol.is_spot_trading_allowed)
            .map(|symbol| (symbol.symbol, symbol.base_asset, symbol.quote_asset))
            .collect();
            
        Ok(tokens)
    }

    /// Calculate correct lot size and quantity for an order
    pub async fn calculate_order_quantity(&self, symbol: &str, is_buy: bool, desired_quantity: f64, price: f64) -> Result<f64> {
        let exchange_info = self.get_exchange_info().await?;
        
        if let Some(symbol_info) = exchange_info.symbols.iter().find(|s| s.symbol == symbol) {
            let mut adjusted_quantity = desired_quantity;
            
            // Apply LOT_SIZE filter
            if let Some(lot_filter) = symbol_info.filters.iter().find(|f| f.filter_type == "LOT_SIZE") {
                if let (Some(min_qty_str), Some(step_size_str)) = (&lot_filter.min_qty, &lot_filter.step_size) {
                    let min_qty: f64 = min_qty_str.parse().unwrap_or(0.0);
                    let step_size: f64 = step_size_str.parse().unwrap_or(0.000001);
                    
                    // Ensure quantity meets minimum
                    if adjusted_quantity < min_qty {
                        adjusted_quantity = min_qty;
                    }
                    
                    // Round to step size
                    adjusted_quantity = (adjusted_quantity / step_size).floor() * step_size;
                    
                    // Remove floating point errors
                    let decimals = step_size.to_string().split('.').nth(1).map(|s| s.len()).unwrap_or(0);
                    adjusted_quantity = (adjusted_quantity * 10_f64.powi(decimals as i32)).round() / 10_f64.powi(decimals as i32);
                }
            }
            
            // Apply MIN_NOTIONAL filter
            if let Some(notional_filter) = symbol_info.filters.iter().find(|f| f.filter_type == "MIN_NOTIONAL") {
                if let Some(min_notional_str) = &notional_filter.min_notional {
                    let min_notional: f64 = min_notional_str.parse().unwrap_or(0.0);
                    let notional_value = adjusted_quantity * price;
                    
                    if notional_value < min_notional {
                        adjusted_quantity = (min_notional / price * 1.001).ceil(); // Add 0.1% buffer
                        
                        // Re-apply LOT_SIZE after adjusting for notional
                        if let Some(lot_filter) = symbol_info.filters.iter().find(|f| f.filter_type == "LOT_SIZE") {
                            if let Some(step_size_str) = &lot_filter.step_size {
                                let step_size: f64 = step_size_str.parse().unwrap_or(0.000001);
                                adjusted_quantity = (adjusted_quantity / step_size).ceil() * step_size;
                                
                                let decimals = step_size.to_string().split('.').nth(1).map(|s| s.len()).unwrap_or(0);
                                adjusted_quantity = (adjusted_quantity * 10_f64.powi(decimals as i32)).round() / 10_f64.powi(decimals as i32);
                            }
                        }
                    }
                }
            }
            
            info!("📏 Quantity calculation for {}: {:.8} → {:.8}", symbol, desired_quantity, adjusted_quantity);
            Ok(adjusted_quantity)
        } else {
            Err(anyhow!("Symbol {} not found in exchange info", symbol))
        }
    }

    // Rate limiting utility methods
    pub fn get_rate_limit_status(&self) -> (u32, u32) {
        self.rate_limiter.get_usage_stats()
    }

    pub async fn wait_for_rate_limit_reset(&self) {
        // Wait for all rate limits to reset
        let max_wait = Duration::from_secs(60); // Maximum wait time
        sleep(max_wait).await;
        info!("Rate limit reset wait completed");
    }

    // Batch operations to reduce API calls
    pub async fn get_multiple_tickers(&self, symbols: &[String]) -> Result<Vec<BinanceTicker>> {
        // Use single request for multiple symbols when possible
        if symbols.len() <= 5 {
            let mut results = Vec::new();
            for symbol in symbols {
                match self.get_ticker(symbol).await {
                    Ok(ticker) => results.push(ticker),
                    Err(e) => warn!("Failed to get ticker for {}: {}", symbol, e),
                }
            }
            Ok(results)
        } else {
            // For many symbols, use the all tickers endpoint and filter
            let all_tickers = self.get_all_tickers().await?;
            let symbol_set: std::collections::HashSet<_> = symbols.iter().collect();
            
            let filtered: Vec<BinanceTicker> = all_tickers
                .into_iter()
                .filter(|ticker| symbol_set.contains(&ticker.symbol))
                .collect();
                
            Ok(filtered)
        }
    }

    // Emergency stop - cancel all open orders
    pub async fn emergency_cancel_all_orders(&self, symbol: &str) -> Result<()> {
        warn!("Emergency cancel all orders for symbol: {}", symbol);
        
        // This would require implementing get_open_orders first
        // For now, just log the intent
        error!("Emergency cancel all orders not fully implemented yet");
        
        Ok(())
    }

    /// Check if a symbol is actively trading (market open)
    pub async fn is_market_open(&self, symbol: &str) -> Result<bool> {
        // Get 24hr ticker to check if market is active
        match self.get_ticker(symbol).await {
            Ok(ticker) => {
                let volume: f64 = ticker.volume.parse().unwrap_or(0.0);
                let price_change: f64 = ticker.price_change_percent.parse().unwrap_or(0.0);
                
                // Market is considered open if there's recent volume and price movement
                let is_active = volume > 1000.0 && price_change.abs() > 0.001;
                
                if !is_active {
                    info!("🕐 Market closed or low activity for {}: Volume={:.0}, Change={:.3}%", 
                        symbol, volume, price_change);
                }
                
                Ok(is_active)
            }
            Err(_) => {
                warn!("❌ Cannot check market status for {}", symbol);
                Ok(false) // Assume closed if we can't check
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct LiveMarketData {
    pub symbol: String,
    pub price: f64,
    pub bid: f64,
    pub ask: f64,
    pub volume: f64,
    pub timestamp: u64,
}

pub struct BinanceWebSocketClient {
    config: BinanceConfig,
    data_sender: Sender<LiveMarketData>,
}

impl BinanceWebSocketClient {
    pub fn new(config: BinanceConfig, data_sender: Sender<LiveMarketData>) -> Self {
        Self { config, data_sender }
    }

    pub async fn start_price_stream(&self, symbols: Vec<String>) -> Result<()> {
        let streams: Vec<String> = symbols.iter()
            .map(|s| format!("{}@ticker", s.to_lowercase()))
            .collect();
        let stream_names = streams.join("/");
        let url = format!("{}/stream?streams={}", self.config.ws_url, stream_names);

        info!("Connecting to Binance WebSocket: {}", url);
        let (ws_stream, _) = connect_async(&url).await?;
        let (mut _write, mut read) = ws_stream.split();

        while let Some(message) = read.next().await {
            match message {
                Ok(Message::Text(text)) => {
                    if let Ok(ticker) = serde_json::from_str::<BinanceTicker>(&text) {
                        let market_data = LiveMarketData {
                            symbol: ticker.symbol.clone(),
                            price: ticker.price.parse().unwrap_or(0.0),
                            bid: 0.0, // Will need to get from order book
                            ask: 0.0, // Will need to get from order book
                            volume: ticker.volume.parse().unwrap_or(0.0),
                            timestamp: Self::get_timestamp(),
                        };
                        
                        if let Err(e) = self.data_sender.send(market_data) {
                            error!("Failed to send market data: {}", e);
                        }
                    }
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

        Ok(())
    }

    fn get_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinancePrice {
    pub symbol: String,
    pub price: String,
}
