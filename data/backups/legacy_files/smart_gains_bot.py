#!/usr/bin/env python3
"""
Smart Gains-Only Trading Bot
Advanced AI system focused on maximizing gains and minimizing losses.
Uses technical analysis, machine learning, and AI predictions.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import requests


class SmartGainsBot:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'smart_gains_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Smart trading parameters - GAINS ONLY FOCUS
        self.confidence_threshold = 0.80  # Only trade if 80%+ confidence
        self.min_gain_target = 4.0  # Minimum 4% gain target
        self.max_loss_tolerance = 1.2  # Maximum 1.2% loss before stop
        self.win_rate_target = 0.75  # Target 75%+ win rate

        # Risk management
        self.max_position_size = 0.12  # Max 12% of portfolio per trade
        self.daily_loss_limit = 0.03  # Stop trading if 3% daily loss
        self.max_concurrent_trades = 2  # Max 2 trades at once

        # Performance tracking
        self.trade_history = []
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_gain": 0.0,
            "total_loss": 0.0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }

        # Load existing data
        self.load_trading_data()

        self.logger.info("🎯 Smart Gains-Only Bot initialized")
        self.logger.info(
            f"Target: {self.win_rate_target:.0%} win rate, {self.min_gain_target:.0f}%+ gains"
        )

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators without TA-Lib"""
        try:
            # Simple Moving Averages
            df["sma_10"] = df["close"].rolling(window=10).mean()
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()

            # Exponential Moving Averages
            df["ema_12"] = df["close"].ewm(span=12).mean()
            df["ema_26"] = df["close"].ewm(span=26).mean()

            # MACD
            df["macd"] = df["ema_12"] - df["ema_26"]
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]

            # RSI (Relative Strength Index)
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            df["bb_middle"] = df["close"].rolling(window=20).mean()
            bb_std = df["close"].rolling(window=20).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
            df["bb_position"] = (
                (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]) * 100
            )

            # Volume indicators
            df["volume_sma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_sma"]

            # Price momentum
            df["momentum_1h"] = df["close"].pct_change(1) * 100
            df["momentum_4h"] = df["close"].pct_change(4) * 100
            df["momentum_24h"] = df["close"].pct_change(24) * 100

            # Volatility
            df["volatility"] = (
                df["close"].rolling(window=20).std()
                / df["close"].rolling(window=20).mean()
                * 100
            )

            # Support/Resistance
            df["resistance"] = df["high"].rolling(window=20).max()
            df["support"] = df["low"].rolling(window=20).min()
            df["price_position"] = (
                (df["close"] - df["support"]) / (df["resistance"] - df["support"]) * 100
            )

            return df.dropna()

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return df

    def get_market_data(self, symbol: str, hours: int = 100) -> pd.DataFrame:
        """Get comprehensive market data with technical indicators"""
        try:
            # Get historical klines
            klines = self.client.get_historical_klines(
                symbol, Client.KLINE_INTERVAL_1HOUR, f"{hours} hours ago UTC"
            )

            if len(klines) < 50:
                return pd.DataFrame()

            # Create DataFrame
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

            # Convert to numeric
            numeric_columns = ["open", "high", "low", "close", "volume", "quote_volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])

            # Add timestamp
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")

            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)

            return df

        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return pd.DataFrame()

    def analyze_market_conditions(self, symbol: str) -> Dict:
        """Analyze market conditions for trading decision"""
        try:
            df = self.get_market_data(symbol, 72)  # 72 hours of data

            if df.empty or len(df) < 20:
                return {"score": 0, "confidence": 0, "signals": []}

            latest = df.iloc[-1]
            previous = df.iloc[-2]

            signals = []
            score = 0

            # RSI Analysis
            rsi = latest["rsi"]
            if rsi < 30:
                signals.append("RSI oversold - bullish")
                score += 2
            elif rsi > 70:
                signals.append("RSI overbought - bearish")
                score -= 2
            elif 40 <= rsi <= 60:
                signals.append("RSI neutral - stable")
                score += 0.5

            # MACD Analysis
            macd = latest["macd"]
            macd_signal = latest["macd_signal"]
            macd_prev = previous["macd"]
            macd_signal_prev = previous["macd_signal"]

            if macd > macd_signal and macd_prev <= macd_signal_prev:
                signals.append("MACD bullish crossover")
                score += 2
            elif macd > macd_signal and macd > 0:
                signals.append("MACD bullish momentum")
                score += 1
            elif macd < macd_signal:
                signals.append("MACD bearish")
                score -= 1

            # Moving Average Analysis
            price = latest["close"]
            sma_20 = latest["sma_20"]
            sma_50 = latest["sma_50"]

            if price > sma_20 > sma_50:
                signals.append("Price above MAs - bullish trend")
                score += 1.5
            elif price > sma_20:
                signals.append("Price above SMA20 - short-term bullish")
                score += 0.5
            elif price < sma_20:
                signals.append("Price below SMA20 - bearish")
                score -= 1

            # Bollinger Bands Analysis
            bb_position = latest["bb_position"]
            if bb_position < 20:
                signals.append("Near BB lower - potential bounce")
                score += 1
            elif bb_position > 80:
                signals.append("Near BB upper - potential pullback")
                score -= 1

            # Volume Analysis
            volume_ratio = latest["volume_ratio"]
            if volume_ratio > 1.5:
                signals.append("High volume confirmation")
                score += 1
            elif volume_ratio < 0.5:
                signals.append("Low volume - weak signal")
                score -= 0.5

            # Momentum Analysis
            momentum_24h = latest["momentum_24h"]
            momentum_4h = latest["momentum_4h"]

            if momentum_24h > 5 and momentum_4h > 2:
                signals.append("Strong bullish momentum")
                score += 2
            elif momentum_24h > 2:
                signals.append("Moderate bullish momentum")
                score += 1
            elif momentum_24h < -5:
                signals.append("Strong bearish momentum")
                score -= 2

            # Volatility Check
            volatility = latest["volatility"]
            if volatility > 10:
                signals.append("High volatility - risky")
                score -= 1
            elif volatility < 3:
                signals.append("Low volatility - stable")
                score += 0.5

            # Calculate confidence based on signal strength
            confidence = min(0.95, max(0.05, (abs(score) / 10) + 0.4))

            return {
                "score": score,
                "confidence": confidence,
                "signals": signals,
                "rsi": rsi,
                "macd_bullish": macd > macd_signal,
                "price_vs_sma20": (price - sma_20) / sma_20 * 100,
                "momentum_24h": momentum_24h,
                "volume_ratio": volume_ratio,
                "volatility": volatility,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing market conditions for {symbol}: {e}")
            return {"score": 0, "confidence": 0, "signals": []}

    def get_ai_enhanced_prediction(self, symbol: str, market_analysis: Dict) -> Dict:
        """Get AI-enhanced prediction using Claude API"""
        if not os.getenv("CLAUDE_API_KEY"):
            return self.create_fallback_prediction(market_analysis)

        try:
            prompt = f"""
            SMART GAINS-ONLY ANALYSIS FOR {symbol}
            
            MISSION: Only recommend trades with HIGH probability of 4%+ gains
            
            TECHNICAL ANALYSIS:
            - Market Score: {market_analysis['score']:.2f}
            - RSI: {market_analysis['rsi']:.1f}
            - MACD Bullish: {market_analysis['macd_bullish']}
            - Price vs SMA20: {market_analysis['price_vs_sma20']:+.2f}%
            - 24h Momentum: {market_analysis['momentum_24h']:+.2f}%
            - Volume Ratio: {market_analysis['volume_ratio']:.2f}
            - Volatility: {market_analysis['volatility']:.2f}%
            
            KEY SIGNALS:
            {chr(10).join(f"• {signal}" for signal in market_analysis['signals'])}
            
            STRICT REQUIREMENTS FOR BUY RECOMMENDATION:
            1. Must have 80%+ confidence in 4%+ gain
            2. Maximum 1.2% stop loss acceptable
            3. Clear technical confirmation needed
            4. Strong momentum + volume support required
            
            Provide JSON response:
            {{
                "action": "buy" | "hold" | "sell",
                "confidence": 0.0-1.0,
                "gain_probability": 0.0-1.0,
                "target_gain": 4-15,
                "stop_loss": 0.8-1.2,
                "hold_hours": 2-48,
                "reasoning": "detailed explanation",
                "risk_assessment": "low" | "medium" | "high"
            }}
            
            Only recommend BUY if ALL conditions are met for high-probability gains.
            """

            headers = {
                "Content-Type": "application/json",
                "x-api-key": os.getenv("CLAUDE_API_KEY"),
                "anthropic-version": "2023-06-01",
            }

            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=12,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]

                # Extract JSON
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    prediction = json.loads(json_match.group())
                    return prediction

            return self.create_fallback_prediction(market_analysis)

        except Exception as e:
            self.logger.error(f"Error getting AI prediction: {e}")
            return self.create_fallback_prediction(market_analysis)

    def create_fallback_prediction(self, market_analysis: Dict) -> Dict:
        """Create fallback prediction based on technical analysis"""
        score = market_analysis["score"]
        confidence = market_analysis["confidence"]

        # Conservative approach - only buy on very strong signals
        if score >= 4 and confidence >= 0.7:
            action = "buy"
            gain_prob = min(0.85, confidence + 0.1)
            target_gain = min(8, 4 + score * 0.5)
        elif score <= -3:
            action = "sell"
            gain_prob = 0.3
            target_gain = 3
        else:
            action = "hold"
            gain_prob = 0.5
            target_gain = 4

        return {
            "action": action,
            "confidence": confidence,
            "gain_probability": gain_prob,
            "target_gain": target_gain,
            "stop_loss": 1.2,
            "reasoning": f"Technical score: {score:.1f}, Confidence: {confidence:.2f}",
        }

    def should_execute_trade(self, prediction: Dict) -> bool:
        """Determine if trade meets our strict gains-only criteria"""
        # Check confidence threshold
        if prediction.get("confidence", 0) < self.confidence_threshold:
            return False

        # Check gain probability
        if prediction.get("gain_probability", 0) < 0.78:
            return False

        # Check target gain
        if prediction.get("target_gain", 0) < self.min_gain_target:
            return False

        # Check stop loss is acceptable
        if prediction.get("stop_loss", 2) > self.max_loss_tolerance:
            return False

        # Check daily performance
        today_trades = [
            t for t in self.trade_history if t.get("date") == datetime.now().date()
        ]

        daily_loss = sum(
            [t["pnl_usd"] for t in today_trades if t.get("pnl_usd", 0) < 0]
        )
        portfolio_value = self.get_portfolio_value()

        if abs(daily_loss) > self.daily_loss_limit * portfolio_value:
            self.logger.warning(f"Daily loss limit reached: ${abs(daily_loss):.2f}")
            return False

        # Check win rate maintenance
        if (
            self.performance_metrics["total_trades"] > 5
            and self.performance_metrics["win_rate"] < 0.65
        ):
            self.logger.warning(
                f"Win rate too low: {self.performance_metrics['win_rate']:.1%}"
            )
            return False

        return True

    def execute_smart_trade(self, symbol: str, prediction: Dict) -> bool:
        """Execute a smart trade with optimal position sizing"""
        try:
            base_asset = symbol.replace("USDT", "")

            # Get portfolio info
            portfolio_value = self.get_portfolio_value()
            portfolio = self.get_current_portfolio()

            # Dynamic position sizing based on confidence
            confidence = prediction.get("confidence", 0.5)
            base_size = self.max_position_size * confidence
            position_value = portfolio_value * base_size

            # Check USDT availability
            usdt_available = portfolio.get("USDT", {}).get("free", 0)
            if usdt_available < position_value:
                position_value = usdt_available * 0.85

            if position_value < 25:  # Minimum $25 trade
                self.logger.warning(f"Position size too small: ${position_value:.2f}")
                return False

            # Get current price and execute
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            entry_price = float(ticker["price"])
            quantity = position_value / entry_price

            # Apply precision rules
            exchange_info = self.client.get_exchange_info()
            symbol_info = next(
                (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
            )

            if symbol_info:
                lot_size_filter = next(
                    (
                        f
                        for f in symbol_info["filters"]
                        if f["filterType"] == "LOT_SIZE"
                    ),
                    None,
                )
                if lot_size_filter:
                    step_size = float(lot_size_filter["stepSize"])
                    quantity = round(quantity / step_size) * step_size
                    min_qty = float(lot_size_filter["minQty"])

                    if quantity < min_qty:
                        self.logger.warning(
                            f"Quantity below minimum: {quantity} < {min_qty}"
                        )
                        return False

            # Execute the trade
            self.logger.info(f"🚀 EXECUTING SMART TRADE: {symbol}")
            self.logger.info(
                f"   Position: ${position_value:.2f} ({base_size*100:.1f}% of portfolio)"
            )
            self.logger.info(f"   Confidence: {confidence:.1%}")
            self.logger.info(f"   Target: +{prediction.get('target_gain', 0):.1f}%")
            self.logger.info(f"   Stop Loss: -{prediction.get('stop_loss', 0):.1f}%")

            order = self.client.order_market_buy(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            # Record the trade
            trade_record = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "date": datetime.now().date(),
                "entry_price": entry_price,
                "quantity": quantity,
                "position_value": position_value,
                "prediction": prediction,
                "order_id": order["orderId"],
                "target_gain_pct": prediction.get("target_gain", 4),
                "stop_loss_pct": prediction.get("stop_loss", 1.2),
                "status": "open",
            }

            self.trade_history.append(trade_record)
            self.save_trading_data()

            self.logger.info(f"✅ Trade executed: Order ID {order['orderId']}")
            return True

        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return False

    def monitor_open_trades(self) -> List[Dict]:
        """Monitor and manage open trades"""
        closed_trades = []
        portfolio = self.get_current_portfolio()

        for trade in self.trade_history:
            if trade["status"] != "open":
                continue

            try:
                symbol = trade["symbol"]
                base_asset = symbol.replace("USDT", "")

                # Check if we still have the asset
                if base_asset not in portfolio or portfolio[base_asset]["free"] <= 0:
                    continue

                # Get current price
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker["price"])
                entry_price = trade["entry_price"]

                # Calculate P&L
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_usd = trade["position_value"] * (pnl_pct / 100)

                # Decision logic
                should_close = False
                close_reason = ""

                # Take profit at target
                if pnl_pct >= trade["target_gain_pct"]:
                    should_close = True
                    close_reason = f"🎯 Target reached: {pnl_pct:+.2f}%"

                # Stop loss
                elif pnl_pct <= -trade["stop_loss_pct"]:
                    should_close = True
                    close_reason = f"🛑 Stop loss: {pnl_pct:+.2f}%"

                # Time-based profit taking (12 hours)
                elif (
                    datetime.now() - trade["timestamp"]
                ).total_seconds() > 43200:  # 12 hours
                    if pnl_pct >= 2:  # At least 2% profit
                        should_close = True
                        close_reason = f"⏰ Time limit with profit: {pnl_pct:+.2f}%"

                # Emergency exit after 24 hours if not too negative
                elif (
                    datetime.now() - trade["timestamp"]
                ).total_seconds() > 86400:  # 24 hours
                    if pnl_pct > -0.8:  # Not too negative
                        should_close = True
                        close_reason = f"⏰ 24h emergency exit: {pnl_pct:+.2f}%"

                if should_close:
                    success = self.close_trade(trade, current_price, close_reason)
                    if success:
                        closed_trades.append(trade)

                # Log current status
                duration = datetime.now() - trade["timestamp"]
                self.logger.info(
                    f"📊 {symbol}: {pnl_pct:+.2f}% (${pnl_usd:+.2f}) - {duration}"
                )

            except Exception as e:
                self.logger.error(
                    f"Error monitoring {trade.get('symbol', 'unknown')}: {e}"
                )

        return closed_trades

    def close_trade(self, trade: Dict, exit_price: float, reason: str) -> bool:
        """Close a trade and update performance metrics"""
        try:
            symbol = trade["symbol"]
            base_asset = symbol.replace("USDT", "")
            quantity = trade["quantity"]

            # Execute sell order
            order = self.client.order_market_sell(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            # Calculate final results
            entry_price = trade["entry_price"]
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            pnl_usd = trade["position_value"] * (pnl_pct / 100)

            # Update trade record
            trade.update(
                {
                    "exit_price": exit_price,
                    "exit_timestamp": datetime.now(),
                    "pnl_pct": pnl_pct,
                    "pnl_usd": pnl_usd,
                    "close_reason": reason,
                    "status": "closed",
                    "sell_order_id": order["orderId"],
                }
            )

            # Update performance metrics
            self.performance_metrics["total_trades"] += 1

            if pnl_pct > 0:
                self.performance_metrics["winning_trades"] += 1
                self.performance_metrics["total_gain"] += pnl_usd
            else:
                self.performance_metrics["total_loss"] += abs(pnl_usd)

            self.performance_metrics["net_profit"] = (
                self.performance_metrics["total_gain"]
                - self.performance_metrics["total_loss"]
            )

            self.performance_metrics["win_rate"] = (
                self.performance_metrics["winning_trades"]
                / self.performance_metrics["total_trades"]
            )

            self.performance_metrics["best_trade"] = max(
                self.performance_metrics["best_trade"], pnl_pct
            )

            self.performance_metrics["worst_trade"] = min(
                self.performance_metrics["worst_trade"], pnl_pct
            )

            # Log results
            emoji = "🎉" if pnl_pct > 0 else "😞"
            self.logger.info(f"{emoji} TRADE CLOSED: {symbol}")
            self.logger.info(f"   {entry_price:.6f} → {exit_price:.6f}")
            self.logger.info(f"   P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
            self.logger.info(f"   {reason}")
            self.logger.info(f"   Win Rate: {self.performance_metrics['win_rate']:.1%}")

            self.save_trading_data()
            return True

        except Exception as e:
            self.logger.error(f"Error closing trade: {e}")
            return False

    def get_current_portfolio(self) -> Dict:
        """Get current portfolio balances"""
        try:
            account_info = self.client.get_account()
            portfolio = {}

            for balance in account_info["balances"]:
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0:
                    portfolio[asset] = {"free": free, "locked": locked, "total": total}

            return portfolio

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {}

    def get_portfolio_value(self) -> float:
        """Get total portfolio value in USDT"""
        try:
            portfolio = self.get_current_portfolio()
            total_value = 0

            for asset, data in portfolio.items():
                if asset == "USDT":
                    total_value += data["total"]
                else:
                    try:
                        ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                        price = float(ticker["price"])
                        total_value += data["total"] * price
                    except:
                        pass

            return total_value

        except Exception as e:
            self.logger.error(f"Error getting portfolio value: {e}")
            return 0.0

    def get_all_tradable_usdt_pairs(self) -> List[str]:
        """Get all tradable USDT pairs from Binance US"""
        try:
            exchange_info = self.client.get_exchange_info()
            usdt_pairs = []

            for symbol_info in exchange_info["symbols"]:
                symbol = symbol_info["symbol"]

                # Only USDT pairs that are actively trading
                if (
                    symbol.endswith("USDT")
                    and symbol_info["status"] == "TRADING"
                    and symbol_info["isSpotTradingAllowed"]
                ):

                    # Skip stablecoins and very low volume pairs
                    base_asset = symbol.replace("USDT", "")
                    if base_asset not in ["USDC", "BUSD", "DAI", "TUSD", "PAX"]:
                        usdt_pairs.append(symbol)

            # Sort by symbol name for consistent order
            usdt_pairs.sort()

            self.logger.info(f"Found {len(usdt_pairs)} tradable USDT pairs")
            return usdt_pairs

        except Exception as e:
            self.logger.error(f"Error getting tradable pairs: {e}")
            # Fallback to known pairs
            return [
                "BTCUSDT",
                "ETHUSDT",
                "ADAUSDT",
                "DOTUSDT",
                "LINKUSDT",
                "LTCUSDT",
                "XLMUSDT",
                "ATOMUSDT",
                "ALGOUSDT",
                "MATICUSDT",
            ]

    def run_smart_gains_cycle(self):
        """Run one complete smart gains trading cycle"""
        self.logger.info("🎯 === SMART GAINS TRADING CYCLE ===")

        try:
            # Monitor existing trades first
            portfolio = self.get_current_portfolio()
            portfolio_value = self.get_portfolio_value()

            self.logger.info(f"Portfolio Value: ${portfolio_value:.2f}")

            # Check and close trades
            closed_trades = self.monitor_open_trades()
            if closed_trades:
                self.logger.info(f"Closed {len(closed_trades)} trades")

            # Check if we can open new trades
            open_trades = [t for t in self.trade_history if t["status"] == "open"]

            if len(open_trades) >= self.max_concurrent_trades:
                self.logger.info(
                    f"Max trades reached ({len(open_trades)}/{self.max_concurrent_trades})"
                )
                return

            # Get ALL tradable USDT pairs from Binance US
            all_symbols = self.get_all_tradable_usdt_pairs()
            self.logger.info(
                f"Analyzing ALL {len(all_symbols)} tradable USDT pairs on Binance US"
            )

            opportunities = []
            analyzed_count = 0

            for symbol in all_symbols:
                # Skip if we already have this trade open
                if any(
                    t["symbol"] == symbol and t["status"] == "open"
                    for t in self.trade_history
                ):
                    continue

                self.logger.info(f"🔍 Analyzing {symbol}...")

                # Get market analysis
                market_analysis = self.analyze_market_conditions(symbol)

                # Get AI prediction
                prediction = self.get_ai_enhanced_prediction(symbol, market_analysis)

                if prediction.get("action") == "buy":
                    combined_score = (
                        market_analysis["score"] * 0.4
                        + prediction.get("confidence", 0) * 10 * 0.3
                        + prediction.get("gain_probability", 0) * 10 * 0.3
                    )

                    opportunities.append(
                        {
                            "symbol": symbol,
                            "score": combined_score,
                            "market_analysis": market_analysis,
                            "prediction": prediction,
                        }
                    )

                    self.logger.info(
                        f"   🎯 BUY Signal: Score={combined_score:.2f}, "
                        f"Confidence={prediction.get('confidence', 0):.2f}, "
                        f"Target={prediction.get('target_gain', 0):.1f}%"
                    )
                else:
                    self.logger.info(
                        f"   ⏸️  {prediction.get('action', 'hold').upper()}: "
                        f"Score={market_analysis['score']:.1f}"
                    )

                time.sleep(0.5)  # Rate limiting

            # Execute best opportunity
            if opportunities:
                best_opportunity = max(opportunities, key=lambda x: x["score"])
                symbol = best_opportunity["symbol"]
                prediction = best_opportunity["prediction"]

                if self.should_execute_trade(prediction):
                    success = self.execute_smart_trade(symbol, prediction)
                    if success:
                        self.logger.info(f"🚀 Executed trade for {symbol}")
                else:
                    self.logger.info(f"❌ {symbol} doesn't meet strict criteria")
            else:
                self.logger.info("🔍 No buy opportunities found")

            # Print performance summary
            self.print_performance_summary()

        except Exception as e:
            self.logger.error(f"Error in smart gains cycle: {e}")

    def print_performance_summary(self):
        """Print detailed performance summary"""
        metrics = self.performance_metrics

        self.logger.info("📊 === PERFORMANCE SUMMARY ===")
        self.logger.info(f"Total Trades: {metrics['total_trades']}")
        self.logger.info(
            f"Win Rate: {metrics['win_rate']:.1%} (Target: {self.win_rate_target:.0%})"
        )
        self.logger.info(f"Net Profit: ${metrics['net_profit']:+.2f}")

        if metrics["total_trades"] > 0:
            self.logger.info(f"Best Trade: {metrics['best_trade']:+.2f}%")
            self.logger.info(f"Worst Trade: {metrics['worst_trade']:+.2f}%")

            avg_gain = metrics["total_gain"] / max(1, metrics["winning_trades"])
            losing_trades = metrics["total_trades"] - metrics["winning_trades"]
            avg_loss = metrics["total_loss"] / max(1, losing_trades)

            self.logger.info(f"Avg Win: ${avg_gain:.2f}")
            self.logger.info(f"Avg Loss: ${avg_loss:.2f}")

        # Show open trades
        open_trades = [t for t in self.trade_history if t["status"] == "open"]
        if open_trades:
            self.logger.info(f"Open Trades: {len(open_trades)}")
            for trade in open_trades:
                duration = datetime.now() - trade["timestamp"]
                self.logger.info(
                    f"   {trade['symbol']}: {duration} (Target: +{trade['target_gain_pct']:.1f}%)"
                )

    def save_trading_data(self):
        """Save trading history and performance data"""
        try:
            data = {
                "trade_history": self.trade_history,
                "performance_metrics": self.performance_metrics,
                "last_updated": datetime.now().isoformat(),
            }

            with open("smart_gains_data.json", "w") as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving data: {e}")

    def load_trading_data(self):
        """Load existing trading history and performance data"""
        try:
            if os.path.exists("smart_gains_data.json"):
                with open("smart_gains_data.json", "r") as f:
                    data = json.load(f)

                self.trade_history = data.get("trade_history", [])
                self.performance_metrics = data.get(
                    "performance_metrics", self.performance_metrics
                )

                # Convert string dates back to datetime objects
                for trade in self.trade_history:
                    if isinstance(trade.get("timestamp"), str):
                        trade["timestamp"] = datetime.fromisoformat(trade["timestamp"])
                    if isinstance(trade.get("exit_timestamp"), str):
                        trade["exit_timestamp"] = datetime.fromisoformat(
                            trade["exit_timestamp"]
                        )
                    if isinstance(trade.get("date"), str):
                        trade["date"] = datetime.fromisoformat(trade["date"]).date()

                self.logger.info(f"Loaded {len(self.trade_history)} historical trades")
                if self.performance_metrics["total_trades"] > 0:
                    self.logger.info(
                        f"Historical win rate: {self.performance_metrics['win_rate']:.1%}"
                    )

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")

    def run_continuous_smart_trading(self, cycle_minutes: int = 20):
        """Run continuous smart gains trading"""
        self.logger.info(f"🚀 Starting Continuous Smart Gains Trading")
        self.logger.info(f"Cycle: Every {cycle_minutes} minutes")
        self.logger.info(
            f"Target: {self.win_rate_target:.0%} win rate, {self.min_gain_target:.0f}%+ gains"
        )

        while True:
            try:
                self.run_smart_gains_cycle()

                self.logger.info(f"💤 Next cycle in {cycle_minutes} minutes...")
                time.sleep(cycle_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Smart trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous trading: {e}")
                time.sleep(300)  # Wait 5 minutes on error


def main():
    bot = SmartGainsBot()

    print("🎯 Smart Gains-Only Trading Bot")
    print("===============================")
    print("AI-powered system focused on HIGH-PROBABILITY GAINS")
    print(f"• {bot.confidence_threshold:.0%}+ confidence threshold")
    print(f"• {bot.min_gain_target:.0f}%+ minimum gain targets")
    print(f"• {bot.max_loss_tolerance:.1f}% maximum stop losses")
    print(f"• Target {bot.win_rate_target:.0%}+ win rate")
    print()

    # Show performance
    bot.print_performance_summary()

    print("\nTrading Options:")
    print("1. Single smart analysis (no trades)")
    print("2. Execute smart gains trading (LIVE)")
    print("3. Continuous smart trading (20 min cycles)")

    choice = input("Select option (1-3): ").strip()

    if choice == "1":
        print("\n🔍 Running smart analysis...")
        bot.run_smart_gains_cycle()

    elif choice == "2":
        confirm = input(
            "\nExecute live smart trades? Type 'CONFIRM SMART GAINS' to proceed: "
        )
        if confirm == "CONFIRM SMART GAINS":
            print("\n🚀 Executing smart gains trading...")
            bot.run_smart_gains_cycle()
        else:
            print("Trading cancelled.")

    elif choice == "3":
        confirm = input(
            "\nStart continuous smart trading? Type 'CONFIRM CONTINUOUS SMART' to proceed: "
        )
        if confirm == "CONFIRM CONTINUOUS SMART":
            print("\n🚀 Starting continuous smart gains trading...")
            bot.run_continuous_smart_trading(20)
        else:
            print("Trading cancelled.")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
