use serde::{Deserialize, Serialize};
use std::fs;
use crate::exchange::ExchangeConfig;
use crate::risk::RiskConfig;

// Parse config.toml (no equations here)

#[derive(Debug, Deserialize, Serialize)]
pub struct Config {
    pub poll_ms: u64,
    pub exchange_endpoint: String,
    pub risk_free_rate: f64,
    pub exchange: ExchangeConfig,
    pub risk: RiskConfig,
    pub basis_arb: BasisArbConfig,
    pub theta: ThetaHarvestConfig,
    pub stat_arb: StatArbConfig,
    pub yield_loop: YieldLoopConfig,
    pub ai: AIConfig,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct BasisArbConfig {
    pub min_apr: f64,
    pub max_position_size: f64,
    pub funding_threshold: f64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct ThetaHarvestConfig {
    pub delta_target: f64,
    pub gamma_limit: f64,
    pub vega_limit: f64,
    pub theta_threshold: f64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct StatArbConfig {
    pub z_entry: f64,
    pub z_exit: f64,
    pub lookback_period: usize,
    pub pairs: Vec<String>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct YieldLoopConfig {
    pub min_net_apr: f64,
    pub leverage_ratio: f64,
    pub rebalance_threshold: f64,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct AIConfig {
    pub enabled: bool,
    pub primary_strategy: String,
    pub ai_score_threshold: f64,
    pub confidence_threshold: f64,
    pub analysis_interval: u64,
    pub cache_ttl: u64,
    pub fallback_to_traditional: bool,
    pub max_hold_duration_hours: Option<f64>,
    pub min_momentum_threshold: Option<f64>,
    pub profit_target: Option<f64>,
    pub stop_loss: Option<f64>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            poll_ms: 500,
            exchange_endpoint: "https://api.binance.com".to_string(),
            risk_free_rate: 0.01,
            exchange: ExchangeConfig {
                endpoint: "https://api.binance.us".to_string(),
                fee_rate: 0.001,
                max_position_size: 10.0,
                live_trading: false, // Set to true for live trading
                symbols: vec!["BTCUSDT".to_string(), "ETHUSDT".to_string(), "SOLUSDT".to_string()],
            },
            risk: RiskConfig {
                max_drawdown: 0.2,
                var_limit: 10000.0,
                max_position_size: 100000.0,
                health_factor_min: 1.5,
            },
            basis_arb: BasisArbConfig {
                min_apr: 0.05,
                max_position_size: 50000.0,
                funding_threshold: 0.01,
            },
            theta: ThetaHarvestConfig {
                delta_target: 0.0,
                gamma_limit: 0.1,
                vega_limit: 1000.0,
                theta_threshold: -10.0,
            },
            stat_arb: StatArbConfig {
                z_entry: 2.0,
                z_exit: 0.5,
                lookback_period: 60,
                pairs: vec!["BTC/ETH".to_string(), "BTC/SOL".to_string()],
            },
            yield_loop: YieldLoopConfig {
                min_net_apr: 0.03,
                leverage_ratio: 2.0,
                rebalance_threshold: 0.05,
            },
            ai: AIConfig {
                enabled: true,
                primary_strategy: "ai_enhanced".to_string(),
                ai_score_threshold: 75.0,
                confidence_threshold: 0.7,
                analysis_interval: 300,
                cache_ttl: 600,
                fallback_to_traditional: true,
                max_hold_duration_hours: Some(24.0),
                min_momentum_threshold: Some(3.0),
                profit_target: Some(0.15),
                stop_loss: Some(0.08),
            },
        }
    }
}

impl Default for AIConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            primary_strategy: "ai_enhanced".to_string(),
            ai_score_threshold: 75.0,
            confidence_threshold: 0.7,
            analysis_interval: 300,
            cache_ttl: 600,
            fallback_to_traditional: true,
            max_hold_duration_hours: Some(24.0),
            min_momentum_threshold: Some(3.0),
            profit_target: Some(0.15),
            stop_loss: Some(0.08),
        }
    }
}

pub fn load(path: &str) -> Config {
    match fs::read_to_string(path) {
        Ok(contents) => {
            toml::from_str(&contents).unwrap_or_else(|e| {
                println!("⚠️ Error parsing config: {}. Using defaults.", e);
                Config::default()
            })
        },
        Err(_) => {
            println!("⚠️ Config file not found. Using defaults.");
            Config::default()
        }
    }
}
