#!/usr/bin/env python3

"""
🚀 VICTORYCHAIN MOMENTUM TRADER
Enterprise-grade momentum trading system with advanced risk management
Author: Senior Developer
Version: 2.0.0
"""

import os
import sys
import time
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional, Tuple, Union, Any
from urllib.parse import urlencode

import requests

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

# Import shared interfaces and utilities
try:
    from victorychain_shared import (
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
        StrategyProvider,
        calculate_position_size,
        calculate_stop_loss,
        calculate_take_profit,
        validate_signal_data,
        format_currency,
        format_percentage,
        DEFAULT_CONFIG,
        get_logger,
    )
    from dataclasses import asdict

    HAS_SHARED_INTERFACES = True
except ImportError as e:
    print(f"Warning: Could not import shared interfaces: {e}")
    # Fallback to local definitions
    from dataclasses import dataclass, asdict
    from enum import Enum

    class OrderType(Enum):
        BUY = "BUY"
        SELL = "SELL"
        HOLD = "HOLD"

    class TradingMode(Enum):
        LIVE = "live"
        DEMO = "demo"
        PAPER = "paper"

    class OrderStatus(Enum):
        PENDING = "pending"
        FILLED = "filled"
        CANCELLED = "cancelled"
        FAILED = "failed"

    HAS_SHARED_INTERFACES = False

# Local imports for backward compatibility
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("momentum_trader.log"), logging.StreamHandler()],
)
logger = get_logger(__name__) if HAS_SHARED_INTERFACES else logging.getLogger(__name__)


@dataclass
class TradingConfig:
    """Trading configuration parameters"""

    min_momentum_threshold: float = 20.0  # Minimum 20% momentum
    max_momentum_threshold: float = 50.0  # Maximum 50% momentum
    min_trade_amount: float = 25.0  # Minimum $25 per trade
    max_position_size: float = 0.25  # Maximum 25% of portfolio
    quality_threshold: float = 0.75  # Minimum quality score
    volume_threshold: float = 1000000.0  # Minimum $1M daily volume
    stop_loss_pct: float = 0.15  # 15% stop loss
    take_profit_pct: float = 0.30  # 30% take profit
    max_concurrent_positions: int = 3  # Maximum positions
    rate_limit_delay: float = 1.0  # API rate limiting
    max_retries: int = 3  # Maximum retry attempts


@dataclass
class MomentumSignal:
    """Momentum trading signal"""

    symbol: str
    current_price: float
    momentum_pct: float
    volume_24h: float
    quality_score: float
    confidence: float
    reasoning: str
    target_amount: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TradeResult:
    """Trade execution result"""

    success: bool
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    executed_qty: Optional[float] = None
    executed_price: Optional[float] = None
    commission: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MomentumTrader:
    """Advanced momentum trading system with risk management"""

    def __init__(
        self,
        config: Optional[TradingConfig] = None,
        mode: TradingMode = TradingMode.DEMO,
    ):
        """
        Initialize momentum trader

        Args:
            config: Trading configuration parameters
            mode: Trading mode (live/demo/paper)
        """
        load_dotenv()

        self.config = config or TradingConfig()
        self.mode = mode

        # API Configuration
        self.api_key = os.getenv("BINANCEUS_KEY")
        self.api_secret = os.getenv("BINANCEUS_SECRET")
        self.base_url = "https://api.binance.us"

        if not self.api_key or not self.api_secret:
            logger.warning("Binance API credentials not found - running in demo mode")
            self.mode = TradingMode.DEMO

        # Initialize Binance client for live trading
        if self.mode == TradingMode.LIVE:
            try:
                self.client = Client(self.api_key, self.api_secret, tld="us")
                logger.info("Connected to Binance US API")
            except Exception as e:
                logger.error(f"Failed to connect to Binance API: {e}")
                self.mode = TradingMode.DEMO

        # Trading state
        self.active_positions: Dict[str, Dict] = {}
        self.order_history: List[TradeResult] = []
        self.last_api_call = 0

        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_pnl = 0.0

        logger.info(f"MomentumTrader initialized in {self.mode.value} mode")

    def _rate_limit(self) -> None:
        """Implement API rate limiting"""
        elapsed = time.time() - self.last_api_call
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self.last_api_call = time.time()

    def _create_signature(self, params: Dict[str, Any]) -> str:
        """Create HMAC SHA256 signature for Binance API"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def get_account_balance(self) -> Dict[str, Dict[str, float]]:
        """
        Get account balance with comprehensive error handling

        Returns:
            Dictionary of asset balances
        """
        if self.mode == TradingMode.DEMO:
            return {
                "USDT": {"free": 1000.0, "locked": 0.0},
                "BTC": {"free": 0.0, "locked": 0.0},
            }

        try:
            self._rate_limit()

            if self.mode == TradingMode.LIVE:
                account_info = self.client.get_account()
                balances = {}

                for balance in account_info["balances"]:
                    free = float(balance["free"])
                    locked = float(balance["locked"])

                    if free > 0 or locked > 0:
                        balances[balance["asset"]] = {"free": free, "locked": locked}

                logger.info(f"Retrieved balances for {len(balances)} assets")
                return balances

        except BinanceAPIException as e:
            logger.error(f"Binance API error getting balance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting balance: {e}")

        return {}

    def get_usdt_balance(self) -> float:
        """
        Get available USDT balance

        Returns:
            Available USDT amount
        """
        try:
            balances = self.get_account_balance()
            usdt_balance = balances.get("USDT", {})
            return float(usdt_balance.get("free", 0.0))
        except Exception as e:
            logger.error(f"Error getting USDT balance: {e}")
            return 0.0

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for symbol

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')

        Returns:
            Current price or None if failed
        """
        try:
            self._rate_limit()

            if self.mode == TradingMode.LIVE:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker["price"])
            else:
                # Use public API for demo mode
                response = requests.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbol": symbol},
                    timeout=10,
                )

                if response.status_code == 200:
                    return float(response.json()["price"])

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")

        return None

    def calculate_position_size(
        self, symbol: str, momentum_pct: float, available_usdt: float
    ) -> float:
        """
        Calculate optimal position size based on momentum and risk

        Args:
            symbol: Trading symbol
            momentum_pct: Momentum percentage
            available_usdt: Available USDT

        Returns:
            Position size in USDT
        """
        try:
            # Base allocation based on momentum strength
            momentum_factor = min(momentum_pct / 30.0, 1.0)  # Scale to max 30%
            base_allocation = momentum_factor * 0.8  # Max 80% momentum allocation

            # Apply portfolio limits
            max_position = available_usdt * self.config.max_position_size
            calculated_size = available_usdt * base_allocation

            # Ensure minimum trade size
            position_size = max(
                min(calculated_size, max_position), self.config.min_trade_amount
            )

            logger.info(
                f"Calculated position size: ${position_size:.2f} "
                f"({position_size/available_usdt*100:.1f}% of portfolio)"
            )

            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return self.config.min_trade_amount

    def execute_momentum_trade(self, signal: MomentumSignal) -> TradeResult:
        """
        Execute momentum trade with comprehensive error handling

        Args:
            signal: Momentum trading signal

        Returns:
            Trade execution result
        """
        logger.info(f"🎯 Executing momentum trade for {signal.symbol}")
        logger.info(f"   Momentum: {signal.momentum_pct:.2f}%")
        logger.info(f"   Confidence: {signal.confidence:.2f}")
        logger.info(f"   Target: ${signal.target_amount:.2f}")

        if self.mode == TradingMode.DEMO:
            return TradeResult(
                success=True,
                order_id=f"DEMO_{int(time.time())}",
                symbol=signal.symbol,
                executed_qty=signal.target_amount / signal.current_price,
                executed_price=signal.current_price,
                commission=0.0,
            )

        try:
            self._rate_limit()

            # Execute market buy order
            order = self.client.order_market_buy(
                symbol=signal.symbol, quoteOrderQty=signal.target_amount
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

            result = TradeResult(
                success=True,
                order_id=order["orderId"],
                symbol=signal.symbol,
                executed_qty=executed_qty,
                executed_price=avg_price,
                commission=total_commission,
            )

            # Update tracking
            self.total_trades += 1
            self.successful_trades += 1
            self.order_history.append(result)

            # Track position
            self.active_positions[signal.symbol] = {
                "quantity": executed_qty,
                "entry_price": avg_price,
                "entry_time": datetime.now(),
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
            }

            logger.info(f"✅ Trade executed successfully:")
            logger.info(f"   Order ID: {result.order_id}")
            logger.info(f"   Quantity: {executed_qty:.6f}")
            logger.info(f"   Price: ${avg_price:.6f}")
            logger.info(f"   Commission: ${total_commission:.6f}")

            return result

        except BinanceOrderException as e:
            error_msg = f"Binance order error: {e}"
            logger.error(error_msg)
            self.total_trades += 1

            return TradeResult(
                success=False, symbol=signal.symbol, error_message=error_msg
            )

        except BinanceAPIException as e:
            error_msg = f"Binance API error: {e}"
            logger.error(error_msg)

            return TradeResult(
                success=False, symbol=signal.symbol, error_message=error_msg
            )

        except Exception as e:
            error_msg = f"Unexpected trading error: {e}"
            logger.error(error_msg)

            return TradeResult(
                success=False, symbol=signal.symbol, error_message=error_msg
            )

    def analyze_momentum_opportunity(
        self, symbol: str, market_data: Dict[str, Any]
    ) -> Optional[MomentumSignal]:
        """
        Analyze if symbol presents valid momentum opportunity

        Args:
            symbol: Trading symbol
            market_data: Market data dictionary

        Returns:
            MomentumSignal if opportunity found, None otherwise
        """
        try:
            price_change_24h = float(market_data.get("priceChangePercent", 0))
            volume_24h = float(market_data.get("quoteVolume", 0))
            current_price = float(market_data.get("lastPrice", 0))

            # Check momentum threshold
            if not (
                self.config.min_momentum_threshold
                <= price_change_24h
                <= self.config.max_momentum_threshold
            ):
                return None

            # Check volume threshold
            if volume_24h < self.config.volume_threshold:
                return None

            # Calculate quality score
            volume_score = min(volume_24h / 10000000.0, 1.0)  # Normalize to $10M
            momentum_score = min(price_change_24h / 30.0, 1.0)  # Normalize to 30%
            quality_score = (volume_score + momentum_score) / 2

            # Check quality threshold
            if quality_score < self.config.quality_threshold:
                return None

            # Calculate confidence based on momentum strength and volume
            confidence = min(
                (price_change_24h - self.config.min_momentum_threshold)
                / (
                    self.config.max_momentum_threshold
                    - self.config.min_momentum_threshold
                ),
                1.0,
            )

            # Calculate target amount
            available_usdt = self.get_usdt_balance()
            target_amount = self.calculate_position_size(
                symbol, price_change_24h, available_usdt
            )

            # Calculate stop loss and take profit
            stop_loss = current_price * (1 - self.config.stop_loss_pct)
            take_profit = current_price * (1 + self.config.take_profit_pct)

            return MomentumSignal(
                symbol=symbol,
                current_price=current_price,
                momentum_pct=price_change_24h,
                volume_24h=volume_24h,
                quality_score=quality_score,
                confidence=confidence,
                reasoning=f"Strong momentum {price_change_24h:.1f}% with high volume ${volume_24h/1000000:.1f}M",
                target_amount=target_amount,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        except Exception as e:
            logger.error(f"Error analyzing momentum for {symbol}: {e}")
            return None

    def scan_momentum_opportunities(self) -> List[MomentumSignal]:
        """
        Scan market for momentum opportunities

        Returns:
            List of momentum signals
        """
        opportunities = []

        try:
            logger.info("🔍 Scanning for momentum opportunities...")

            # Get 24hr ticker data
            if self.mode == TradingMode.LIVE:
                tickers = self.client.get_ticker()
            else:
                response = requests.get(
                    f"{self.base_url}/api/v3/ticker/24hr", timeout=10
                )
                if response.status_code == 200:
                    tickers = response.json()
                else:
                    logger.error("Failed to fetch ticker data")
                    return []

            # Filter USDT pairs
            usdt_tickers = [t for t in tickers if t["symbol"].endswith("USDT")]

            logger.info(f"Analyzing {len(usdt_tickers)} USDT pairs...")

            for ticker in usdt_tickers:
                signal = self.analyze_momentum_opportunity(ticker["symbol"], ticker)
                if signal:
                    opportunities.append(signal)

            # Sort by quality score and confidence
            opportunities.sort(
                key=lambda x: (x.quality_score * x.confidence), reverse=True
            )

            logger.info(f"Found {len(opportunities)} momentum opportunities")

            return opportunities[:5]  # Return top 5

        except Exception as e:
            logger.error(f"Error scanning momentum opportunities: {e}")
            return []

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get trading performance summary

        Returns:
            Performance metrics dictionary
        """
        success_rate = (
            self.successful_trades / self.total_trades * 100
            if self.total_trades > 0
            else 0
        )

        return {
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "success_rate": f"{success_rate:.1f}%",
            "total_pnl": self.total_pnl,
            "active_positions": len(self.active_positions),
            "mode": self.mode.value,
            "last_update": datetime.now().isoformat(),
        }

    def run_momentum_trading_session(self, duration_minutes: int = 60) -> None:
        """
        Run complete momentum trading session

        Args:
            duration_minutes: Session duration in minutes
        """
        logger.info(
            f"🚀 Starting momentum trading session ({duration_minutes} minutes)"
        )

        session_start = datetime.now()
        session_end = session_start + timedelta(minutes=duration_minutes)

        try:
            while datetime.now() < session_end:
                # Scan for opportunities
                opportunities = self.scan_momentum_opportunities()

                if opportunities:
                    logger.info(f"📊 Top momentum opportunity:")
                    top_signal = opportunities[0]
                    logger.info(
                        f"   {top_signal.symbol}: {top_signal.momentum_pct:.2f}%"
                    )
                    logger.info(f"   Quality: {top_signal.quality_score:.2f}")
                    logger.info(f"   Confidence: {top_signal.confidence:.2f}")

                    # Check if we should trade
                    if (
                        len(self.active_positions)
                        < self.config.max_concurrent_positions
                        and top_signal.target_amount >= self.config.min_trade_amount
                    ):

                        # Execute trade
                        result = self.execute_momentum_trade(top_signal)

                        if result.success:
                            logger.info("✅ Trade executed successfully")
                        else:
                            logger.error(f"❌ Trade failed: {result.error_message}")
                    else:
                        logger.info(
                            "⏸️ Skipping trade (position limits or insufficient funds)"
                        )
                else:
                    logger.info("📉 No momentum opportunities found")

                # Wait before next scan
                time.sleep(300)  # 5 minutes between scans

        except KeyboardInterrupt:
            logger.info("Session interrupted by user")
        except Exception as e:
            logger.error(f"Session error: {e}")
        finally:
            # Print final performance
            performance = self.get_performance_summary()
            logger.info("📈 Session Summary:")
            for key, value in performance.items():
                logger.info(f"   {key}: {value}")


def main():
    """Main execution function"""
    try:
        # Initialize trader
        config = TradingConfig(
            min_momentum_threshold=20.0,
            max_momentum_threshold=45.0,
            quality_threshold=0.7,
        )

        trader = MomentumTrader(config=config, mode=TradingMode.DEMO)

        # Run trading session
        trader.run_momentum_trading_session(duration_minutes=30)

    except Exception as e:
        logger.error(f"Main execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
