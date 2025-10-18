#!/usr/bin/env python3
"""
VictoryChain Core - Consolidated Trading System
All-in-one trading bot with multiple strategies and AI analysis
"""

import os
import json
import sys
import logging
import requests
import time
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VictoryChainCore:
    def __init__(self):
        load_dotenv()

        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        # Trading configuration
        self.config = {
            "min_balance": 10.0,
            "max_position_pct": 0.8,
            "stop_loss_pct": 0.08,
            "take_profit_pct": 0.15,
            "momentum_threshold": 5.0,
            "similarity_threshold": 50.0,
        }

        # MAGICUSDT winning pattern (reference)
        self.reference_pattern = {
            "performance": 18.81,
            "momentum_score": 0.998,
            "range_position": 0.97,
            "pattern_type": "MOMENTUM_SURGE",
        }

        print("🚀 VictoryChain Core Initialized")
        print("🎯 Multi-Strategy Trading System Ready")

    def get_account_info(self):
        """Get account balance and holdings"""
        try:
            account = self.client.get_account()
            balances = {}
            total_usdt_value = 0

            for balance in account["balances"]:
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])

                if free > 0 or locked > 0:
                    balances[asset] = {
                        "free": free,
                        "locked": locked,
                        "total": free + locked,
                    }

                    if asset == "USDT":
                        total_usdt_value += free + locked
                    elif free + locked > 0:
                        # Get USDT value for other assets
                        try:
                            ticker = self.client.get_symbol_ticker(
                                symbol=f"{asset}USDT"
                            )
                            price = float(ticker["price"])
                            total_usdt_value += (free + locked) * price
                        except:
                            pass

            return {
                "balances": balances,
                "total_usdt_value": total_usdt_value,
                "usdt_balance": balances.get("USDT", {}).get("free", 0),
            }

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_all_tokens(self):
        """Get all tradable USDT pairs with 24h data"""
        try:
            tickers = self.client.get_ticker()
            usdt_pairs = []

            for ticker in tickers:
                symbol = ticker["symbol"]
                if symbol.endswith("USDT") and symbol != "USDCUSDT":
                    usdt_pairs.append(ticker)

            logger.info(f"Found {len(usdt_pairs)} tradable USDT pairs")
            return usdt_pairs

        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return []

    def analyze_momentum(self, tokens_data):
        """Analyze momentum patterns similar to reference"""
        opportunities = []

        for token in tokens_data:
            try:
                symbol = token["symbol"]
                price_change = float(token["priceChangePercent"])
                current_price = float(token["lastPrice"])
                high_24h = float(token["highPrice"])
                low_24h = float(token["lowPrice"])
                volume = float(token["quoteVolume"])

                # Skip weak performers
                if price_change < self.config["momentum_threshold"] or volume < 1000:
                    continue

                # Calculate similarity to reference pattern
                range_position = (
                    (current_price - low_24h) / (high_24h - low_24h)
                    if high_24h != low_24h
                    else 0.5
                )

                # Scoring algorithm
                performance_score = min(abs(price_change) / 20.0, 1.0) * 40
                momentum_score = (1 if price_change > 0 else 0) * 30
                position_score = range_position * 20
                volume_score = min(volume / 50000, 1.0) * 10

                similarity = (
                    performance_score + momentum_score + position_score + volume_score
                )

                if similarity >= self.config["similarity_threshold"]:
                    opportunities.append(
                        {
                            "symbol": symbol,
                            "similarity": similarity,
                            "price_change": price_change,
                            "range_position": range_position,
                            "current_price": current_price,
                            "volume": volume,
                            "high_24h": high_24h,
                            "low_24h": low_24h,
                        }
                    )

            except (ValueError, KeyError):
                continue

        # Sort by similarity
        opportunities.sort(key=lambda x: x["similarity"], reverse=True)
        return opportunities

    def analyze_with_claude(self, top_opportunities):
        """Enhanced Claude analysis for top opportunities"""
        if not self.claude_api_key or not top_opportunities:
            return None

        prompt = f"""
Analyze these crypto trading opportunities for momentum patterns:

TOP OPPORTUNITIES:
{json.dumps([{
    'symbol': opp['symbol'],
    'change': f"{opp['price_change']:+.2f}%",
    'similarity': f"{opp['similarity']:.1f}%",
    'price': f"${opp['current_price']:.6f}",
    'volume': f"${opp['volume']:,.0f}",
    'range_pos': f"{opp['range_position']:.1%}"
} for opp in top_opportunities[:10]], indent=2)}

Provide:
1. Risk assessment for each token
2. Entry/exit recommendations
3. Portfolio allocation suggestions
4. Market timing analysis

Return structured analysis with specific trading advice.
"""

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

            if response.status_code == 200:
                return response.json()["content"][0]["text"]
            else:
                logger.error(f"Claude API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")

        return None

    def calculate_position_size(self, usdt_balance, similarity_score):
        """Calculate optimal position size based on similarity and balance"""
        base_pct = min(self.config["max_position_pct"], 0.2)  # Start with 20% max

        # Adjust based on similarity score
        if similarity_score >= 80:
            multiplier = 1.0  # Full allocation for high similarity
        elif similarity_score >= 70:
            multiplier = 0.8
        elif similarity_score >= 60:
            multiplier = 0.6
        else:
            multiplier = 0.4

        position_size = usdt_balance * base_pct * multiplier
        return min(position_size, usdt_balance * self.config["max_position_pct"])

    def display_analysis_results(self, opportunities, claude_analysis=None):
        """Display comprehensive analysis results"""
        print("\n🏆 VICTORYCHAIN ANALYSIS RESULTS")
        print("=" * 60)

        if claude_analysis:
            print("🧠 Claude AI Insights:")
            print(
                claude_analysis[:1000] + "..."
                if len(claude_analysis) > 1000
                else claude_analysis
            )
            print("")

        print(f"🎯 Found {len(opportunities)} high-potential opportunities")

        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. {opp['symbol']}")
            print(f"   🎯 Similarity Score: {opp['similarity']:.1f}%")
            print(f"   📈 24h Change: {opp['price_change']:+.2f}%")
            print(f"   📊 Range Position: {opp['range_position']:.1%}")
            print(f"   💰 Price: ${opp['current_price']:.6f}")
            print(f"   💸 Volume: ${opp['volume']:,.0f}")

            if opp["similarity"] >= 80:
                print(f"   🚀 EXCEPTIONAL - Top trading candidate!")
            elif opp["similarity"] >= 70:
                print(f"   ⚡ EXCELLENT - Strong opportunity")
            elif opp["similarity"] >= 60:
                print(f"   ✅ GOOD - Consider for portfolio")

    def get_trading_recommendation(self, opportunities, account_info):
        """Generate specific trading recommendations"""
        if not opportunities or not account_info:
            return None

        usdt_balance = account_info["usdt_balance"]

        if usdt_balance < self.config["min_balance"]:
            print(
                f"\n❌ Insufficient balance: ${usdt_balance:.2f} < ${self.config['min_balance']}"
            )
            return None

        best_opp = opportunities[0]
        position_size = self.calculate_position_size(
            usdt_balance, best_opp["similarity"]
        )

        recommendation = {
            "symbol": best_opp["symbol"],
            "action": "BUY",
            "position_size": position_size,
            "entry_price": best_opp["current_price"],
            "take_profit": best_opp["current_price"]
            * (1 + self.config["take_profit_pct"]),
            "stop_loss": best_opp["current_price"] * (1 - self.config["stop_loss_pct"]),
            "similarity": best_opp["similarity"],
            "confidence": "HIGH" if best_opp["similarity"] >= 75 else "MEDIUM",
        }

        print(f"\n💡 TRADING RECOMMENDATION")
        print("=" * 35)
        print(f"🎯 Symbol: {recommendation['symbol']}")
        print(f"📊 Similarity: {recommendation['similarity']:.1f}%")
        print(f"💰 Position Size: ${recommendation['position_size']:.2f}")
        print(f"🎯 Entry: ${recommendation['entry_price']:.6f}")
        print(
            f"🚀 Take Profit: ${recommendation['take_profit']:.6f} (+{self.config['take_profit_pct']:.0%})"
        )
        print(
            f"🛡️  Stop Loss: ${recommendation['stop_loss']:.6f} (-{self.config['stop_loss_pct']:.0%})"
        )
        print(f"⚡ Confidence: {recommendation['confidence']}")

        return recommendation

    def execute_trade(self, recommendation):
        """Execute the recommended trade (with confirmation)"""
        symbol = recommendation["symbol"]
        position_size = recommendation["position_size"]

        print(f"\n🚨 EXECUTE TRADE CONFIRMATION")
        print(f"Symbol: {symbol}")
        print(f"Amount: ${position_size:.2f}")
        print(f"Confidence: {recommendation['confidence']}")

        confirm = input("\nType 'EXECUTE' to place order: ")

        if confirm != "EXECUTE":
            print("❌ Trade cancelled")
            return False

        try:
            # Place market buy order
            order = self.client.order_market_buy(
                symbol=symbol, quoteOrderQty=position_size
            )

            print(f"✅ Order executed successfully!")
            print(f"Order ID: {order['orderId']}")
            print(f"Status: {order['status']}")

            # Save trade record
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "side": "BUY",
                "amount": position_size,
                "order_id": order["orderId"],
                "recommendation": recommendation,
            }

            with open("trade_history.json", "a") as f:
                f.write(json.dumps(trade_record) + "\n")

            return True

        except BinanceAPIException as e:
            print(f"❌ Trade execution failed: {e}")
            return False

    def run_analysis(self, execute_trades=False):
        """Run complete analysis and optional trade execution"""
        print("🔍 Starting VictoryChain Analysis...")

        # Get account info
        account_info = self.get_account_info()
        if not account_info:
            print("❌ Failed to get account information")
            return

        print(f"💰 Portfolio Value: ${account_info['total_usdt_value']:.2f}")
        print(f"💵 Available USDT: ${account_info['usdt_balance']:.2f}")

        # Get market data
        tokens_data = self.get_all_tokens()
        if not tokens_data:
            print("❌ Failed to get market data")
            return

        # Analyze momentum opportunities
        opportunities = self.analyze_momentum(tokens_data)

        if not opportunities:
            print("❌ No opportunities found matching criteria")
            return

        # Enhanced Claude analysis
        claude_analysis = self.analyze_with_claude(opportunities)

        # Display results
        self.display_analysis_results(opportunities, claude_analysis)

        # Generate trading recommendation
        recommendation = self.get_trading_recommendation(opportunities, account_info)

        if recommendation and execute_trades:
            success = self.execute_trade(recommendation)
            if success:
                print("🎉 Trade executed successfully!")

        # Save analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = f"victorychain_analysis_{timestamp}.json"

        with open(analysis_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "account_info": account_info,
                    "opportunities": opportunities[:10],
                    "claude_analysis": claude_analysis,
                    "recommendation": recommendation,
                    "config": self.config,
                },
                f,
                indent=2,
            )

        print(f"\n✅ Analysis saved to: {analysis_file}")
        print("🎉 VictoryChain Analysis Complete!")


def main():
    """Main function"""
    print("🚀 VICTORYCHAIN CORE TRADING SYSTEM")
    print("=" * 50)

    # Safety warning
    print("\n⚠️  TRADING RISK WARNING:")
    print("   This is a live trading system")
    print("   Only trade with money you can afford to lose")
    print("   Cryptocurrency trading involves significant risk")

    # Initialize system
    vc = VictoryChainCore()

    # Run analysis
    vc.run_analysis(execute_trades=False)

    # Ask for trade execution
    if input("\n🚨 Execute recommended trades? (y/N): ").lower() == "y":
        vc.run_analysis(execute_trades=True)


if __name__ == "__main__":
    main()
