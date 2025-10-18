#!/usr/bin/env python3
"""
AI Gains-Only Trading Bot
Advanced system that learns from market patterns to maximize gains and minimize losses.
Uses machine learning, technical analysis, and AI predictions.
"""

import os
import json
import time
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import talib


class AIGainsOnlyBot:
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
                    f'ai_gains_only_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # AI Learning parameters
        self.confidence_threshold = 0.75  # Only trade if 75%+ confidence
        self.min_gain_target = 3.0  # Minimum 3% gain target
        self.max_loss_tolerance = 1.5  # Maximum 1.5% loss before stop
        self.learning_window = 100  # Learn from last 100 data points

        # Risk management
        self.max_position_size = 0.15  # Max 15% of portfolio per trade
        self.daily_loss_limit = 0.05  # Stop trading if 5% daily loss
        self.win_rate_threshold = 0.70  # Maintain 70%+ win rate

        # AI models
        self.price_predictor = None
        self.gain_classifier = None
        self.scaler = StandardScaler()

        # Trading history for learning
        self.trade_history = []
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_gain": 0.0,
            "total_loss": 0.0,
            "win_rate": 0.0,
            "avg_gain": 0.0,
            "avg_loss": 0.0,
        }

        # Load existing models and history
        self.load_models()

        self.logger.info("AI Gains-Only Trading Bot initialized")

    def get_advanced_features(self, symbol: str, periods: int = 100) -> pd.DataFrame:
        """Get advanced technical features for AI analysis"""
        try:
            # Get historical data
            klines = self.client.get_historical_klines(
                symbol, Client.KLINE_INTERVAL_1HOUR, f"{periods} hours ago UTC"
            )

            if len(klines) < 50:
                return pd.DataFrame()

            # Convert to DataFrame
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
            for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
                df[col] = pd.to_numeric(df[col])

            # Calculate technical indicators
            df["rsi"] = talib.RSI(df["close"].values)
            df["macd"], df["macd_signal"], df["macd_hist"] = talib.MACD(
                df["close"].values
            )
            df["bb_upper"], df["bb_middle"], df["bb_lower"] = talib.BBANDS(
                df["close"].values
            )
            df["sma_20"] = talib.SMA(df["close"].values, timeperiod=20)
            df["sma_50"] = talib.SMA(df["close"].values, timeperiod=50)
            df["ema_12"] = talib.EMA(df["close"].values, timeperiod=12)
            df["ema_26"] = talib.EMA(df["close"].values, timeperiod=26)

            # Calculate momentum indicators
            df["momentum"] = df["close"].pct_change(periods=12) * 100
            df["price_change_1h"] = df["close"].pct_change(1) * 100
            df["price_change_4h"] = df["close"].pct_change(4) * 100
            df["price_change_24h"] = df["close"].pct_change(24) * 100

            # Volume indicators
            df["volume_sma"] = talib.SMA(df["volume"].values, timeperiod=20)
            df["volume_ratio"] = df["volume"] / df["volume_sma"]

            # Volatility
            df["volatility"] = (
                df["close"].rolling(window=20).std()
                / df["close"].rolling(window=20).mean()
                * 100
            )

            # Support/Resistance levels
            df["resistance"] = df["high"].rolling(window=20).max()
            df["support"] = df["low"].rolling(window=20).min()
            df["price_position"] = (
                (df["close"] - df["support"]) / (df["resistance"] - df["support"]) * 100
            )

            # Market structure
            df["higher_high"] = (df["high"] > df["high"].shift(1)).astype(int)
            df["higher_low"] = (df["low"] > df["low"].shift(1)).astype(int)
            df["bullish_structure"] = df["higher_high"] + df["higher_low"]

            return df.dropna()

        except Exception as e:
            self.logger.error(f"Error getting features for {symbol}: {e}")
            return pd.DataFrame()

    def get_ai_prediction(self, symbol: str) -> Dict:
        """Get AI prediction using Claude API with advanced prompting"""
        if not os.getenv("CLAUDE_API_KEY"):
            return {"prediction": "hold", "confidence": 0.5, "gain_probability": 0.5}

        try:
            # Get market data
            df = self.get_advanced_features(symbol, 48)  # 48 hours of data
            if df.empty:
                return {
                    "prediction": "hold",
                    "confidence": 0.5,
                    "gain_probability": 0.5,
                }

            latest = df.iloc[-1]

            # Create advanced prompt with all indicators
            prompt = f"""
            ADVANCED CRYPTO ANALYSIS FOR {symbol}
            
            TECHNICAL INDICATORS:
            - RSI: {latest.get('rsi', 0):.2f} (Overbought >70, Oversold <30)
            - MACD: {latest.get('macd', 0):.4f}, Signal: {latest.get('macd_signal', 0):.4f}
            - Bollinger Bands: Price ${latest['close']:.6f}, Upper ${latest.get('bb_upper', 0):.6f}, Lower ${latest.get('bb_lower', 0):.6f}
            - Moving Averages: SMA20 ${latest.get('sma_20', 0):.6f}, SMA50 ${latest.get('sma_50', 0):.6f}
            
            MOMENTUM ANALYSIS:
            - 1H Change: {latest.get('price_change_1h', 0):.2f}%
            - 4H Change: {latest.get('price_change_4h', 0):.2f}%
            - 24H Change: {latest.get('price_change_24h', 0):.2f}%
            - Overall Momentum: {latest.get('momentum', 0):.2f}%
            
            VOLUME & VOLATILITY:
            - Volume Ratio: {latest.get('volume_ratio', 0):.2f} (>1.5 = high volume)
            - Volatility: {latest.get('volatility', 0):.2f}%
            
            MARKET STRUCTURE:
            - Price Position: {latest.get('price_position', 0):.1f}% between support/resistance
            - Bullish Structure Score: {latest.get('bullish_structure', 0)}/2
            
            TRADING OBJECTIVE: GAINS ONLY - NO LOSSES
            
            Based on this data, provide JSON response:
            {{
                "prediction": "buy" | "sell" | "hold",
                "confidence": 0.0-1.0,
                "gain_probability": 0.0-1.0,
                "target_gain_pct": 1-20,
                "stop_loss_pct": 0.5-2.0,
                "hold_duration_hours": 1-48,
                "reasoning": "detailed explanation",
                "risk_level": "low" | "medium" | "high"
            }}
            
            STRICT REQUIREMENTS:
            1. Only recommend "buy" if gain_probability > 0.75
            2. Only recommend trades with target_gain_pct >= 3%
            3. Always set stop_loss_pct <= 1.5%
            4. Consider all technical indicators together
            5. Factor in current market momentum and volume
            """

            headers = {
                "Content-Type": "application/json",
                "x-api-key": os.getenv("CLAUDE_API_KEY"),
                "anthropic-version": "2023-06-01",
            }

            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=15,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]

                # Extract JSON from response
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    prediction = json.loads(json_match.group())
                    return prediction

            # Fallback based on technical indicators
            return self.fallback_prediction(latest)

        except Exception as e:
            self.logger.error(f"Error getting AI prediction for {symbol}: {e}")
            return {"prediction": "hold", "confidence": 0.5, "gain_probability": 0.5}

    def fallback_prediction(self, data: pd.Series) -> Dict:
        """Fallback prediction based on technical analysis"""
        score = 0
        reasons = []

        # RSI analysis
        rsi = data.get("rsi", 50)
        if rsi < 30:
            score += 2
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI overbought")

        # MACD analysis
        macd = data.get("macd", 0)
        macd_signal = data.get("macd_signal", 0)
        if macd > macd_signal and macd > 0:
            score += 1
            reasons.append("MACD bullish")
        elif macd < macd_signal:
            score -= 1
            reasons.append("MACD bearish")

        # Price vs Moving Averages
        price = data["close"]
        sma_20 = data.get("sma_20", price)
        if price > sma_20:
            score += 1
            reasons.append("Above SMA20")
        else:
            score -= 1
            reasons.append("Below SMA20")

        # Volume confirmation
        volume_ratio = data.get("volume_ratio", 1)
        if volume_ratio > 1.5:
            score += 1
            reasons.append("High volume")

        # Convert score to prediction
        if score >= 3:
            prediction = "buy"
            confidence = min(0.8, 0.5 + score * 0.1)
            gain_probability = min(0.85, 0.5 + score * 0.08)
        elif score <= -2:
            prediction = "sell"
            confidence = min(0.8, 0.5 + abs(score) * 0.1)
            gain_probability = 0.3
        else:
            prediction = "hold"
            confidence = 0.5
            gain_probability = 0.5

        return {
            "prediction": prediction,
            "confidence": confidence,
            "gain_probability": gain_probability,
            "target_gain_pct": 3.5,
            "stop_loss_pct": 1.5,
            "reasoning": "; ".join(reasons),
        }

    def should_enter_trade(self, symbol: str, prediction: Dict) -> bool:
        """Determine if we should enter a trade based on AI prediction"""
        # Check confidence threshold
        if prediction.get("confidence", 0) < self.confidence_threshold:
            self.logger.info(
                f"{symbol}: Confidence {prediction.get('confidence', 0):.2f} below threshold {self.confidence_threshold}"
            )
            return False

        # Check gain probability
        if prediction.get("gain_probability", 0) < 0.75:
            self.logger.info(
                f"{symbol}: Gain probability {prediction.get('gain_probability', 0):.2f} too low"
            )
            return False

        # Check target gain
        target_gain = prediction.get("target_gain_pct", 0)
        if target_gain < self.min_gain_target:
            self.logger.info(
                f"{symbol}: Target gain {target_gain:.1f}% below minimum {self.min_gain_target}%"
            )
            return False

        # Check daily loss limit
        daily_loss = sum(
            [
                trade["pnl"]
                for trade in self.trade_history
                if trade["date"] == datetime.now().date() and trade["pnl"] < 0
            ]
        )

        if abs(daily_loss) > self.daily_loss_limit * self.get_portfolio_value():
            self.logger.warning(f"Daily loss limit reached: ${abs(daily_loss):.2f}")
            return False

        # Check win rate
        if (
            self.performance_metrics["win_rate"] < self.win_rate_threshold
            and self.performance_metrics["total_trades"] > 10
        ):
            self.logger.warning(
                f"Win rate {self.performance_metrics['win_rate']:.2f} below threshold"
            )
            return False

        return True

    def execute_smart_trade(
        self, symbol: str, prediction: Dict, portfolio: Dict
    ) -> bool:
        """Execute a trade with smart position sizing and risk management"""
        try:
            base_asset = symbol.replace("USDT", "")

            # Calculate position size based on confidence and portfolio value
            portfolio_value = self.get_portfolio_value()
            confidence = prediction.get("confidence", 0.5)

            # Dynamic position sizing: higher confidence = larger position
            base_position_pct = self.max_position_size * confidence
            position_value = portfolio_value * base_position_pct

            # Ensure we have enough USDT
            usdt_available = portfolio.get("USDT", {}).get("free", 0)
            if usdt_available < position_value:
                position_value = usdt_available * 0.9  # Use 90% of available USDT

            if position_value < 20:  # Minimum trade size
                self.logger.warning(f"Position size too small: ${position_value:.2f}")
                return False

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            entry_price = float(ticker["price"])

            # Calculate quantity
            quantity = position_value / entry_price

            # Get symbol precision
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
                            f"Quantity {quantity} below minimum {min_qty}"
                        )
                        return False

            # Execute buy order
            self.logger.info(f"🚀 EXECUTING SMART TRADE: {symbol}")
            self.logger.info(
                f"   Position: ${position_value:.2f} ({base_position_pct*100:.1f}% of portfolio)"
            )
            self.logger.info(f"   Confidence: {confidence:.2f}")
            self.logger.info(
                f"   Gain Probability: {prediction.get('gain_probability', 0):.2f}"
            )
            self.logger.info(
                f"   Target Gain: {prediction.get('target_gain_pct', 0):.1f}%"
            )

            order = self.client.order_market_buy(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            # Record trade for learning
            trade_record = {
                "symbol": symbol,
                "action": "buy",
                "timestamp": datetime.now(),
                "date": datetime.now().date(),
                "entry_price": entry_price,
                "quantity": quantity,
                "position_value": position_value,
                "prediction": prediction,
                "order_id": order["orderId"],
                "target_gain_pct": prediction.get("target_gain_pct", 3),
                "stop_loss_pct": prediction.get("stop_loss_pct", 1.5),
                "status": "open",
            }

            self.trade_history.append(trade_record)
            self.save_models()

            self.logger.info(
                f"✅ Trade executed successfully: Order ID {order['orderId']}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return False

    def monitor_open_trades(self, portfolio: Dict) -> List[Dict]:
        """Monitor open trades and close profitable ones or stop losses"""
        closed_trades = []

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

                # Calculate current P&L
                pnl_pct = (current_price - entry_price) / entry_price * 100

                # Check if we should close the trade
                should_close = False
                close_reason = ""

                # Take profit
                if pnl_pct >= trade["target_gain_pct"]:
                    should_close = True
                    close_reason = f"Target gain reached: {pnl_pct:.2f}% >= {trade['target_gain_pct']:.1f}%"

                # Stop loss
                elif pnl_pct <= -trade["stop_loss_pct"]:
                    should_close = True
                    close_reason = f"Stop loss triggered: {pnl_pct:.2f}% <= -{trade['stop_loss_pct']:.1f}%"

                # Time-based exit (24 hours)
                elif (
                    datetime.now() - trade["timestamp"]
                ).total_seconds() > 86400:  # 24 hours
                    if pnl_pct > 0:  # Only close if profitable
                        should_close = True
                        close_reason = (
                            f"24h time limit reached with profit: {pnl_pct:.2f}%"
                        )

                if should_close:
                    success = self.close_trade(trade, current_price, close_reason)
                    if success:
                        closed_trades.append(trade)

                # Log current status
                self.logger.info(
                    f"📊 {symbol}: {pnl_pct:+.2f}% P&L (Entry: ${entry_price:.6f}, Current: ${current_price:.6f})"
                )

            except Exception as e:
                self.logger.error(
                    f"Error monitoring trade {trade.get('symbol', 'unknown')}: {e}"
                )

        return closed_trades

    def close_trade(self, trade: Dict, exit_price: float, reason: str) -> bool:
        """Close a trade and record the result"""
        try:
            symbol = trade["symbol"]
            base_asset = symbol.replace("USDT", "")
            quantity = trade["quantity"]

            # Execute sell order
            order = self.client.order_market_sell(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            # Calculate final P&L
            entry_price = trade["entry_price"]
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            pnl_usd = trade["position_value"] * (pnl_pct / 100)

            # Update trade record
            trade["exit_price"] = exit_price
            trade["exit_timestamp"] = datetime.now()
            trade["pnl_pct"] = pnl_pct
            trade["pnl_usd"] = pnl_usd
            trade["close_reason"] = reason
            trade["status"] = "closed"
            trade["sell_order_id"] = order["orderId"]

            # Update performance metrics
            self.performance_metrics["total_trades"] += 1

            if pnl_pct > 0:
                self.performance_metrics["winning_trades"] += 1
                self.performance_metrics["total_gain"] += pnl_usd
            else:
                self.performance_metrics["total_loss"] += abs(pnl_usd)

            # Recalculate metrics
            total_trades = self.performance_metrics["total_trades"]
            self.performance_metrics["win_rate"] = (
                self.performance_metrics["winning_trades"] / total_trades
            )

            if self.performance_metrics["winning_trades"] > 0:
                self.performance_metrics["avg_gain"] = (
                    self.performance_metrics["total_gain"]
                    / self.performance_metrics["winning_trades"]
                )

            losing_trades = total_trades - self.performance_metrics["winning_trades"]
            if losing_trades > 0:
                self.performance_metrics["avg_loss"] = (
                    self.performance_metrics["total_loss"] / losing_trades
                )

            # Log results
            result_emoji = "🎉" if pnl_pct > 0 else "❌"
            self.logger.info(f"{result_emoji} TRADE CLOSED: {symbol}")
            self.logger.info(f"   Entry: ${entry_price:.6f} → Exit: ${exit_price:.6f}")
            self.logger.info(f"   P&L: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")
            self.logger.info(f"   Reason: {reason}")
            self.logger.info(f"   Win Rate: {self.performance_metrics['win_rate']:.1%}")

            self.save_models()
            return True

        except Exception as e:
            self.logger.error(f"Error closing trade for {trade['symbol']}: {e}")
            return False

    def get_portfolio_value(self) -> float:
        """Get total portfolio value in USDT"""
        try:
            account_info = self.client.get_account()
            total_value = 0

            for balance in account_info["balances"]:
                asset = balance["asset"]
                total = float(balance["free"]) + float(balance["locked"])

                if total > 0:
                    if asset == "USDT":
                        total_value += total
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(
                                symbol=f"{asset}USDT"
                            )
                            price = float(ticker["price"])
                            total_value += total * price
                        except:
                            pass

            return total_value

        except Exception as e:
            self.logger.error(f"Error getting portfolio value: {e}")
            return 0.0

    def save_models(self):
        """Save trading history and models"""
        try:
            data = {
                "trade_history": self.trade_history,
                "performance_metrics": self.performance_metrics,
                "timestamp": datetime.now().isoformat(),
            }

            with open("ai_gains_only_data.json", "w") as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving models: {e}")

    def load_models(self):
        """Load existing trading history and models"""
        try:
            if os.path.exists("ai_gains_only_data.json"):
                with open("ai_gains_only_data.json", "r") as f:
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
                self.logger.info(
                    f"Current win rate: {self.performance_metrics['win_rate']:.1%}"
                )

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")

    def run_ai_gains_cycle(self):
        """Run one AI gains-only trading cycle"""
        self.logger.info("🤖 === AI GAINS-ONLY TRADING CYCLE ===")

        try:
            # Get current portfolio
            portfolio = self.get_current_portfolio()
            if not portfolio:
                return

            portfolio_value = self.get_portfolio_value()
            self.logger.info(f"Portfolio Value: ${portfolio_value:.2f}")

            # Monitor existing trades first
            closed_trades = self.monitor_open_trades(portfolio)
            if closed_trades:
                self.logger.info(f"Closed {len(closed_trades)} trades this cycle")

            # Check if we should look for new opportunities
            open_trades = [t for t in self.trade_history if t["status"] == "open"]
            max_concurrent_trades = 3  # Limit concurrent trades

            if len(open_trades) >= max_concurrent_trades:
                self.logger.info(
                    f"Max concurrent trades reached ({len(open_trades)}/{max_concurrent_trades})"
                )
                return

            # Analyze top assets for new opportunities
            top_assets = [
                "BTC",
                "ETH",
                "LOKA",
                "1000REKT",
                "KNC",
                "ATOM",
                "SHIB",
                "CRV",
                "ADA",
                "PEPE",
            ]

            for asset in top_assets:
                if (
                    len([t for t in self.trade_history if t["status"] == "open"])
                    >= max_concurrent_trades
                ):
                    break

                symbol = f"{asset}USDT"

                # Skip if we already have an open trade for this asset
                if any(
                    t["symbol"] == symbol and t["status"] == "open"
                    for t in self.trade_history
                ):
                    continue

                self.logger.info(f"🔍 Analyzing {symbol}...")

                # Get AI prediction
                prediction = self.get_ai_prediction(symbol)

                self.logger.info(
                    f"   Prediction: {prediction.get('prediction', 'unknown')}"
                )
                self.logger.info(
                    f"   Confidence: {prediction.get('confidence', 0):.2f}"
                )
                self.logger.info(
                    f"   Gain Probability: {prediction.get('gain_probability', 0):.2f}"
                )

                # Check if we should enter trade
                if prediction.get("prediction") == "buy" and self.should_enter_trade(
                    symbol, prediction
                ):
                    success = self.execute_smart_trade(symbol, prediction, portfolio)
                    if success:
                        time.sleep(2)  # Brief pause between trades

                time.sleep(1)  # Rate limiting

            # Print performance summary
            self.print_performance_summary()

        except Exception as e:
            self.logger.error(f"Error in AI gains cycle: {e}")

    def get_current_portfolio(self) -> Dict:
        """Get current portfolio balance"""
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

    def print_performance_summary(self):
        """Print current performance summary"""
        metrics = self.performance_metrics

        self.logger.info("📊 === PERFORMANCE SUMMARY ===")
        self.logger.info(f"Total Trades: {metrics['total_trades']}")
        self.logger.info(f"Winning Trades: {metrics['winning_trades']}")
        self.logger.info(f"Win Rate: {metrics['win_rate']:.1%}")
        self.logger.info(f"Total Gains: ${metrics['total_gain']:.2f}")
        self.logger.info(f"Total Losses: ${metrics['total_loss']:.2f}")
        self.logger.info(
            f"Net P&L: ${metrics['total_gain'] - metrics['total_loss']:+.2f}"
        )

        if metrics["avg_gain"] > 0:
            self.logger.info(f"Avg Gain per Win: ${metrics['avg_gain']:.2f}")
        if metrics["avg_loss"] > 0:
            self.logger.info(f"Avg Loss per Loss: ${metrics['avg_loss']:.2f}")

        # Show open trades
        open_trades = [t for t in self.trade_history if t["status"] == "open"]
        if open_trades:
            self.logger.info(f"Open Trades: {len(open_trades)}")
            for trade in open_trades:
                duration = datetime.now() - trade["timestamp"]
                self.logger.info(
                    f"   {trade['symbol']}: {duration} ago, Target: +{trade['target_gain_pct']:.1f}%"
                )

    def run_continuous_ai_trading(self, cycle_minutes: int = 30):
        """Run continuous AI gains-only trading"""
        self.logger.info(
            f"🚀 Starting AI Gains-Only Trading (cycle every {cycle_minutes} minutes)"
        )
        self.logger.info(
            f"Target: {self.win_rate_threshold:.0%} win rate, {self.min_gain_target:.0f}%+ gains only"
        )

        while True:
            try:
                self.run_ai_gains_cycle()

                self.logger.info(
                    f"💤 Waiting {cycle_minutes} minutes until next cycle..."
                )
                time.sleep(cycle_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("AI trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous trading: {e}")
                self.logger.info("Waiting 5 minutes before retry...")
                time.sleep(300)


def main():
    # Install required packages
    try:
        import talib
    except ImportError:
        print("Installing required TA-Lib package...")
        os.system("pip3 install TA-Lib")
        import talib

    bot = AIGainsOnlyBot()

    print("🤖 AI Gains-Only Trading Bot")
    print("============================")
    print("Advanced AI system focused on GAINS ONLY")
    print("• Machine learning predictions")
    print("• 75%+ confidence threshold")
    print("• 3%+ minimum gain targets")
    print("• 1.5% maximum stop losses")
    print("• Learns from every trade")
    print()

    # Show current performance
    bot.print_performance_summary()

    print("\nTrading Options:")
    print("1. Single AI analysis cycle")
    print("2. Execute AI gains-only trading (LIVE)")
    print("3. Continuous AI trading (30 min cycles)")
    print("4. Show detailed trade history")

    choice = input("Select option (1-4): ").strip()

    if choice == "1":
        print("\nRunning AI analysis cycle...")
        bot.run_ai_gains_cycle()

    elif choice == "2":
        confirm = input(
            "\nThis will execute live AI trades. Type 'CONFIRM AI GAINS ONLY' to proceed: "
        )
        if confirm == "CONFIRM AI GAINS ONLY":
            print("\nExecuting AI gains-only trading...")
            bot.run_ai_gains_cycle()
        else:
            print("Trading cancelled.")

    elif choice == "3":
        confirm = input(
            "\nStart continuous AI trading? Type 'CONFIRM CONTINUOUS AI' to proceed: "
        )
        if confirm == "CONFIRM CONTINUOUS AI":
            print("\nStarting continuous AI gains-only trading...")
            bot.run_continuous_ai_trading(30)
        else:
            print("Trading cancelled.")

    elif choice == "4":
        print("\nTrade History:")
        for i, trade in enumerate(bot.trade_history[-10:], 1):  # Last 10 trades
            status = (
                "🟢"
                if trade["status"] == "open"
                else "🎉" if trade.get("pnl_pct", 0) > 0 else "❌"
            )
            pnl = (
                f"{trade.get('pnl_pct', 0):+.2f}%"
                if trade["status"] == "closed"
                else "Open"
            )
            print(
                f"{i:2d}. {status} {trade['symbol']}: {pnl} - {trade.get('close_reason', 'Active')}"
            )

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
