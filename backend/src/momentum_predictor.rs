use serde::{Deserialize, Serialize};
use reqwest::Client;
use anyhow::{Result, anyhow};
use tracing::{info, warn, error};
use std::collections::HashMap;
use chrono::{Utc, Duration};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MomentumPrediction {
    pub symbol: String,
    pub current_price: f64,
    pub predicted_price_24h: f64,
    pub predicted_gain_percent: f64,
    pub confidence_score: f64, // 0-100
    pub momentum_strength: f64, // 0-10
    pub volume_surge_factor: f64,
    pub technical_score: f64,
    pub ai_reasoning: String,
    pub entry_recommendation: EntryRecommendation,
    pub risk_level: RiskLevel,
    pub hold_duration_hours: f64,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EntryRecommendation {
    StrongBuy,
    Buy,
    Hold,
    Avoid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    VeryHigh,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalAnalysis {
    pub rsi: f64,
    pub macd_signal: String, // "bullish", "bearish", "neutral"
    pub bollinger_squeeze: bool,
    pub volume_breakout: bool,
    pub support_resistance_level: f64,
    pub fibonacci_level: f64,
    pub momentum_oscillator: f64,
}

pub struct MomentumPredictor {
    client: Client,
    claude_api_key: String,
    prediction_cache: HashMap<String, MomentumPrediction>,
    cache_ttl_seconds: u64,
}

impl MomentumPredictor {
    pub fn new(claude_api_key: String) -> Self {
        Self {
            client: Client::new(),
            claude_api_key,
            prediction_cache: HashMap::new(),
            cache_ttl_seconds: 300, // 5 minutes
        }
    }

    pub async fn predict_high_momentum_tokens(&mut self, symbols: &[String]) -> Result<Vec<MomentumPrediction>> {
        info!("🔮 Analyzing {} tokens for 20-30% momentum opportunities", symbols.len());
        
        let mut predictions = Vec::new();
        let mut batch_symbols = Vec::new();
        
        // Process in batches of 10 to avoid rate limits
        for symbol in symbols {
            batch_symbols.push(symbol.clone());
            
            if batch_symbols.len() >= 10 {
                let batch_predictions = self.analyze_token_batch(&batch_symbols).await?;
                predictions.extend(batch_predictions);
                batch_symbols.clear();
                
                // Rate limiting delay
                tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            }
        }
        
        // Process remaining symbols
        if !batch_symbols.is_empty() {
            let batch_predictions = self.analyze_token_batch(&batch_symbols).await?;
            predictions.extend(batch_predictions);
        }
        
        // Filter for high momentum potential (20%+ predicted gains)
        let high_momentum_tokens: Vec<MomentumPrediction> = predictions
            .into_iter()
            .filter(|p| p.predicted_gain_percent >= 20.0 && p.confidence_score >= 70.0)
            .collect();
        
        info!("🚀 Found {} tokens with 20%+ momentum potential", high_momentum_tokens.len());
        
        Ok(high_momentum_tokens)
    }

    async fn analyze_token_batch(&mut self, symbols: &[String]) -> Result<Vec<MomentumPrediction>> {
        let mut predictions = Vec::new();
        
        for symbol in symbols {
            // Check cache first
            if let Some(cached) = self.get_cached_prediction(symbol) {
                predictions.push(cached);
                continue;
            }
            
            // Get market data
            let market_data = self.fetch_market_data(symbol).await?;
            let technical_analysis = self.calculate_technical_indicators(&market_data).await?;
            
            // Get AI prediction
            let ai_prediction = self.get_ai_momentum_prediction(symbol, &market_data, &technical_analysis).await?;
            
            // Cache the prediction
            self.prediction_cache.insert(symbol.clone(), ai_prediction.clone());
            predictions.push(ai_prediction);
        }
        
        Ok(predictions)
    }

    async fn get_ai_momentum_prediction(
        &self,
        symbol: &str,
        market_data: &MarketData,
        technical: &TechnicalAnalysis,
    ) -> Result<MomentumPrediction> {
        let prompt = format!(
            r#"Analyze this cryptocurrency for 20-30% momentum potential in the next 24-48 hours:

SYMBOL: {}
CURRENT PRICE: ${:.6}
24H CHANGE: {:.2}%
24H VOLUME: ${:.0}
RSI: {:.1}
MACD: {}
BOLLINGER SQUEEZE: {}
VOLUME BREAKOUT: {}

ANALYSIS REQUIREMENTS:
1. Predict if this token can gain 20-30% in next 24-48 hours
2. Provide confidence score (0-100)
3. Identify key momentum catalysts
4. Assess risk level
5. Recommend optimal hold duration

Focus on:
- Volume surge patterns
- Technical breakout signals  
- Market sentiment shifts
- Whale activity indicators
- News/catalyst potential
- Support/resistance levels

Respond with specific price targets and reasoning for 20%+ gains."#,
            symbol,
            market_data.current_price,
            market_data.price_change_24h,
            market_data.volume_24h,
            technical.rsi,
            technical.macd_signal,
            technical.bollinger_squeeze,
            technical.volume_breakout
        );

        let response = self.call_claude_api(&prompt).await?;
        let prediction = self.parse_ai_response(symbol, &response, market_data)?;
        
        Ok(prediction)
    }

    async fn call_claude_api(&self, prompt: &str) -> Result<String> {
        let payload = serde_json::json!({
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 400,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        });

        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.claude_api_key)
            .header("Content-Type", "application/json")
            .header("anthropic-version", "2023-06-01")
            .json(&payload)
            .send()
            .await?;

        if response.status().is_success() {
            let result: serde_json::Value = response.json().await?;
            let content = result["content"][0]["text"]
                .as_str()
                .ok_or_else(|| anyhow!("Invalid response format"))?;
            Ok(content.to_string())
        } else {
            error!("Claude API error: {}", response.status());
            Err(anyhow!("Claude API request failed"))
        }
    }

    fn parse_ai_response(&self, symbol: &str, response: &str, market_data: &MarketData) -> Result<MomentumPrediction> {
        // Parse AI response for key metrics
        let confidence_score = self.extract_confidence_score(response);
        let predicted_gain = self.extract_predicted_gain(response);
        let hold_duration = self.extract_hold_duration(response);
        let risk_level = self.determine_risk_level(response, predicted_gain);
        let entry_recommendation = self.determine_entry_recommendation(confidence_score, predicted_gain);
        
        let predicted_price = market_data.current_price * (1.0 + predicted_gain / 100.0);
        
        Ok(MomentumPrediction {
            symbol: symbol.to_string(),
            current_price: market_data.current_price,
            predicted_price_24h: predicted_price,
            predicted_gain_percent: predicted_gain,
            confidence_score,
            momentum_strength: self.calculate_momentum_strength(market_data),
            volume_surge_factor: market_data.volume_change_24h,
            technical_score: self.calculate_technical_score(market_data),
            ai_reasoning: response.to_string(),
            entry_recommendation,
            risk_level,
            hold_duration_hours: hold_duration,
            timestamp: Utc::now().timestamp() as u64,
        })
    }

    fn extract_confidence_score(&self, response: &str) -> f64 {
        // Look for confidence percentages in the response
        if let Some(captures) = regex::Regex::new(r"confidence[:\s]*(\d+)%?")
            .unwrap()
            .captures(response.to_lowercase().as_str()) 
        {
            captures[1].parse().unwrap_or(50.0)
        } else if response.to_lowercase().contains("high confidence") {
            85.0
        } else if response.to_lowercase().contains("medium confidence") {
            65.0
        } else if response.to_lowercase().contains("low confidence") {
            35.0
        } else {
            50.0
        }
    }

    fn extract_predicted_gain(&self, response: &str) -> f64 {
        // Look for percentage gains in the response
        let gain_regex = regex::Regex::new(r"(\d+(?:\.\d+)?)%?\s*(?:gain|increase|upside)").unwrap();
        
        if let Some(captures) = gain_regex.captures(response.to_lowercase().as_str()) {
            captures[1].parse().unwrap_or(0.0)
        } else if response.to_lowercase().contains("20-30%") || response.to_lowercase().contains("25%") {
            25.0
        } else if response.to_lowercase().contains("strong bullish") {
            22.0
        } else if response.to_lowercase().contains("bullish") {
            15.0
        } else {
            5.0
        }
    }

    fn extract_hold_duration(&self, response: &str) -> f64 {
        if response.to_lowercase().contains("24 hours") || response.to_lowercase().contains("1 day") {
            24.0
        } else if response.to_lowercase().contains("48 hours") || response.to_lowercase().contains("2 days") {
            48.0
        } else if response.to_lowercase().contains("short term") {
            12.0
        } else {
            36.0 // Default 36 hours
        }
    }

    fn determine_risk_level(&self, response: &str, predicted_gain: f64) -> RiskLevel {
        let response_lower = response.to_lowercase();
        
        if response_lower.contains("high risk") || predicted_gain > 35.0 {
            RiskLevel::VeryHigh
        } else if response_lower.contains("medium risk") || predicted_gain > 25.0 {
            RiskLevel::High
        } else if response_lower.contains("moderate risk") || predicted_gain > 15.0 {
            RiskLevel::Medium
        } else {
            RiskLevel::Low
        }
    }

    fn determine_entry_recommendation(&self, confidence: f64, predicted_gain: f64) -> EntryRecommendation {
        if confidence >= 80.0 && predicted_gain >= 25.0 {
            EntryRecommendation::StrongBuy
        } else if confidence >= 70.0 && predicted_gain >= 20.0 {
            EntryRecommendation::Buy
        } else if confidence >= 60.0 && predicted_gain >= 10.0 {
            EntryRecommendation::Hold
        } else {
            EntryRecommendation::Avoid
        }
    }

    fn calculate_momentum_strength(&self, market_data: &MarketData) -> f64 {
        let price_momentum = (market_data.price_change_24h.abs() / 10.0).min(3.0);
        let volume_momentum = (market_data.volume_change_24h / 50.0).min(3.0);
        let volatility_factor = (market_data.volatility / 5.0).min(2.0);
        
        (price_momentum + volume_momentum + volatility_factor).min(10.0)
    }

    fn calculate_technical_score(&self, market_data: &MarketData) -> f64 {
        let mut score = 50.0;
        
        // Price momentum
        if market_data.price_change_24h > 5.0 {
            score += 20.0;
        } else if market_data.price_change_24h > 2.0 {
            score += 10.0;
        }
        
        // Volume surge
        if market_data.volume_change_24h > 100.0 {
            score += 25.0;
        } else if market_data.volume_change_24h > 50.0 {
            score += 15.0;
        }
        
        // Volatility (can be good for momentum)
        if market_data.volatility > 3.0 && market_data.volatility < 8.0 {
            score += 10.0;
        }
        
        score.min(100.0)
    }

    fn get_cached_prediction(&self, symbol: &str) -> Option<MomentumPrediction> {
        if let Some(prediction) = self.prediction_cache.get(symbol) {
            let age = Utc::now().timestamp() as u64 - prediction.timestamp;
            if age < self.cache_ttl_seconds {
                return Some(prediction.clone());
            }
        }
        None
    }

    async fn fetch_market_data(&self, symbol: &str) -> Result<MarketData> {
        // This would integrate with your existing market data fetching
        // For now, return mock data - in real implementation, use your Binance client
        Ok(MarketData {
            symbol: symbol.to_string(),
            current_price: 1.0,
            price_change_24h: 5.0,
            volume_24h: 1000000.0,
            volume_change_24h: 25.0,
            volatility: 4.5,
            market_cap: 100000000.0,
        })
    }

    async fn calculate_technical_indicators(&self, _market_data: &MarketData) -> Result<TechnicalAnalysis> {
        // Mock technical analysis - implement with real TA library
        Ok(TechnicalAnalysis {
            rsi: 65.0,
            macd_signal: "bullish".to_string(),
            bollinger_squeeze: true,
            volume_breakout: true,
            support_resistance_level: 0.95,
            fibonacci_level: 1.05,
            momentum_oscillator: 7.5,
        })
    }

    pub fn get_top_momentum_predictions(&self, count: usize) -> Vec<MomentumPrediction> {
        let mut predictions: Vec<MomentumPrediction> = self.prediction_cache
            .values()
            .cloned()
            .collect();
        
        // Sort by predicted gain * confidence score
        predictions.sort_by(|a, b| {
            let score_a = a.predicted_gain_percent * (a.confidence_score / 100.0);
            let score_b = b.predicted_gain_percent * (b.confidence_score / 100.0);
            score_b.partial_cmp(&score_a).unwrap()
        });
        
        predictions.truncate(count);
        predictions
    }
}

#[derive(Debug, Clone)]
pub struct MarketData {
    pub symbol: String,
    pub current_price: f64,
    pub price_change_24h: f64,
    pub volume_24h: f64,
    pub volume_change_24h: f64,
    pub volatility: f64,
    pub market_cap: f64,
}
