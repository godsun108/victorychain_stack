# train_model.py
"""
Train a RandomForest model for VictoryBot signal ranking.
- Input: CSV file with columns: symbol, volatility, trend, liquidity, pnl, label
- Output: victorybot_rf_model.pkl (saved in this directory)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "victorybot_rf_model.pkl")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train VictoryBot ML model")
    parser.add_argument("--csv", required=True, help="Path to training CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    # Features: volatility, trend, liquidity, pnl
    X = df[["volatility", "trend", "liquidity", "pnl"]].values
    # Label: 1 = good trade, 0 = bad trade
    y = df["label"].values
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"Model trained and saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
