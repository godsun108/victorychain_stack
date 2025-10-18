"""
LIVE BINANCE US INTEGRATION
==========================
Real-time trading data and execution using Binance US API
"""

import ccxt
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import time
from dataclasses import dataclass


@dataclass
class LiveMarketData:
    """Live market data from Binance US"""

    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    bid: float
    ask: float
    timestamp: datetime


@dataclass
class LiveTradeSignal:
    """Live trading signal with real market data"""

    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float
    reasoning: str
    risk_score: float


class BinanceUSLiveConnector:
    """Live connection to Binance US with real API credentials"""

    def __init__(self):
        # Your actual Binance US API credentials
        self.api_key = (
            "o0KEblMxyczeSMETOFC5Kp7wheZJVVk0JQ5tfGv5TGiLXX909VqcR59ofWFoytVX"
        )
        self.api_secret = (
            "bjzQ1ZB3qoxE62r5uofcrPSLUYsYqqFyfzZaAdgjOBNHSZlnNiBXXm2zKBM8PMYg"
        )

        # Initialize Binance US exchange
        self.exchange = None
        self.is_connected = False
        self.account_info = None
        self.trading_pairs = []

        # Live data cache
        self.live_prices = {}
        self.live_orderbook = {}
        self.live_trades = {}

        # Initialize connection synchronously
        self._initialize_connection_sync()

    def _initialize_connection_sync(self):
        """Initialize live connection to Binance US (synchronous)"""
        try:
            print("🔗 Connecting to Binance US with live API credentials...")

            # Initialize Binance US exchange
            self.exchange = ccxt.binanceus(
                {
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "sandbox": False,  # LIVE TRADING
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "spot",  # Spot trading
                    },
                }
            )

            # Test connection and get account info
            self._test_connection_sync()

            # Load available trading pairs
            self._load_trading_pairs_sync()

            self.is_connected = True
            print("✅ Successfully connected to Binance US LIVE API!")

        except Exception as e:
            print(f"❌ Failed to connect to Binance US: {e}")
            self.is_connected = False

    def _test_connection_sync(self):
        """Test API connection and get account information (synchronous)"""
        try:
            # Get account information
            self.account_info = self.exchange.fetch_balance()

            print("💰 LIVE ACCOUNT INFORMATION:")
            total_usdt = self.account_info.get("total", {}).get("USDT", 0)
            free_usdt = self.account_info.get("free", {}).get("USDT", 0)
            used_usdt = self.account_info.get("used", {}).get("USDT", 0)

            print(f"   Total Balance: ${total_usdt:.2f} USDT")
            print(f"   Free Balance: ${free_usdt:.2f} USDT")
            print(f"   Used Balance: ${used_usdt:.2f} USDT")

            # Show non-zero balances
            for currency, balance in self.account_info.get("total", {}).items():
                if balance and balance > 0.001:
                    print(f"   {currency}: {balance:.6f}")

        except Exception as e:
            print(f"⚠️ Account info error: {e}")
            raise

    def _load_trading_pairs_sync(self):
        """Load all available trading pairs from Binance US (synchronous)"""
        try:
            markets = self.exchange.load_markets()

            # Filter for USDT pairs
            usdt_pairs = [symbol for symbol in markets.keys() if "/USDT" in symbol]

            # Filter for high-volume pairs
            self.trading_pairs = usdt_pairs[:50]  # Top 50 pairs

            print(f"📊 Loaded {len(self.trading_pairs)} trading pairs:")
            for i, pair in enumerate(self.trading_pairs[:10]):  # Show first 10
                print(f"   {i+1}. {pair}")
            if len(self.trading_pairs) > 10:
                print(f"   ... and {len(self.trading_pairs) - 10} more pairs")

        except Exception as e:
            print(f"❌ Error loading trading pairs: {e}")
            raise

    async def _initialize_connection(self):
        """Initialize live connection to Binance US"""
        try:
            print("🔗 Connecting to Binance US with live API credentials...")

            # Initialize Binance US exchange
            self.exchange = ccxt.binanceus(
                {
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "sandbox": False,  # LIVE TRADING
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "spot",  # Spot trading
                    },
                }
            )

            # Test connection and get account info
            await self._test_connection()

            # Load available trading pairs
            await self._load_trading_pairs()

            self.is_connected = True
            print("✅ Successfully connected to Binance US LIVE API!")

        except Exception as e:
            print(f"❌ Failed to connect to Binance US: {e}")
            self.is_connected = False

    async def _test_connection(self):
        """Test API connection and get account information"""
        try:
            # Get account information
            self.account_info = self.exchange.fetch_balance()

            print("💰 LIVE ACCOUNT INFORMATION:")
            print(f"   Total Balance: ${self.account_info['total']['USDT']:.2f} USDT")
            print(f"   Free Balance: ${self.account_info['free']['USDT']:.2f} USDT")
            print(f"   Used Balance: ${self.account_info['used']['USDT']:.2f} USDT")

            # Show non-zero balances
            for currency, balance in self.account_info["total"].items():
                if balance and balance > 0.001:
                    print(f"   {currency}: {balance:.6f}")

        except Exception as e:
            print(f"⚠️ Account info error: {e}")
            raise

    async def _load_trading_pairs(self):
        """Load all available trading pairs from Binance US"""
        try:
            markets = self.exchange.load_markets()

            # Filter for USDT pairs
            usdt_pairs = [symbol for symbol in markets.keys() if "/USDT" in symbol]

            # Filter for high-volume pairs
            self.trading_pairs = usdt_pairs[:50]  # Top 50 pairs

            print(f"📊 Loaded {len(self.trading_pairs)} trading pairs:")
            for i, pair in enumerate(self.trading_pairs[:10]):  # Show first 10
                print(f"   {i+1}. {pair}")
            if len(self.trading_pairs) > 10:
                print(f"   ... and {len(self.trading_pairs) - 10} more pairs")

        except Exception as e:
            print(f"❌ Error loading trading pairs: {e}")
            raise

    async def get_live_market_data(
        self, symbols: List[str] = None
    ) -> List[LiveMarketData]:
        """Get live market data for specified symbols"""
        if not self.is_connected:
            raise Exception("Not connected to Binance US")

        if symbols is None:
            symbols = self.trading_pairs[:20]  # Default to top 20 pairs

        live_data = []

        try:
            print(f"📡 Fetching live data for {len(symbols)} symbols...")

            # Fetch 24hr ticker data
            tickers = self.exchange.fetch_tickers(symbols)

            for symbol in symbols:
                if symbol in tickers:
                    ticker = tickers[symbol]

                    # Get order book for bid/ask
                    try:
                        orderbook = self.exchange.fetch_order_book(symbol, limit=5)
                        bid = (
                            orderbook["bids"][0][0]
                            if orderbook["bids"]
                            else ticker["last"]
                        )
                        ask = (
                            orderbook["asks"][0][0]
                            if orderbook["asks"]
                            else ticker["last"]
                        )
                    except:
                        bid = ask = ticker["last"]

                    market_data = LiveMarketData(
                        symbol=symbol,
                        price=ticker["last"],
                        change_24h=ticker["percentage"],
                        volume_24h=ticker["quoteVolume"],
                        high_24h=ticker["high"],
                        low_24h=ticker["low"],
                        bid=bid,
                        ask=ask,
                        timestamp=datetime.now(),
                    )

                    live_data.append(market_data)

                    # Cache the data
                    self.live_prices[symbol] = market_data

            print(f"✅ Successfully fetched live data for {len(live_data)} symbols")
            return live_data

        except Exception as e:
            print(f"❌ Error fetching live market data: {e}")
            return []

    async def get_live_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get live order book for a symbol"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            self.live_orderbook[symbol] = orderbook
            return orderbook
        except Exception as e:
            print(f"❌ Error fetching orderbook for {symbol}: {e}")
            return {}

    async def get_live_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for a symbol"""
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            self.live_trades[symbol] = trades
            return trades
        except Exception as e:
            print(f"❌ Error fetching trades for {symbol}: {e}")
            return []

    def get_account_balance(self) -> Dict:
        """Get current account balance"""
        return self.account_info if self.account_info else {}

    async def place_live_order(
        self, symbol: str, side: str, amount: float, price: float = None
    ) -> Dict:
        """Place a live order (USE WITH EXTREME CAUTION)"""
        try:
            print(f"⚠️ LIVE ORDER ATTEMPT: {side} {amount} {symbol} at {price}")
            print("🛑 ORDER BLOCKED FOR SAFETY - This is a demo mode")
            print("🔧 To enable live trading, remove this safety block")

            # SAFETY BLOCK - Remove this to enable live trading
            return {
                "id": "DEMO_ORDER_123",
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": price,
                "status": "DEMO_BLOCKED",
                "timestamp": datetime.now().isoformat(),
            }

            # UNCOMMENT BELOW FOR LIVE TRADING (REMOVE SAFETY BLOCK)
            """
            if price:
                # Limit order
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                # Market order
                order = self.exchange.create_market_order(symbol, side, amount)
            
            print(f"✅ Order placed: {order['id']}")
            return order
            """

        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return {}


class LiveTradingAnalyzer:
    """Analyze live market data for trading opportunities"""

    def __init__(self, binance_connector: BinanceUSLiveConnector):
        self.binance = binance_connector
        self.signals_generated = 0
        self.opportunities_found = 0

    async def analyze_live_opportunities(
        self, symbols: List[str] = None
    ) -> List[LiveTradeSignal]:
        """Analyze live market data for trading opportunities"""
        print("🔍 Analyzing live market opportunities...")

        # Get live market data
        live_data = await self.binance.get_live_market_data(symbols)

        signals = []

        for data in live_data:
            # Generate trading signals based on live data
            signal = await self._generate_live_signal(data)
            if signal:
                signals.append(signal)

        # Sort by confidence
        signals.sort(key=lambda x: x.confidence, reverse=True)

        self.signals_generated += len(signals)
        self.opportunities_found += len([s for s in signals if s.action != "HOLD"])

        return signals[:10]  # Top 10 signals

    async def _generate_live_signal(
        self, data: LiveMarketData
    ) -> Optional[LiveTradeSignal]:
        """Generate trading signal from live market data"""
        try:
            # Get additional data for analysis
            orderbook = await self.binance.get_live_orderbook(data.symbol, limit=10)
            recent_trades = await self.binance.get_live_trades(data.symbol, limit=50)

            # Analyze price momentum
            momentum_score = self._analyze_momentum(data)

            # Analyze order book
            liquidity_score = self._analyze_liquidity(orderbook)

            # Analyze recent trades
            volume_score = self._analyze_volume(recent_trades, data)

            # Generate overall signal
            overall_score = (momentum_score + liquidity_score + volume_score) / 3

            # Determine action
            if overall_score > 7.5 and data.change_24h > 5:
                action = "BUY"
                confidence = min(0.95, overall_score / 10)
                target_price = data.price * 1.10  # 10% target
                stop_loss = data.price * 0.95  # 5% stop loss
                reasoning = f"Strong momentum: +{data.change_24h:.1f}%, High liquidity"
            elif overall_score < 3.0 and data.change_24h < -10:
                action = "SELL"
                confidence = min(0.90, (10 - overall_score) / 10)
                target_price = data.price * 0.90  # 10% down target
                stop_loss = data.price * 1.05  # 5% stop loss (short)
                reasoning = f"Weak momentum: {data.change_24h:.1f}%, Oversold signal"
            else:
                action = "HOLD"
                confidence = 0.5
                target_price = data.price
                stop_loss = data.price * 0.95
                reasoning = "Neutral market conditions"

            # Calculate position size (2% of account balance)
            account_balance = self.binance.get_account_balance()
            usdt_balance = account_balance.get("total", {}).get(
                "USDT", 1000
            )  # Default $1000
            position_size = (usdt_balance * 0.02) / data.price  # 2% position

            return LiveTradeSignal(
                symbol=data.symbol,
                action=action,
                confidence=confidence,
                entry_price=data.price,
                target_price=target_price,
                stop_loss=stop_loss,
                position_size=position_size,
                reasoning=reasoning,
                risk_score=self._calculate_risk_score(data, overall_score),
            )

        except Exception as e:
            print(f"❌ Error generating signal for {data.symbol}: {e}")
            return None

    def _analyze_momentum(self, data: LiveMarketData) -> float:
        """Analyze price momentum (0-10 score)"""
        change = abs(data.change_24h)
        if change > 20:
            return 9.0
        elif change > 10:
            return 7.0
        elif change > 5:
            return 6.0
        elif change > 2:
            return 5.0
        else:
            return 3.0

    def _analyze_liquidity(self, orderbook: Dict) -> float:
        """Analyze order book liquidity (0-10 score)"""
        if not orderbook or "bids" not in orderbook:
            return 3.0

        # Calculate bid-ask spread
        if orderbook["bids"] and orderbook["asks"]:
            bid = orderbook["bids"][0][0]
            ask = orderbook["asks"][0][0]
            spread = (ask - bid) / bid * 100

            if spread < 0.1:
                return 9.0
            elif spread < 0.5:
                return 7.0
            elif spread < 1.0:
                return 5.0
            else:
                return 3.0

        return 5.0

    def _analyze_volume(self, trades: List[Dict], data: LiveMarketData) -> float:
        """Analyze trading volume (0-10 score)"""
        if data.volume_24h > 10_000_000:  # $10M+
            return 9.0
        elif data.volume_24h > 1_000_000:  # $1M+
            return 7.0
        elif data.volume_24h > 100_000:  # $100K+
            return 5.0
        else:
            return 3.0

    def _calculate_risk_score(
        self, data: LiveMarketData, overall_score: float
    ) -> float:
        """Calculate risk score (1-10, higher = riskier)"""
        base_risk = 5.0

        # Volatility risk
        if abs(data.change_24h) > 20:
            base_risk += 2.0
        elif abs(data.change_24h) > 10:
            base_risk += 1.0

        # Volume risk
        if data.volume_24h < 100_000:
            base_risk += 1.5

        # Signal confidence risk
        if overall_score < 5.0:
            base_risk += 1.0

        return min(10.0, max(1.0, base_risk))


async def run_live_analysis_demo():
    """Run live analysis demo with real Binance US data"""
    print("🚀 STARTING LIVE BINANCE US ANALYSIS")
    print("=" * 80)

    # Initialize live connector
    connector = BinanceUSLiveConnector()

    if not connector.is_connected:
        print("❌ Failed to connect to Binance US")
        return

    # Initialize analyzer
    analyzer = LiveTradingAnalyzer(connector)

    # Get live market data
    print("\n📊 FETCHING LIVE MARKET DATA...")
    live_data = await connector.get_live_market_data()

    # Show live market overview
    print(f"\n💹 LIVE MARKET OVERVIEW ({len(live_data)} symbols):")
    print("-" * 60)
    for i, data in enumerate(live_data[:10]):  # Top 10
        change_emoji = "🟢" if data.change_24h > 0 else "🔴"
        print(
            f"{i+1:2d}. {data.symbol:12s} ${data.price:8.4f} {change_emoji} {data.change_24h:+6.2f}% Vol: ${data.volume_24h:,.0f}"
        )

    # Analyze opportunities
    print(f"\n🔍 ANALYZING LIVE TRADING OPPORTUNITIES...")
    signals = await analyzer.analyze_live_opportunities()

    # Display trading signals
    print(f"\n🎯 LIVE TRADING SIGNALS ({len(signals)} found):")
    print("=" * 80)

    for i, signal in enumerate(signals):
        action_emoji = (
            "🟢"
            if signal.action == "BUY"
            else "🔴" if signal.action == "SELL" else "⚪"
        )
        print(f"\n{i+1}. {action_emoji} {signal.action} {signal.symbol}")
        print(
            f"   💰 Entry: ${signal.entry_price:.4f} | Target: ${signal.target_price:.4f} | Stop: ${signal.stop_loss:.4f}"
        )
        print(
            f"   📊 Confidence: {signal.confidence:.2f} | Risk: {signal.risk_score:.1f}/10 | Size: {signal.position_size:.4f}"
        )
        print(f"   💡 Reasoning: {signal.reasoning}")

    # Performance summary
    print(f"\n📈 LIVE ANALYSIS SUMMARY:")
    print("=" * 40)
    print(f"🎯 Signals Generated: {analyzer.signals_generated}")
    print(f"🔍 Opportunities Found: {analyzer.opportunities_found}")
    print(f"💰 Account Balance: ${connector.account_info['total']['USDT']:.2f} USDT")
    print(
        f"🔗 API Status: {'✅ Connected' if connector.is_connected else '❌ Disconnected'}"
    )
    print(f"📊 Trading Pairs: {len(connector.trading_pairs)} active")

    # Show top movers
    top_gainers = sorted(live_data, key=lambda x: x.change_24h, reverse=True)[:5]
    top_losers = sorted(live_data, key=lambda x: x.change_24h)[:5]

    print(f"\n🚀 TOP GAINERS (24h):")
    for i, data in enumerate(top_gainers):
        print(f"   {i+1}. {data.symbol}: +{data.change_24h:.2f}%")

    print(f"\n📉 TOP LOSERS (24h):")
    for i, data in enumerate(top_losers):
        print(f"   {i+1}. {data.symbol}: {data.change_24h:.2f}%")

    print("\n✅ LIVE ANALYSIS COMPLETE!")
    print("🚨 Trading signals are for analysis only. Use proper risk management!")

    return connector, analyzer


if __name__ == "__main__":
    # Run live analysis
    connector, analyzer = asyncio.run(run_live_analysis_demo())
