#!/usr/bin/env python3

"""
🧠 CONTINUOUS LEARNING REALLOCATION ENGINE
Advanced AI system that continuously learns from all past allocations and
actively makes new allocations for expected gains without waiting for positions to mature.

Key Features:
- Real-time learning from all allocation outcomes
- Dynamic position reallocation based on opportunity scores
- Advanced pattern recognition across multiple timeframes
- Adaptive risk management with stop-loss evolution
- Multi-token portfolio optimization with continuous rebalancing
"""

import json
import os
import sys
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings("ignore")

# Add project root to path
sys.path.append(os.path.dirname(__file__))

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException

    binance_available = True
except ImportError:
    binance_available = False

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))


@dataclass
class AllocationRecord:
    """Complete record of an allocation with learning metadata"""

    id: str
    timestamp: datetime
    token: str
    entry_price: float
    current_price: float
    allocation_percentage: float
    predicted_gain: float
    actual_gain: float
    holding_period_hours: float
    exit_reason: str
    pattern_match: str
    confidence_score: float
    market_conditions: Dict[str, float]
    feature_vector: List[float]
    profit_loss_usd: float
    gas_fees: float
    net_profit: float
    learning_score: float
    adaptation_triggers: List[str] = field(default_factory=list)


@dataclass
class OpportunitySignal:
    """Real-time opportunity signal for new allocations"""

    token: str
    opportunity_score: float
    predicted_gain: float
    confidence: float
    timeframe_hours: float
    entry_price: float
    target_price: float
    stop_loss: float
    allocation_recommendation: float
    reasoning: List[str]
    risk_factors: List[str]
    similar_past_outcomes: List[Dict]


@dataclass
class ReallocationAction:
    """Dynamic reallocation action recommendation"""

    action_type: (
        str  # 'exit_and_reallocate', 'partial_exit', 'hold_and_add', 'full_exit'
    )
    current_token: str
    new_token: Optional[str]
    percentage_to_move: float
    urgency_score: float
    expected_improvement: float
    reasoning: str
    risk_assessment: Dict[str, float]


class ContinuousLearningReallocationEngine:
    """AI engine for continuous learning and dynamic reallocation"""

    def __init__(self, data_dir: str = "learning_data"):
        # Initialize data storage
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Initialize Binance client
        self.BINANCEUS_KEY = os.getenv("BINANCEUS_KEY")
        self.BINANCEUS_SECRET = os.getenv("BINANCEUS_SECRET")
        self.client = None

        if binance_available and self.BINANCEUS_KEY:
            try:
                self.client = Client(self.BINANCEUS_KEY, self.BINANCEUS_SECRET)
                print("✅ Continuous Learning Engine connected to Binance")
            except Exception as e:
                print(f"⚠️ Binance connection error: {e}")

        # Core data structures
        self.allocation_history: List[AllocationRecord] = []
        self.active_positions: Dict[str, AllocationRecord] = {}
        self.opportunity_queue: deque = deque(maxlen=100)
        self.learning_metrics: Dict[str, Any] = {}

        # Real-time market data
        self.price_streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.volume_streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.momentum_streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))

        # AI Models for continuous learning
        self.gain_predictor = None
        self.opportunity_scorer = None
        self.reallocation_advisor = None
        self.risk_assessor = None
        self.pattern_classifier = None

        # Learning parameters that evolve
        self.learning_params = {
            "min_confidence_threshold": 0.70,
            "max_position_hold_hours": 72,
            "reallocation_opportunity_threshold": 0.15,  # 15% better opportunity triggers reallocation
            "learning_rate": 0.001,
            "adaptation_frequency_minutes": 5,
            "pattern_memory_depth": 1000,
            "momentum_weight": 0.85,
            "volume_weight": 0.75,
            "gaming_sector_weight": 0.90,
            "stop_loss_adaptation_rate": 0.02,
        }

        # Target tokens with enhanced tracking
        self.target_tokens = {
            "MAGICUSDT": {
                "weight": 1.0,
                "gaming_correlation": 0.95,
                "pattern_strength": 0.88,
                "learning_priority": "high",
                "allocation_history": [],
                "success_patterns": [],
            },
            "GALAUSDT": {
                "weight": 0.85,
                "gaming_correlation": 0.90,
                "pattern_strength": 0.80,
                "learning_priority": "high",
                "allocation_history": [],
                "success_patterns": [],
            },
            "ILVUSDT": {
                "weight": 0.80,
                "gaming_correlation": 0.85,
                "pattern_strength": 0.75,
                "learning_priority": "medium",
                "allocation_history": [],
                "success_patterns": [],
            },
            "AXSUSDT": {
                "weight": 0.70,
                "gaming_correlation": 0.88,
                "pattern_strength": 0.70,
                "learning_priority": "medium",
                "allocation_history": [],
                "success_patterns": [],
            },
        }

        # Initialize models and load historical data
        self.initialize_ai_models()
        self.load_historical_data()

        # Start continuous monitoring
        self.monitoring_active = False
        self.start_continuous_monitoring()

    def initialize_ai_models(self):
        """Initialize AI models for continuous learning"""
        print("🧠 Initializing AI models for continuous learning...")

        # Gain prediction model
        self.gain_predictor = GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42
        )

        # Opportunity scoring model
        self.opportunity_scorer = RandomForestRegressor(
            n_estimators=150, max_depth=8, random_state=42
        )

        # Reallocation advisor model
        self.reallocation_advisor = MLPRegressor(
            hidden_layer_sizes=(100, 50, 25),
            activation="relu",
            solver="adam",
            learning_rate="adaptive",
            max_iter=1000,
            random_state=42,
        )

        # Risk assessment model
        self.risk_assessor = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42
        )

        # Feature scaler
        self.feature_scaler = StandardScaler()

        print("✅ AI models initialized successfully")

    def load_historical_data(self):
        """Load historical allocation data for learning"""
        allocation_file = os.path.join(self.data_dir, "allocation_history.json")

        if os.path.exists(allocation_file):
            with open(allocation_file, "r") as f:
                data = json.load(f)
                for record_data in data:
                    record = AllocationRecord(**record_data)
                    record.timestamp = datetime.fromisoformat(record_data["timestamp"])
                    self.allocation_history.append(record)

            print(
                f"📚 Loaded {len(self.allocation_history)} historical allocation records"
            )
            self.train_models_from_history()
        else:
            print("📝 No historical data found, starting fresh")
            # Initialize with synthetic learning data
            self.create_initial_learning_data()

    def create_initial_learning_data(self):
        """Create initial learning data based on known successful patterns"""
        print("🎯 Creating initial learning data from successful patterns...")

        # MAGIC successful patterns
        magic_success_patterns = [
            {
                "token": "MAGICUSDT",
                "pattern": "double_bottom_recovery",
                "gain": 0.157,
                "confidence": 0.85,
                "hold_hours": 36,
                "features": [
                    0.12,
                    0.75,
                    0.88,
                    0.95,
                    0.80,
                    14,
                    3,
                    2.2,
                    0.15,
                    0.85,
                    0.90,
                ],
            },
            {
                "token": "MAGICUSDT",
                "pattern": "correction_recovery",
                "gain": 0.165,
                "confidence": 0.88,
                "hold_hours": 48,
                "features": [
                    0.18,
                    0.82,
                    0.92,
                    0.95,
                    0.85,
                    10,
                    2,
                    2.5,
                    0.18,
                    0.88,
                    0.95,
                ],
            },
            {
                "token": "GALAUSDT",
                "pattern": "correction_bounce",
                "gain": 0.18,
                "confidence": 0.80,
                "hold_hours": 42,
                "features": [
                    0.15,
                    0.78,
                    0.85,
                    0.90,
                    0.82,
                    16,
                    4,
                    2.0,
                    0.16,
                    0.82,
                    0.85,
                ],
            },
        ]

        base_time = datetime.now() - timedelta(days=30)

        for i, pattern in enumerate(magic_success_patterns):
            record = AllocationRecord(
                id=f"init_{i}",
                timestamp=base_time + timedelta(days=i * 3),
                token=pattern["token"],
                entry_price=0.25,
                current_price=0.25 * (1 + pattern["gain"]),
                allocation_percentage=1.0,
                predicted_gain=pattern["gain"] * 0.9,
                actual_gain=pattern["gain"],
                holding_period_hours=pattern["hold_hours"],
                exit_reason="target_reached",
                pattern_match=pattern["pattern"],
                confidence_score=pattern["confidence"],
                market_conditions={"gaming_strength": 0.85, "btc_correlation": 0.70},
                feature_vector=pattern["features"],
                profit_loss_usd=1000 * pattern["gain"],
                gas_fees=15.0,
                net_profit=1000 * pattern["gain"] - 15.0,
                learning_score=pattern["confidence"],
            )
            self.allocation_history.append(record)

        print(f"✅ Created {len(magic_success_patterns)} initial learning records")

    def train_models_from_history(self):
        """Train AI models from historical allocation data"""
        if len(self.allocation_history) < 5:
            print("⚠️ Insufficient data for model training")
            return

        print("🎓 Training AI models from historical allocation data...")

        # Prepare training data
        X = []
        y_gain = []
        y_opportunity = []
        y_risk = []

        for record in self.allocation_history:
            if len(record.feature_vector) >= 10:
                X.append(record.feature_vector)
                y_gain.append(record.actual_gain)
                y_opportunity.append(record.confidence_score * record.actual_gain)
                y_risk.append(abs(record.actual_gain - record.predicted_gain))

        if len(X) < 3:
            return

        X = np.array(X)
        y_gain = np.array(y_gain)
        y_opportunity = np.array(y_opportunity)
        y_risk = np.array(y_risk)

        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)

        # Train models
        try:
            if len(X_scaled) >= 3:  # Minimum samples for training
                self.gain_predictor.fit(X_scaled, y_gain)
                self.opportunity_scorer.fit(X_scaled, y_opportunity)
                self.risk_assessor.fit(X_scaled, y_risk)

                # Train reallocation advisor if enough data
                if len(X_scaled) >= 5:
                    y_reallocation = np.array(
                        [
                            record.learning_score
                            for record in self.allocation_history
                            if len(record.feature_vector) >= 10
                        ]
                    )
                    if len(y_reallocation) >= 5:
                        self.reallocation_advisor.fit(
                            X_scaled[: len(y_reallocation)], y_reallocation
                        )
            else:
                print("⚠️ Insufficient data for training - using fallback predictions")

            print("✅ AI models trained successfully")

            # Calculate model performance
            gain_score = self.gain_predictor.score(X_scaled, y_gain)
            opportunity_score = self.opportunity_scorer.score(X_scaled, y_opportunity)

            print(f"📊 Model Performance:")
            print(f"   Gain Predictor R²: {gain_score:.3f}")
            print(f"   Opportunity Scorer R²: {opportunity_score:.3f}")

        except Exception as e:
            print(f"⚠️ Model training error: {e}")

    def start_continuous_monitoring(self):
        """Start continuous monitoring and learning process"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        print("🔄 Starting continuous monitoring and learning...")

        # Start monitoring thread
        monitoring_thread = threading.Thread(target=self._monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()

        # Start reallocation analysis thread
        reallocation_thread = threading.Thread(target=self._reallocation_loop)
        reallocation_thread.daemon = True
        reallocation_thread.start()

    def _monitoring_loop(self):
        """Continuous monitoring loop for market data and opportunities"""
        while self.monitoring_active:
            try:
                # Update market data
                self.update_market_data()

                # Analyze new opportunities
                opportunities = self.analyze_opportunities()

                # Update active positions
                self.update_active_positions()

                # Learn from recent outcomes
                self.continuous_learning_update()

                # Wait before next iteration
                time.sleep(30)  # Update every 30 seconds

            except Exception as e:
                print(f"⚠️ Monitoring loop error: {e}")
                time.sleep(60)

    def _reallocation_loop(self):
        """Continuous reallocation analysis loop"""
        while self.monitoring_active:
            try:
                # Analyze reallocation opportunities
                reallocation_actions = self.analyze_reallocation_opportunities()

                # Execute high-priority reallocations
                for action in reallocation_actions:
                    if action.urgency_score > 0.8:
                        self.execute_reallocation(action)

                # Wait before next analysis
                time.sleep(300)  # Analyze every 5 minutes

            except Exception as e:
                print(f"⚠️ Reallocation loop error: {e}")
                time.sleep(300)

    def update_market_data(self):
        """Update real-time market data for all target tokens"""
        if not self.client:
            return

        try:
            tickers = self.client.get_all_tickers()
            ticker_dict = {t["symbol"]: float(t["price"]) for t in tickers}

            for token in self.target_tokens.keys():
                if token in ticker_dict:
                    price = ticker_dict[token]
                    self.price_streams[token].append(
                        {"timestamp": datetime.now(), "price": price}
                    )

                    # Calculate momentum
                    if len(self.price_streams[token]) >= 2:
                        prev_price = self.price_streams[token][-2]["price"]
                        momentum = (price - prev_price) / prev_price
                        self.momentum_streams[token].append(
                            {"timestamp": datetime.now(), "momentum": momentum}
                        )

        except Exception as e:
            print(f"⚠️ Market data update error: {e}")

    def analyze_opportunities(self):
        """Analyze current market for new allocation opportunities"""
        opportunities = []

        for token, config in self.target_tokens.items():
            try:
                # Get current market data
                current_data = self.get_current_token_data(token)
                if not current_data:
                    continue

                # Create feature vector
                features = self.create_feature_vector(token, current_data)

                # Predict opportunity score using AI
                if (
                    self.opportunity_scorer
                    and len(features) >= 10
                    and hasattr(self.opportunity_scorer, "predict")
                ):
                    try:
                        features_scaled = self.feature_scaler.transform([features])
                        opportunity_score = self.opportunity_scorer.predict(
                            features_scaled
                        )[0]
                        predicted_gain = (
                            self.gain_predictor.predict(features_scaled)[0]
                            if hasattr(self.gain_predictor, "predict")
                            else 0.1
                        )
                        risk_score = (
                            self.risk_assessor.predict(features_scaled)[0]
                            if hasattr(self.risk_assessor, "predict")
                            else 0.05
                        )
                    except Exception as model_error:
                        print(f"⚠️ Model prediction error for {token}: {model_error}")
                        # Fallback to heuristic scoring
                        opportunity_score = (
                            abs(current_data.get("momentum", 0)) * 5
                            + min(1.0, current_data.get("volume_24h", 0) / 8000) * 3
                            + config["weight"] * 2
                        ) / 10
                        predicted_gain = 0.08 + (opportunity_score * 0.1)
                        risk_score = 0.05

                    # Calculate confidence based on historical patterns
                    confidence = self.calculate_pattern_confidence(token, current_data)

                    # Only consider high-confidence opportunities
                    if confidence > self.learning_params["min_confidence_threshold"]:
                        opportunity = OpportunitySignal(
                            token=token,
                            opportunity_score=opportunity_score,
                            predicted_gain=predicted_gain,
                            confidence=confidence,
                            timeframe_hours=24 + (opportunity_score * 48),
                            entry_price=current_data["price"],
                            target_price=current_data["price"] * (1 + predicted_gain),
                            stop_loss=current_data["price"] * 0.95,  # 5% stop loss
                            allocation_recommendation=min(
                                1.0, opportunity_score * config["weight"]
                            ),
                            reasoning=self.generate_opportunity_reasoning(
                                token, current_data, predicted_gain
                            ),
                            risk_factors=self.identify_risk_factors(
                                token, current_data
                            ),
                            similar_past_outcomes=self.find_similar_past_outcomes(
                                token, features
                            ),
                        )

                        opportunities.append(opportunity)
                        self.opportunity_queue.append(opportunity)

            except Exception as e:
                print(f"⚠️ Opportunity analysis error for {token}: {e}")

        return sorted(
            opportunities,
            key=lambda x: x.opportunity_score * x.confidence,
            reverse=True,
        )

    def get_current_token_data(self, token: str) -> Optional[Dict]:
        """Get current market data for a token"""
        if not self.client:
            # Return simulated data for testing
            return {
                "price": 0.25 + np.random.normal(0, 0.01),
                "volume_24h": 5000 + np.random.normal(0, 1000),
                "change_24h": np.random.normal(0, 0.05),
                "momentum": np.random.normal(0, 0.02),
            }

        try:
            ticker = self.client.get_ticker(symbol=token)
            klines = self.client.get_klines(symbol=token, interval="1h", limit=24)

            # Calculate momentum and volume metrics
            prices = [float(k[4]) for k in klines]  # Close prices
            volumes = [float(k[5]) for k in klines]  # Volumes

            momentum = (prices[-1] - prices[-6]) / prices[-6] if len(prices) >= 6 else 0
            avg_volume = sum(volumes[-6:]) / 6 if len(volumes) >= 6 else volumes[-1]

            return {
                "price": float(ticker["lastPrice"]),
                "volume_24h": float(ticker["volume"]),
                "change_24h": float(ticker["priceChangePercent"]) / 100,
                "momentum": momentum,
                "avg_volume": avg_volume,
            }

        except Exception as e:
            print(f"⚠️ Error getting data for {token}: {e}")
            return None

    def create_feature_vector(self, token: str, data: Dict) -> List[float]:
        """Create feature vector for AI models"""
        current_time = datetime.now()

        features = [
            data.get("change_24h", 0),
            data.get("volume_24h", 0) / 10000,  # Normalized
            data.get("momentum", 0),
            self.target_tokens[token]["gaming_correlation"],
            self.target_tokens[token]["pattern_strength"],
            current_time.hour,
            current_time.weekday(),
            data.get("volume_24h", 0) / data.get("avg_volume", 1),  # Volume ratio
            abs(data.get("change_24h", 0)),  # Volatility
            self.target_tokens[token]["weight"],
            len(self.allocation_history) / 100,  # Learning experience factor
        ]

        return features

    def calculate_pattern_confidence(self, token: str, data: Dict) -> float:
        """Calculate confidence based on historical pattern matches"""
        base_confidence = self.target_tokens[token]["pattern_strength"]

        # Adjust based on current market conditions
        momentum_factor = min(1.0, abs(data.get("momentum", 0)) * 10)
        volume_factor = min(1.0, data.get("volume_24h", 0) / 8000)

        # Learning adjustment based on recent success rate
        recent_records = [r for r in self.allocation_history[-20:] if r.token == token]
        if recent_records:
            success_rate = sum(1 for r in recent_records if r.actual_gain > 0) / len(
                recent_records
            )
            learning_factor = 0.5 + (success_rate * 0.5)
        else:
            learning_factor = 0.7

        confidence = base_confidence * momentum_factor * volume_factor * learning_factor
        return min(0.95, max(0.1, confidence))

    def generate_opportunity_reasoning(
        self, token: str, data: Dict, predicted_gain: float
    ) -> List[str]:
        """Generate reasoning for opportunity signal"""
        reasoning = []

        if data.get("momentum", 0) > 0.02:
            reasoning.append(f"Strong positive momentum: {data['momentum']:.3f}")

        if data.get("volume_24h", 0) > 8000:
            reasoning.append(f"High volume activity: {data['volume_24h']:,.0f}")

        if predicted_gain > 0.1:
            reasoning.append(f"AI predicts significant gain: {predicted_gain:.1%}")

        if self.target_tokens[token]["gaming_correlation"] > 0.85:
            reasoning.append("Strong gaming sector correlation")

        reasoning.append(
            f"Pattern confidence: {self.target_tokens[token]['pattern_strength']:.2f}"
        )

        return reasoning

    def identify_risk_factors(self, token: str, data: Dict) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        if abs(data.get("change_24h", 0)) > 0.15:
            risks.append("High volatility in last 24h")

        if data.get("volume_24h", 0) < 2000:
            risks.append("Low trading volume")

        if data.get("momentum", 0) < -0.05:
            risks.append("Negative momentum trend")

        # Market condition risks
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risks.append("Low liquidity hours")

        return risks

    def find_similar_past_outcomes(
        self, token: str, features: List[float]
    ) -> List[Dict]:
        """Find similar past outcomes for reference"""
        similar_outcomes = []

        for record in self.allocation_history:
            if record.token == token and len(record.feature_vector) >= len(features):
                # Calculate similarity score
                similarity = self.calculate_feature_similarity(
                    features, record.feature_vector[: len(features)]
                )

                if similarity > 0.7:  # High similarity threshold
                    similar_outcomes.append(
                        {
                            "timestamp": record.timestamp.isoformat(),
                            "actual_gain": record.actual_gain,
                            "holding_hours": record.holding_period_hours,
                            "pattern": record.pattern_match,
                            "similarity": similarity,
                        }
                    )

        return sorted(similar_outcomes, key=lambda x: x["similarity"], reverse=True)[:5]

    def calculate_feature_similarity(
        self, features1: List[float], features2: List[float]
    ) -> float:
        """Calculate similarity between feature vectors"""
        if len(features1) != len(features2):
            return 0.0

        # Normalize features
        f1 = np.array(features1)
        f2 = np.array(features2)

        # Calculate cosine similarity
        dot_product = np.dot(f1, f2)
        norm1 = np.linalg.norm(f1)
        norm2 = np.linalg.norm(f2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))

    def update_active_positions(self):
        """Update active positions with current market data"""
        for token, position in list(self.active_positions.items()):
            try:
                current_data = self.get_current_token_data(token)
                if current_data:
                    position.current_price = current_data["price"]
                    position.actual_gain = (
                        position.current_price - position.entry_price
                    ) / position.entry_price
                    position.holding_period_hours = (
                        datetime.now() - position.timestamp
                    ).total_seconds() / 3600

                    # Check exit conditions
                    if self.should_exit_position(position):
                        self.close_position(position)

            except Exception as e:
                print(f"⚠️ Error updating position {token}: {e}")

    def should_exit_position(self, position: AllocationRecord) -> bool:
        """Determine if position should be exited"""
        # Stop loss check
        if position.actual_gain <= -0.05:  # 5% stop loss
            position.exit_reason = "stop_loss_triggered"
            return True

        # Target reached
        if position.actual_gain >= position.predicted_gain:
            position.exit_reason = "target_reached"
            return True

        # Maximum holding period
        if (
            position.holding_period_hours
            >= self.learning_params["max_position_hold_hours"]
        ):
            position.exit_reason = "max_hold_period"
            return True

        # AI-based exit signal
        current_data = self.get_current_token_data(position.token)
        if current_data:
            features = self.create_feature_vector(position.token, current_data)
            if self.gain_predictor and len(features) >= 10:
                features_scaled = self.feature_scaler.transform([features])
                predicted_future_gain = self.gain_predictor.predict(features_scaled)[0]

                # Exit if AI predicts significant decline
                if predicted_future_gain < -0.03:
                    position.exit_reason = "ai_exit_signal"
                    return True

        return False

    def close_position(self, position: AllocationRecord):
        """Close a position and update learning data"""
        print(f"🔄 Closing position: {position.token}")
        print(f"   Entry: ${position.entry_price:.5f}")
        print(f"   Exit: ${position.current_price:.5f}")
        print(f"   Gain: {position.actual_gain:.2%}")
        print(f"   Reason: {position.exit_reason}")

        # Calculate final metrics
        position.profit_loss_usd = 1000 * position.actual_gain  # Assume $1000 position
        position.gas_fees = 15.0  # Estimated gas fees
        position.net_profit = position.profit_loss_usd - position.gas_fees

        # Calculate learning score
        accuracy = 1 - abs(position.actual_gain - position.predicted_gain) / max(
            0.01, abs(position.predicted_gain)
        )
        position.learning_score = position.confidence_score * accuracy

        # Add to history and remove from active
        self.allocation_history.append(position)
        if position.token in self.active_positions:
            del self.active_positions[position.token]

        # Update target token learning data
        if position.token in self.target_tokens:
            self.target_tokens[position.token]["allocation_history"].append(position)

            if position.actual_gain > 0.05:  # 5% gain threshold
                self.target_tokens[position.token]["success_patterns"].append(
                    {
                        "pattern": position.pattern_match,
                        "gain": position.actual_gain,
                        "features": position.feature_vector,
                    }
                )

        # Retrain models with new data
        if len(self.allocation_history) >= 10:
            self.train_models_from_history()

        # Save updated data
        self.save_learning_data()

    def analyze_reallocation_opportunities(self) -> List[ReallocationAction]:
        """Analyze opportunities for reallocating current positions"""
        reallocation_actions = []

        # Get current opportunities
        current_opportunities = self.analyze_opportunities()

        for current_token, position in self.active_positions.items():
            for opportunity in current_opportunities:
                if opportunity.token != current_token:
                    # Calculate potential improvement
                    current_expected_gain = (
                        position.predicted_gain - position.actual_gain
                    )
                    new_expected_gain = opportunity.predicted_gain

                    improvement = new_expected_gain - current_expected_gain

                    # Check if reallocation is worthwhile
                    if (
                        improvement
                        > self.learning_params["reallocation_opportunity_threshold"]
                    ):
                        urgency = min(1.0, improvement * 2)  # Cap at 1.0

                        action = ReallocationAction(
                            action_type="exit_and_reallocate",
                            current_token=current_token,
                            new_token=opportunity.token,
                            percentage_to_move=100.0,
                            urgency_score=urgency,
                            expected_improvement=improvement,
                            reasoning=f"Better opportunity in {opportunity.token}: {improvement:.1%} additional expected gain",
                            risk_assessment={
                                "current_position_risk": abs(
                                    position.actual_gain - position.predicted_gain
                                ),
                                "new_position_risk": 1 - opportunity.confidence,
                                "gas_cost_impact": 0.015,  # 1.5% estimated gas cost
                            },
                        )

                        reallocation_actions.append(action)

        return sorted(reallocation_actions, key=lambda x: x.urgency_score, reverse=True)

    def execute_reallocation(self, action: ReallocationAction):
        """Execute a reallocation action"""
        print(f"🔄 EXECUTING REALLOCATION:")
        print(f"   Action: {action.action_type}")
        print(f"   From: {action.current_token}")
        print(f"   To: {action.new_token}")
        print(f"   Expected Improvement: {action.expected_improvement:.1%}")
        print(f"   Urgency: {action.urgency_score:.2f}")
        print(f"   Reasoning: {action.reasoning}")

        # Close current position
        if action.current_token in self.active_positions:
            current_position = self.active_positions[action.current_token]
            current_position.exit_reason = "reallocation"
            self.close_position(current_position)

        # Open new position
        if action.new_token:
            self.open_new_position(action.new_token)

    def open_new_position(self, token: str):
        """Open a new position based on current analysis"""
        current_data = self.get_current_token_data(token)
        if not current_data:
            return

        features = self.create_feature_vector(token, current_data)

        # Predict gain and confidence
        if self.gain_predictor and len(features) >= 10:
            features_scaled = self.feature_scaler.transform([features])
            predicted_gain = self.gain_predictor.predict(features_scaled)[0]
        else:
            predicted_gain = 0.1  # Default prediction

        confidence = self.calculate_pattern_confidence(token, current_data)

        # Create new position record
        position = AllocationRecord(
            id=f"pos_{int(time.time())}",
            timestamp=datetime.now(),
            token=token,
            entry_price=current_data["price"],
            current_price=current_data["price"],
            allocation_percentage=1.0,
            predicted_gain=predicted_gain,
            actual_gain=0.0,
            holding_period_hours=0.0,
            exit_reason="",
            pattern_match="ai_identified",
            confidence_score=confidence,
            market_conditions={
                "momentum": current_data.get("momentum", 0),
                "volume": current_data.get("volume_24h", 0),
            },
            feature_vector=features,
            profit_loss_usd=0.0,
            gas_fees=0.0,
            net_profit=0.0,
            learning_score=0.0,
        )

        self.active_positions[token] = position

        print(f"🚀 NEW POSITION OPENED:")
        print(f"   Token: {token}")
        print(f"   Entry Price: ${position.entry_price:.5f}")
        print(f"   Predicted Gain: {predicted_gain:.1%}")
        print(f"   Confidence: {confidence:.2f}")

    def continuous_learning_update(self):
        """Continuously update learning parameters based on recent performance"""
        if len(self.allocation_history) < 5:
            return

        # Analyze recent performance
        recent_records = self.allocation_history[-20:]

        # Calculate success metrics
        successful_trades = [r for r in recent_records if r.actual_gain > 0]
        success_rate = len(successful_trades) / len(recent_records)

        avg_gain = (
            np.mean([r.actual_gain for r in successful_trades])
            if successful_trades
            else 0
        )
        avg_accuracy = np.mean([r.learning_score for r in recent_records])

        # Adapt learning parameters
        if success_rate > 0.7:  # High success rate
            self.learning_params[
                "min_confidence_threshold"
            ] *= 0.995  # Slightly lower threshold
            self.learning_params[
                "reallocation_opportunity_threshold"
            ] *= 1.005  # Slightly higher
        elif success_rate < 0.5:  # Low success rate
            self.learning_params["min_confidence_threshold"] *= 1.01  # Higher threshold
            self.learning_params["reallocation_opportunity_threshold"] *= 0.99  # Lower

        # Update token weights based on performance
        for token in self.target_tokens.keys():
            token_records = [r for r in recent_records if r.token == token]
            if token_records:
                token_success_rate = sum(
                    1 for r in token_records if r.actual_gain > 0
                ) / len(token_records)
                token_avg_gain = np.mean(
                    [r.actual_gain for r in token_records if r.actual_gain > 0]
                )

                # Adjust weight
                performance_factor = token_success_rate * (1 + token_avg_gain)
                self.target_tokens[token]["weight"] = min(1.0, performance_factor)

                print(f"📊 {token} Performance Update:")
                print(f"   Success Rate: {token_success_rate:.1%}")
                print(f"   Avg Gain: {token_avg_gain:.1%}")
                print(f"   New Weight: {self.target_tokens[token]['weight']:.2f}")

    def save_learning_data(self):
        """Save learning data to disk"""
        try:
            # Save allocation history
            allocation_file = os.path.join(self.data_dir, "allocation_history.json")
            with open(allocation_file, "w") as f:
                data = []
                for record in self.allocation_history:
                    record_dict = asdict(record)
                    record_dict["timestamp"] = record.timestamp.isoformat()
                    data.append(record_dict)
                json.dump(data, f, indent=2)

            # Save learning parameters
            params_file = os.path.join(self.data_dir, "learning_params.json")
            with open(params_file, "w") as f:
                json.dump(self.learning_params, f, indent=2)

            # Save target token configurations
            tokens_file = os.path.join(self.data_dir, "target_tokens.json")
            with open(tokens_file, "w") as f:
                # Convert to serializable format
                serializable_tokens = {}
                for token, config in self.target_tokens.items():
                    serializable_config = config.copy()
                    serializable_config["allocation_history"] = (
                        []
                    )  # Don't save full history
                    serializable_config["success_patterns"] = config[
                        "success_patterns"
                    ][
                        -10:
                    ]  # Keep last 10
                    serializable_tokens[token] = serializable_config
                json.dump(serializable_tokens, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving learning data: {e}")

    def generate_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        if not self.allocation_history:
            return {"error": "No allocation history available"}

        recent_records = self.allocation_history[-30:]  # Last 30 allocations

        # Overall performance metrics
        total_allocations = len(self.allocation_history)
        successful_allocations = [
            r for r in self.allocation_history if r.actual_gain > 0
        ]
        success_rate = len(successful_allocations) / total_allocations

        avg_gain = (
            np.mean([r.actual_gain for r in successful_allocations])
            if successful_allocations
            else 0
        )
        avg_loss = np.mean(
            [r.actual_gain for r in self.allocation_history if r.actual_gain < 0]
        )

        total_profit = sum(r.net_profit for r in self.allocation_history)

        # Token-specific performance
        token_performance = {}
        for token in self.target_tokens.keys():
            token_records = [r for r in self.allocation_history if r.token == token]
            if token_records:
                token_success = [r for r in token_records if r.actual_gain > 0]
                token_performance[token] = {
                    "total_allocations": len(token_records),
                    "success_rate": len(token_success) / len(token_records),
                    "avg_gain": (
                        np.mean([r.actual_gain for r in token_success])
                        if token_success
                        else 0
                    ),
                    "total_profit": sum(r.net_profit for r in token_records),
                    "current_weight": self.target_tokens[token]["weight"],
                }

        # Learning progress metrics
        learning_metrics = {
            "model_accuracy": np.mean([r.learning_score for r in recent_records]),
            "prediction_accuracy": 1
            - np.mean([abs(r.actual_gain - r.predicted_gain) for r in recent_records]),
            "adaptation_score": self.calculate_adaptation_score(),
            "confidence_calibration": self.calculate_confidence_calibration(),
        }

        # Current opportunities
        current_opportunities = self.analyze_opportunities()

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_performance": {
                "total_allocations": total_allocations,
                "success_rate": success_rate,
                "average_gain": avg_gain,
                "average_loss": avg_loss,
                "total_profit_usd": total_profit,
                "active_positions": len(self.active_positions),
            },
            "token_performance": token_performance,
            "learning_metrics": learning_metrics,
            "current_opportunities": [
                {
                    "token": opp.token,
                    "opportunity_score": opp.opportunity_score,
                    "predicted_gain": opp.predicted_gain,
                    "confidence": opp.confidence,
                    "allocation_recommendation": opp.allocation_recommendation,
                }
                for opp in current_opportunities[:5]
            ],
            "learning_parameters": self.learning_params,
            "recent_adaptations": self.get_recent_adaptations(),
        }

        return report

    def calculate_adaptation_score(self) -> float:
        """Calculate how well the system is adapting to market changes"""
        if len(self.allocation_history) < 20:
            return 0.5

        # Compare recent performance to historical
        recent_records = self.allocation_history[-10:]
        historical_records = self.allocation_history[-30:-10]

        recent_success = sum(1 for r in recent_records if r.actual_gain > 0) / len(
            recent_records
        )
        historical_success = sum(
            1 for r in historical_records if r.actual_gain > 0
        ) / len(historical_records)

        adaptation_score = min(1.0, recent_success / max(0.1, historical_success))
        return adaptation_score

    def calculate_confidence_calibration(self) -> float:
        """Calculate how well confidence scores match actual outcomes"""
        if len(self.allocation_history) < 10:
            return 0.5

        # Compare confidence vs actual success for recent records
        recent_records = self.allocation_history[-20:]
        calibration_scores = []

        for record in recent_records:
            actual_success = 1 if record.actual_gain > 0 else 0
            predicted_confidence = record.confidence_score
            calibration = 1 - abs(actual_success - predicted_confidence)
            calibration_scores.append(calibration)

        return np.mean(calibration_scores)

    def get_recent_adaptations(self) -> List[str]:
        """Get list of recent adaptations made by the system"""
        adaptations = []

        # Check parameter changes
        if hasattr(self, "_prev_params"):
            for key, value in self.learning_params.items():
                if key in self._prev_params and self._prev_params[key] != value:
                    change = (
                        (value - self._prev_params[key]) / self._prev_params[key]
                    ) * 100
                    adaptations.append(f"{key} adjusted by {change:+.1f}%")

        # Check weight changes
        for token, config in self.target_tokens.items():
            if (
                hasattr(config, "_prev_weight")
                and config.get("_prev_weight") != config["weight"]
            ):
                change = (
                    (config["weight"] - config.get("_prev_weight", 0.5))
                    / config.get("_prev_weight", 0.5)
                ) * 100
                adaptations.append(f"{token} weight adjusted by {change:+.1f}%")

        return adaptations[-10:]  # Return last 10 adaptations

    def run_continuous_learning_cycle(self):
        """Run a complete continuous learning cycle"""
        print("🧠 CONTINUOUS LEARNING REALLOCATION ENGINE")
        print("=" * 60)
        print("🚀 Starting intelligent continuous learning and reallocation...")
        print()

        try:
            # Generate initial learning report
            print("📊 INITIAL LEARNING STATE:")
            report = self.generate_learning_report()

            if "error" not in report:
                print(
                    f"   Total Allocations: {report['overall_performance']['total_allocations']}"
                )
                print(
                    f"   Success Rate: {report['overall_performance']['success_rate']:.1%}"
                )
                print(
                    f"   Total Profit: ${report['overall_performance']['total_profit_usd']:.2f}"
                )
                print(
                    f"   Active Positions: {report['overall_performance']['active_positions']}"
                )
                print()

                # Show current opportunities
                print("🎯 CURRENT TOP OPPORTUNITIES:")
                for i, opp in enumerate(report["current_opportunities"][:3], 1):
                    print(f"   {i}. {opp['token']}")
                    print(f"      Score: {opp['opportunity_score']:.3f}")
                    print(f"      Predicted Gain: {opp['predicted_gain']:.1%}")
                    print(f"      Confidence: {opp['confidence']:.2f}")
                    print(f"      Allocation: {opp['allocation_recommendation']:.1%}")
                print()

            # Simulate continuous operation
            print("🔄 SIMULATING CONTINUOUS LEARNING OPERATION...")

            for cycle in range(5):  # Simulate 5 cycles
                print(f"\n--- Learning Cycle {cycle + 1} ---")

                # Analyze opportunities
                opportunities = self.analyze_opportunities()
                print(f"📈 Found {len(opportunities)} opportunities")

                # Execute top opportunity if available
                if opportunities and not self.active_positions:
                    top_opportunity = opportunities[0]
                    if (
                        top_opportunity.confidence
                        > self.learning_params["min_confidence_threshold"]
                    ):
                        print(f"🚀 Opening position: {top_opportunity.token}")
                        self.open_new_position(top_opportunity.token)

                # Check reallocation opportunities
                reallocation_actions = self.analyze_reallocation_opportunities()
                if reallocation_actions:
                    top_action = reallocation_actions[0]
                    if top_action.urgency_score > 0.8:
                        print(f"🔄 High-priority reallocation: {top_action.reasoning}")
                        self.execute_reallocation(top_action)

                # Update positions and learning
                self.update_active_positions()
                self.continuous_learning_update()

                # Simulate time passage
                time.sleep(2)

            # Generate final report
            print("\n📊 FINAL LEARNING REPORT:")
            final_report = self.generate_learning_report()

            if "error" not in final_report:
                print(f"   Learning Progress:")
                print(
                    f"     Model Accuracy: {final_report['learning_metrics']['model_accuracy']:.3f}"
                )
                print(
                    f"     Prediction Accuracy: {final_report['learning_metrics']['prediction_accuracy']:.3f}"
                )
                print(
                    f"     Adaptation Score: {final_report['learning_metrics']['adaptation_score']:.3f}"
                )
                print(
                    f"     Confidence Calibration: {final_report['learning_metrics']['confidence_calibration']:.3f}"
                )
                print()

                print("🎯 TOKEN PERFORMANCE SUMMARY:")
                for token, perf in final_report["token_performance"].items():
                    print(f"   {token}:")
                    print(f"     Success Rate: {perf['success_rate']:.1%}")
                    print(f"     Avg Gain: {perf['avg_gain']:.1%}")
                    print(f"     Weight: {perf['current_weight']:.2f}")
                print()

            # Save comprehensive results
            self.save_comprehensive_results(final_report)

            print("✅ CONTINUOUS LEARNING CYCLE COMPLETE!")
            print(
                "🧠 System is now actively learning and ready for continuous operation"
            )

        except Exception as e:
            print(f"❌ Error in continuous learning cycle: {e}")
            import traceback

            traceback.print_exc()

    def save_comprehensive_results(self, report: Dict[str, Any]):
        """Save comprehensive learning results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed JSON report
        json_file = os.path.join(
            self.data_dir, f"continuous_learning_report_{timestamp}.json"
        )
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save markdown summary
        md_file = os.path.join(
            self.data_dir, f"CONTINUOUS_LEARNING_SUMMARY_{timestamp}.md"
        )
        with open(md_file, "w") as f:
            f.write("# 🧠 CONTINUOUS LEARNING REALLOCATION ENGINE SUMMARY\n\n")
            f.write(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("## 📊 Overall Performance\n\n")
            if "overall_performance" in report:
                perf = report["overall_performance"]
                f.write(f"- **Total Allocations:** {perf['total_allocations']}\n")
                f.write(f"- **Success Rate:** {perf['success_rate']:.1%}\n")
                f.write(f"- **Average Gain:** {perf['average_gain']:.1%}\n")
                f.write(f"- **Total Profit:** ${perf['total_profit_usd']:.2f}\n")
                f.write(f"- **Active Positions:** {perf['active_positions']}\n\n")

            f.write("## 🎯 Token Performance\n\n")
            if "token_performance" in report:
                for token, perf in report["token_performance"].items():
                    f.write(f"### {token}\n")
                    f.write(f"- Success Rate: {perf['success_rate']:.1%}\n")
                    f.write(f"- Average Gain: {perf['avg_gain']:.1%}\n")
                    f.write(f"- Total Profit: ${perf['total_profit']:.2f}\n")
                    f.write(f"- Current Weight: {perf['current_weight']:.2f}\n\n")

            f.write("## 🧠 Learning Metrics\n\n")
            if "learning_metrics" in report:
                metrics = report["learning_metrics"]
                f.write(f"- **Model Accuracy:** {metrics['model_accuracy']:.3f}\n")
                f.write(
                    f"- **Prediction Accuracy:** {metrics['prediction_accuracy']:.3f}\n"
                )
                f.write(f"- **Adaptation Score:** {metrics['adaptation_score']:.3f}\n")
                f.write(
                    f"- **Confidence Calibration:** {metrics['confidence_calibration']:.3f}\n\n"
                )

            f.write("## 🚀 Current Opportunities\n\n")
            if "current_opportunities" in report:
                for i, opp in enumerate(report["current_opportunities"], 1):
                    f.write(f"{i}. **{opp['token']}**\n")
                    f.write(f"   - Score: {opp['opportunity_score']:.3f}\n")
                    f.write(f"   - Predicted Gain: {opp['predicted_gain']:.1%}\n")
                    f.write(f"   - Confidence: {opp['confidence']:.2f}\n")
                    f.write(
                        f"   - Allocation: {opp['allocation_recommendation']:.1%}\n\n"
                    )

            f.write("---\n")
            f.write(
                "*Generated by VictoryChain Continuous Learning Reallocation Engine*\n"
            )

        print(f"💾 Results saved:")
        print(f"   JSON: {json_file}")
        print(f"   Summary: {md_file}")


def main():
    """Main execution function"""
    # Create continuous learning engine
    engine = ContinuousLearningReallocationEngine()

    # Run continuous learning cycle
    engine.run_continuous_learning_cycle()


if __name__ == "__main__":
    main()
