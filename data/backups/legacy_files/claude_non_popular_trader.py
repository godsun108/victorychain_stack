#!/usr/bin/env python3
"""
Claude-Powered Non-Popular Token Trader
Uses Claude AI to analyze market patterns and make intelligent trades on less popular tokens
Focuses on micro-cap and nano-cap tokens for higher potential returns
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
import anthropic


class ClaudeNonPopularTrader:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Initialize Claude client
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'claude_trader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Focus on non-popular tokens (low volume)
        self.volume_thresholds = {
            "avoid_popular": 100_000,  # Avoid tokens >$100K volume (too popular)
            "min_volume": 1_000,  # Minimum $1K volume (avoid dust)
            "sweet_spot_max": 50_000,  # Sweet spot: $1K-$50K volume
            "micro_cap_max": 25_000,  # Micro caps: $1K-$25K volume
        }

        # Non-popular token trading parameters
        self.trading_params = {
            "max_position_size": 0.08,  # 8% max per position (higher risk)
            "stop_loss": 0.06,  # 6% stop loss
            "take_profit_1": 0.15,  # 15% first target
            "take_profit_2": 0.30,  # 30% second target
            "max_positions": 3,  # Max 3 non-popular positions
            "min_confidence": 0.75,  # 75% AI confidence required
        }

        # Learning data storage
        self.learning_data = {
            "successful_patterns": [],
            "failed_patterns": [],
            "market_conditions": [],
            "token_behaviors": {},
        }

        self.load_learning_data()
        self.logger.info("🤖 Claude-Powered Non-Popular Token Trader initialized")
        self.logger.info("🎯 Focus: Micro-cap and nano-cap tokens for maximum alpha")

    def load_learning_data(self):
        """Load historical learning data"""
        try:
            if os.path.exists("claude_learning_data.json"):
                with open("claude_learning_data.json", "r") as f:
                    self.learning_data = json.load(f)
                self.logger.info(
                    f"📚 Loaded learning data: {len(self.learning_data.get('successful_patterns', []))} successful patterns"
                )
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")

    def save_learning_data(self):
        """Save learning data for future use"""
        try:
            with open("claude_learning_data.json", "w") as f:
                json.dump(self.learning_data, f, indent=2, default=str)
            self.logger.info("💾 Learning data saved")
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")

    def get_non_popular_tokens(self) -> List[Dict]:
        """Get list of non-popular tokens (low volume, high potential)"""
        try:
            # Get 24h ticker for all symbols
            tickers = self.client.get_ticker()

            non_popular = []
            for ticker in tickers:
                symbol = ticker["symbol"]

                # Only USDT pairs
                if not symbol.endswith("USDT"):
                    continue

                # Skip major stablecoins
                base_asset = symbol.replace("USDT", "")
                if base_asset in ["USDC", "BUSD", "DAI", "TUSD"]:
                    continue

                volume_usd = float(ticker["quoteVolume"])
                price_change = float(ticker["priceChangePercent"])

                # Filter for non-popular tokens
                if (
                    self.volume_thresholds["min_volume"]
                    <= volume_usd
                    <= self.volume_thresholds["avoid_popular"]
                ):

                    non_popular.append(
                        {
                            "symbol": symbol,
                            "volume_usd": volume_usd,
                            "price_change_24h": price_change,
                            "current_price": float(ticker["lastPrice"]),
                            "high_24h": float(ticker["highPrice"]),
                            "low_24h": float(ticker["lowPrice"]),
                            "volume_24h": float(ticker["volume"]),
                        }
                    )

            # Sort by volume (lowest first - most non-popular)
            non_popular.sort(key=lambda x: x["volume_usd"])

            self.logger.info(f"🔍 Found {len(non_popular)} non-popular tokens")
            return non_popular

        except Exception as e:
            self.logger.error(f"Error getting non-popular tokens: {e}")
            return []

    def get_detailed_analysis(self, symbol: str) -> Dict:
        """Get detailed technical analysis for a token"""
        try:
            # Get kline data
            klines = self.client.get_klines(
                symbol=symbol, interval="1h", limit=168
            )  # 7 days

            if not klines:
                return {}

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
                    "quote_asset_volume",
                    "number_of_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                    "ignore",
                ],
            )

            # Convert to numeric
            for col in ["open", "high", "low", "close", "volume", "quote_asset_volume"]:
                df[col] = pd.to_numeric(df[col])

            # Calculate technical indicators
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()

            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = df["close"].ewm(span=12).mean()
            ema_26 = df["close"].ewm(span=26).mean()
            df["macd"] = ema_12 - ema_26
            df["macd_signal"] = df["macd"].ewm(span=9).mean()

            # Bollinger Bands
            bb_period = 20
            df["bb_middle"] = df["close"].rolling(window=bb_period).mean()
            bb_std = df["close"].rolling(window=bb_period).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

            # Volume analysis
            df["volume_ma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            analysis = {
                "symbol": symbol,
                "current_price": latest["close"],
                "rsi": latest["rsi"],
                "macd": latest["macd"],
                "macd_signal": latest["macd_signal"],
                "bb_position": (latest["close"] - latest["bb_lower"])
                / (latest["bb_upper"] - latest["bb_lower"])
                * 100,
                "volume_ratio": latest["volume_ratio"],
                "price_vs_sma20": (latest["close"] / latest["sma_20"] - 1) * 100,
                "price_vs_sma50": (latest["close"] / latest["sma_50"] - 1) * 100,
                "volatility": df["close"].pct_change().std() * 100,
                "momentum_1h": (latest["close"] / prev["close"] - 1) * 100,
                "momentum_24h": (
                    (latest["close"] / df["close"].iloc[-24] - 1) * 100
                    if len(df) >= 24
                    else 0
                ),
                "recent_high": df["high"].tail(24).max(),
                "recent_low": df["low"].tail(24).min(),
                "trade_count": latest["number_of_trades"],
                "avg_trade_size": (
                    latest["quote_asset_volume"] / latest["number_of_trades"]
                    if latest["number_of_trades"] > 0
                    else 0
                ),
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {}

    def claude_analyze_token(self, token_data: Dict, market_context: Dict) -> Dict:
        """Use Claude AI to analyze token and provide trading recommendation"""
        try:
            # Prepare analysis prompt
            prompt = f"""
You are an expert cryptocurrency trader specializing in non-popular, low-volume tokens for maximum alpha generation.

Analyze this non-popular token for trading opportunity:

TOKEN: {token_data.get('symbol', 'Unknown')}
Volume (24h): ${token_data.get('volume_usd', 0):,.0f} (NON-POPULAR RANGE)
Price Change (24h): {token_data.get('price_change_24h', 0):+.2f}%
Current Price: ${token_data.get('current_price', 0):.6f}

TECHNICAL ANALYSIS:
- RSI: {token_data.get('rsi', 50):.1f}
- MACD: {token_data.get('macd', 0):.6f}
- MACD Signal: {token_data.get('macd_signal', 0):.6f}
- Bollinger Band Position: {token_data.get('bb_position', 50):.1f}%
- Volume Ratio: {token_data.get('volume_ratio', 1):.2f}x
- Price vs SMA20: {token_data.get('price_vs_sma20', 0):+.2f}%
- Price vs SMA50: {token_data.get('price_vs_sma50', 0):+.2f}%
- Volatility: {token_data.get('volatility', 0):.2f}%
- 1h Momentum: {token_data.get('momentum_1h', 0):+.2f}%
- 24h Momentum: {token_data.get('momentum_24h', 0):+.2f}%
- Recent High: ${token_data.get('recent_high', 0):.6f}
- Recent Low: ${token_data.get('recent_low', 0):.6f}
- Average Trade Size: ${token_data.get('avg_trade_size', 0):.2f}

MARKET CONTEXT:
- Total Non-Popular Tokens Analyzed: {market_context.get('total_tokens', 0)}
- Average Market Change: {market_context.get('avg_change', 0):+.2f}%
- Market Sentiment: {market_context.get('sentiment', 'Neutral')}

LEARNING FROM PAST TRADES:
{self.format_learning_data()}

TRADING CRITERIA FOR NON-POPULAR TOKENS:
- Focus on tokens with $1K-$100K daily volume (avoid mainstream)
- Look for technical breakouts with volume confirmation
- Identify oversold conditions in quality projects
- Find tokens with unique narratives or catalysts
- Target 15-30% gains (higher than popular tokens)
- Accept higher volatility for higher returns

Please provide:
1. RECOMMENDATION: BUY/SELL/HOLD with confidence (0-100%)
2. REASONING: Why this token presents an opportunity
3. ENTRY_PRICE: Optimal entry point
4. STOP_LOSS: Risk management level
5. TAKE_PROFIT_1: First target (15% typical)
6. TAKE_PROFIT_2: Second target (30% typical)
7. POSITION_SIZE: Recommended % of portfolio (1-8%)
8. RISK_FACTORS: Key risks to monitor
9. CATALYSTS: Potential positive drivers
10. LEARNING_PATTERN: What pattern this represents for future learning

Format as JSON for easy parsing.
"""

            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            analysis_text = response.content[0].text

            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                json_start = analysis_text.find("{")
                json_end = analysis_text.rfind("}") + 1

                if json_start != -1 and json_end != -1:
                    json_str = analysis_text[json_start:json_end]
                    claude_analysis = json.loads(json_str)
                else:
                    # Fallback: parse key information
                    claude_analysis = self.parse_claude_response(analysis_text)

                self.logger.info(
                    f"🤖 Claude analyzed {token_data.get('symbol')}: {claude_analysis.get('RECOMMENDATION', 'UNKNOWN')}"
                )
                return claude_analysis

            except json.JSONDecodeError:
                # Fallback parsing
                return self.parse_claude_response(analysis_text)

        except Exception as e:
            self.logger.error(f"Error with Claude analysis: {e}")
            return {
                "RECOMMENDATION": "HOLD",
                "confidence": 0,
                "REASONING": f"Analysis failed: {e}",
            }

    def parse_claude_response(self, text: str) -> Dict:
        """Parse Claude response when JSON parsing fails"""
        analysis = {
            "RECOMMENDATION": "HOLD",
            "confidence": 0,
            "REASONING": "Failed to parse response",
            "ENTRY_PRICE": 0,
            "STOP_LOSS": 0,
            "TAKE_PROFIT_1": 0,
            "TAKE_PROFIT_2": 0,
            "POSITION_SIZE": 0,
            "RISK_FACTORS": [],
            "CATALYSTS": [],
            "LEARNING_PATTERN": "unknown",
        }

        # Simple text parsing
        if "BUY" in text.upper():
            analysis["RECOMMENDATION"] = "BUY"
            analysis["confidence"] = 70
        elif "SELL" in text.upper():
            analysis["RECOMMENDATION"] = "SELL"
            analysis["confidence"] = 70

        return analysis

    def format_learning_data(self) -> str:
        """Format learning data for Claude context"""
        successful = len(self.learning_data.get("successful_patterns", []))
        failed = len(self.learning_data.get("failed_patterns", []))

        summary = f"Successful patterns: {successful}, Failed patterns: {failed}\n"

        # Add recent successful patterns
        if successful > 0:
            recent_success = self.learning_data["successful_patterns"][-3:]  # Last 3
            summary += "Recent successful patterns:\n"
            for pattern in recent_success:
                summary += f"- {pattern.get('pattern', 'Unknown')}: {pattern.get('outcome', 'Unknown')}\n"

        return summary

    def execute_trade_decision(
        self, symbol: str, claude_analysis: Dict, token_data: Dict
    ) -> bool:
        """Execute trade based on Claude's analysis"""
        try:
            recommendation = claude_analysis.get("RECOMMENDATION", "HOLD")
            confidence = claude_analysis.get("confidence", 0)

            if (
                recommendation == "BUY"
                and confidence >= self.trading_params["min_confidence"]
            ):
                return self.execute_buy_order(symbol, claude_analysis, token_data)
            elif recommendation == "SELL":
                return self.execute_sell_order(symbol, claude_analysis)

            return False

        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
            return False

    def execute_buy_order(self, symbol: str, analysis: Dict, token_data: Dict) -> bool:
        """Execute buy order for non-popular token"""
        try:
            # Get account balance
            account = self.client.get_account()
            usdt_balance = 0

            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"])
                    break

            if usdt_balance < 10:  # Minimum $10 to trade
                self.logger.warning(f"Insufficient USDT balance: ${usdt_balance}")
                return False

            # Calculate position size
            position_size_pct = (
                min(
                    analysis.get("POSITION_SIZE", 5),
                    self.trading_params["max_position_size"] * 100,
                )
                / 100
            )
            position_value = usdt_balance * position_size_pct

            # Get current price and calculate quantity
            current_price = token_data["current_price"]
            quantity = position_value / current_price

            # Get symbol info for precision
            symbol_info = self.client.get_symbol_info(symbol)
            step_size = 0.00000001  # Default

            for filter in symbol_info["filters"]:
                if filter["filterType"] == "LOT_SIZE":
                    step_size = float(filter["stepSize"])
                    break

            # Round quantity to proper precision
            quantity = round(quantity - (quantity % step_size), 8)

            if quantity * current_price < 10:  # Minimum order value
                self.logger.warning(f"Order value too small for {symbol}")
                return False

            # Place market buy order
            self.logger.info(
                f"🛒 Placing BUY order for {symbol}: {quantity} @ ${current_price:.6f}"
            )

            order = self.client.order_market_buy(symbol=symbol, quantity=quantity)

            # Record trade
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": current_price,
                "value": quantity * current_price,
                "claude_analysis": analysis,
                "token_data": token_data,
                "order_id": order["orderId"],
            }

            # Save trade record
            self.save_trade_record(trade_record)

            self.logger.info(
                f"✅ BUY order executed for {symbol}: Order ID {order['orderId']}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error executing buy order for {symbol}: {e}")
            return False

    def save_trade_record(self, trade_record: Dict):
        """Save trade record for learning"""
        try:
            filename = f"claude_trades_{datetime.now().strftime('%Y%m%d')}.json"

            trades = []
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    trades = json.load(f)

            trades.append(trade_record)

            with open(filename, "w") as f:
                json.dump(trades, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving trade record: {e}")

    def monitor_positions(self):
        """Monitor open positions and manage exits"""
        try:
            account = self.client.get_account()
            positions = []

            for balance in account["balances"]:
                if balance["asset"] != "USDT" and float(balance["free"]) > 0:
                    symbol = balance["asset"] + "USDT"
                    positions.append(
                        {
                            "symbol": symbol,
                            "quantity": float(balance["free"]),
                            "asset": balance["asset"],
                        }
                    )

            for position in positions:
                self.check_exit_conditions(position)

        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")

    def check_exit_conditions(self, position: Dict):
        """Check if position should be closed"""
        try:
            symbol = position["symbol"]

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker["price"])

            # Load trade record to get entry price
            entry_price = self.get_entry_price(symbol)
            if not entry_price:
                return

            # Calculate P&L
            pnl_pct = (current_price / entry_price - 1) * 100

            # Check exit conditions
            should_exit = False
            exit_reason = ""

            if pnl_pct <= -self.trading_params["stop_loss"] * 100:
                should_exit = True
                exit_reason = f"Stop loss hit: {pnl_pct:.2f}%"
            elif pnl_pct >= self.trading_params["take_profit_2"] * 100:
                should_exit = True
                exit_reason = f"Take profit 2 hit: {pnl_pct:.2f}%"
            elif pnl_pct >= self.trading_params["take_profit_1"] * 100:
                # Use Claude to decide if we should take profit or hold
                claude_exit = self.claude_exit_decision(
                    symbol, current_price, entry_price, pnl_pct
                )
                if claude_exit:
                    should_exit = True
                    exit_reason = f"Claude recommended exit: {pnl_pct:.2f}%"

            if should_exit:
                self.execute_sell_order(symbol, {"reason": exit_reason})

        except Exception as e:
            self.logger.error(
                f"Error checking exit conditions for {position['symbol']}: {e}"
            )

    def claude_exit_decision(
        self, symbol: str, current_price: float, entry_price: float, pnl_pct: float
    ) -> bool:
        """Use Claude to make exit decision when in profit"""
        try:
            # Get fresh analysis
            token_data = self.get_token_current_state(symbol)

            prompt = f"""
You are managing a profitable position in a non-popular token. Should you take profits or hold?

POSITION INFO:
Symbol: {symbol}
Entry Price: ${entry_price:.6f}
Current Price: ${current_price:.6f}
Current P&L: {pnl_pct:+.2f}%

CURRENT TECHNICAL STATE:
{json.dumps(token_data, indent=2)}

The first take profit target of 15% has been hit. Should I:
1. TAKE_PROFIT - Lock in gains now
2. HOLD - Continue holding for higher targets

Consider:
- Non-popular tokens can be more volatile
- Technical momentum and volume
- Risk of reversal vs potential for more gains

Respond with just "TAKE_PROFIT" or "HOLD" and brief reasoning.
"""

            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            decision = response.content[0].text.upper()
            return "TAKE_PROFIT" in decision

        except Exception as e:
            self.logger.error(f"Error with Claude exit decision: {e}")
            return True  # Default to taking profit on error

    def get_token_current_state(self, symbol: str) -> Dict:
        """Get current state of token for exit decision"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return {
                "current_price": float(ticker["price"]),
                "timestamp": datetime.now().isoformat(),
            }
        except:
            return {}

    def get_entry_price(self, symbol: str) -> Optional[float]:
        """Get entry price from trade records"""
        try:
            filename = f"claude_trades_{datetime.now().strftime('%Y%m%d')}.json"

            if os.path.exists(filename):
                with open(filename, "r") as f:
                    trades = json.load(f)

                # Find most recent buy for this symbol
                for trade in reversed(trades):
                    if trade["symbol"] == symbol and trade["action"] == "BUY":
                        return trade["price"]

            return None

        except Exception as e:
            self.logger.error(f"Error getting entry price for {symbol}: {e}")
            return None

    def execute_sell_order(self, symbol: str, analysis: Dict) -> bool:
        """Execute sell order"""
        try:
            # Get current balance
            account = self.client.get_account()
            asset = symbol.replace("USDT", "")
            quantity = 0

            for balance in account["balances"]:
                if balance["asset"] == asset:
                    quantity = float(balance["free"])
                    break

            if quantity <= 0:
                return False

            # Place market sell order
            self.logger.info(f"💰 Placing SELL order for {symbol}: {quantity}")

            order = self.client.order_market_sell(symbol=symbol, quantity=quantity)

            self.logger.info(
                f"✅ SELL order executed for {symbol}: {analysis.get('reason', 'Exit strategy')}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error executing sell order for {symbol}: {e}")
            return False

    def run_trading_session(self):
        """Run a complete trading session"""
        self.logger.info("🚀 Starting Claude-powered non-popular token trading session")

        # Get non-popular tokens
        tokens = self.get_non_popular_tokens()

        if not tokens:
            self.logger.warning("No non-popular tokens found")
            return

        # Focus on top candidates (lowest volume = most non-popular)
        top_candidates = tokens[:20]  # Top 20 least popular

        market_context = {
            "total_tokens": len(tokens),
            "avg_change": sum(t["price_change_24h"] for t in tokens) / len(tokens),
            "sentiment": (
                "Bearish"
                if sum(t["price_change_24h"] for t in tokens) < 0
                else "Bullish"
            ),
        }

        trades_made = 0
        max_trades = 3  # Maximum trades per session

        for token in top_candidates:
            if trades_made >= max_trades:
                break

            symbol = token["symbol"]
            self.logger.info(
                f"🔍 Analyzing non-popular token: {symbol} (Vol: ${token['volume_usd']:,.0f})"
            )

            # Get detailed analysis
            detailed_analysis = self.get_detailed_analysis(symbol)
            if not detailed_analysis:
                continue

            # Combine token data
            combined_data = {**token, **detailed_analysis}

            # Get Claude's analysis
            claude_analysis = self.claude_analyze_token(combined_data, market_context)

            # Execute trade if recommended
            if self.execute_trade_decision(symbol, claude_analysis, combined_data):
                trades_made += 1
                time.sleep(2)  # Brief pause between trades

            time.sleep(1)  # Rate limiting

        # Monitor existing positions
        self.monitor_positions()

        # Save learning data
        self.save_learning_data()

        self.logger.info(f"🏁 Trading session complete. Trades made: {trades_made}")


def main():
    """Main execution"""
    print("🤖 Claude-Powered Non-Popular Token Trader")
    print("=" * 50)
    print("Focus: Finding alpha in micro-cap and nano-cap tokens")
    print("Strategy: AI-driven analysis of less popular tokens")
    print("=" * 50)

    trader = ClaudeNonPopularTrader()
    trader.run_trading_session()


if __name__ == "__main__":
    main()
