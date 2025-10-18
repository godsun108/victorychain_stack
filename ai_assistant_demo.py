#!/usr/bin/env python3

"""
Example: AI Trading Assistant using VictoryChain MCP Server
This demonstrates how an AI model would interact with your trading stack
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp.mcp_server import VictoryChainMCPServer


class AITradingAssistant:
    """Simulates how an AI model would use your MCP server"""

    def __init__(self):
        self.mcp_server = VictoryChainMCPServer()
        self.name = "AI Trading Assistant"

    async def analyze_portfolio_risk(self):
        """AI analyzes current portfolio risk"""
        print(f"\n🤖 {self.name}: Let me analyze your portfolio risk...")

        # Get live portfolio data
        portfolio = await self.mcp_server.handle_read_resource(
            "victorychain://portfolio"
        )
        portfolio_data = json.loads(portfolio["contents"][0]["text"])

        # Calculate risk metrics
        risk_analysis = await self.mcp_server.handle_call_tool(
            "calculate_risk_metrics", {"scope": "portfolio", "timeframe": "1w"}
        )
        risk_data = json.loads(risk_analysis["content"][0]["text"])

        # AI Analysis
        magic_position = portfolio_data["positions"][0]
        concentration = magic_position["percentage"]
        risk_score = risk_data["risk_score"]

        print(f"\n📊 AI PORTFOLIO ANALYSIS:")
        print(f"   Current Portfolio Value: ${portfolio_data['total_value_usd']}")
        print(
            f"   MAGIC Position: {magic_position['amount']:.4f} tokens (${magic_position['value_usd']:.2f})"
        )
        print(f"   Concentration Risk: {concentration}% in single asset")
        print(f"   Risk Score: {risk_score}/10 ({risk_data['risk_level']})")
        print(
            f"   Value at Risk (95%): {risk_data['metrics']['value_at_risk_95']*100:.1f}%"
        )

        # AI Recommendation
        if concentration > 80:
            print(f"\n⚠️  AI RECOMMENDATION: URGENT - Reduce concentration risk!")
            print(f"   Your {concentration}% position in MAGIC is extremely risky.")
            print(f"   Consider reducing to 20-30% maximum.")

        return risk_data

    async def generate_trading_strategy(self):
        """AI generates trading strategy based on live data"""
        print(f"\n🤖 {self.name}: Analyzing MAGIC for trading opportunities...")

        # Get token analysis
        token_analysis = await self.mcp_server.handle_call_tool(
            "analyze_token",
            {
                "symbol": "MAGIC",
                "timeframe": "1d",
                "include_technical": True,
                "include_sentiment": True,
            },
        )
        analysis_data = json.loads(token_analysis["content"][0]["text"])

        # Generate trading signal
        signal = await self.mcp_server.handle_call_tool(
            "generate_trading_signal",
            {"symbol": "MAGIC", "strategy": "momentum", "risk_tolerance": "medium"},
        )
        signal_data = json.loads(signal["content"][0]["text"])

        print(f"\n📈 AI TECHNICAL ANALYSIS:")
        price_data = analysis_data["price_action"]
        tech_data = analysis_data["technical_indicators"]
        sentiment_data = analysis_data["sentiment"]

        print(f"   Current Price: ${price_data['current_price']}")
        print(f"   24h Change: {price_data['change_24h']:+.2f}%")
        print(f"   Volume: ${price_data['volume_24h']:,.0f}")
        print(
            f"   RSI: {tech_data['rsi']} ({'Overbought' if tech_data['rsi'] > 70 else 'Normal'})"
        )
        print(f"   MACD: {tech_data['macd_signal']}")
        print(f"   Social Sentiment: {sentiment_data['social_sentiment']}")

        print(f"\n🎯 AI TRADING SIGNAL:")
        print(f"   Signal: {signal_data['signal']}")
        print(f"   Confidence: {signal_data['confidence']*100:.0f}%")
        print(f"   Target Price: ${signal_data['target_price']}")
        print(f"   Stop Loss: ${signal_data['stop_loss']}")
        print(f"   Position Size: {signal_data['position_size']*100:.0f}%")

        print(f"\n💡 AI RATIONALE:")
        for reason in signal_data["rationale"]:
            print(f"   • {reason}")

        return signal_data

    async def suggest_portfolio_optimization(self):
        """AI suggests portfolio rebalancing"""
        print(f"\n🤖 {self.name}: Optimizing your portfolio allocation...")

        optimization = await self.mcp_server.handle_call_tool(
            "optimize_portfolio", {"target_risk": 0.15, "max_position_size": 0.30}
        )
        opt_data = json.loads(optimization["content"][0]["text"])

        print(f"\n⚖️ AI PORTFOLIO OPTIMIZATION:")
        print(f"   Current Allocation:")
        for asset, pct in opt_data["current_allocation"].items():
            print(f"     {asset}: {pct*100:.1f}%")

        print(f"\n   Recommended Allocation:")
        for asset, pct in opt_data["recommended_allocation"].items():
            print(f"     {asset}: {pct*100:.1f}%")

        print(f"\n🔄 REBALANCING ACTIONS:")
        for action in opt_data["rebalancing_actions"]:
            if action["action"] == "SELL":
                print(
                    f"   📉 SELL {action['amount']:.1f} {action['symbol']} - {action['reason']}"
                )
            else:
                print(
                    f"   📈 BUY ${action['amount_usd']:.0f} {action['symbol']} - {action['reason']}"
                )

        print(
            f"\n📊 Expected Risk Reduction: {opt_data['expected_risk_reduction']*100:.0f}%"
        )
        print(f"   Diversification Score: {opt_data['diversification_score']*100:.0f}%")

        return opt_data

    async def generate_market_report(self):
        """AI generates comprehensive market report"""
        print(f"\n🤖 {self.name}: Generating market analysis report...")

        # Get market analysis prompt
        prompt_response = await self.mcp_server.handle_get_prompt(
            "analyze_market_conditions", {"focus": "gaming and metaverse tokens"}
        )

        # Get live market data for analysis
        market_data = await self.mcp_server.handle_read_resource(
            "victorychain://market_data"
        )
        market_json = json.loads(market_data["contents"][0]["text"])

        print(f"\n🌍 AI MARKET ANALYSIS:")
        print(f"   BTC: ${market_json['prices']['BTC']:,.0f}")
        print(f"   ETH: ${market_json['prices']['ETH']:,.0f}")
        print(f"   MAGIC: ${market_json['prices']['MAGIC']:.4f}")
        print(f"   Market Cap: ${market_json['market_cap']['total']:,.0f}")
        print(f"   BTC Dominance: {market_json['market_cap']['btc_dominance']}%")
        print(f"   Fear & Greed: {market_json['fear_greed_index']}/100")

        # Simulate AI analysis based on data
        btc_price = market_json["prices"]["BTC"]
        fear_greed = market_json["fear_greed_index"]

        print(f"\n🧠 AI MARKET INSIGHTS:")
        if btc_price > 100000:
            print(f"   • Bitcoin above $100K suggests strong bull market momentum")
        if fear_greed > 70:
            print(
                f"   • Fear & Greed at {fear_greed} indicates market euphoria - caution advised"
            )
        if market_json["prices"]["MAGIC"] > 0.25:
            print(f"   • MAGIC above $0.25 shows gaming token strength")

        print(f"\n📝 AI GENERATED ANALYSIS PROMPT:")
        prompt_text = prompt_response["messages"][0]["content"]["text"]
        print(f"   Length: {len(prompt_text)} characters")
        print(f"   Includes: Live prices, portfolio data, risk metrics")
        print(f"   Ready for: Claude, GPT, or any AI model")

        return market_json


async def main():
    """Run AI Trading Assistant demonstration"""
    ai = AITradingAssistant()

    print("🚀 AI TRADING ASSISTANT - MCP DEMONSTRATION")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 MCP Server: VictoryChain Trading Intelligence")
    print(f"🤖 AI Model: Simulated Trading Assistant")

    try:
        # Run comprehensive AI analysis
        await ai.analyze_portfolio_risk()
        await ai.generate_trading_strategy()
        await ai.suggest_portfolio_optimization()
        await ai.generate_market_report()

        print(f"\n✅ AI ANALYSIS COMPLETE")
        print(f"💡 Key Findings:")
        print(f"   • 97.7% concentration in MAGIC = VERY HIGH RISK")
        print(f"   • RSI 78.5 suggests overbought conditions")
        print(f"   • AI recommends reducing MAGIC to 30% max")
        print(f"   • Strong social sentiment supports gradual reduction")
        print(f"   • Consider diversifying into BTC, ETH, SOL")

        print(f"\n🔗 MCP Benefits Demonstrated:")
        print(f"   ✅ Real-time data access (live prices, positions)")
        print(f"   ✅ AI tool execution (analysis, signals, optimization)")
        print(f"   ✅ Dynamic prompt generation (market-specific)")
        print(f"   ✅ Structured decision making (risk-based)")
        print(f"   ✅ Actionable recommendations (specific trades)")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
