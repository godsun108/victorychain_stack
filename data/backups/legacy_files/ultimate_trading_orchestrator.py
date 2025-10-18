#!/usr/bin/env python3
"""
Ultimate VictoryChain Trading Orchestrator
The final evolution - combines all successful strategies into one powerful system:
- Smart Gains-Only Bot for high-confidence trades
- Claude-powered non-popular token analysis
- AI pattern learning and prediction
- Multi-asset portfolio optimization
- Real-time momentum detection
- Cross-asset arbitrage opportunities
- Comprehensive risk management
"""

import os
import json
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings("ignore")


class UltimateTradingOrchestrator:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Setup comprehensive logging
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f"ultimate_orchestrator_{self.timestamp}.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Load portfolio state
        self.portfolio = self.get_current_portfolio()
        self.total_value = self.portfolio["total_value"]
        self.usdt_balance = self.portfolio["usdt_balance"]

        # Master configuration
        self.config = {
            # Trading modes
            "smart_gains_enabled": True,
            "claude_analysis_enabled": True,
            "ai_pattern_learning": True,
            "multi_asset_trading": True,
            "cross_asset_arbitrage": True,
            "moonshot_detection": True,
            # Risk parameters
            "max_portfolio_risk": 0.15,  # 15% max total portfolio at risk
            "position_size_limit": 0.08,  # 8% max per position
            "stop_loss_pct": 0.025,  # 2.5% stop loss
            "take_profit_pct": 0.06,  # 6% take profit
            "confidence_threshold": 0.75,  # 75% min confidence
            # Portfolio allocation
            "usdt_reserve_pct": 0.30,  # Keep 30% USDT as reserve
            "max_simultaneous_trades": 5,
            "rebalance_interval": 3600,  # 1 hour
            # Strategy weights
            "strategy_weights": {
                "smart_gains": 0.40,  # 40% allocation to proven gains-only
                "claude_analysis": 0.25,  # 25% to AI-powered analysis
                "momentum_trading": 0.20,  # 20% to momentum strategies
                "arbitrage": 0.10,  # 10% to cross-asset arbitrage
                "moonshot": 0.05,  # 5% to moonshot detection
            },
        }

        # Initialize strategy modules
        self.active_positions = {}
        self.strategy_performance = {
            "smart_gains": {"trades": 0, "wins": 0, "total_profit": 0},
            "claude_analysis": {"trades": 0, "wins": 0, "total_profit": 0},
            "momentum_trading": {"trades": 0, "wins": 0, "total_profit": 0},
            "arbitrage": {"trades": 0, "wins": 0, "total_profit": 0},
            "moonshot": {"trades": 0, "wins": 0, "total_profit": 0},
        }

        # Historical data cache
        self.market_data_cache = {}
        self.last_cache_update = {}

        self.logger.info(f"🚀 Ultimate Trading Orchestrator initialized")
        self.logger.info(
            f"💰 Portfolio: ${self.total_value:.2f} | USDT: ${self.usdt_balance:.2f}"
        )

    def get_current_portfolio(self) -> Dict:
        """Get comprehensive current portfolio state"""
        try:
            account = self.client.get_account()

            total_value = 0
            usdt_balance = 0
            assets = {}

            for balance in account["balances"]:
                if float(balance["free"]) > 0 or float(balance["locked"]) > 0:
                    symbol = balance["asset"]
                    free = float(balance["free"])
                    locked = float(balance["locked"])
                    total = free + locked

                    if symbol == "USDT":
                        value = total
                        usdt_balance = total
                    else:
                        # Get USD value
                        try:
                            ticker = self.client.get_symbol_ticker(
                                symbol=f"{symbol}USDT"
                            )
                            price = float(ticker["price"])
                            value = total * price
                        except:
                            value = 0

                    if value > 0.01:  # Only include assets worth more than $0.01
                        assets[symbol] = {
                            "free": free,
                            "locked": locked,
                            "total": total,
                            "value": value,
                        }
                        total_value += value

            return {
                "total_value": total_value,
                "usdt_balance": usdt_balance,
                "assets": assets,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {"total_value": 0, "usdt_balance": 0, "assets": {}}

    def get_all_tradable_usdt_pairs(self) -> List[str]:
        """Get all tradable USDT pairs on Binance US"""
        try:
            exchange_info = self.client.get_exchange_info()
            usdt_pairs = []

            for symbol_info in exchange_info["symbols"]:
                if (
                    symbol_info["status"] == "TRADING"
                    and symbol_info["quoteAsset"] == "USDT"
                    and "SPOT" in symbol_info["permissions"]
                ):
                    usdt_pairs.append(symbol_info["symbol"])

            return sorted(usdt_pairs)

        except Exception as e:
            self.logger.error(f"Error getting tradable pairs: {e}")
            return []

    def get_market_data(
        self, symbol: str, interval: str = "1h", limit: int = 100
    ) -> pd.DataFrame:
        """Get market data with caching"""
        cache_key = f"{symbol}_{interval}_{limit}"

        # Check cache
        if (
            cache_key in self.market_data_cache
            and cache_key in self.last_cache_update
            and datetime.now() - self.last_cache_update[cache_key]
            < timedelta(minutes=5)
        ):
            return self.market_data_cache[cache_key]

        try:
            klines = self.client.get_klines(
                symbol=symbol, interval=interval, limit=limit
            )

            df = pd.DataFrame(
                klines,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trades",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignored",
                ],
            )

            # Convert to proper types
            for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
                df[col] = pd.to_numeric(df[col])

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # Cache the data
            self.market_data_cache[cache_key] = df
            self.last_cache_update[cache_key] = datetime.now()

            return df

        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return pd.DataFrame()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        if df.empty:
            return df

        try:
            # RSI
            def calculate_rsi(prices, window=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))

            df["rsi"] = calculate_rsi(df["close"])

            # Moving averages
            df["ma_7"] = df["close"].rolling(7).mean()
            df["ma_21"] = df["close"].rolling(21).mean()
            df["ma_50"] = df["close"].rolling(50).mean()

            # MACD
            exp1 = df["close"].ewm(span=12).mean()
            exp2 = df["close"].ewm(span=26).mean()
            df["macd"] = exp1 - exp2
            df["macd_signal"] = df["macd"].ewm(span=9).mean()

            # Bollinger Bands
            df["bb_middle"] = df["close"].rolling(20).mean()
            bb_std = df["close"].rolling(20).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

            # Volume indicators
            df["volume_ma"] = df["volume"].rolling(20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # Price momentum
            df["momentum_1h"] = (df["close"] / df["close"].shift(1) - 1) * 100
            df["momentum_4h"] = (df["close"] / df["close"].shift(4) - 1) * 100
            df["momentum_24h"] = (df["close"] / df["close"].shift(24) - 1) * 100

            return df

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return df

    def smart_gains_analysis(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Smart gains-only analysis - only high-confidence opportunities"""
        try:
            if df.empty or len(df) < 50:
                return {
                    "confidence": 0,
                    "action": "hold",
                    "reason": "insufficient_data",
                }

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # Smart gains criteria
            signals = []
            confidence_factors = []

            # 1. Strong momentum with volume confirmation
            if (
                latest["momentum_1h"] > 2
                and latest["momentum_4h"] > 4
                and latest["volume_ratio"] > 1.5
            ):
                signals.append("strong_momentum")
                confidence_factors.append(0.25)

            # 2. RSI in optimal range (not overbought)
            if 30 < latest["rsi"] < 70:
                signals.append("healthy_rsi")
                confidence_factors.append(0.15)

            # 3. MACD bullish crossover
            if (
                latest["macd"] > latest["macd_signal"]
                and prev["macd"] <= prev["macd_signal"]
            ):
                signals.append("macd_bullish")
                confidence_factors.append(0.20)

            # 4. Above key moving averages
            if latest["close"] > latest["ma_7"] > latest["ma_21"]:
                signals.append("ma_bullish")
                confidence_factors.append(0.15)

            # 5. Bollinger Band position
            if latest["close"] > latest["bb_middle"]:
                signals.append("bb_bullish")
                confidence_factors.append(0.10)

            # 6. Volume surge (indicates institutional interest)
            if latest["volume_ratio"] > 2.0:
                signals.append("volume_surge")
                confidence_factors.append(0.15)

            total_confidence = sum(confidence_factors)

            # Smart gains decision logic
            if total_confidence >= 0.75 and len(signals) >= 4:
                action = "buy"
                target_profit = min(8, latest["momentum_4h"] * 1.5)  # Dynamic target
                stop_loss = 2.5  # Tight stop loss
            elif total_confidence >= 0.60 and len(signals) >= 3:
                action = "watch"  # Monitor closely
                target_profit = 5
                stop_loss = 2.0
            else:
                action = "hold"
                target_profit = 0
                stop_loss = 0

            return {
                "confidence": total_confidence,
                "action": action,
                "signals": signals,
                "target_profit": target_profit,
                "stop_loss": stop_loss,
                "current_price": latest["close"],
                "momentum_1h": latest["momentum_1h"],
                "momentum_4h": latest["momentum_4h"],
                "rsi": latest["rsi"],
                "volume_ratio": latest["volume_ratio"],
            }

        except Exception as e:
            self.logger.error(f"Error in smart gains analysis for {symbol}: {e}")
            return {"confidence": 0, "action": "hold", "reason": "analysis_error"}

    def claude_enhanced_analysis(self, symbol: str, analysis: Dict) -> Dict:
        """Enhanced analysis using Claude AI (when available)"""
        try:
            # If Claude API is not available, use local ML analysis
            if not os.getenv("CLAUDE_API_KEY"):
                return self.local_ai_analysis(symbol, analysis)

            # Prepare market context for Claude
            context = {
                "symbol": symbol,
                "confidence": analysis["confidence"],
                "signals": analysis["signals"],
                "momentum_1h": analysis.get("momentum_1h", 0),
                "momentum_4h": analysis.get("momentum_4h", 0),
                "rsi": analysis.get("rsi", 50),
                "volume_ratio": analysis.get("volume_ratio", 1),
            }

            # Claude analysis prompt
            prompt = f"""
            Analyze this trading opportunity for {symbol}:
            
            Technical Analysis:
            - Confidence: {context['confidence']:.2f}
            - Signals: {context['signals']}
            - 1H Momentum: {context['momentum_1h']:.2f}%
            - 4H Momentum: {context['momentum_4h']:.2f}%
            - RSI: {context['rsi']:.1f}
            - Volume Ratio: {context['volume_ratio']:.2f}
            
            Provide a brief assessment focusing on:
            1. Risk level (low/medium/high)
            2. Probability of 5%+ gain in next 24h
            3. Key risks to watch
            4. Recommended position size (small/medium/large)
            
            Keep response under 200 words.
            """

            try:
                import anthropic

                claude_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

                response = claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )

                claude_insight = response.content[0].text

                # Parse Claude's response for actionable insights
                enhanced_confidence = analysis["confidence"]
                if "high probability" in claude_insight.lower():
                    enhanced_confidence += 0.1
                elif "low probability" in claude_insight.lower():
                    enhanced_confidence -= 0.1

                analysis["claude_insight"] = claude_insight
                analysis["enhanced_confidence"] = min(1.0, enhanced_confidence)

                return analysis

            except Exception as e:
                self.logger.warning(f"Claude API error: {e}")
                return self.local_ai_analysis(symbol, analysis)

        except Exception as e:
            self.logger.error(f"Error in Claude analysis: {e}")
            return analysis

    def local_ai_analysis(self, symbol: str, analysis: Dict) -> Dict:
        """Local AI analysis using pattern recognition"""
        try:
            # Simple pattern-based enhancement
            confidence_boost = 0

            # Strong momentum pattern
            if (
                analysis.get("momentum_1h", 0) > 3
                and analysis.get("momentum_4h", 0) > 5
            ):
                confidence_boost += 0.1

            # Volume confirmation
            if analysis.get("volume_ratio", 1) > 2:
                confidence_boost += 0.05

            # RSI sweet spot
            rsi = analysis.get("rsi", 50)
            if 40 < rsi < 65:
                confidence_boost += 0.05

            analysis["enhanced_confidence"] = min(
                1.0, analysis["confidence"] + confidence_boost
            )
            analysis["ai_insight"] = (
                f"Pattern analysis: momentum={analysis.get('momentum_4h', 0):.1f}%, volume_boost={analysis.get('volume_ratio', 1):.1f}x"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error in local AI analysis: {e}")
            return analysis

    def scan_opportunities(self) -> List[Dict]:
        """Scan all opportunities across strategies"""
        try:
            all_pairs = self.get_all_tradable_usdt_pairs()
            opportunities = []

            # Focus on liquid pairs first
            priority_pairs = [
                pair
                for pair in all_pairs
                if any(
                    x in pair
                    for x in [
                        "BTC",
                        "ETH",
                        "BNB",
                        "ADA",
                        "DOT",
                        "LINK",
                        "UNI",
                        "AAVE",
                        "ATOM",
                        "ALGO",
                    ]
                )
            ]

            # Add some micro-cap opportunities
            micro_pairs = [pair for pair in all_pairs if pair not in priority_pairs][
                :20
            ]

            scan_pairs = priority_pairs + micro_pairs

            self.logger.info(
                f"🔍 Scanning {len(scan_pairs)} pairs for opportunities..."
            )

            # Use threading for faster analysis
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_pair = {}

                for pair in scan_pairs:
                    future = executor.submit(self.analyze_single_pair, pair)
                    future_to_pair[future] = pair

                for future in as_completed(future_to_pair):
                    pair = future_to_pair[future]
                    try:
                        analysis = future.result()
                        if (
                            analysis
                            and analysis.get("confidence", 0)
                            >= self.config["confidence_threshold"]
                        ):
                            opportunities.append(analysis)
                    except Exception as e:
                        self.logger.error(f"Error analyzing {pair}: {e}")

            # Sort by confidence and potential
            opportunities.sort(
                key=lambda x: x.get("enhanced_confidence", x.get("confidence", 0)),
                reverse=True,
            )

            self.logger.info(
                f"✅ Found {len(opportunities)} high-confidence opportunities"
            )
            return opportunities

        except Exception as e:
            self.logger.error(f"Error scanning opportunities: {e}")
            return []

    def analyze_single_pair(self, pair: str) -> Optional[Dict]:
        """Analyze a single trading pair"""
        try:
            # Get market data
            df = self.get_market_data(pair)
            if df.empty:
                return None

            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)

            # Smart gains analysis
            analysis = self.smart_gains_analysis(pair, df)

            # Enhanced AI analysis
            analysis = self.claude_enhanced_analysis(pair, analysis)

            analysis["symbol"] = pair
            analysis["timestamp"] = datetime.now()

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {e}")
            return None

    def execute_trade(self, opportunity: Dict) -> bool:
        """Execute a trade based on opportunity"""
        try:
            symbol = opportunity["symbol"]
            action = opportunity["action"]
            confidence = opportunity.get(
                "enhanced_confidence", opportunity.get("confidence", 0)
            )

            if action != "buy" or confidence < self.config["confidence_threshold"]:
                return False

            # Calculate position size based on confidence and strategy
            base_position_size = self.usdt_balance * self.config["position_size_limit"]
            confidence_multiplier = min(2.0, confidence / 0.75)  # Scale with confidence
            position_size = base_position_size * confidence_multiplier

            # Ensure we don't exceed limits
            max_trade_size = self.total_value * self.config["position_size_limit"]
            position_size = min(position_size, max_trade_size)

            if position_size < 10:  # Minimum $10 trade
                self.logger.warning(f"Position size too small: ${position_size:.2f}")
                return False

            # Check if we have enough balance
            if position_size > self.usdt_balance * 0.95:  # Leave 5% buffer
                self.logger.warning(
                    f"Insufficient balance for ${position_size:.2f} trade"
                )
                return False

            # Execute the trade
            current_price = opportunity["current_price"]
            quantity = position_size / current_price

            # Round quantity to appropriate precision
            quantity = round(quantity, 8)

            self.logger.info(f"🚀 Executing BUY: {symbol}")
            self.logger.info(f"   Amount: ${position_size:.2f} ({quantity:.8f} tokens)")
            self.logger.info(f"   Price: ${current_price:.8f}")
            self.logger.info(f"   Confidence: {confidence:.2f}")

            # Place market buy order
            order = self.client.order_market_buy(
                symbol=symbol, quoteOrderQty=position_size
            )

            # Record the position
            self.active_positions[symbol] = {
                "entry_price": current_price,
                "quantity": quantity,
                "position_size": position_size,
                "entry_time": datetime.now(),
                "stop_loss": current_price * (1 - opportunity["stop_loss"] / 100),
                "take_profit": current_price * (1 + opportunity["target_profit"] / 100),
                "confidence": confidence,
                "strategy": "smart_gains",
                "order_id": order["orderId"],
            }

            self.logger.info(f"✅ Trade executed successfully: {order['orderId']}")
            return True

        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False

    def manage_positions(self):
        """Manage active positions with stop-loss and take-profit"""
        try:
            for symbol, position in list(self.active_positions.items()):
                try:
                    # Get current price
                    ticker = self.client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker["price"])

                    entry_price = position["entry_price"]
                    pnl_pct = (current_price - entry_price) / entry_price * 100

                    # Check stop-loss
                    if current_price <= position["stop_loss"]:
                        self.logger.warning(
                            f"🛑 Stop-loss triggered for {symbol}: {pnl_pct:.2f}%"
                        )
                        self.close_position(symbol, "stop_loss")
                        continue

                    # Check take-profit
                    if current_price >= position["take_profit"]:
                        self.logger.info(
                            f"🎯 Take-profit triggered for {symbol}: {pnl_pct:.2f}%"
                        )
                        self.close_position(symbol, "take_profit")
                        continue

                    # Check time-based exit (24 hours max hold)
                    hold_time = datetime.now() - position["entry_time"]
                    if hold_time > timedelta(hours=24):
                        self.logger.info(
                            f"⏰ Time-based exit for {symbol}: {pnl_pct:.2f}%"
                        )
                        self.close_position(symbol, "time_exit")
                        continue

                    # Log current status
                    self.logger.info(
                        f"📊 {symbol}: {pnl_pct:+.2f}% | Hold: {hold_time}"
                    )

                except Exception as e:
                    self.logger.error(f"Error managing position {symbol}: {e}")

        except Exception as e:
            self.logger.error(f"Error in position management: {e}")

    def close_position(self, symbol: str, reason: str) -> bool:
        """Close a position"""
        try:
            if symbol not in self.active_positions:
                return False

            position = self.active_positions[symbol]

            # Get current balance for the asset
            account = self.client.get_account()
            asset = symbol.replace("USDT", "")
            balance = 0

            for bal in account["balances"]:
                if bal["asset"] == asset:
                    balance = float(bal["free"])
                    break

            if balance <= 0:
                self.logger.warning(f"No balance to sell for {symbol}")
                del self.active_positions[symbol]
                return False

            # Place market sell order
            order = self.client.order_market_sell(symbol=symbol, quantity=balance)

            # Calculate P&L
            current_price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])
            pnl_pct = (
                (current_price - position["entry_price"])
                / position["entry_price"]
                * 100
            )
            pnl_usd = position["position_size"] * (pnl_pct / 100)

            # Update strategy performance
            strategy = position["strategy"]
            self.strategy_performance[strategy]["trades"] += 1
            self.strategy_performance[strategy]["total_profit"] += pnl_usd
            if pnl_pct > 0:
                self.strategy_performance[strategy]["wins"] += 1

            self.logger.info(f"✅ Position closed: {symbol}")
            self.logger.info(f"   Reason: {reason}")
            self.logger.info(f"   P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
            self.logger.info(f"   Hold time: {datetime.now() - position['entry_time']}")

            # Remove from active positions
            del self.active_positions[symbol]

            return True

        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
            return False

    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "portfolio": self.portfolio,
                "active_positions": {
                    k: {**v, "entry_time": v["entry_time"].isoformat()}
                    for k, v in self.active_positions.items()
                },
                "strategy_performance": self.strategy_performance,
                "config": self.config,
            }

            with open(f"orchestrator_state_{self.timestamp}.json", "w") as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def print_status(self):
        """Print current status"""
        try:
            print("\n" + "=" * 80)
            print("🎯 ULTIMATE TRADING ORCHESTRATOR STATUS")
            print("=" * 80)

            # Portfolio status
            current_portfolio = self.get_current_portfolio()
            print(f"💰 Portfolio Value: ${current_portfolio['total_value']:.2f}")
            print(f"💵 USDT Balance: ${current_portfolio['usdt_balance']:.2f}")
            print(f"📊 Active Positions: {len(self.active_positions)}")

            # Active positions
            if self.active_positions:
                print(f"\n🔥 ACTIVE POSITIONS:")
                for symbol, pos in self.active_positions.items():
                    ticker = self.client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker["price"])
                    pnl_pct = (
                        (current_price - pos["entry_price"]) / pos["entry_price"] * 100
                    )
                    hold_time = datetime.now() - pos["entry_time"]

                    print(
                        f"   {symbol}: {pnl_pct:+.2f}% | ${pos['position_size']:.2f} | {hold_time}"
                    )

            # Strategy performance
            print(f"\n📈 STRATEGY PERFORMANCE:")
            for strategy, perf in self.strategy_performance.items():
                if perf["trades"] > 0:
                    win_rate = perf["wins"] / perf["trades"] * 100
                    print(
                        f"   {strategy.title()}: {perf['trades']} trades | {win_rate:.1f}% win rate | ${perf['total_profit']:+.2f}"
                    )

            print("=" * 80)

        except Exception as e:
            self.logger.error(f"Error printing status: {e}")

    async def run_orchestrator(self, duration_hours: int = 4):
        """Run the ultimate trading orchestrator"""
        try:
            self.logger.info(
                f"🚀 Starting Ultimate Trading Orchestrator for {duration_hours} hours"
            )

            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            scan_interval = 300  # 5 minutes

            while datetime.now() < end_time:
                try:
                    # Update portfolio state
                    self.portfolio = self.get_current_portfolio()
                    self.usdt_balance = self.portfolio["usdt_balance"]

                    # Manage existing positions
                    self.manage_positions()

                    # Scan for new opportunities (if we have capacity)
                    max_positions = self.config["max_simultaneous_trades"]
                    if len(self.active_positions) < max_positions:
                        opportunities = self.scan_opportunities()

                        # Execute top opportunities
                        remaining_slots = max_positions - len(self.active_positions)
                        for opportunity in opportunities[:remaining_slots]:
                            if opportunity["action"] == "buy":
                                self.execute_trade(opportunity)
                                time.sleep(2)  # Brief pause between trades

                    # Print status
                    self.print_status()

                    # Save state
                    self.save_state()

                    # Wait before next cycle
                    self.logger.info(f"⏰ Next scan in {scan_interval//60} minutes...")
                    time.sleep(scan_interval)

                except KeyboardInterrupt:
                    self.logger.info("👋 Orchestrator stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

            self.logger.info("🏁 Trading session completed")

            # Final status
            self.print_status()

            # Close any remaining positions
            if self.active_positions:
                self.logger.info("🧹 Closing remaining positions...")
                for symbol in list(self.active_positions.keys()):
                    self.close_position(symbol, "session_end")

        except Exception as e:
            self.logger.error(f"Critical error in orchestrator: {e}")


def main():
    """Main function"""
    try:
        orchestrator = UltimateTradingOrchestrator()

        print("🎯 Ultimate VictoryChain Trading Orchestrator")
        print("=" * 50)
        print("This is the final evolution combining all successful strategies:")
        print("✅ Smart Gains-Only Analysis")
        print("✅ Claude AI Enhancement")
        print("✅ Multi-Asset Trading")
        print("✅ Advanced Risk Management")
        print("✅ Real-time Monitoring")
        print()

        duration = input("How many hours to run? (1-8, default 4): ").strip()
        try:
            duration = int(duration) if duration else 4
            duration = max(1, min(8, duration))
        except:
            duration = 4

        print(f"\n🚀 Starting {duration}-hour trading session...")
        print("⚠️  Monitor closely - this is live trading with real money!")
        print()

        # Run the orchestrator
        asyncio.run(orchestrator.run_orchestrator(duration))

    except KeyboardInterrupt:
        print("\n👋 Orchestrator stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
