"""
victory_bot/strategies/ml_signals.py
Pluggable ML/AI model interface for trading signals.
"""

from typing import List


class MLSignals:
    def __init__(self, model=None):
        self.model = model

    def get_signals(self, features) -> List[str]:
        if self.model is None:
            return []
        return self.model.predict(features)
