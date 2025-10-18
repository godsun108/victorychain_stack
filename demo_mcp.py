#!/usr/bin/env python3

"""
Demo script showing MCP capabilities for VictoryChain stack
"""

import json
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.mcp.mcp_server import VictoryChainMCPServer


async def demo_mcp_capabilities():
    server = VictoryChainMCPServer()

    print("🔗 MCP CAPABILITIES FOR VICTORYCHAIN STACK")
    print("=" * 60)

    # Show available resources
    resources = await server.handle_list_resources()
    print("📊 AVAILABLE DATA RESOURCES:")
    for resource in resources["resources"]:
        print(f'  • {resource["name"]}: {resource["description"]}')

    print("\n🛠️  AVAILABLE AI TOOLS:")
    tools = await server.handle_list_tools()
    for tool in tools["tools"]:
        print(f'  • {tool["name"]}: {tool["description"]}')

    print("\n💡 AVAILABLE AI PROMPTS:")
    prompts = await server.handle_list_prompts()
    for prompt in prompts["prompts"]:
        print(f'  • {prompt["name"]}: {prompt["description"]}')

    print("\n🚀 LIVE DATA EXAMPLE - Portfolio Resource:")
    try:
        portfolio_data = await server.handle_read_resource("victorychain://portfolio")
        portfolio_json = json.loads(portfolio_data["contents"][0]["text"])
        print(f'  Total Value: ${portfolio_json["total_value_usd"]}')
        print(f'  MAGIC Position: {portfolio_json["positions"][0]["amount"]} tokens')
        print(f'  Portfolio Weight: {portfolio_json["positions"][0]["percentage"]}%')
        print(f'  Risk Level: {portfolio_json["risk_metrics"]["concentration_risk"]}')
    except Exception as e:
        print(f"  Error: {e}")

    print("\n🎯 AI TOOL EXAMPLE - Token Analysis:")
    try:
        analysis = await server.handle_call_tool("analyze_token", {"symbol": "MAGIC"})
        analysis_data = json.loads(analysis["content"][0]["text"])
        print(f'  Current Price: ${analysis_data["price_action"]["current_price"]}')
        print(f'  24h Change: {analysis_data["price_action"]["change_24h"]}%')
        print(f'  RSI: {analysis_data["technical_indicators"]["rsi"]}')
        print(f'  MACD Signal: {analysis_data["technical_indicators"]["macd_signal"]}')
        print(f'  Social Sentiment: {analysis_data["sentiment"]["social_sentiment"]}')
    except Exception as e:
        print(f"  Error: {e}")

    print("\n📈 RISK METRICS EXAMPLE:")
    try:
        risk_data = await server.handle_call_tool(
            "calculate_risk_metrics", {"scope": "portfolio"}
        )
        risk_json = json.loads(risk_data["content"][0]["text"])
        print(f'  Portfolio VaR (95%): {risk_json["metrics"]["value_at_risk_95"]}')
        print(f'  Concentration Risk: {risk_json["metrics"]["concentration_risk"]}')
        print(f'  Risk Score: {risk_json["risk_score"]}/10')
        print(f'  Risk Level: {risk_json["risk_level"]}')
    except Exception as e:
        print(f"  Error: {e}")

    print("\n🤖 AI PROMPT EXAMPLE - Market Analysis:")
    try:
        prompt = await server.handle_get_prompt(
            "analyze_market_conditions", {"focus": "MAGIC token"}
        )
        prompt_text = prompt["messages"][0]["content"]["text"]
        print("  Generated AI Prompt (first 300 chars):")
        print(f'  "{prompt_text[:300]}..."')
    except Exception as e:
        print(f"  Error: {e}")

    print("\n🎉 MCP INTEGRATION BENEFITS:")
    print("  ✅ Standardized AI model access to trading data")
    print("  ✅ Real-time portfolio and market intelligence")
    print("  ✅ Structured tool calling for trading operations")
    print("  ✅ Dynamic prompt generation for analysis")
    print("  ✅ Cross-platform AI model compatibility")
    print("  ✅ Extensible architecture for new capabilities")


if __name__ == "__main__":
    asyncio.run(demo_mcp_capabilities())
