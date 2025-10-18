use serde::{Deserialize, Serialize};
use reqwest::Client;
use anyhow::{Result, anyhow};
use tracing::{info, warn, error, debug};
use std::collections::HashMap;
use crate::binance::{BinanceClient, BinanceTicker};

/// AI-powered token analysis using Claude/Hugging Face APIs
#[derive(Debug, Clone)]
pub struct AITokenAnalyzer {
    client: Client,
    huggingface_api_key: Option<String>,
    claude_api_key: Option<String>,
    analysis_cache: HashMap<String, AIAnalysisResult>,
    cache_ttl: u64, // seconds
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenAnalysisData {
    pub symbol: String,
    pub price_change_24h: f64,
    pub volume_24h: f64,
    pub price: f64,
    pub market_cap_rank: Option<u32>,
    pub volume_change: f64,
    pub price_volatility: f64,
    pub technical_indicators: TechnicalIndicators,
    pub market_sentiment: f64, // -1 to 1
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TechnicalIndicators {
    pub rsi: f64,
    pub macd_signal: f64,
    pub bollinger_position: f64, // 0-1, where 0.5 is middle band
    pub volume_profile: f64,
    pub momentum_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIAnalysisResult {
    pub symbol: String,
    pub ai_score: f64, // 0-100, AI confidence in momentum
    pub predicted_direction: String, // "bullish", "bearish", "neutral"
    pub risk_level: f64, // 0-1
    pub hold_duration_hours: f64,
    pub confidence: f64, // 0-1
    pub reasoning: String,
    pub timestamp: u64,
}

#[derive(Debug, Serialize, Deserialize)]
struct HuggingFaceRequest {
    inputs: String,
    parameters: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize)]
struct HuggingFaceResponse {
    generated_text: Option<String>,
    score: Option<f64>,
    label: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    messages: Vec<ClaudeMessage>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeResponse {
    content: Vec<ClaudeContent>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeContent {
    #[serde(rename = "type")]
    content_type: String,
    text: String,
}

impl AITokenAnalyzer {
    pub fn new() -> Self {
        let client = Client::new();
        
        // Try to get API keys from environment
        let huggingface_api_key = std::env::var("HUGGINGFACE_API_KEY").ok();
        let claude_api_key = std::env::var("CLAUDE_API_KEY").ok();
        
        if huggingface_api_key.is_none() && claude_api_key.is_none() {
            warn!("⚠️ No AI API keys found. AI analysis will use advanced technical analysis fallback.");
            warn!("   Set HUGGINGFACE_API_KEY or CLAUDE_API_KEY environment variables for full AI features.");
        } else {
            info!("🤖 AI analyzer initialized with available API keys");
        }
        
        Self {
            client,
            huggingface_api_key,
            claude_api_key,
            analysis_cache: HashMap::new(),
            cache_ttl: 300, // 5 minutes cache
        }
    }

    /// Analyze all tokens and return top AI-recommended picks
    pub async fn analyze_all_tokens(&mut self, binance_client: &BinanceClient) -> Result<Vec<AIAnalysisResult>> {
        info!("🤖 Starting AI-powered analysis of all Binance US tokens...");
        
        // Get all tickers from Binance
        let tickers = binance_client.get_all_tickers().await?;
        let mut analysis_results = Vec::new();
        
        // Filter to USDT pairs only
        let usdt_tickers: Vec<_> = tickers.into_iter()
            .filter(|t| t.symbol.ends_with("USDT") && t.symbol != "USDCUSDT")
            .collect();
        
        info!("🔍 Analyzing {} USDT trading pairs with AI...", usdt_tickers.len());
        
        // Analyze tokens in batches to avoid rate limits
        let batch_size = 10;
        for chunk in usdt_tickers.chunks(batch_size) {
            let mut batch_analyses = Vec::new();
            
            for ticker in chunk {
                match self.analyze_single_token(ticker, binance_client).await {
                    Ok(analysis) => {
                        batch_analyses.push(analysis);
                    }
                    Err(e) => {
                        debug!("Failed to analyze {}: {}", ticker.symbol, e);
                    }
                }
                
                // Small delay to respect API limits
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
            
            analysis_results.extend(batch_analyses);
            
            // Longer delay between batches
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }
        
        // Sort by AI score (highest first)
        analysis_results.sort_by(|a, b| b.ai_score.partial_cmp(&a.ai_score).unwrap_or(std::cmp::Ordering::Equal));
        
        info!("🎯 AI Analysis Complete! Top 5 recommendations:");
        for (i, result) in analysis_results.iter().take(5).enumerate() {
            info!("   {}. {} - AI Score: {:.1}/100 ({}) - Risk: {:.1}/10", 
                i+1, result.symbol, result.ai_score, result.predicted_direction, result.risk_level * 10.0);
        }
        
        Ok(analysis_results)
    }

    async fn analyze_single_token(&mut self, ticker: &BinanceTicker, binance_client: &BinanceClient) -> Result<AIAnalysisResult> {
        // Check cache first
        let current_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs();
            
        if let Some(cached) = self.analysis_cache.get(&ticker.symbol) {
            if current_time - cached.timestamp < self.cache_ttl {
                return Ok(cached.clone());
            }
        }
        
        // Prepare token data for AI analysis
        let token_data = self.prepare_token_data(ticker, binance_client).await?;
        
        // Try different AI services
        let analysis = if let Some(result) = self.analyze_with_claude(&token_data).await? {
            result
        } else if let Some(result) = self.analyze_with_huggingface(&token_data).await? {
            result
        } else {
            // Fallback to traditional technical analysis
            self.fallback_technical_analysis(&token_data).await?
        };
        
        // Cache the result
        self.analysis_cache.insert(ticker.symbol.clone(), analysis.clone());
        
        Ok(analysis)
    }

    async fn prepare_token_data(&self, ticker: &BinanceTicker, _binance_client: &BinanceClient) -> Result<TokenAnalysisData> {
        let price_change_24h: f64 = ticker.price_change_percent.parse().unwrap_or(0.0);
        let volume_24h: f64 = ticker.volume.parse().unwrap_or(0.0);
        let price: f64 = ticker.price.parse().unwrap_or(0.0);
        
        // Calculate technical indicators
        let technical_indicators = TechnicalIndicators {
            rsi: self.calculate_rsi(&ticker.symbol).await.unwrap_or(50.0),
            macd_signal: if price_change_24h > 0.0 { 1.0 } else { -1.0 },
            bollinger_position: 0.5, // Simplified
            volume_profile: (volume_24h / 1000000.0).min(1.0), // Normalize
            momentum_score: price_change_24h / 100.0,
        };
        
        Ok(TokenAnalysisData {
            symbol: ticker.symbol.clone(),
            price_change_24h,
            volume_24h,
            price,
            market_cap_rank: None,
            volume_change: 0.0, // Would need historical data
            price_volatility: price_change_24h.abs() / 100.0,
            technical_indicators,
            market_sentiment: (price_change_24h / 100.0).max(-1.0).min(1.0),
        })
    }

    async fn analyze_with_claude(&self, token_data: &TokenAnalysisData) -> Result<Option<AIAnalysisResult>> {
        let api_key = match &self.claude_api_key {
            Some(key) => key,
            None => return Ok(None),
        };

        let prompt = format!(
            "Analyze this cryptocurrency token for momentum trading potential:
            
Symbol: {}
24h Price Change: {:.2}%
24h Volume: ${:.0}
Current Price: ${:.8}
RSI: {:.1}
Market Sentiment: {:.2}
Volatility: {:.2}%

Please provide:
1. AI confidence score (0-100) for bullish momentum in next 1-6 hours
2. Predicted direction (bullish/bearish/neutral)  
3. Risk level (0.0-1.0)
4. Recommended hold duration in hours
5. Brief reasoning

Respond in JSON format:
{{
  \"ai_score\": 85.5,
  \"predicted_direction\": \"bullish\",
  \"risk_level\": 0.3,
  \"hold_duration_hours\": 2.5,
  \"confidence\": 0.8,
  \"reasoning\": \"Strong momentum with high volume support\"
}}",
            token_data.symbol,
            token_data.price_change_24h,
            token_data.volume_24h,
            token_data.price,
            token_data.technical_indicators.rsi,
            token_data.market_sentiment,
            token_data.price_volatility * 100.0
        );

        let request = ClaudeRequest {
            model: "claude-3-5-sonnet-20241022".to_string(),
            max_tokens: 500,
            messages: vec![
                ClaudeMessage {
                    role: "user".to_string(),
                    content: prompt,
                }
            ],
        };

        let response = self.client
            .post("https://api.anthropic.com/v1/messages")
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Content-Type", "application/json")
            .header("anthropic-version", "2023-06-01")
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            warn!("Claude API error: {}", response.status());
            return Ok(None);
        }

        let claude_response: ClaudeResponse = response.json().await?;
        
        if let Some(content) = claude_response.content.first() {
            // Try to parse JSON from the response
            if let Ok(analysis_data) = serde_json::from_str::<serde_json::Value>(&content.text) {
                return Ok(Some(AIAnalysisResult {
                    symbol: token_data.symbol.clone(),
                    ai_score: analysis_data["ai_score"].as_f64().unwrap_or(50.0),
                    predicted_direction: analysis_data["predicted_direction"].as_str().unwrap_or("neutral").to_string(),
                    risk_level: analysis_data["risk_level"].as_f64().unwrap_or(0.5),
                    hold_duration_hours: analysis_data["hold_duration_hours"].as_f64().unwrap_or(1.0),
                    confidence: analysis_data["confidence"].as_f64().unwrap_or(0.5),
                    reasoning: analysis_data["reasoning"].as_str().unwrap_or("AI analysis").to_string(),
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs(),
                }));
            }
        }

        Ok(None)
    }

    async fn analyze_with_huggingface(&self, token_data: &TokenAnalysisData) -> Result<Option<AIAnalysisResult>> {
        let api_key = match &self.huggingface_api_key {
            Some(key) => key,
            None => return Ok(None),
        };

        let prompt = format!(
            "Cryptocurrency Analysis: {} - Price Change: {:.2}%, Volume: ${:.0}, RSI: {:.1}. 
             Predict if this token will have bullish momentum in the next 1-6 hours. 
             Consider: market sentiment, volume, technical indicators. 
             Rate confidence 0-100.",
            token_data.symbol,
            token_data.price_change_24h,
            token_data.volume_24h,
            token_data.technical_indicators.rsi
        );

        let mut parameters = HashMap::new();
        parameters.insert("max_new_tokens".to_string(), serde_json::Value::Number(serde_json::Number::from(200)));
        parameters.insert("temperature".to_string(), serde_json::Value::Number(serde_json::Number::from_f64(0.1).unwrap()));

        let request = HuggingFaceRequest {
            inputs: prompt,
            parameters,
        };

        let response = self.client
            .post("https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium")
            .header("Authorization", format!("Bearer {}", api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            warn!("HuggingFace API error: {}", response.status());
            return Ok(None);
        }

        let hf_response: Vec<HuggingFaceResponse> = response.json().await?;
        
        if let Some(result) = hf_response.first() {
            if let Some(generated_text) = &result.generated_text {
                // Simple parsing of generated text for momentum signals
                let text_lower = generated_text.to_lowercase();
                let bullish_score = if text_lower.contains("bullish") || text_lower.contains("buy") || text_lower.contains("positive") {
                    75.0
                } else if text_lower.contains("bearish") || text_lower.contains("sell") || text_lower.contains("negative") {
                    25.0
                } else {
                    50.0
                };

                return Ok(Some(AIAnalysisResult {
                    symbol: token_data.symbol.clone(),
                    ai_score: bullish_score,
                    predicted_direction: if bullish_score > 60.0 { "bullish" } else if bullish_score < 40.0 { "bearish" } else { "neutral" }.to_string(),
                    risk_level: token_data.price_volatility,
                    hold_duration_hours: 2.0,
                    confidence: 0.6,
                    reasoning: format!("HuggingFace analysis: {}", generated_text.chars().take(100).collect::<String>()),
                    timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs(),
                }));
            }
        }

        Ok(None)
    }

    async fn fallback_technical_analysis(&self, token_data: &TokenAnalysisData) -> Result<AIAnalysisResult> {
        // Advanced technical analysis as fallback
        let mut score: f64 = 50.0;
        
        // Price momentum component (40% weight)
        if token_data.price_change_24h > 5.0 {
            score += 20.0;
        } else if token_data.price_change_24h > 1.0 {
            score += 10.0;
        } else if token_data.price_change_24h < -5.0 {
            score -= 20.0;
        }
        
        // Volume component (30% weight)  
        if token_data.volume_24h > 1000000.0 {
            score += 15.0;
        } else if token_data.volume_24h > 100000.0 {
            score += 8.0;
        }
        
        // RSI component (20% weight)
        let rsi = token_data.technical_indicators.rsi;
        if rsi > 70.0 {
            score -= 5.0; // Overbought
        } else if rsi < 30.0 {
            score += 10.0; // Oversold opportunity
        } else if rsi > 50.0 && rsi < 70.0 {
            score += 5.0; // Healthy uptrend
        }
        
        // Volatility adjustment (10% weight)
        if token_data.price_volatility > 0.1 {
            score -= 5.0; // Too volatile
        } else if token_data.price_volatility > 0.05 {
            score += 2.0; // Good volatility for momentum
        }
        
        score = score.max(0.0).min(100.0);
        
        let direction = if score > 65.0 {
            "bullish"
        } else if score < 35.0 {
            "bearish"
        } else {
            "neutral"
        };
        
        Ok(AIAnalysisResult {
            symbol: token_data.symbol.clone(),
            ai_score: score,
            predicted_direction: direction.to_string(),
            risk_level: token_data.price_volatility,
            hold_duration_hours: if score > 75.0 { 4.0 } else { 1.5 },
            confidence: 0.7,
            reasoning: format!("Technical analysis: momentum {:.1}%, volume ${:.0}, RSI {:.1}", 
                token_data.price_change_24h, token_data.volume_24h, rsi),
            timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs(),
        })
    }

    async fn calculate_rsi(&self, _symbol: &str) -> Result<f64> {
        // Simplified RSI calculation - in production, you'd use historical price data
        Ok(50.0 + (rand::random::<f64>() - 0.5) * 40.0) // Random RSI for demo
    }

    pub fn get_top_ai_picks(&self, analyses: &[AIAnalysisResult], limit: usize) -> Vec<AIAnalysisResult> {
        let mut sorted = analyses.to_vec();
        sorted.sort_by(|a, b| {
            // Sort by AI score with risk adjustment
            let score_a = a.ai_score * (1.0 - a.risk_level * 0.3);
            let score_b = b.ai_score * (1.0 - b.risk_level * 0.3);
            score_b.partial_cmp(&score_a).unwrap_or(std::cmp::Ordering::Equal)
        });
        
        sorted.into_iter()
            .filter(|a| a.predicted_direction == "bullish" && a.ai_score > 60.0)
            .take(limit)
            .collect()
    }
}
