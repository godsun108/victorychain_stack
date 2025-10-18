#!/usr/bin/env python3

"""
BTC-FREE EXECUTION ENGINE
========================
Illiquidity-aware execution for micro-cap framework
- 4-leg simultaneous execution ladder
- Portfolio-flat execution in minutes
- Micro-cap liquidity optimization
- Real-time order management
"""

import ccxt
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import time
import logging
from dataclasses import dataclass, field
from enum import Enum

# --- Error Logging Setup ---
logging.basicConfig(
    filename="execution_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)


def log_error(msg):
    print(msg)
    logging.error(msg)


class OrderType(Enum):
    PASSIVE_MAKER = "passive_maker"
    HIDDEN_ICEBERG = "hidden_iceberg"
    SMART_LIMIT = "smart_limit"
    POV_TWAP = "pov_twap"


@dataclass
class ExecutionLeg:
    """Single execution leg"""

    leg_id: int
    order_type: OrderType
    symbol: str
    side: str  # 'buy' or 'sell'
    size_usd: float
    price: float
    participation_limit: float
    slice_size_pct: float
    target_pct: float
    status: str = "pending"
    filled_amount: float = 0.0
    avg_fill_price: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class PortfolioExecution:
    """Complete portfolio execution plan"""

    execution_id: str
    timestamp: datetime
    total_portfolio_value: float
    long_positions: Dict[str, float]
    hedge_positions: Dict[str, float]
    execution_legs: List[ExecutionLeg] = field(default_factory=list)
    status: str = "pending"
    target_completion_minutes: int = 5


class BTCFreeExecutionEngine:
    """
    Advanced execution engine for BTC-free micro-cap framework
    Implements illiquidity-aware ladder execution
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.active_executions: Dict[str, PortfolioExecution] = {}
        self.market_data: Dict[str, Dict] = {}

        # Execution parameters
        self.max_participation_rate = 0.10  # 10% max of book depth
        self.target_completion_time = 5  # 5 minutes target
        self.slice_interval = 30  # 30 seconds between slices

    def setup_exchange(self):
        """Initialize exchange with advanced order types"""
        try:
            self.exchange = ccxt.binanceus(
                {
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "sandbox": False,
                    "rateLimit": 1200,
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "spot",
                        "adjustForTimeDifference": True,
                    },
                }
            )
            print("✅ Execution engine initialized")
        except Exception as e:
            print(f"❌ Exchange setup failed: {e}")
            # Use paper trading mode
            self.exchange = ccxt.binanceus({"sandbox": True})

    async def get_orderbook_depth(self, symbol: str, limit: int = 100) -> Dict:
        """Get orderbook depth for liquidity analysis"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)

            # Calculate depth metrics
            bids = orderbook["bids"]
            asks = orderbook["asks"]

            bid_depth_5pct = (
                sum(qty for price, qty in bids if price >= bids[0][0] * 0.95)
                if bids
                else 0
            )
            ask_depth_5pct = (
                sum(qty for price, qty in asks if price <= asks[0][0] * 1.05)
                if asks
                else 0
            )

            spread = (
                (asks[0][0] - bids[0][0]) / bids[0][0] * 100 if bids and asks else 0
            )

            return {
                "bid_depth_5pct": bid_depth_5pct,
                "ask_depth_5pct": ask_depth_5pct,
                "spread_pct": spread,
                "best_bid": bids[0][0] if bids else 0,
                "best_ask": asks[0][0] if asks else 0,
                "total_bid_depth": sum(qty for _, qty in bids),
                "total_ask_depth": sum(qty for _, qty in asks),
            }

        except Exception as e:
            print(f"❌ Failed to get orderbook for {symbol}: {e}")
            return {}

    async def calculate_atr(self, symbol: str, periods: int = 14) -> float:
        """Calculate Average True Range for smart limit orders"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, "1h", limit=periods + 1)

            if len(ohlcv) < periods:
                return 0.0

            true_ranges = []
            for i in range(1, len(ohlcv)):
                high = ohlcv[i][2]
                low = ohlcv[i][3]
                prev_close = ohlcv[i - 1][4]

                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                true_ranges.append(tr)

            return np.mean(true_ranges)

        except Exception as e:
            return 0.0

    def create_execution_legs(
        self,
        symbol: str,
        side: str,
        total_size_usd: float,
        current_price: float,
        orderbook: Dict,
        atr: float,
    ) -> List[ExecutionLeg]:
        """
        Create 4-leg execution ladder
        """
        legs = []

        # Leg 1: Passive maker (30%)
        leg_1 = ExecutionLeg(
            leg_id=1,
            order_type=OrderType.PASSIVE_MAKER,
            symbol=symbol,
            side=side,
            size_usd=total_size_usd * 0.30,
            price=current_price * (0.9975 if side == "buy" else 1.0025),  # ±0.25%
            participation_limit=0.05,  # 5% of book depth
            slice_size_pct=0.005,  # 0.5% of daily volume
            target_pct=30,
        )
        legs.append(leg_1)

        # Leg 2: Hidden iceberg at prior high (20%)
        if side == "buy":
            # For longs, place at resistance level
            leg_2_price = current_price * 1.02  # 2% above current
        else:
            # For shorts, place at support level
            leg_2_price = current_price * 0.98  # 2% below current

        leg_2 = ExecutionLeg(
            leg_id=2,
            order_type=OrderType.HIDDEN_ICEBERG,
            symbol=symbol,
            side=side,
            size_usd=total_size_usd * 0.20,
            price=leg_2_price,
            participation_limit=0.08,  # 8% of book depth
            slice_size_pct=0.01,  # 1% of daily volume
            target_pct=20,
        )
        legs.append(leg_2)

        # Leg 3: Smart limit on 0.5x ATR dip (30%)
        if side == "buy":
            leg_3_price = current_price - (0.5 * atr)
        else:
            leg_3_price = current_price + (0.5 * atr)

        leg_3 = ExecutionLeg(
            leg_id=3,
            order_type=OrderType.SMART_LIMIT,
            symbol=symbol,
            side=side,
            size_usd=total_size_usd * 0.30,
            price=leg_3_price,
            participation_limit=0.08,  # 8% of book depth
            slice_size_pct=0.01,  # 1% of daily volume
            target_pct=30,
        )
        legs.append(leg_3)

        # Leg 4: PoV-TWAP over 45 minutes (20%)
        leg_4 = ExecutionLeg(
            leg_id=4,
            order_type=OrderType.POV_TWAP,
            symbol=symbol,
            side=side,
            size_usd=total_size_usd * 0.20,
            price=current_price,  # Market price
            participation_limit=0.10,  # 10% max participation
            slice_size_pct=0.02,  # 2% of daily volume
            target_pct=20,
        )
        legs.append(leg_4)

        return legs

    async def execute_passive_maker(self, leg: ExecutionLeg) -> Dict:
        """Execute passive maker leg"""
        print(f"  🎯 Leg 1: Passive maker ${leg.size_usd:,.0f} @ ${leg.price:.6f}")
        try:
            quantity = leg.size_usd / leg.price
            min_amount = self.exchange.markets[leg.symbol]["limits"]["amount"]["min"]
            if quantity < min_amount:
                print(
                    f"❌ Order amount {quantity:.4f} is below minimum ({min_amount}) for {leg.symbol}. Skipping."
                )
                leg.status = "failed"
                return {}
            order = {
                "symbol": leg.symbol,
                "side": leg.side,
                "amount": quantity,
                "price": leg.price,
                "type": "limit",
                "timeInForce": "GTC",
            }
            # In live trading: result = self.exchange.create_order(**order)
            result = {
                "id": f"passive_{leg.symbol}_{int(time.time())}",
                "status": "open",
                "filled": 0,
                "remaining": quantity,
            }
            leg.status = "submitted"
            leg.start_time = datetime.now()
            return result
        except Exception as e:
            log_error(f"❌ Passive maker failed: {e}")
            leg.status = "failed"
            return {}

    async def execute_hidden_iceberg(self, leg: ExecutionLeg) -> Dict:
        """Execute hidden iceberg leg"""
        print(f"  🧊 Leg 2: Hidden iceberg ${leg.size_usd:,.0f} @ ${leg.price:.6f}")
        try:
            total_quantity = leg.size_usd / leg.price
            min_amount = self.exchange.markets[leg.symbol]["limits"]["amount"]["min"]
            if total_quantity < min_amount:
                print(
                    f"❌ Order amount {total_quantity:.4f} is below minimum ({min_amount}) for {leg.symbol}. Skipping."
                )
                leg.status = "failed"
                return {}
            chunk_size = total_quantity * 0.1  # 10% chunks
            results = []
            for i in range(10):  # 10 chunks
                chunk_order = {
                    "symbol": leg.symbol,
                    "side": leg.side,
                    "amount": chunk_size,
                    "price": leg.price,
                    "type": "limit",
                    "timeInForce": "IOC",
                }
                # In live trading: result = self.exchange.create_order(**chunk_order)
                result = {
                    "id": f"iceberg_{leg.symbol}_{i}_{int(time.time())}",
                    "status": "filled",
                    "filled": chunk_size * 0.8,
                    "remaining": chunk_size * 0.2,
                }
                results.append(result)
                await asyncio.sleep(5)
            leg.status = "executed"
            leg.end_time = datetime.now()
            leg.filled_amount = sum(r["filled"] for r in results)
            return {"chunks": results, "total_filled": leg.filled_amount}
        except Exception as e:
            print(f"❌ Iceberg execution failed: {e}")
            leg.status = "failed"
            return {}

    async def execute_smart_limit(self, leg: ExecutionLeg) -> Dict:
        """Execute smart limit on ATR dip"""
        print(f"  🎯 Leg 3: Smart limit ${leg.size_usd:,.0f} @ ${leg.price:.6f}")
        try:
            quantity = leg.size_usd / leg.price
            min_amount = self.exchange.markets[leg.symbol]["limits"]["amount"]["min"]
            if quantity < min_amount:
                print(
                    f"❌ Order amount {quantity:.4f} is below minimum ({min_amount}) for {leg.symbol}. Skipping."
                )
                leg.status = "failed"
                return {}
            order = {
                "symbol": leg.symbol,
                "side": leg.side,
                "amount": quantity,
                "price": leg.price,
                "type": "limit",
                "timeInForce": "GTC",
            }
            # Monitor and adjust price if needed
            # In live trading: result = self.exchange.create_order(**order)
            result = {
                "id": f"smart_{leg.symbol}_{int(time.time())}",
                "status": "partially_filled",
                "filled": quantity * 0.6,
                "remaining": quantity * 0.4,
            }
            leg.status = "partially_filled"
            leg.filled_amount = result["filled"]
            return result
        except Exception as e:
            print(f"❌ Smart limit failed: {e}")
            leg.status = "failed"
            return {}

    async def execute_pov_twap(self, leg: ExecutionLeg) -> Dict:
        """Execute Percentage of Volume TWAP"""
        print(f"  📊 Leg 4: PoV-TWAP ${leg.size_usd:,.0f} over 45 minutes")
        try:
            total_quantity = leg.size_usd / leg.price
            min_amount = self.exchange.markets[leg.symbol]["limits"]["amount"]["min"]
            if total_quantity < min_amount:
                print(
                    f"❌ Order amount {total_quantity:.4f} is below minimum ({min_amount}) for {leg.symbol}. Skipping."
                )
                leg.status = "failed"
                return {}
            duration_minutes = 45
            slices = duration_minutes * 2
            slice_quantity = total_quantity / slices
            filled_total = 0
            for i in range(min(10, slices)):
                ticker = self.exchange.fetch_ticker(leg.symbol)
                current_volume = float(ticker.get("quoteVolume", 0))
                max_slice = current_volume * leg.participation_limit / slices
                actual_slice = min(slice_quantity, max_slice)
                slice_order = {
                    "symbol": leg.symbol,
                    "side": leg.side,
                    "amount": actual_slice,
                    "type": "market",
                }
                # In live trading: result = self.exchange.create_order(**slice_order)
                filled_total += actual_slice * 0.95
                await asyncio.sleep(30)
            leg.status = "executed"
            leg.end_time = datetime.now()
            leg.filled_amount = filled_total
            return {"slices_executed": 10, "total_filled": filled_total}
        except Exception as e:
            print(f"❌ PoV-TWAP failed: {e}")
            leg.status = "failed"
            return {}

    MAX_POSITION_SIZE_USD = 10000  # Place this near the top of your file

    async def execute_single_token(
        self, symbol: str, side: str, target_size_usd: float
    ):
        """Execute complete 4-leg ladder for single token"""
        print(f"\n🎯 Executing {side} ladder for {symbol}: ${target_size_usd:,.0f}")

        if target_size_usd > self.MAX_POSITION_SIZE_USD:
            log_error(
                f"Position size ${target_size_usd} exceeds max allowed for {symbol}. Skipping."
            )
            return {}

        try:
            # Get market data
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = float(ticker["last"])

            # Get orderbook depth
            orderbook = await self.get_orderbook_depth(symbol)

            # Calculate ATR
            atr = await self.calculate_atr(symbol)

            # Create execution legs
            legs = self.create_execution_legs(
                symbol, side, target_size_usd, current_price, orderbook, atr
            )

            # Execute all legs simultaneously
            tasks = []
            for leg in legs:
                if leg.order_type == OrderType.PASSIVE_MAKER:
                    tasks.append(self.execute_passive_maker(leg))
                elif leg.order_type == OrderType.HIDDEN_ICEBERG:
                    tasks.append(self.execute_hidden_iceberg(leg))
                elif leg.order_type == OrderType.SMART_LIMIT:
                    tasks.append(self.execute_smart_limit(leg))
                elif leg.order_type == OrderType.POV_TWAP:
                    tasks.append(self.execute_pov_twap(leg))

            # Execute all legs in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Calculate total fill
            total_filled_usd = sum(leg.filled_amount * current_price for leg in legs)
            fill_percentage = (total_filled_usd / target_size_usd) * 100

            print(f"✅ {symbol} execution complete: {fill_percentage:.1f}% filled")

            return {
                "symbol": symbol,
                "target_size_usd": target_size_usd,
                "filled_size_usd": total_filled_usd,
                "fill_percentage": fill_percentage,
                "legs": legs,
                "execution_results": results,
            }

        except Exception as e:
            print(f"❌ Execution failed for {symbol}: {e}")
            return {}

    async def execute_portfolio_ladder(
        self, long_positions: Dict[str, float], hedge_positions: Dict[str, float]
    ):
        """
        Execute complete portfolio with simultaneous ladders
        Achieve portfolio-flat execution in minutes
        """
        print("🚀 EXECUTING PORTFOLIO LADDER")
        print("=" * 40)

        execution_id = f"exec_{int(time.time())}"
        start_time = datetime.now()

        # Create portfolio execution plan
        portfolio_execution = PortfolioExecution(
            execution_id=execution_id,
            timestamp=start_time,
            total_portfolio_value=sum(long_positions.values())
            + sum(hedge_positions.values()),
            long_positions=long_positions,
            hedge_positions=hedge_positions,
        )

        self.active_executions[execution_id] = portfolio_execution

        # Prepare all execution tasks
        execution_tasks = []

        # Long positions
        for symbol, size_usd in long_positions.items():
            if size_usd > 1000:  # Min $1k position
                execution_tasks.append(
                    self.execute_single_token(symbol, "buy", size_usd)
                )

        # Hedge positions (shorts)
        for symbol, size_usd in hedge_positions.items():
            if size_usd > 1000:  # Min $1k position
                execution_tasks.append(
                    self.execute_single_token(symbol, "sell", size_usd)
                )

        print(f"📊 Executing {len(execution_tasks)} positions simultaneously...")

        # Execute entire portfolio simultaneously
        portfolio_results = await asyncio.gather(
            *execution_tasks, return_exceptions=True
        )

        execution_time = datetime.now() - start_time

        # Calculate portfolio execution summary
        total_target = portfolio_execution.total_portfolio_value
        total_filled = sum(
            r.get("filled_size_usd", 0)
            for r in portfolio_results
            if isinstance(r, dict)
        )
        portfolio_fill_rate = (
            (total_filled / total_target) * 100 if total_target > 0 else 0
        )

        portfolio_execution.status = "completed"

        execution_summary = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "execution_time_seconds": execution_time.total_seconds(),
            "target_completion_minutes": portfolio_execution.target_completion_minutes,
            "portfolio_summary": {
                "total_positions": len(execution_tasks),
                "long_positions": len(long_positions),
                "hedge_positions": len(hedge_positions),
                "total_target_usd": total_target,
                "total_filled_usd": total_filled,
                "portfolio_fill_rate": portfolio_fill_rate,
            },
            "position_results": portfolio_results,
            "execution_efficiency": {
                "time_vs_target": execution_time.total_seconds()
                / (portfolio_execution.target_completion_minutes * 60),
                "fill_rate_vs_target": portfolio_fill_rate / 95.0,  # Target 95% fill
                "parallel_execution": True,
                "portfolio_flat_achieved": execution_time.total_seconds()
                < 300,  # <5 minutes
            },
        }

        # Save execution report
        with open(f"execution_report_{execution_id}.json", "w") as f:
            json.dump(execution_summary, f, indent=2, default=str)

        print(f"\n📊 EXECUTION SUMMARY")
        print("=" * 25)
        print(f"Execution ID: {execution_id}")
        print(f"Execution time: {execution_time.total_seconds():.1f} seconds")
        print(f"Target positions: {len(execution_tasks)}")
        print(f"Portfolio fill rate: {portfolio_fill_rate:.1f}%")
        print(
            f"Portfolio flat: {'✅' if execution_time.total_seconds() < 300 else '❌'}"
        )
        print(f"💾 Report saved: execution_report_{execution_id}.json")

        return execution_summary


class MultiTimeframeMomentum:
    def __init__(self, exchange, min_momentum=0.01, lookback=24, top_n=10):
        self.exchange = exchange
        self.min_momentum = min_momentum
        self.lookback = lookback
        self.top_n = top_n

    # ...rest of the class...


async def demo_execution_engine():
    """Demo the BTC-free execution engine"""
    print("🎭 DEMO: BTC-Free Execution Engine")
    print("=" * 40)

    engine = BTCFreeExecutionEngine()
    engine.setup_exchange()

    # Example portfolio
    long_positions = {
        "ADAUSDT": 15000,
        "DOGEUSDT": 12000,
        "LTCUSDT": 18000,
        "SOLUSDT": 20000,
        "XLMUSDT": 10000,
    }

    hedge_positions = {
        "SHIBUSDT": 8000,
        "FLOKIUSDT": 6000,
        "BONKUSDT": 7000,
        "PEPEUSDT": 5000,
    }

    await engine.execute_portfolio_ladder(long_positions, hedge_positions)


if __name__ == "__main__":
    asyncio.run(demo_execution_engine())
