use nalgebra::{DMatrix, DVector};
use statrs::distribution::{Normal, ContinuousCDF, Continuous};

// ALL EQUATIONS MODULE

/// Kelly fraction: f* = (μ − r_f) / σ²
pub fn kelly_fraction(mu: f64, r_f: f64, sigma2: f64) -> f64 {
    (mu - r_f) / sigma2
}

/// Risk-Parity weights: solve minimize ∑_{i≠j} w_i w_j Cov[i,j]
/// subject to ∑ w_i = 1, w_i ≥ 0
pub fn risk_parity_weights(cov: &DMatrix<f64>) -> DVector<f64> {
    let n = cov.nrows();
    let mut weights = DVector::from_element(n, 1.0 / n as f64);
    
    // Simple equal-risk contribution approximation
    for _ in 0..100 {
        let mut new_weights = DVector::zeros(n);
        for i in 0..n {
            let vol_contrib = (cov.row(i) * &weights)[0];
            new_weights[i] = 1.0 / vol_contrib.sqrt();
        }
        new_weights /= new_weights.sum();
        weights = new_weights;
    }
    weights
}

/// Black-Scholes Greeks:
/// d1 = (ln(S/K) + (r + σ²/2)T) / (σ sqrt(T))
/// d2 = d1 − σ sqrt(T)
/// Δ = N(d1), Γ = N'(d1)/(Sσ√T), Vega = S N'(d1) √T
pub struct BSGreeks { 
    pub delta: f64, 
    pub gamma: f64, 
    pub vega: f64,
    pub theta: f64 
}

pub fn black_scholes_greeks(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> BSGreeks {
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    
    let normal = Normal::new(0.0, 1.0).unwrap();
    let n_d1 = normal.cdf(d1);
    let n_prime_d1 = normal.pdf(d1);
    
    BSGreeks {
        delta: n_d1,
        gamma: n_prime_d1 / (s * sigma * sqrt_t),
        vega: s * n_prime_d1 * sqrt_t / 100.0, // Divide by 100 for 1% move
        theta: -(s * n_prime_d1 * sigma / (2.0 * sqrt_t) + r * k * (-r * t).exp() * normal.cdf(d2)) / 365.0,
    }
}

/// GARCH(1,1) update: σ²_t = α₀ + α₁ ε²_{t−1} + β₁ σ²_{t−1}
pub fn garch_next(alpha0: f64, alpha1: f64, beta1: f64, eps2_prev: f64, sigma2_prev: f64) -> f64 {
    alpha0 + alpha1 * eps2_prev + beta1 * sigma2_prev
}

/// Z-score calculation for statistical arbitrage
pub fn z_score(spread: f64, mean: f64, std: f64) -> f64 {
    (spread - mean) / std
}

/// Value at Risk calculation
pub fn var_95(portfolio_std: f64) -> f64 {
    let z_95 = 1.645; // 95% confidence interval
    z_95 * portfolio_std
}
