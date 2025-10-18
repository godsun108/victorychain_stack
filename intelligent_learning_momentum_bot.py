#!/usr/bin/env python3

"""
🧠 INTELLIGENT LEARNING MOMENTUM BOT
Advanced AI that learns what to do and uses all learned analysis as parameters
Continuously adapts and improves based on outcomes and market feedback
"""

import json
import os
import sys
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import uuid
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import random
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import pickle

# Add project root to path
sys.path.append(os.path.dirname(__file__))

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    binance_available = True
except ImportError:
    binance_available = False

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

@dataclass
class TokenAnalysis:
    """Comprehensive token analysis with learning metadata"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    momentum_score: float
    pattern_match: str
    confidence: float
    target_gain: float
    risk_level: str
    gaming_correlation: float
    learning_weight: float
    ai_prediction: float
    feature_vector: List[float]

@dataclass
class LearningEvent:
    """Enhanced learning event with outcome tracking"""
    timestamp: datetime
    token: str
    action: str
    predicted_outcome: float
    actual_outcome: float
    accuracy: float
    pattern: str
    market_conditions: Dict
    feature_vector: List[float]
    profit_loss: float
    learning_score: float

@dataclass
class AdaptationRule:
    """Rule for adapting bot behavior"""
    condition: str
    action: str
    weight_adjustment: float
    trigger_count: int
    success_rate: float

class IntelligentLearningMomentumBot:
    """AI-powered bot that learns what to do from all analysis parameters"""
    
    def __init__(self):
        # Initialize Binance client
        self.BINANCEUS_KEY = os.getenv('BINANCEUS_KEY')
        self.BINANCEUS_SECRET = os.getenv('BINANCEUS_SECRET')
        self.client = None
        
        if binance_available and self.BINANCEUS_KEY:
            try:
                self.client = Client(self.BINANCEUS_KEY, self.BINANCEUS_SECRET)
                print("✅ Intelligent Learning Bot connected to Binance")
            except Exception as e:
                print(f"⚠️ Binance client error: {e}")
        
        # Advanced learning database with AI models
        self.learning_database = {
            "token_patterns": {
                "MAGICUSDT": {
                    "double_bottom_recovery": {"success_rate": 0.80, "avg_gain": 0.157, "weight": 1.0, "confidence": 0.85},
                    "volume_breakout": {"success_rate": 0.75, "avg_gain": 0.124, "weight": 0.9, "confidence": 0.78},
                    "gaming_momentum": {"success_rate": 0.70, "avg_gain": 0.089, "weight": 0.8, "confidence": 0.72},
                    "correction_recovery": {"success_rate": 0.82, "avg_gain": 0.165, "weight": 0.95, "confidence": 0.88}
                },
                "GALAUSDT": {
                    "correction_bounce": {"success_rate": 0.75, "avg_gain": 0.18, "weight": 0.85, "confidence": 0.80},
                    "gaming_correlation": {"success_rate": 0.70, "avg_gain": 0.15, "weight": 0.8, "confidence": 0.75},
                    "ecosystem_growth": {"success_rate": 0.65, "avg_gain": 0.12, "weight": 0.7, "confidence": 0.68},
                    "volume_accumulation": {"success_rate": 0.72, "avg_gain": 0.14, "weight": 0.75, "confidence": 0.70}
                },
                "ILVUSDT": {
                    "gaming_leadership": {"success_rate": 0.78, "avg_gain": 0.145, "weight": 0.9, "confidence": 0.82},
                    "nft_correlation": {"success_rate": 0.72, "avg_gain": 0.135, "weight": 0.8, "confidence": 0.75},
                    "momentum_surge": {"success_rate": 0.76, "avg_gain": 0.16, "weight": 0.85, "confidence": 0.80}
                },
                "AXSUSDT": {
                    "gaming_recovery": {"success_rate": 0.68, "avg_gain": 0.125, "weight": 0.75, "confidence": 0.70},
                    "adoption_growth": {"success_rate": 0.65, "avg_gain": 0.11, "weight": 0.7, "confidence": 0.67}
                }
            },
            "market_conditions": {
                "gaming_sector_strength": 0.85,
                "crypto_market_sentiment": 0.70,
                "volume_threshold_multiplier": 2.2,
                "momentum_persistence": 0.75,
                "correlation_strength": 0.82
            },
            "learned_parameters": {
                "optimal_entry_timing": "correction_phase_with_volume",
                "best_hold_duration": "3-7_days",
                "risk_reward_ratio": 2.8,
                "max_correlation_exposure": 0.85,
                "momentum_confirmation_threshold": 0.75,
                "ai_confidence_threshold": 0.70
            }
        }
        
        # AI Learning Components
        self.feature_names = [
            "price_change_24h", "volume_24h", "momentum_score", "gaming_correlation",
            "pattern_strength", "market_hour", "day_of_week", "volume_ratio",
            "price_volatility", "sector_strength", "learning_weight"
        ]
        
        # AI Models for prediction
        self.outcome_predictor = None
        self.pattern_classifier = None
        self.risk_assessor = None
        self.load_or_create_models()
        
        # Dynamic learning weights that adapt
        self.adaptive_weights = {
            "pattern_recognition": 0.35,
            "volume_analysis": 0.25,
            "gaming_correlation": 0.20,
            "market_timing": 0.15,
            "risk_management": 0.05,
            "ai_prediction": 0.30  # New AI component
        }
        
        # Intelligent focus parameters that adapt
        self.adaptive_parameters = {
            "momentum_threshold": 3.0,
            "volume_surge_min": 1.2,
            "gaming_correlation_min": 0.5,
            "confidence_threshold": 0.60,
            "ai_confidence_min": 0.65,
            "max_tokens_focus": 3,
            "adaptation_rate": 0.15
        }
        
        # Learning history and adaptation
        self.learning_events = deque(maxlen=1000)
        self.adaptation_rules = []
        self.performance_history = defaultdict(list)
        self.learning_cycles = 0
        self.total_profit_loss = 0.0
        
        # Initialize with successful patterns from our analysis
        self._initialize_learning_from_analysis()
    
    def _initialize_learning_from_analysis(self):
        """Initialize learning database from all our previous analysis"""
        
        # Add learning events from MAGIC analysis
        magic_events = [
            {
                "token": "MAGICUSDT",
                "pattern": "double_bottom_recovery",
                "outcome": 0.157,
                "accuracy": 0.85,
                "market_conditions": {"gaming_strength": 0.80, "correction_phase": True}
            },
            {
                "token": "GALAUSDT", 
                "pattern": "correction_bounce",
                "outcome": 0.18,
                "accuracy": 0.80,
                "market_conditions": {"gaming_strength": 0.75, "volume_surge": True}
            }
        ]
        
        for event_data in magic_events:
            event = LearningEvent(
                timestamp=datetime.now() - timedelta(days=random.randint(1, 30)),
                token=event_data["token"],
                action="BUY",
                predicted_outcome=event_data["outcome"] * 0.9,  # Slightly conservative prediction
                actual_outcome=event_data["outcome"],
                accuracy=event_data["accuracy"],
                pattern=event_data["pattern"],
                market_conditions=event_data["market_conditions"],
                feature_vector=self._generate_sample_features(),
                profit_loss=event_data["outcome"] * 1000,  # $1000 investment
                learning_score=event_data["accuracy"]
            )
            self.learning_events.append(event)
        
        print(f"🧠 Initialized with {len(self.learning_events)} learning events from analysis")
    
    def load_or_create_models(self):
        """Load existing AI models or create new ones"""
        try:
            with open('ai_models.pkl', 'rb') as f:
                models = pickle.load(f)
                self.outcome_predictor = models['outcome_predictor']
                self.pattern_classifier = models['pattern_classifier'] 
                self.risk_assessor = models['risk_assessor']
                print("✅ Loaded existing AI models")
        except FileNotFoundError:
            # Create new models
            self.outcome_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
            self.pattern_classifier = RandomForestRegressor(n_estimators=50, random_state=42)
            self.risk_assessor = LinearRegression()
            
            # Train with initial data
            self._train_initial_models()
            print("🤖 Created and trained new AI models")
    
    def _train_initial_models(self):
        """Train models with initial synthetic data based on our analysis"""
        
        # Generate training data from known patterns
        X_train = []
        y_outcome = []
        y_pattern = []
        y_risk = []
        
        for _ in range(200):  # Generate 200 synthetic training samples
            features = self._generate_sample_features()
            X_train.append(features)
            
            # Simulate outcomes based on our known patterns
            if features[2] > 7:  # High momentum
                outcome = random.uniform(0.08, 0.20)
                pattern_strength = random.uniform(0.7, 0.9)
                risk = random.uniform(0.1, 0.3)
            elif features[2] > 4:  # Medium momentum
                outcome = random.uniform(0.03, 0.12)
                pattern_strength = random.uniform(0.5, 0.8)
                risk = random.uniform(0.2, 0.5)
            else:  # Low momentum
                outcome = random.uniform(-0.05, 0.08)
                pattern_strength = random.uniform(0.3, 0.6)
                risk = random.uniform(0.4, 0.8)
            
            y_outcome.append(outcome)
            y_pattern.append(pattern_strength)
            y_risk.append(risk)
        
        # Train models
        self.outcome_predictor.fit(X_train, y_outcome)
        self.pattern_classifier.fit(X_train, y_pattern)
        self.risk_assessor.fit(X_train, y_risk)
        
        # Save models
        self.save_models()
    
    def _generate_sample_features(self) -> List[float]:
        """Generate sample feature vector"""
        return [
            random.uniform(-15, 15),  # price_change_24h
            random.uniform(5000, 25000),  # volume_24h
            random.uniform(1, 10),  # momentum_score
            random.uniform(0.3, 1.0),  # gaming_correlation
            random.uniform(0.4, 0.9),  # pattern_strength
            random.randint(0, 23),  # market_hour
            random.randint(0, 6),  # day_of_week
            random.uniform(0.5, 3.0),  # volume_ratio
            random.uniform(0.02, 0.25),  # price_volatility
            random.uniform(0.5, 1.0),  # sector_strength
            random.uniform(0.1, 1.0)  # learning_weight
        ]
    
    def save_models(self):
        """Save trained AI models"""
        models = {
            'outcome_predictor': self.outcome_predictor,
            'pattern_classifier': self.pattern_classifier,
            'risk_assessor': self.risk_assessor
        }
        with open('ai_models.pkl', 'wb') as f:
            pickle.dump(models, f)
    
    def extract_features(self, symbol: str, price: float, change_24h: float, 
                        volume_24h: float, market_conditions: Dict) -> List[float]:
        """Extract feature vector for AI prediction"""
        
        gaming_correlation = self._calculate_gaming_correlation(symbol)
        pattern_strength = self._calculate_pattern_strength(symbol, change_24h)
        learning_weight = self._calculate_learning_weight(symbol)
        
        return [
            change_24h,  # price_change_24h
            volume_24h,  # volume_24h
            self._calculate_momentum_score(symbol, price, change_24h, volume_24h),  # momentum_score
            gaming_correlation,  # gaming_correlation
            pattern_strength,  # pattern_strength
            datetime.now().hour,  # market_hour
            datetime.now().weekday(),  # day_of_week
            volume_24h / 10000,  # volume_ratio (normalized)
            abs(change_24h) / 100,  # price_volatility
            market_conditions.get("gaming_sector_strength", 0.7),  # sector_strength
            learning_weight  # learning_weight
        ]
    
    def _calculate_pattern_strength(self, symbol: str, change_24h: float) -> float:
        """Calculate pattern strength based on learned data"""
        
        token_patterns = self.learning_database["token_patterns"].get(symbol, {})
        if not token_patterns:
            return 0.5
        
        # Find matching pattern
        pattern = self._identify_dominant_pattern(symbol, change_24h, 10000)
        if pattern in token_patterns:
            return token_patterns[pattern].get("confidence", 0.5)
        
        return 0.5
    
    def predict_outcome_with_ai(self, symbol: str, price: float, change_24h: float,
                               volume_24h: float) -> Tuple[float, float, float]:
        """Use AI to predict outcome, pattern strength, and risk"""
        
        market_conditions = self._get_current_market_conditions()
        features = self.extract_features(symbol, price, change_24h, volume_24h, market_conditions)
        
        # Make predictions
        predicted_outcome = self.outcome_predictor.predict([features])[0]
        pattern_strength = self.pattern_classifier.predict([features])[0] 
        risk_level = self.risk_assessor.predict([features])[0]
        
        return predicted_outcome, pattern_strength, risk_level
    
    def analyze_all_momentum_tokens_with_ai(self) -> List[TokenAnalysis]:
        """Enhanced token analysis with AI predictions"""
        
        market_data = self._simulate_enhanced_market_data()
        analyzed_tokens = []
        
        print("🤖 AI-Enhanced Token Analysis")
        print("=" * 50)
        
        for token_data in market_data:
            symbol = token_data["symbol"]
            price = token_data["price"]
            change_24h = token_data["price_change_24h"]
            volume_24h = token_data["volume_24h_usdt"]
            
            # AI predictions
            predicted_outcome, pattern_strength, ai_risk = self.predict_outcome_with_ai(
                symbol, price, change_24h, volume_24h
            )
            
            # Traditional analysis
            momentum_score = self._calculate_momentum_score(symbol, price, change_24h, volume_24h)
            pattern_match = self._identify_dominant_pattern(symbol, change_24h, volume_24h)
            confidence = self._calculate_pattern_confidence(symbol, pattern_match)
            target_gain = self._estimate_target_gain(symbol, pattern_match)
            risk_level = self._assess_risk_level(symbol, change_24h, volume_24h)
            gaming_correlation = self._calculate_gaming_correlation(symbol)
            learning_weight = self._calculate_learning_weight(symbol)
            
            # Combine AI and traditional analysis
            combined_confidence = (confidence + pattern_strength) / 2
            combined_target = (target_gain + predicted_outcome) / 2
            
            # Feature vector for learning
            market_conditions = self._get_current_market_conditions()
            feature_vector = self.extract_features(symbol, price, change_24h, volume_24h, market_conditions)
            
            # Only include tokens that meet AI-enhanced criteria
            if (momentum_score >= self.adaptive_parameters["momentum_threshold"] and
                combined_confidence >= self.adaptive_parameters["confidence_threshold"] and
                gaming_correlation >= self.adaptive_parameters["gaming_correlation_min"] and
                pattern_strength >= self.adaptive_parameters["ai_confidence_min"]):
                
                analysis = TokenAnalysis(
                    symbol=symbol,
                    price=price,
                    change_24h=change_24h,
                    volume_24h=volume_24h,
                    momentum_score=momentum_score,
                    pattern_match=pattern_match,
                    confidence=combined_confidence,
                    target_gain=combined_target,
                    risk_level=risk_level,
                    gaming_correlation=gaming_correlation,
                    learning_weight=learning_weight,
                    ai_prediction=predicted_outcome,
                    feature_vector=feature_vector
                )
                
                analyzed_tokens.append(analysis)
                print(f"✅ {symbol}: AI={predicted_outcome:.1%}, Traditional={target_gain:.1%}, Combined={combined_target:.1%}")
        
        # Sort by AI-enhanced composite score
        analyzed_tokens.sort(key=lambda x: self._calculate_ai_composite_score(x), reverse=True)
        
        return analyzed_tokens
    
    def _simulate_enhanced_market_data(self) -> List[Dict]:
        """Enhanced market simulation with more realistic data"""
        base_time = datetime.now()
        
        return [
            {
                "symbol": "MAGICUSDT",
                "price": 0.2380,
                "price_change_24h": -8.45,  # Correction opportunity
                "volume_24h_usdt": 12500,
                "sector": "gaming",
                "pattern_indicators": ["correction_bounce", "volume_accumulation"]
            },
            {
                "symbol": "GALAUSDT", 
                "price": 0.01509,
                "price_change_24h": -3.29,  # Mild correction
                "volume_24h_usdt": 15800,
                "sector": "gaming",
                "pattern_indicators": ["ecosystem_growth", "correction_bounce"]
            },
            {
                "symbol": "ILVUSDT",
                "price": 18.93,
                "price_change_24h": 12.45,  # Strong momentum
                "volume_24h_usdt": 28500,
                "sector": "gaming",
                "pattern_indicators": ["momentum_surge", "gaming_leadership"]
            },
            {
                    symbol=symbol,
                    price=price,
                    change_24h=change_24h,
                    volume_24h=volume_24h,
                    momentum_score=momentum_score,
                    pattern_match=pattern_match,
                    confidence=combined_confidence,
                    target_gain=combined_target,
                    risk_level=risk_level,
                    gaming_correlation=gaming_correlation,
                    learning_weight=learning_weight,
                    ai_prediction=predicted_outcome,
                    feature_vector=feature_vector
                )
                
                analyzed_tokens.append(analysis)
                print(f"✅ {symbol}: AI={predicted_outcome:.1%}, Traditional={target_gain:.1%}, Combined={combined_target:.1%}")
        
        # Sort by AI-enhanced composite score
        analyzed_tokens.sort(key=lambda x: self._calculate_ai_composite_score(x), reverse=True)
        
        return analyzed_tokens
    
    def _simulate_enhanced_market_data(self) -> List[Dict]:
        """Enhanced market simulation with more realistic data"""
        base_time = datetime.now()
        
        return [
            {
                "symbol": "MAGICUSDT",
                "price": 0.2380,
                "price_change_24h": -8.45,  # Correction opportunity
                "volume_24h_usdt": 12500,
                "sector": "gaming",
                "pattern_indicators": ["correction_bounce", "volume_accumulation"]
            },
            {
                "symbol": "GALAUSDT", 
                "price": 0.01509,
                "price_change_24h": -3.29,  # Mild correction
                "volume_24h_usdt": 15800,
                "sector": "gaming",
                "pattern_indicators": ["ecosystem_growth", "correction_bounce"]
            },
            {
                "symbol": "ILVUSDT",
                "price": 18.93,
                "price_change_24h": 12.45,  # Strong momentum
                "volume_24h_usdt": 28500,
                "sector": "gaming",
                "pattern_indicators": ["momentum_surge", "gaming_leadership"]
            },
            {
                "symbol": "AXSUSDT",
                "price": 2.278,
                "price_change_24h": 5.62,  # Moderate momentum
                "volume_24h_usdt": 18900,
                "sector": "gaming",
                "pattern_indicators": ["gaming_recovery", "adoption_growth"]
            },
            {
                "symbol": "SANDUSDT",
                "price": 0.345,
                "price_change_24h": 8.24,  # Good momentum
                "volume_24h_usdt": 22100,
                "sector": "gaming",
                "pattern_indicators": ["gaming_momentum", "volume_breakout"]
            },
            {
                "symbol": "MANAUSDT",
                "price": 0.425,
                "price_change_24h": 4.85,
                "volume_24h_usdt": 16200,
                "sector": "gaming",
                "pattern_indicators": ["gaming_correlation", "accumulation"]
            },
            {
                "symbol": "ENJUSDT",
                "price": 0.189,
                "price_change_24h": 2.15,
                "volume_24h_usdt": 11800,
                "sector": "gaming",
                "pattern_indicators": ["gaming_correlation", "consolidation"]
            }
        ]
    
    def _calculate_ai_composite_score(self, analysis: TokenAnalysis) -> float:
        """Calculate AI-enhanced composite score"""
        
        score = 0.0
        
        # Traditional weighted components
        score += analysis.momentum_score * self.adaptive_weights["pattern_recognition"]
        score += (analysis.volume_24h / 10000) * self.adaptive_weights["volume_analysis"]
        score += analysis.gaming_correlation * 10 * self.adaptive_weights["gaming_correlation"]
        score += analysis.confidence * 10 * self.adaptive_weights["market_timing"]
        score += (1.0 if analysis.risk_level == "LOW" else 0.5) * 10 * self.adaptive_weights["risk_management"]
        
        # AI prediction component
        score += analysis.ai_prediction * 50 * self.adaptive_weights["ai_prediction"]
        
        # Learning weight bonus
        score += analysis.learning_weight * 3
        
        # Pattern synergy bonus (when AI and traditional agree)
        if abs(analysis.ai_prediction - analysis.target_gain) < 0.05:
            score += 2.0  # Synergy bonus
        
        return score
    
    def learn_from_outcomes(self, execution_results: Dict):
        """Learn from actual outcomes and adapt behavior"""
        
        print("🧠 LEARNING FROM OUTCOMES")
        print("=" * 40)
        
        total_learning_score = 0.0
        adaptation_needed = False
        
        for order in execution_results.get("orders", []):
            symbol = order["symbol"]
            predicted_outcome = order.get("predicted_outcome", 0)
            
            # Simulate actual outcome (in real trading, this would come from market data)
            actual_outcome = self._simulate_actual_outcome(order)
            
            # Calculate accuracy
            accuracy = 1.0 - abs(predicted_outcome - actual_outcome) / max(abs(predicted_outcome), 0.01)
            accuracy = max(0.0, min(1.0, accuracy))
            
            # Calculate profit/loss
            amount = order["amount"]
            profit_loss = amount * actual_outcome
            
            # Create learning event
            learning_event = LearningEvent(
                timestamp=datetime.now(),
                token=symbol,
                action=order["action"],
                predicted_outcome=predicted_outcome,
                actual_outcome=actual_outcome,
                accuracy=accuracy,
                pattern=order.get("pattern", ""),
                market_conditions=self._get_current_market_conditions(),
                feature_vector=order.get("feature_vector", []),
                profit_loss=profit_loss,
                learning_score=accuracy
            )
            
            self.learning_events.append(learning_event)
            self.total_profit_loss += profit_loss
            total_learning_score += accuracy
            
            # Update pattern performance
            self._update_pattern_performance(symbol, order.get("pattern", ""), accuracy, actual_outcome)
            
            print(f"📊 {symbol}: Predicted={predicted_outcome:.1%}, Actual={actual_outcome:.1%}, Accuracy={accuracy:.1%}")
            print(f"   💰 P&L: ${profit_loss:+.2f}")
            
            # Check if adaptation is needed
            if accuracy < 0.6:
                adaptation_needed = True
        
        # Adapt if needed
        if adaptation_needed:
            self._adapt_parameters()
        
        # Retrain AI models with new data
        self._retrain_ai_models()
        
        avg_learning_score = total_learning_score / len(execution_results.get("orders", []))
        print(f"\n🎯 Average Learning Score: {avg_learning_score:.1%}")
        print(f"💰 Total P&L: ${self.total_profit_loss:+.2f}")
        
        self.learning_cycles += 1
    
    def _simulate_actual_outcome(self, order: Dict) -> float:
        """Simulate actual market outcome (in real trading, this comes from market data)"""
        
        predicted = order.get("predicted_outcome", 0)
        symbol = order["symbol"]
        pattern = order.get("pattern", "")
        
        # Get historical performance for this pattern
        token_patterns = self.learning_database["token_patterns"].get(symbol, {})
        if pattern in token_patterns:
            historical_avg = token_patterns[pattern].get("avg_gain", predicted)
            success_rate = token_patterns[pattern].get("success_rate", 0.7)
            
            # Simulate outcome based on success rate
            if random.random() < success_rate:
                # Successful outcome with some noise
                actual = historical_avg + random.uniform(-0.03, 0.05)
            else:
                # Failed outcome
                actual = random.uniform(-0.08, -0.02)
        else:
            # No historical data, add noise to prediction
            actual = predicted + random.uniform(-0.05, 0.05)
        
        return actual
    
    def _update_pattern_performance(self, symbol: str, pattern: str, accuracy: float, outcome: float):
        """Update pattern performance in learning database"""
        
        if symbol not in self.learning_database["token_patterns"]:
            self.learning_database["token_patterns"][symbol] = {}
        
        if pattern not in self.learning_database["token_patterns"][symbol]:
            self.learning_database["token_patterns"][symbol][pattern] = {
                "success_rate": 0.5,
                "avg_gain": 0.05,
                "weight": 0.5,
                "confidence": 0.5
            }
        
        pattern_data = self.learning_database["token_patterns"][symbol][pattern]
        
        # Update with exponential moving average
        alpha = 0.2  # Learning rate
        pattern_data["success_rate"] = (1 - alpha) * pattern_data["success_rate"] + alpha * accuracy
        if len(self.learning_events) < 10:
            return  # Need more data
        
        # Prepare training data from learning events
        X_train = []
        y_outcome = []
        y_pattern = []
        y_risk = []
        
        for event in self.learning_events:
            if event.feature_vector:
                X_train.append(event.feature_vector)
                y_outcome.append(event.actual_outcome)
                y_pattern.append(event.accuracy)
                
                # Calculate risk based on outcome volatility
                risk = abs(event.actual_outcome - event.predicted_outcome)
                y_risk.append(risk)
        
        if len(X_train) >= 10:
            # Retrain models
            self.outcome_predictor.fit(X_train, y_outcome)
            self.pattern_classifier.fit(X_train, y_pattern)
            self.risk_assessor.fit(X_train, y_risk)
            
            # Save updated models
            self.save_models()
            print(f"🤖 Retrained AI models with {len(X_train)} data points")
    
    # Include other helper methods from the original bot
    def _calculate_momentum_score(self, symbol: str, price: float, change_24h: float, volume_24h: float) -> float:
        """Calculate comprehensive momentum score"""
        base_score = 0.0
        
        # Price momentum component
        if change_24h > 8:
            base_score += 4.0
        elif change_24h > 5:
            base_score += 3.0
        elif change_24h > 0:
            base_score += 1.5
        elif change_24h > -5:
            base_score += 1.0  # Correction opportunity
        
        # Volume momentum component  
        volume_threshold = 10000  
        if volume_24h > volume_threshold * 2:
            base_score += 3.0
        elif volume_24h > volume_threshold:
            base_score += 2.0
        elif volume_24h > volume_threshold * 0.5:
            base_score += 1.0
        
        # Gaming sector bonus
        if symbol in ["MAGICUSDT", "GALAUSDT", "ILVUSDT", "AXSUSDT", "SANDUSDT"]:
            base_score += 2.0
        
        # Learned pattern bonus
        token_patterns = self.learning_database["token_patterns"].get(symbol, {})
        if token_patterns:
            pattern_bonus = max([p.get("success_rate", 0) * p.get("weight", 0) 
                               for p in token_patterns.values()])
            base_score += pattern_bonus * 2
        
        return min(base_score, 10.0)
    
    def _identify_dominant_pattern(self, symbol: str, change_24h: float, volume_24h: float) -> str:
        """Identify the dominant pattern for this token"""
        
        # Gaming tokens in correction (opportunity)
        if change_24h < -5:
            return "correction_bounce"
        elif change_24h < -2:
            return "correction_recovery"
        
        # Strong momentum patterns
        elif change_24h > 8 and volume_24h > 20000:
            return "momentum_surge"
        elif change_24h > 5 and volume_24h > 15000:
            return "momentum_breakout"
        
        # Volume patterns
        elif volume_24h > 20000:
            return "volume_surge"
        elif volume_24h > 15000:
            return "volume_breakout"
        
        # Gaming sector patterns
        elif symbol in ["ILVUSDT", "AXSUSDT"] and change_24h > 3:
            return "gaming_leadership"
        elif symbol in ["MAGICUSDT", "GALAUSDT"] and change_24h > 0:
            return "gaming_recovery"
        
        # Default patterns
        elif -2 <= change_24h <= 2:
            return "accumulation"
        else:
            return "consolidation"
    
    def _calculate_pattern_confidence(self, symbol: str, pattern: str) -> float:
        """Calculate confidence based on learned pattern performance"""
        
        token_patterns = self.learning_database["token_patterns"].get(symbol, {})
        base_confidence = 0.50
        
        if pattern in token_patterns:
            pattern_data = token_patterns[pattern]
            base_confidence = pattern_data.get("confidence", 0.50)
        
        # Adjust for market conditions and learning
        market_strength = self.learning_database["market_conditions"]["gaming_sector_strength"]
        market_adjustment = (market_strength - 0.5) * 0.2
        learning_adjustment = self._calculate_learning_weight(symbol) * 0.1
        
        final_confidence = base_confidence + market_adjustment + learning_adjustment
        return min(0.95, max(0.30, final_confidence))
    
    def _estimate_target_gain(self, symbol: str, pattern: str) -> float:
        """Estimate target gain based on learned patterns"""
        
        token_patterns = self.learning_database["token_patterns"].get(symbol, {})
        
        default_gains = {
            "correction_bounce": 0.20,
            "correction_recovery": 0.15,
            "momentum_surge": 0.18,
            "momentum_breakout": 0.15,
            "volume_surge": 0.12,
            "volume_breakout": 0.10,
            "gaming_leadership": 0.14,
            "gaming_recovery": 0.12,
            "accumulation": 0.08,
            "consolidation": 0.05
        }
        
        base_gain = default_gains.get(pattern, 0.08)
        
        if pattern in token_patterns:
            learned_gain = token_patterns[pattern].get("avg_gain", base_gain)
            base_gain = (base_gain + learned_gain) / 2
        
        gaming_multiplier = self.learning_database["market_conditions"]["gaming_sector_strength"]
        adjusted_gain = base_gain * gaming_multiplier
        
        return min(0.50, adjusted_gain)
    
    def _assess_risk_level(self, symbol: str, change_24h: float, volume_24h: float) -> str:
        """Assess risk level for the token"""
        volatility = abs(change_24h)
        
        if volatility > 15:
            return "HIGH"
        elif volatility > 8:
            return "MEDIUM"
        elif volume_24h < 8000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_gaming_correlation(self, symbol: str) -> float:
        """Calculate correlation with gaming sector"""
        gaming_correlations = {
            "MAGICUSDT": 1.0,
            "GALAUSDT": 0.75,
            "ILVUSDT": 0.85,
            "AXSUSDT": 0.70,
            "SANDUSDT": 0.68,
            "MANAUSDT": 0.65,
            "ENJUSDT": 0.60
        }
        return gaming_correlations.get(symbol, 0.30)
    
    def _calculate_learning_weight(self, symbol: str) -> float:
        """Calculate how much the bot has learned about this token"""
        token_events = len([e for e in self.learning_events if e.token == symbol])
        pattern_count = len(self.learning_database["token_patterns"].get(symbol, {}))
        
        base_weight = min(1.0, token_events / 15.0)
        pattern_weight = min(1.0, pattern_count / 4.0)
        
        return (base_weight + pattern_weight) / 2
    
    def _get_current_market_conditions(self) -> Dict:
        """Get current market conditions for learning"""
        return {
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "gaming_sector_strength": self.learning_database["market_conditions"]["gaming_sector_strength"],
            "market_sentiment": "adaptive_learning",
            "learning_cycles": self.learning_cycles
        }
    
    def run_intelligent_learning_cycle(self, portfolio_value: float = 1000.0) -> Dict:
        """Run complete intelligent learning cycle"""
        
        print("🧠 INTELLIGENT LEARNING MOMENTUM BOT")
        print("=" * 60)
        print("🎯 AI-powered learning with continuous adaptation")
        print("🚀 Using all learned analysis parameters for optimal momentum focus")
        print()
        
        # Phase 1: AI-Enhanced Analysis
        print("🤖 PHASE 1: AI-Enhanced Token Analysis")
        print("-" * 40)
        focused_tokens = self.analyze_all_momentum_tokens_with_ai()
        
        if not focused_tokens:
            print("❌ No suitable tokens found meeting AI criteria")
            return {"error": "No suitable tokens"}
        
        print(f"✅ Selected {len(focused_tokens)} optimal tokens with AI")
        print()
        
        # Phase 2: Generate Strategy
        print("🚀 PHASE 2: Generate AI-Optimized Strategy")
        print("-" * 40)
        strategy = self.generate_ai_strategy(focused_tokens)
        print("✅ AI strategy generated")
        print()
        
        # Phase 3: Execute Strategy
        print("⚡ PHASE 3: Execute Learning Strategy")
        print("-" * 40)
        execution = self.execute_ai_strategy(strategy, portfolio_value)
        print("✅ Strategy executed")
        print()
        
        # Phase 4: Learn from Outcomes
        print("🧠 PHASE 4: Learn and Adapt")
        print("-" * 40)
        self.learn_from_outcomes(execution)
        print("✅ Learning complete")
        print()
        
        # Generate comprehensive results
        results = {
            "timestamp": datetime.now().isoformat(),
            "learning_cycle": self.learning_cycles,
            "focused_tokens": [asdict(token) for token in focused_tokens],
            "strategy": strategy,
            "execution": execution,
            "learning_summary": {
                "total_events": len(self.learning_events),
                "total_profit_loss": self.total_profit_loss,
                "adaptive_parameters": self.adaptive_parameters,
                "learning_weights": self.adaptive_weights,
                "ai_models_trained": True
            }
        }
        
        return results
    
    def generate_ai_strategy(self, focused_tokens: List[TokenAnalysis]) -> Dict:
        """Generate AI-optimized strategy"""
        
        strategy = {
            "strategy_type": "ai_learning_momentum",
            "timestamp": datetime.now().isoformat(),
            "learning_cycle": self.learning_cycles,
            "ai_confidence": statistics.mean([t.ai_prediction for t in focused_tokens]),
            "total_allocation": 0.95,
            "positions": {},
            "reasoning": "AI-learned momentum with continuous adaptation"
        }
        
        # Calculate AI-weighted allocations
        total_ai_score = sum(self._calculate_ai_composite_score(token) for token in focused_tokens)
        
        for token in focused_tokens:
            ai_score = self._calculate_ai_composite_score(token)
            allocation = 0.95 * (ai_score / total_ai_score)
            
            strategy["positions"][token.symbol] = {
                "allocation": allocation,
                "price": token.price,
                "ai_target": token.price * (1 + token.ai_prediction),
                "traditional_target": token.price * (1 + token.target_gain),
                "combined_target": token.price * (1 + (token.ai_prediction + token.target_gain) / 2),
                "stop_loss": token.price * 0.85,  # 15% stop loss
                "confidence": token.confidence,
                "ai_prediction": token.ai_prediction,
                "pattern": token.pattern_match,
                "feature_vector": token.feature_vector,
                "reasoning": f"AI Score: {ai_score:.2f}, Prediction: {token.ai_prediction:.1%}",
                "risk_level": token.risk_level
            }
        
        strategy["positions"]["CASH_RESERVE"] = {
            "allocation": 0.05,
            "reasoning": "Emergency fund and learning opportunities"
        }
        
        return strategy
    
    def execute_ai_strategy(self, strategy: Dict, portfolio_value: float) -> Dict:
        """Execute AI-optimized strategy"""
        
        execution = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy["strategy_type"],
            "learning_cycle": self.learning_cycles,
            "portfolio_value": portfolio_value,
            "orders": [],
            "total_invested": 0.0,
            "ai_feedback": []
        }
        
        for symbol, position in strategy["positions"].items():
            if symbol == "CASH_RESERVE":
                continue
            
            allocation = position["allocation"]
            amount = portfolio_value * allocation
            price = position["price"]
            ai_prediction = position["ai_prediction"]
            
            if amount < 10:
                continue
            
            quantity = amount / price
            
            order = {
                "symbol": symbol,
                "action": "BUY",
                "amount": amount,
                "quantity": quantity,
                "price": price,
                "ai_target": position["ai_target"],
                "combined_target": position["combined_target"],
                "stop_loss": position["stop_loss"],
                "confidence": position["confidence"],
                "ai_prediction": ai_prediction,
                "predicted_outcome": ai_prediction,  # For learning
                "pattern": position["pattern"],
                "feature_vector": position["feature_vector"],
                "reasoning": position["reasoning"],
                "status": "AI_EXECUTED"
            }
            
            execution["orders"].append(order)
            execution["total_invested"] += amount
            execution["ai_feedback"].append(f"AI predicted {ai_prediction:.1%} for {symbol}")
            
            print(f"🎯 {symbol}: ${amount:.2f} ({allocation:.0%})")
            print(f"   AI Prediction: {ai_prediction:.1%}")
            print(f"   Combined Target: ${position['combined_target']:.4f}")
            print(f"   Confidence: {position['confidence']:.0%}")
        
        return execution

    # Continuous Learning Integration
    def integrate_continuous_learning(self, continuous_engine):
        """Integrate with continuous learning reallocation engine"""
        self.continuous_engine = continuous_engine
        print("🔗 Integrated with Continuous Learning Reallocation Engine")
        
        # Share learning data
        if hasattr(continuous_engine, 'allocation_history'):
            for record in continuous_engine.allocation_history[-50:]:  # Last 50 records
                self.update_learning_from_allocation(record)
    
    def update_learning_from_allocation(self, allocation_record):
        """Update learning database from allocation record"""
        token = allocation_record.token
        pattern = allocation_record.pattern_match
        actual_gain = allocation_record.actual_gain
        
        # Update token patterns in learning database
        if token not in self.learning_database["token_patterns"]:
            self.learning_database["token_patterns"][token] = {}
        
        if pattern not in self.learning_database["token_patterns"][token]:
            self.learning_database["token_patterns"][token][pattern] = {
                "success_rate": 0.5,
                "avg_gain": 0.0,
                "weight": 0.5,
                "confidence": 0.5,
                "sample_count": 0
            }
        
        # Update pattern statistics with continuous learning
        pattern_data = self.learning_database["token_patterns"][token][pattern]
        sample_count = pattern_data.get("sample_count", 0)
        
        # Weighted average update
        alpha = 0.1  # Learning rate
        if actual_gain > 0:
            pattern_data["success_rate"] = (1 - alpha) * pattern_data["success_rate"] + alpha * 1.0
        else:
            pattern_data["success_rate"] = (1 - alpha) * pattern_data["success_rate"] + alpha * 0.0
        
        pattern_data["avg_gain"] = (1 - alpha) * pattern_data["avg_gain"] + alpha * actual_gain
        pattern_data["sample_count"] = sample_count + 1
        
        # Update confidence based on sample size and consistency
        consistency = 1 - abs(actual_gain - pattern_data["avg_gain"]) / max(0.01, abs(pattern_data["avg_gain"]))
        pattern_data["confidence"] = min(0.95, pattern_data["confidence"] * 0.99 + consistency * 0.01)
        
        # Update weight based on recent performance
        if pattern_data["success_rate"] > 0.7 and pattern_data["avg_gain"] > 0.05:
            pattern_data["weight"] = min(1.0, pattern_data["weight"] * 1.01)
        elif pattern_data["success_rate"] < 0.4:
            pattern_data["weight"] = max(0.1, pattern_data["weight"] * 0.99)
    
    def suggest_reallocation_opportunity(self) -> Optional[Dict[str, Any]]:
        """Suggest reallocation opportunities based on momentum analysis"""
        if not hasattr(self, 'continuous_engine') or not self.continuous_engine:
            return None
        
        # Generate current signals
        signals = self.generate_ai_trading_signals()
        if not signals:
            return None
        
        # Find best opportunity
        best_signal = max(signals, key=lambda s: s.ai_confidence * s.momentum_score)
        
        # Check if it's significantly better than current positions
        current_positions = getattr(self.continuous_engine, 'active_positions', {})
        
        if not current_positions:
            return {
                "action": "new_position",
                "token": best_signal.symbol,
                "confidence": best_signal.ai_confidence,
                "predicted_gain": best_signal.target_gain,
                "reasoning": f"High momentum signal with {best_signal.ai_confidence:.1%} confidence"
            }
        
        # Compare with existing positions
        for token, position in current_positions.items():
            improvement = best_signal.target_gain - position.predicted_gain
            if improvement > 0.1 and best_signal.ai_confidence > 0.8:  # 10% better and high confidence
                return {
                    "action": "reallocation",
                    "from_token": token,
                    "to_token": best_signal.symbol,
                    "confidence": best_signal.ai_confidence,
                    "expected_improvement": improvement,
                    "reasoning": f"Momentum analysis suggests {improvement:.1%} improvement by switching to {best_signal.symbol}"
                }
        
        return None

def main():
    """Main execution function"""
    print("🧠 INTELLIGENT LEARNING MOMENTUM BOT")
    print("=" * 70)
    print("🤖 AI-powered learning that adapts from all analysis parameters")
    print("🎯 Continuous improvement through outcome-based learning")
    print("🚀 Focus on optimal momentum tokens with adaptive strategies")
    print()
    
    # Initialize intelligent bot
    bot = IntelligentLearningMomentumBot()
    
    # Run learning cycle
    portfolio_value = float(input("Enter portfolio value (default $1000): ") or "1000")
    results = bot.run_intelligent_learning_cycle(portfolio_value)
    
    if "error" not in results:
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intelligent_learning_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to {filename}")
        print(f"🧠 Learning Cycle #{results['learning_cycle']} complete!")
        print(f"💰 Total P&L: ${bot.total_profit_loss:+.2f}")
        print(f"📊 Learning Events: {len(bot.learning_events)}")
        print("\n✅ INTELLIGENT LEARNING BOT SESSION COMPLETE!")
        print("🔄 Bot has learned and adapted for future cycles!")

if __name__ == "__main__":
    main()
