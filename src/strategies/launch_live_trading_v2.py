#!/usr/bin/env python3

"""
🚀 VICTORYCHAIN LIVE TRADING SYSTEM
Enterprise-grade Claude AI-powered cryptocurrency trading platform
Author: Senior Developer
Version: 2.0.0
"""

import os
import sys
import json
import time
import logging
import warnings
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional, Union, Any, Tuple

# External imports with error handling
try:
    import requests
    import numpy as np
    import pandas as pd

    HAS_EXTERNAL_LIBS = True
except ImportError as e:
    print(f"Warning: Some external libraries not available: {e}")
    HAS_EXTERNAL_LIBS = False

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException

    HAS_BINANCE = True
except ImportError:
    print("Warning: Binance library not available")
    HAS_BINANCE = False

try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
except ImportError:
    print("Warning: python-dotenv not available")
    HAS_DOTENV = False

# Import VictoryChain modules
try:
    from core.victorychain_shared import (
        OrderType,
        StrategyType,
        TradingMode,
        OrderStatus,
        RiskLevel,
        ConfidenceLevel,
        MarketData,
        TradingSignal,
        TradeResult,
        PortfolioPosition,
        TradingConfig,
        AnalysisResult,
        BaseStrategy,
        BaseTrader,
        TradingEngine,
        calculate_position_size,
        calculate_stop_loss,
        calculate_take_profit,
        validate_signal_data,
        format_currency,
        format_percentage,
        DEFAULT_CONFIG,
        get_logger,
        asdict,
    )

    HAS_SHARED_INTERFACES = True
except ImportError as e:
    print(f"Warning: Could not import shared interfaces: {e}")
    from dataclasses import dataclass, asdict
    from enum import Enum

    HAS_SHARED_INTERFACES = False

try:
    from core.victorychain_core_v2 import VictoryChainCore

    HAS_CORE = True
except ImportError as e:
    print(f"Warning: Could not import VictoryChain core: {e}")
    HAS_CORE = False

try:
    from strategies.momentum_trader_v2 import MomentumTrader

    HAS_MOMENTUM_TRADER = True
except ImportError as e:
    print(f"Warning: Could not import momentum trader: {e}")
    HAS_MOMENTUM_TRADER = False

try:
    from ai.claude_token_optimizer import ClaudeTokenOptimizer

    HAS_CLAUDE_OPTIMIZER = True
except ImportError as e:
    print(f"Warning: Could not import Claude optimizer: {e}")
    HAS_CLAUDE_OPTIMIZER = False

# Suppress pandas warnings
if HAS_EXTERNAL_LIBS:
    warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'victorychain_live_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)
logger = get_logger(__name__) if HAS_SHARED_INTERFACES else logging.getLogger(__name__)


class TradingStrategy(Enum):
    """Trading strategy types"""

    MOMENTUM = "momentum"
    CONSOLIDATION = "consolidation"
    ARBITRAGE = "arbitrage"
    HYBRID = "hybrid"


class ConfidenceLevel(Enum):
    """Confidence levels for trading decisions"""

    LOW = 0.6
    MEDIUM = 0.75
    HIGH = 0.85
    EXTREME = 0.95


@dataclass
class TradingConfig:
    """Trading system configuration"""

    # Strategy parameters
    strategy: TradingStrategy = TradingStrategy.HYBRID
    min_gain_target: float = 4.0  # 4% minimum gain target
    max_loss_tolerance: float = 1.5  # 1.5% maximum loss
    confidence_threshold: float = 0.75  # 75% minimum confidence

    # Position management
    max_position_size: float = 0.90  # 90% maximum position size
    min_trade_amount: float = 25.0  # $25 minimum trade
    max_concurrent_positions: int = 1  # Single position strategy

    # Risk management
    emergency_stop_loss: float = 0.25  # 25% emergency stop
    daily_loss_limit: float = 0.15  # 15% daily loss limit

    # Claude AI optimization
    claude_batch_size: int = 20  # Batch size for analysis
    claude_cache_ttl: int = 300  # 5 minutes cache
    max_claude_tokens: int = 4000  # Token limit per request

    # Market analysis
    volume_threshold: float = 10000.0  # Minimum daily volume
    quality_threshold: float = 0.70  # Minimum quality score
    similarity_threshold: float = 70.0  # Pattern similarity threshold


@dataclass
class MarketData:
    """Enhanced market data structure"""

    symbol: str
    current_price: float
    price_change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    range_position: float
    momentum_score: float
    quality_score: float
    volatility: float
    volume_category: str
    timestamp: datetime


@dataclass
class TradingSignal:
    """Trading signal with comprehensive data"""

    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    target_amount: float
    expected_return: float
    risk_assessment: str
    reasoning: str
    claude_analysis: bool
    similarity_score: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TradeExecution:
    """Trade execution result"""

    success: bool
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    executed_qty: Optional[float] = None
    executed_price: Optional[float] = None
    commission: Optional[float] = None
    error_message: Optional[str] = None
    execution_time: datetime = None

    def __post_init__(self):
        if self.execution_time is None:
            self.execution_time = datetime.now()


@dataclass
class WinningPattern:
    """MAGICUSDT winning pattern reference"""

    performance: float = 32.32
    momentum_score: float = 0.998
    range_position: float = 0.882
    pattern_type: str = "MOMENTUM_SURGE"
    controlled_volatility: bool = True
    technical_alignment: bool = True


class ClaudeAnalyzer:
    """Claude AI integration for market analysis"""

    def __init__(self, api_key: str, config: TradingConfig):
        self.api_key = api_key
        self.config = config
        self.cache = {}
        self.last_request_time = 0
        self.rate_limit_delay = 1.0

    def _rate_limit(self) -> None:
        """Implement rate limiting for Claude API"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _get_cache_key(self, data: List[Dict]) -> str:
        """Generate cache key for market data"""
        import hashlib

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached analysis is still valid"""
        if key not in self.cache:
            return False
        return time.time() - self.cache[key]["timestamp"] < self.config.claude_cache_ttl

    def _optimize_prompt(self, prompt: str) -> str:
        """Optimize prompt to reduce token usage"""
        optimizations = [
            ("As an expert cryptocurrency trading advisor", "Expert crypto advisor"),
            ("comprehensive analysis", "analysis"),
            ("detailed explanation", "explanation"),
            ("in the current market conditions", "currently"),
            ("analyze this data", "analyze"),
        ]

        optimized = prompt
        for old, new in optimizations:
            optimized = optimized.replace(old, new)

        return optimized

    def analyze_market_opportunities(
        self, market_data: List[MarketData]
    ) -> Dict[str, Any]:
        """
        Analyze market opportunities using Claude AI

        Args:
            market_data: List of market data objects

        Returns:
            Analysis result with recommendations
        """
        if not self.api_key:
            logger.warning("Claude API key not available, using fallback analysis")
            return self._fallback_analysis(market_data)

        # Prepare data for analysis
        analysis_data = [
            asdict(data) for data in market_data[: self.config.claude_batch_size]
        ]
        cache_key = self._get_cache_key(analysis_data)

        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info("Using cached Claude analysis")
            return self.cache[cache_key]["result"]

        try:
            self._rate_limit()

            # Create optimized prompt
            prompt = self._create_analysis_prompt(market_data)
            optimized_prompt = self._optimize_prompt(prompt)

            # Make Claude API request
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": self.config.max_claude_tokens,
                    "messages": [{"role": "user", "content": optimized_prompt}],
                },
                timeout=30,
            )

            if response.status_code == 200:
                claude_response = response.json()
                analysis_text = claude_response["content"][0]["text"]

                # Parse structured data if available
                structured_data = self._parse_claude_response(analysis_text)

                result = {
                    "analysis_text": analysis_text,
                    "structured_data": structured_data,
                    "claude_analysis": True,
                    "confidence": 0.85,
                    "timestamp": datetime.now(),
                }

                # Cache result
                self.cache[cache_key] = {"result": result, "timestamp": time.time()}

                logger.info("Claude analysis completed successfully")
                return result

            else:
                logger.error(f"Claude API error: {response.status_code}")
                return self._fallback_analysis(market_data)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._fallback_analysis(market_data)

    def _create_analysis_prompt(self, market_data: List[MarketData]) -> str:
        """Create optimized analysis prompt"""
        winning_pattern = WinningPattern()

        # Prepare market data summary
        data_summary = []
        for data in market_data[: self.config.claude_batch_size]:
            data_summary.append(
                {
                    "symbol": data.symbol,
                    "change": f"{data.price_change_24h:.2f}%",
                    "price": f"${data.current_price:.6f}",
                    "volume": f"${data.volume_24h:,.0f}",
                    "range_pos": f"{data.range_position:.1%}",
                    "momentum": f"{data.momentum_score:.3f}",
                    "quality": f"{data.quality_score:.3f}",
                }
            )

        prompt = f"""Expert crypto advisor analysis needed.

WINNING REFERENCE: MAGICUSDT pattern
- Performance: +{winning_pattern.performance:.1f}%
- Momentum: {winning_pattern.momentum_score}
- Range: {winning_pattern.range_position:.1%}
- Type: {winning_pattern.pattern_type}

MARKET DATA ({len(data_summary)} tokens):
{json.dumps(data_summary, indent=1)}

ANALYSIS REQUIREMENTS:
1. Find TOP 3 tokens matching MAGICUSDT pattern
2. Score similarity (0-100%)
3. Assess risk/reward for each
4. Minimum 4% gain targets
5. Maximum 1.5% loss tolerance

Return JSON with:
{{
  "recommendations": [
    {{
      "symbol": "TOKEN",
      "confidence": 0.85,
      "similarity": 85,
      "expected_return": 6.5,
      "risk_level": "medium",
      "reasoning": "brief explanation"
    }}
  ],
  "market_summary": "brief overview"
}}"""

        return prompt

    def _parse_claude_response(self, response_text: str) -> Optional[Dict]:
        """Parse structured data from Claude response"""
        try:
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.debug(f"Failed to parse Claude JSON: {e}")
        return None

    def _fallback_analysis(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Fallback analysis when Claude is unavailable"""
        logger.info("Using fallback pattern matching analysis")

        winning_pattern = WinningPattern()
        recommendations = []

        for data in market_data:
            # Calculate similarity to winning pattern
            if data.price_change_24h < 3.0:  # Skip low performers
                continue

            performance_score = (
                min(data.price_change_24h / winning_pattern.performance, 1.0) * 35
            )
            momentum_score = data.momentum_score * 25
            range_score = data.range_position * 20
            quality_score = data.quality_score * 20

            similarity = (
                performance_score + momentum_score + range_score + quality_score
            )

            if similarity >= self.config.similarity_threshold:
                recommendations.append(
                    {
                        "symbol": data.symbol,
                        "confidence": min(similarity / 100.0, 0.95),
                        "similarity": similarity,
                        "expected_return": data.price_change_24h
                        * 0.3,  # Conservative estimate
                        "risk_level": "medium",
                        "reasoning": f"Pattern match {similarity:.1f}%, momentum {data.momentum_score:.2f}",
                    }
                )

        # Sort by similarity score
        recommendations.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "analysis_text": f"Fallback analysis found {len(recommendations)} opportunities",
            "structured_data": {
                "recommendations": recommendations[:3],
                "market_summary": f"Analyzed {len(market_data)} tokens, found {len(recommendations)} matches",
            },
            "claude_analysis": False,
            "confidence": 0.70,
            "timestamp": datetime.now(),
        }


class VictoryChainLiveTrader:
    """Enterprise-grade live trading system"""

    def __init__(self, config: Optional[TradingConfig] = None):
        """
        Initialize trading system

        Args:
            config: Trading configuration
        """
        load_dotenv()

        self.config = config or TradingConfig()

        # API Configuration
        self.api_key = os.getenv("BINANCEUS_KEY")
        self.api_secret = os.getenv("BINANCEUS_SECRET")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials required")

        # Initialize clients
        try:
            self.client = Client(self.api_key, self.api_secret, tld="us")
            logger.info("Connected to Binance US API")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise

        # Initialize Claude analyzer
        self.claude_analyzer = ClaudeAnalyzer(self.claude_api_key or "", self.config)

        # Trading state
        self.active_positions: Dict[str, Dict] = {}
        self.trade_history: List[TradeExecution] = []
        self.daily_pnl = 0.0
        self.session_start_time = datetime.now()

        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_volume = 0.0

        # Market data cache
        self.market_cache: Dict[str, Any] = {}
        self.cache_timestamp = 0

        logger.info("VictoryChain Live Trading System initialized")
        logger.info(f"Strategy: {self.config.strategy.value}")
        logger.info(f"Max position size: {self.config.max_position_size*100:.1f}%")

    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance with error handling"""
        try:
            account_info = self.client.get_account()
            balances = {}

            for balance in account_info["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])

                if free > 0 or locked > 0:
                    balances[balance["asset"]] = {
                        "free": free,
                        "locked": locked,
                        "total": free + locked,
                    }

            return balances

        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}

    def get_usdt_balance(self) -> float:
        """Get available USDT balance"""
        try:
            balances = self.get_account_balance()
            usdt_data = balances.get("USDT", {})
            return usdt_data.get("free", 0.0)
        except Exception as e:
            logger.error(f"Error getting USDT balance: {e}")
            return 0.0

    def fetch_market_data(self) -> List[MarketData]:
        """
        Fetch and process market data

        Returns:
            List of market data objects
        """
        # Check cache first
        if (time.time() - self.cache_timestamp) < self.config.claude_cache_ttl:
            cached_data = self.market_cache.get("market_data")
            if cached_data:
                logger.info("Using cached market data")
                return cached_data

        try:
            logger.info("Fetching market data from Binance US...")

            # Get exchange info for tradable symbols
            exchange_info = self.client.get_exchange_info()
            tradable_symbols = set()

            for symbol_info in exchange_info["symbols"]:
                symbol = symbol_info["symbol"]
                if (
                    symbol.endswith("USDT")
                    and symbol_info["status"] == "TRADING"
                    and symbol != "USDCUSDT"
                ):
                    tradable_symbols.add(symbol)

            # Get 24hr ticker data
            tickers = self.client.get_ticker()
            market_data = []

            for ticker in tickers:
                if ticker["symbol"] not in tradable_symbols:
                    continue

                try:
                    symbol = ticker["symbol"]
                    current_price = float(ticker["lastPrice"])
                    price_change_24h = float(ticker["priceChangePercent"])
                    volume_24h = float(ticker["quoteVolume"])
                    high_24h = float(ticker["highPrice"])
                    low_24h = float(ticker["lowPrice"])

                    # Skip low volume tokens
                    if volume_24h < self.config.volume_threshold:
                        continue

                    # Calculate advanced metrics
                    price_range = high_24h - low_24h if high_24h != low_24h else 0.01
                    range_position = (
                        (current_price - low_24h) / price_range
                        if price_range > 0
                        else 0.5
                    )
                    momentum_score = min(abs(price_change_24h) / 20.0, 1.0)
                    volatility = price_range / current_price if current_price > 0 else 0

                    # Volume categorization
                    if volume_24h >= 100000:
                        volume_category = "high"
                    elif volume_24h >= 50000:
                        volume_category = "medium"
                    else:
                        volume_category = "low"

                    # Quality score calculation
                    volume_score = min(volume_24h / 1000000.0, 1.0)
                    performance_score = min(abs(price_change_24h) / 30.0, 1.0)
                    stability_score = 1.0 - min(volatility, 1.0)
                    quality_score = (
                        volume_score + performance_score + stability_score
                    ) / 3

                    market_data.append(
                        MarketData(
                            symbol=symbol,
                            current_price=current_price,
                            price_change_24h=price_change_24h,
                            volume_24h=volume_24h,
                            high_24h=high_24h,
                            low_24h=low_24h,
                            range_position=range_position,
                            momentum_score=momentum_score,
                            quality_score=quality_score,
                            volatility=volatility,
                            volume_category=volume_category,
                            timestamp=datetime.now(),
                        )
                    )

                except (ValueError, ZeroDivisionError) as e:
                    logger.debug(
                        f"Error processing {ticker.get('symbol', 'unknown')}: {e}"
                    )
                    continue

            # Sort by quality score
            market_data.sort(key=lambda x: x.quality_score, reverse=True)

            # Update cache
            self.market_cache["market_data"] = market_data
            self.cache_timestamp = time.time()

            logger.info(f"Processed {len(market_data)} tradable tokens")
            return market_data

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return []

    def generate_trading_signals(
        self, market_data: List[MarketData]
    ) -> List[TradingSignal]:
        """
        Generate trading signals using Claude AI and pattern matching

        Args:
            market_data: Market data list

        Returns:
            List of trading signals
        """
        # Filter promising opportunities
        opportunities = [
            data
            for data in market_data
            if (
                data.price_change_24h >= self.config.min_gain_target
                and data.quality_score >= self.config.quality_threshold
            )
        ]

        if not opportunities:
            logger.info("No opportunities meet minimum criteria")
            return []

        logger.info(f"Analyzing {len(opportunities)} promising opportunities")

        # Get Claude AI analysis
        analysis_result = self.claude_analyzer.analyze_market_opportunities(
            opportunities
        )

        signals = []
        structured_data = analysis_result.get("structured_data", {})
        recommendations = structured_data.get("recommendations", [])

        # Convert recommendations to trading signals
        for rec in recommendations[:3]:  # Top 3 recommendations
            try:
                symbol = rec["symbol"]
                confidence = float(rec.get("confidence", 0.7))
                expected_return = float(rec.get("expected_return", 5.0))
                similarity = float(rec.get("similarity", 70.0))

                # Skip if confidence too low
                if confidence < self.config.confidence_threshold:
                    continue

                # Find corresponding market data
                market_info = next(
                    (data for data in opportunities if data.symbol == symbol), None
                )

                if not market_info:
                    continue

                # Calculate position size
                available_usdt = self.get_usdt_balance()
                position_size = self._calculate_position_size(
                    available_usdt, confidence, expected_return
                )

                # Create trading signal
                signal = TradingSignal(
                    symbol=symbol,
                    action="BUY",
                    confidence=confidence,
                    target_amount=position_size,
                    expected_return=expected_return,
                    risk_assessment=rec.get("risk_level", "medium"),
                    reasoning=rec.get("reasoning", "Pattern match"),
                    claude_analysis=analysis_result["claude_analysis"],
                    similarity_score=similarity,
                    stop_loss=market_info.current_price
                    * (1 - self.config.max_loss_tolerance / 100),
                    take_profit=market_info.current_price * (1 + expected_return / 100),
                )

                signals.append(signal)

            except Exception as e:
                logger.error(f"Error creating signal for {rec}: {e}")
                continue

        # Sort by confidence and expected return
        signals.sort(key=lambda x: x.confidence * x.expected_return, reverse=True)

        logger.info(f"Generated {len(signals)} trading signals")
        return signals

    def _calculate_position_size(
        self, available_usdt: float, confidence: float, expected_return: float
    ) -> float:
        """Calculate optimal position size"""
        # Base allocation based on confidence and expected return
        confidence_factor = (confidence - 0.6) / 0.4  # Scale 0.6-1.0 to 0-1
        return_factor = min(expected_return / 10.0, 1.0)  # Scale to max 10%

        allocation_pct = (
            self.config.max_position_size * confidence_factor * return_factor
        )
        allocation_pct = max(allocation_pct, 0.1)  # Minimum 10%

        position_size = available_usdt * allocation_pct

        # Ensure minimum trade amount
        return max(position_size, self.config.min_trade_amount)

    def execute_trade(self, signal: TradingSignal) -> TradeExecution:
        """
        Execute trading signal

        Args:
            signal: Trading signal to execute

        Returns:
            Trade execution result
        """
        logger.info(f"🎯 Executing trade for {signal.symbol}")
        logger.info(f"   Action: {signal.action}")
        logger.info(f"   Amount: ${signal.target_amount:.2f}")
        logger.info(f"   Confidence: {signal.confidence:.2%}")
        logger.info(f"   Expected Return: {signal.expected_return:.1f}%")

        try:
            if signal.action == "BUY":
                # Execute market buy order
                order = self.client.order_market_buy(
                    symbol=signal.symbol, quoteOrderQty=signal.target_amount
                )
            else:
                logger.warning(f"Unsupported action: {signal.action}")
                return TradeExecution(
                    success=False, error_message=f"Unsupported action: {signal.action}"
                )

            # Parse order result
            executed_qty = float(order.get("executedQty", 0))
            fills = order.get("fills", [])

            # Calculate average price and commission
            total_cost = 0.0
            total_commission = 0.0

            for fill in fills:
                total_cost += float(fill["price"]) * float(fill["qty"])
                total_commission += float(fill["commission"])

            avg_price = total_cost / executed_qty if executed_qty > 0 else 0

            result = TradeExecution(
                success=True,
                order_id=str(order["orderId"]),
                symbol=signal.symbol,
                executed_qty=executed_qty,
                executed_price=avg_price,
                commission=total_commission,
            )

            # Update tracking
            self.total_trades += 1
            self.successful_trades += 1
            self.total_volume += signal.target_amount
            self.trade_history.append(result)

            # Track position
            self.active_positions[signal.symbol] = {
                "quantity": executed_qty,
                "entry_price": avg_price,
                "entry_time": datetime.now(),
                "signal": signal,
            }

            logger.info(f"✅ Trade executed successfully:")
            logger.info(f"   Order ID: {result.order_id}")
            logger.info(f"   Quantity: {executed_qty:.6f}")
            logger.info(f"   Price: ${avg_price:.6f}")
            logger.info(f"   Commission: ${total_commission:.6f}")

            return result

        except BinanceOrderException as e:
            error_msg = f"Order execution failed: {e}"
            logger.error(error_msg)
            self.total_trades += 1

            return TradeExecution(
                success=False, symbol=signal.symbol, error_message=error_msg
            )

        except Exception as e:
            error_msg = f"Unexpected trading error: {e}"
            logger.error(error_msg)

            return TradeExecution(
                success=False, symbol=signal.symbol, error_message=error_msg
            )

    def liquidate_all_positions(self) -> List[TradeExecution]:
        """
        Liquidate all active positions before new allocation

        Returns:
            List of liquidation results
        """
        if not self.active_positions:
            logger.info("No active positions to liquidate")
            return []

        logger.info(f"🔄 Liquidating {len(self.active_positions)} positions...")

        results = []
        for symbol, position in list(self.active_positions.items()):
            try:
                # Get current balance
                balances = self.get_account_balance()
                asset = symbol.replace("USDT", "")
                asset_balance = balances.get(asset, {})
                available_qty = asset_balance.get("free", 0.0)

                if available_qty <= 0:
                    logger.info(f"No {asset} balance to sell")
                    continue

                # Execute market sell order
                order = self.client.order_market_sell(
                    symbol=symbol, quantity=available_qty
                )

                # Parse result
                executed_qty = float(order.get("executedQty", 0))
                fills = order.get("fills", [])

                total_proceeds = 0.0
                total_commission = 0.0

                for fill in fills:
                    total_proceeds += float(fill["price"]) * float(fill["qty"])
                    total_commission += float(fill["commission"])

                avg_price = total_proceeds / executed_qty if executed_qty > 0 else 0

                result = TradeExecution(
                    success=True,
                    order_id=str(order["orderId"]),
                    symbol=symbol,
                    executed_qty=executed_qty,
                    executed_price=avg_price,
                    commission=total_commission,
                )

                results.append(result)

                # Calculate P&L
                entry_price = position.get("entry_price", avg_price)
                pnl = (avg_price - entry_price) * executed_qty - total_commission
                self.daily_pnl += pnl

                logger.info(f"✅ Liquidated {symbol}:")
                logger.info(f"   Quantity: {executed_qty:.6f}")
                logger.info(f"   Price: ${avg_price:.6f}")
                logger.info(f"   P&L: ${pnl:.2f}")

                # Remove from active positions
                del self.active_positions[symbol]

            except Exception as e:
                error_msg = f"Failed to liquidate {symbol}: {e}"
                logger.error(error_msg)

                results.append(
                    TradeExecution(
                        success=False, symbol=symbol, error_message=error_msg
                    )
                )

        return results

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        success_rate = (
            self.successful_trades / self.total_trades * 100
            if self.total_trades > 0
            else 0
        )

        session_duration = datetime.now() - self.session_start_time

        return {
            "session_duration": str(session_duration),
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "success_rate": f"{success_rate:.1f}%",
            "daily_pnl": f"${self.daily_pnl:.2f}",
            "total_volume": f"${self.total_volume:.2f}",
            "active_positions": len(self.active_positions),
            "strategy": self.config.strategy.value,
            "claude_enabled": bool(self.claude_api_key),
            "last_update": datetime.now().isoformat(),
        }

    def run_trading_session(self, duration_minutes: int = 60) -> None:
        """
        Run complete trading session

        Args:
            duration_minutes: Session duration in minutes
        """
        logger.info(
            f"🚀 Starting VictoryChain trading session ({duration_minutes} minutes)"
        )
        logger.info(f"Strategy: {self.config.strategy.value}")
        logger.info(f"Max position: {self.config.max_position_size*100:.1f}%")

        session_start = datetime.now()
        session_end = session_start + timedelta(minutes=duration_minutes)
        scan_interval = 300  # 5 minutes between scans

        try:
            while datetime.now() < session_end:
                logger.info("📊 Starting market analysis cycle...")

                # 1. Fetch market data
                market_data = self.fetch_market_data()
                if not market_data:
                    logger.warning("No market data available, waiting...")
                    time.sleep(scan_interval)
                    continue

                # 2. Generate trading signals
                signals = self.generate_trading_signals(market_data)

                if signals:
                    top_signal = signals[0]
                    logger.info(f"🎯 Top opportunity: {top_signal.symbol}")
                    logger.info(
                        f"   Expected return: {top_signal.expected_return:.1f}%"
                    )
                    logger.info(f"   Confidence: {top_signal.confidence:.1%}")
                    logger.info(f"   Target amount: ${top_signal.target_amount:.2f}")

                    # 3. Check if we should trade
                    available_usdt = self.get_usdt_balance()

                    if (
                        top_signal.confidence >= self.config.confidence_threshold
                        and available_usdt >= self.config.min_trade_amount
                    ):

                        # 4. Liquidate existing positions first
                        if self.active_positions:
                            liquidation_results = self.liquidate_all_positions()
                            logger.info(
                                f"Liquidated {len(liquidation_results)} positions"
                            )

                        # 5. Execute new trade
                        result = self.execute_trade(top_signal)

                        if result.success:
                            logger.info("✅ Trade executed successfully")
                        else:
                            logger.error(f"❌ Trade failed: {result.error_message}")
                    else:
                        logger.info(
                            "⏸️ Skipping trade (low confidence or insufficient funds)"
                        )
                else:
                    logger.info("📉 No trading opportunities found")

                # 6. Performance update
                performance = self.get_performance_summary()
                logger.info("📈 Performance Summary:")
                for key, value in performance.items():
                    logger.info(f"   {key}: {value}")

                # Wait before next cycle
                logger.info(
                    f"⏰ Waiting {scan_interval//60} minutes until next scan..."
                )
                time.sleep(scan_interval)

        except KeyboardInterrupt:
            logger.info("Trading session interrupted by user")
        except Exception as e:
            logger.error(f"Trading session error: {e}")
        finally:
            # Final performance summary
            final_performance = self.get_performance_summary()
            logger.info("🏁 Final Session Summary:")
            for key, value in final_performance.items():
                logger.info(f"   {key}: {value}")


def main():
    """Main execution function"""
    try:
        # Create trading configuration
        config = TradingConfig(
            strategy=TradingStrategy.HYBRID,
            min_gain_target=4.0,
            max_loss_tolerance=1.5,
            confidence_threshold=0.75,
            max_position_size=0.85,  # 85% max position size
        )

        # Initialize trading system
        trader = VictoryChainLiveTrader(config)

        # Show initial status
        logger.info("=== VictoryChain Live Trading System ===")
        logger.info(f"USDT Balance: ${trader.get_usdt_balance():.2f}")
        logger.info(f"Active Positions: {len(trader.active_positions)}")

        # Run trading session
        trader.run_trading_session(duration_minutes=60)

    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
