# advanced_model.py
"""
VictoryBot ML Model for Signal Ranking
- Use scikit-learn RandomForest as a starting point
- Features: volatility, trend, liquidity, past PnL
- To train: use train_model.py with your historical data
- To predict: call predict_scores(signals, analytics, symbol_performance)
"""
import numpy as np
import os
import pickle

MODEL_PATH = os.path.join(os.path.dirname(__file__), "victorybot_rf_model.pkl")


# --- Prediction function for live_bot.py ---
def predict_scores(signals, analytics, symbol_performance=None):
    """
    Args:
        signals: list of symbol strings
        analytics: list of tuples (symbol, volatility, trend, liquidity)
        symbol_performance: dict of {symbol: realized_pnl}
    Returns:
        dict {symbol: score}
    """
    # Load model
    if not os.path.exists(MODEL_PATH):
        # Fallback: simple scoring if no model
        return {s: fallback_score(s, analytics, symbol_performance) for s in signals}
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    # Build feature matrix
    X = []
    for s in signals:
        row = [0, 0, 0, 0]
        for a in analytics:
            if a[0] == s:
                row = [
                    float(a[1]) if isinstance(a[1], (float, int)) else 0,
                    float(a[2]) if isinstance(a[2], (float, int)) else 0,
                    float(a[3]) if isinstance(a[3], (float, int)) else 0,
                    float(symbol_performance.get(s, 0)) if symbol_performance else 0,
                ]
        X.append(row)
    X = np.array(X)
    scores = (
        model.predict_proba(X)[:, 1]
        if hasattr(model, "predict_proba")
        else model.predict(X)
    )
    return {s: float(score) for s, score in zip(signals, scores)}


def fallback_score(s, analytics, symbol_performance=None):
    # Simple rule: higher trend + lower volatility + higher liquidity + past pnl
    for a in analytics:
        if a[0] == s:
            vol = float(a[1]) if isinstance(a[1], (float, int)) else 0.01
            trend = float(a[2]) if isinstance(a[2], (float, int)) else 0
            liq = float(a[3]) if isinstance(a[3], (float, int)) else 0
            pnl = float(symbol_performance.get(s, 0)) if symbol_performance else 0
            return 0.5 * trend - 0.3 * vol + 0.00001 * liq + 0.2 * pnl
    return 0
