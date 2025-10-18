use crate::math::var_95;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Risk Manager equations:
// VaR_95 = z_{0.95} * portfolio_std
// health_factor = equity / required_margin
// Circuit breaker: if drawdown ≥ threshold, halt all trading.

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskConfig {
    pub max_drawdown: f64,
    pub var_limit: f64,
    pub max_position_size: f64,
    pub health_factor_min: f64,
}

pub struct RiskManager {
    config: RiskConfig,
    positions: HashMap<String, f64>,
    pnl_history: Vec<f64>,
    total_equity: f64,
    required_margin: f64,
    trading_halted: bool,
}

impl RiskManager {
    pub fn new(config: RiskConfig) -> Self {
        Self {
            config,
            positions: HashMap::new(),
            pnl_history: Vec::new(),
            total_equity: 100000.0, // Starting with $100k
            required_margin: 0.0,
            trading_halted: false,
        }
    }

    /// Calculate portfolio VaR at 95% confidence
    pub fn calculate_var(&self) -> f64 {
        if self.pnl_history.len() < 2 {
            return 0.0;
        }

        let mean_pnl = self.pnl_history.iter().sum::<f64>() / self.pnl_history.len() as f64;
        let variance = self.pnl_history
            .iter()
            .map(|&x| (x - mean_pnl).powi(2))
            .sum::<f64>() / (self.pnl_history.len() - 1) as f64;
        
        let portfolio_std = variance.sqrt();
        var_95(portfolio_std)
    }

    /// Calculate health factor: equity / required_margin
    pub fn health_factor(&self) -> f64 {
        if self.required_margin == 0.0 {
            f64::INFINITY
        } else {
            self.total_equity / self.required_margin
        }
    }

    /// Check if current drawdown exceeds threshold
    pub fn check_drawdown(&mut self) -> bool {
        if self.pnl_history.is_empty() {
            return false;
        }

        let peak = self.pnl_history.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
        let current = *self.pnl_history.last().unwrap();
        let drawdown = (peak - current) / peak;

        if drawdown >= self.config.max_drawdown {
            self.trading_halted = true;
            println!("🚨 Circuit breaker triggered! Drawdown: {:.2}%", drawdown * 100.0);
            true
        } else {
            false
        }
    }

    /// Validate if a trade meets risk criteria
    pub fn validate_trade(&self, symbol: &str, size: f64) -> bool {
        if self.trading_halted {
            return false;
        }

        // Check position size limits
        let current_position = self.positions.get(symbol).unwrap_or(&0.0);
        let new_position = current_position + size;
        
        if new_position.abs() > self.config.max_position_size {
            println!("⚠️ Position size limit exceeded for {}", symbol);
            return false;
        }

        // Check health factor
        if self.health_factor() < self.config.health_factor_min {
            println!("⚠️ Health factor too low: {:.2}", self.health_factor());
            return false;
        }

        // Check VaR limit
        let current_var = self.calculate_var();
        if current_var > self.config.var_limit {
            println!("⚠️ VaR limit exceeded: {:.2}", current_var);
            return false;
        }

        true
    }

    /// Update position and risk metrics
    pub fn update_position(&mut self, symbol: &str, size: f64, pnl: f64) {
        *self.positions.entry(symbol.to_string()).or_insert(0.0) += size;
        self.pnl_history.push(pnl);
        self.total_equity += pnl;
        
        // Keep only last 252 days of PnL history (rolling window)
        if self.pnl_history.len() > 252 {
            self.pnl_history.remove(0);
        }

        self.check_drawdown();
    }

    pub fn is_trading_halted(&self) -> bool {
        self.trading_halted
    }

    pub fn resume_trading(&mut self) {
        self.trading_halted = false;
        println!("✅ Trading resumed");
    }
}
