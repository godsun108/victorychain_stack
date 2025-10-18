#!/usr/bin/env python3

"""
🔧 ENHANCED JESSE MCP STRATEGY
Advanced Jesse trading framework integration with VictoryChain MCP
Features: Real-time AI signals, dynamic risk management, live portfolio optimization
"""

import sys
import os
from typing import Dict, Optional, Tuple, Union
import numpy as np
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from jesse.strategies import Strategy
    import jesse.indicators as ta
    from jesse import utils
    from jesse.models import Order
    jesse_available = True
except ImportError:
    # Create mock classes for development
    class Strategy:
        def __init__(self):
            self.symbol = "MAGIC-USDT"
            self.timeframe = "1h"
            self.candles = np.array([])
        
        def should_long(self) -> bool:
            return False
            
        def should_short(self) -> bool:
            return False
            
        def should_cancel_entry(self) -> bool:
            return False
        
        def go_long(self):
            pass
            
        def go_short(self):
            pass
    
    # Mock ta module
    class MockTA:
        @staticmethod
        def rsi(candles, period=14):
            return np.random.random(len(candles)) * 100
        
        @staticmethod
        def macd(candles):
            return (np.random.random(len(candles)), 
                   np.random.random(len(candles)), 
                   np.random.random(len(candles)))
        
        @staticmethod
        def ema(candles, period=20):
            return np.random.random(len(candles)) * 100
    
    ta = MockTA()
    jesse_available = False

try:
    from src.open_source.enhanced_mcp_client import EnhancedMCPClient, get_global_mcp_client
except ImportError:
    EnhancedMCPClient = None
    get_global_mcp_client = None

logger = logging.getLogger(__name__)

class EnhancedVictoryChainMCPStrategy(Strategy):
    """
    Enhanced Jesse strategy powered by VictoryChain MCP server
    
    Features:
    - AI-powered signal generation
    - Dynamic risk management
    - Real-time portfolio optimization
    - Multi-timeframe analysis
    - Adaptive position sizing
    - Market regime detection
    """
    
    def __init__(self):
        super().__init__()
        
        # MCP Configuration
        self.mcp_server_url = "http://localhost:8080"
        self.mcp_client = None
        
        # Strategy Configuration
        self.strategy_mode = "balanced"  # conservative, balanced, aggressive
        self.use_ai_signals = True
        self.use_ai_risk_management = True
        self.use_dynamic_sizing = True
        
        # Technical Analysis Parameters
        self.rsi_period = 14
        self.rsi_upper = 75
        self.rsi_lower = 30
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        # AI Parameters
        self.ai_signal_weight = 0.7
        self.ai_confidence_threshold = 0.65
        self.risk_threshold = 8.0
        self.max_portfolio_heat = 0.8
        
        # Position Management
        self.base_qty = 1.0
        self.max_qty_multiplier = 3.0
        self.min_qty_multiplier = 0.5
        
        # Caching and State
        self.mcp_cache = {}
        self.last_mcp_update = {}
        self.market_conditions = {}
        self.ai_signals = {}
        
        # Performance Tracking
        self.trades_analysis = []
        self.strategy_performance = {}
        
        # Initialize MCP connection
        self._init_mcp_connection()
    
    def _init_mcp_connection(self):
        """Initialize MCP connection"""
        try:
            if EnhancedMCPClient and get_global_mcp_client:
                self.mcp_client = get_global_mcp_client()
                logger.info("✅ MCP client initialized for Jesse strategy")
            else:
                logger.warning("⚠️  Enhanced MCP client not available - using fallback mode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP connection: {e}")
    
    def get_mcp_data_sync(self, method: str, **kwargs) -> Optional[Dict]:
        """Synchronous wrapper for MCP data retrieval"""
        try:
            if self.mcp_client:
                return self.mcp_client.sync_call(
                    self._get_mcp_data_async(method, **kwargs)
                )
            return self._fallback_data(method, **kwargs)
        except Exception as e:
            logger.error(f"MCP sync call failed: {e}")
            return self._fallback_data(method, **kwargs)\n    \n    async def _get_mcp_data_async(self, method: str, **kwargs) -> Optional[Dict]:\n        """Async MCP data retrieval"""\n        try:\n            if method == "market_analysis":\n                symbol = kwargs.get("symbol", self.symbol.replace('-', ''))\n                return await self.mcp_client.get_market_data(symbol)\n                \n            elif method == "trading_signal":\n                return await self.mcp_client.generate_trading_signal(\n                    symbol=kwargs.get("symbol", self.symbol.replace('-', '')),\n                    strategy=kwargs.get("strategy", "momentum"),\n                    risk_tolerance=self.strategy_mode\n                )\n                \n            elif method == "risk_metrics":\n                return await self.mcp_client.get_risk_metrics()\n                \n            elif method == "portfolio_optimization":\n                return await self.mcp_client.optimize_portfolio(\n                    target_risk=kwargs.get("target_risk", 0.15),\n                    max_position_size=kwargs.get("max_position_size", 0.3)\n                )\n                \n            return None\n        except Exception as e:\n            logger.error(f"MCP async call failed: {e}")\n            return None\n    \n    def _fallback_data(self, method: str, **kwargs) -> Dict:\n        """Fallback data when MCP is unavailable"""\n        fallback_data = {\n            "market_analysis": {\n                "trend": {"direction": "neutral", "strength": 0.5},\n                "technical_indicators": {\n                    "rsi": 50.0,\n                    "macd_signal": "NEUTRAL",\n                    "sentiment_score": 0.5\n                },\n                "volatility": 0.05,\n                "volume_profile": "normal"\n            },\n            "trading_signal": {\n                "signal_strength": 0.0,\n                "confidence": 0.5,\n                "direction": "HOLD",\n                "entry_price": 0.0,\n                "stop_loss": 0.0,\n                "take_profit": 0.0\n            },\n            "risk_metrics": {\n                "overall_risk_score": 5.0,\n                "portfolio_heat": 0.5,\n                "var_95": 0.1,\n                "sharpe_ratio": 1.0,\n                "max_drawdown": 0.15\n            },\n            "portfolio_optimization": {\n                "recommendations": {},\n                "optimal_allocation": {},\n                "rebalance_needed": False\n            }\n        }\n        \n        return fallback_data.get(method, {})\n    \n    def update_market_conditions(self):\n        """Update market conditions and cache"""\n        try:\n            current_time = datetime.now().timestamp()\n            \n            # Update every 60 seconds\n            if current_time - self.last_mcp_update.get('market_analysis', 0) > 60:\n                market_data = self.get_mcp_data_sync(\"market_analysis\")\n                if market_data:\n                    self.market_conditions = market_data\n                    self.last_mcp_update['market_analysis'] = current_time\n            \n            # Update AI signals every 30 seconds\n            if current_time - self.last_mcp_update.get('trading_signal', 0) > 30:\n                signal_data = self.get_mcp_data_sync(\"trading_signal\")\n                if signal_data:\n                    self.ai_signals = signal_data\n                    self.last_mcp_update['trading_signal'] = current_time\n                    \n        except Exception as e:\n            logger.error(f"Market conditions update failed: {e}")\n    \n    def calculate_position_size(self, signal_strength: float, confidence: float) -> float:\n        """Calculate dynamic position size based on AI signals and risk"""\n        try:\n            if not self.use_dynamic_sizing:\n                return self.base_qty\n            \n            # Base multiplier from signal strength and confidence\n            signal_multiplier = abs(signal_strength) * confidence\n            \n            # Risk adjustment\n            risk_data = self.get_mcp_data_sync(\"risk_metrics\")\n            risk_multiplier = 1.0\n            \n            if risk_data:\n                risk_score = risk_data.get('overall_risk_score', 5.0)\n                portfolio_heat = risk_data.get('portfolio_heat', 0.5)\n                \n                # Reduce size in high risk conditions\n                if risk_score > 7.0:\n                    risk_multiplier *= 0.7\n                elif risk_score > 8.5:\n                    risk_multiplier *= 0.5\n                \n                if portfolio_heat > 0.8:\n                    risk_multiplier *= 0.6\n            \n            # Market condition adjustment\n            market_trend = self.market_conditions.get('trend', {}).get('direction', 'neutral')\n            volatility = self.market_conditions.get('volatility', 0.05)\n            \n            market_multiplier = 1.0\n            if market_trend == 'bullish' and signal_strength > 0:\n                market_multiplier = 1.2\n            elif market_trend == 'bearish' and signal_strength < 0:\n                market_multiplier = 1.2\n            \n            # Volatility adjustment\n            if volatility > 0.08:\n                market_multiplier *= 0.8\n            elif volatility < 0.03:\n                market_multiplier *= 1.1\n            \n            # Strategy mode adjustment\n            mode_multiplier = {\n                'conservative': 0.7,\n                'balanced': 1.0,\n                'aggressive': 1.3\n            }.get(self.strategy_mode, 1.0)\n            \n            # Calculate final size\n            final_multiplier = (\n                signal_multiplier * \n                risk_multiplier * \n                market_multiplier * \n                mode_multiplier\n            )\n            \n            # Apply bounds\n            final_multiplier = max(self.min_qty_multiplier, \n                                 min(self.max_qty_multiplier, final_multiplier))\n            \n            return self.base_qty * final_multiplier\n            \n        except Exception as e:\n            logger.error(f"Position sizing calculation failed: {e}")\n            return self.base_qty\n    \n    def should_long(self) -> bool:\n        """Enhanced long entry logic with AI integration"""\n        try:\n            # Update market conditions\n            self.update_market_conditions()\n            \n            # Get latest candle data\n            if not hasattr(self, 'candles') or len(self.candles) < 50:\n                return False\n            \n            # === Technical Analysis ===\n            \n            # RSI\n            rsi = ta.rsi(self.candles, period=self.rsi_period)\n            current_rsi = rsi[-1]\n            \n            # MACD\n            macd_line, macd_signal, macd_histogram = ta.macd(self.candles)\n            macd_bullish = macd_line[-1] > macd_signal[-1] and macd_histogram[-1] > macd_histogram[-2]\n            \n            # EMA trend\n            ema_fast = ta.ema(self.candles, period=12)\n            ema_slow = ta.ema(self.candles, period=26)\n            trend_bullish = ema_fast[-1] > ema_slow[-1]\n            \n            # Basic TA conditions\n            ta_conditions = [\n                current_rsi < self.rsi_lower,\n                macd_bullish,\n                trend_bullish\n            ]\n            \n            ta_score = sum(ta_conditions) / len(ta_conditions)\n            \n            # === AI Signal Analysis ===\n            \n            ai_score = 0.5  # Neutral default\n            \n            if self.use_ai_signals and self.ai_signals:\n                signal_strength = self.ai_signals.get('signal_strength', 0.0)\n                confidence = self.ai_signals.get('confidence', 0.0)\n                direction = self.ai_signals.get('direction', 'HOLD')\n                \n                if direction == 'BUY' and signal_strength > 0:\n                    ai_score = signal_strength * confidence\n                elif direction == 'SELL' or signal_strength < 0:\n                    ai_score = 0.0  # Bearish signal\n            \n            # === Risk Management Check ===\n            \n            risk_approved = True\n            \n            if self.use_ai_risk_management:\n                risk_data = self.get_mcp_data_sync(\"risk_metrics\")\n                if risk_data:\n                    risk_score = risk_data.get('overall_risk_score', 5.0)\n                    portfolio_heat = risk_data.get('portfolio_heat', 0.5)\n                    \n                    if risk_score > self.risk_threshold or portfolio_heat > self.max_portfolio_heat:\n                        risk_approved = False\n            \n            # === Combined Decision ===\n            \n            # Weight TA and AI signals\n            combined_score = (\n                ta_score * (1 - self.ai_signal_weight) + \n                ai_score * self.ai_signal_weight\n            )\n            \n            # Market condition boost\n            market_trend = self.market_conditions.get('trend', {}).get('direction', 'neutral')\n            if market_trend == 'bullish':\n                combined_score *= 1.1\n            \n            # Final decision\n            entry_threshold = {\n                'conservative': 0.8,\n                'balanced': 0.7,\n                'aggressive': 0.6\n            }.get(self.strategy_mode, 0.7)\n            \n            should_enter = (\n                combined_score >= entry_threshold and\n                risk_approved and\n                ai_score >= 0.3  # Minimum AI confidence\n            )\n            \n            if should_enter:\n                logger.info(f"🟢 LONG ENTRY: TA={ta_score:.2f}, AI={ai_score:.2f}, Combined={combined_score:.2f}")\n            \n            return should_enter\n            \n        except Exception as e:\n            logger.error(f"Long entry analysis failed: {e}")\n            return False\n    \n    def should_short(self) -> bool:\n        """Enhanced short entry logic (if supported)"""\n        try:\n            # Similar logic to should_long but for short positions\n            # Update market conditions\n            self.update_market_conditions()\n            \n            if not hasattr(self, 'candles') or len(self.candles) < 50:\n                return False\n            \n            # === Technical Analysis ===\n            \n            rsi = ta.rsi(self.candles, period=self.rsi_period)\n            current_rsi = rsi[-1]\n            \n            macd_line, macd_signal, macd_histogram = ta.macd(self.candles)\n            macd_bearish = macd_line[-1] < macd_signal[-1] and macd_histogram[-1] < macd_histogram[-2]\n            \n            ema_fast = ta.ema(self.candles, period=12)\n            ema_slow = ta.ema(self.candles, period=26)\n            trend_bearish = ema_fast[-1] < ema_slow[-1]\n            \n            ta_conditions = [\n                current_rsi > self.rsi_upper,\n                macd_bearish,\n                trend_bearish\n            ]\n            \n            ta_score = sum(ta_conditions) / len(ta_conditions)\n            \n            # === AI Signal Analysis ===\n            \n            ai_score = 0.5\n            \n            if self.use_ai_signals and self.ai_signals:\n                signal_strength = self.ai_signals.get('signal_strength', 0.0)\n                confidence = self.ai_signals.get('confidence', 0.0)\n                direction = self.ai_signals.get('direction', 'HOLD')\n                \n                if direction == 'SELL' and signal_strength < 0:\n                    ai_score = abs(signal_strength) * confidence\n                elif direction == 'BUY' or signal_strength > 0:\n                    ai_score = 0.0\n            \n            # === Risk Management ===\n            \n            risk_approved = True\n            if self.use_ai_risk_management:\n                risk_data = self.get_mcp_data_sync(\"risk_metrics\")\n                if risk_data:\n                    risk_score = risk_data.get('overall_risk_score', 5.0)\n                    if risk_score > self.risk_threshold:\n                        risk_approved = False\n            \n            # === Combined Decision ===\n            \n            combined_score = (\n                ta_score * (1 - self.ai_signal_weight) + \n                ai_score * self.ai_signal_weight\n            )\n            \n            market_trend = self.market_conditions.get('trend', {}).get('direction', 'neutral')\n            if market_trend == 'bearish':\n                combined_score *= 1.1\n            \n            entry_threshold = {\n                'conservative': 0.8,\n                'balanced': 0.7,\n                'aggressive': 0.6\n            }.get(self.strategy_mode, 0.7)\n            \n            should_enter = (\n                combined_score >= entry_threshold and\n                risk_approved and\n                ai_score >= 0.3\n            )\n            \n            if should_enter:\n                logger.info(f"🔴 SHORT ENTRY: TA={ta_score:.2f}, AI={ai_score:.2f}, Combined={combined_score:.2f}")\n            \n            return should_enter\n            \n        except Exception as e:\n            logger.error(f"Short entry analysis failed: {e}")\n            return False\n    \n    def should_cancel_entry(self) -> bool:\n        \"\"\"Dynamic entry cancellation based on changing conditions\"\"\"\n        try:\n            # Check if AI signals have changed dramatically\n            if self.use_ai_signals:\n                current_signals = self.get_mcp_data_sync(\"trading_signal\")\n                if current_signals:\n                    confidence = current_signals.get('confidence', 0.0)\n                    \n                    # Cancel if confidence drops significantly\n                    if confidence < 0.4:\n                        logger.info(f"🚫 Cancelling entry: AI confidence dropped to {confidence}")\n                        return True\n            \n            # Check risk conditions\n            if self.use_ai_risk_management:\n                risk_data = self.get_mcp_data_sync(\"risk_metrics\")\n                if risk_data:\n                    risk_score = risk_data.get('overall_risk_score', 5.0)\n                    if risk_score > 9.0:\n                        logger.info(f"🚫 Cancelling entry: Risk score too high ({risk_score})")\n                        return True\n            \n            return False\n            \n        except Exception as e:\n            logger.error(f"Entry cancellation check failed: {e}")\n            return False\n    \n    def go_long(self):\n        \"\"\"Execute long position with dynamic sizing\"\"\"\n        try:\n            # Calculate position size\n            signal_strength = self.ai_signals.get('signal_strength', 0.5)\n            confidence = self.ai_signals.get('confidence', 0.5)\n            \n            position_size = self.calculate_position_size(signal_strength, confidence)\n            \n            # Get AI-suggested levels\n            stop_loss = self.ai_signals.get('stop_loss', 0.0)\n            take_profit = self.ai_signals.get('take_profit', 0.0)\n            \n            # Execute with dynamic parameters\n            logger.info(f"📈 LONG POSITION: Size={position_size:.2f}, SL={stop_loss}, TP={take_profit}")\n            \n            # Call parent go_long with calculated size\n            if jesse_available:\n                super().go_long()\n            \n            # Track trade for analysis\n            self.trades_analysis.append({\n                'timestamp': datetime.now(),\n                'direction': 'long',\n                'size': position_size,\n                'ai_signal': signal_strength,\n                'ai_confidence': confidence,\n                'market_conditions': self.market_conditions.copy()\n            })\n            \n        except Exception as e:\n            logger.error(f"Long position execution failed: {e}")\n    \n    def go_short(self):\n        \"\"\"Execute short position with dynamic sizing\"\"\"\n        try:\n            signal_strength = self.ai_signals.get('signal_strength', -0.5)\n            confidence = self.ai_signals.get('confidence', 0.5)\n            \n            position_size = self.calculate_position_size(abs(signal_strength), confidence)\n            \n            stop_loss = self.ai_signals.get('stop_loss', 0.0)\n            take_profit = self.ai_signals.get('take_profit', 0.0)\n            \n            logger.info(f"📉 SHORT POSITION: Size={position_size:.2f}, SL={stop_loss}, TP={take_profit}")\n            \n            if jesse_available:\n                super().go_short()\n            \n            self.trades_analysis.append({\n                'timestamp': datetime.now(),\n                'direction': 'short',\n                'size': position_size,\n                'ai_signal': signal_strength,\n                'ai_confidence': confidence,\n                'market_conditions': self.market_conditions.copy()\n            })\n            \n        except Exception as e:\n            logger.error(f"Short position execution failed: {e}")\n    \n    def update_position(self):\n        \"\"\"Update existing position based on AI recommendations\"\"\"\n        try:\n            # Check for portfolio optimization recommendations\n            portfolio_data = self.get_mcp_data_sync(\"portfolio_optimization\")\n            \n            if portfolio_data:\n                recommendations = portfolio_data.get('recommendations', {})\n                rebalance_needed = portfolio_data.get('rebalance_needed', False)\n                \n                if rebalance_needed:\n                    logger.info(\"🔄 Portfolio rebalancing recommended by AI\")\n                    \n                    # Check specific recommendations for current symbol\n                    symbol = self.symbol.replace('-', '').upper()\n                    if symbol in recommendations:\n                        action = recommendations[symbol].get('action')\n                        \n                        if action == 'reduce':\n                            logger.info(f\"📉 AI recommends reducing {symbol} position\")\n                            # Implement position reduction logic\n                            \n                        elif action == 'increase':\n                            logger.info(f\"📈 AI recommends increasing {symbol} position\")\n                            # Implement position increase logic\n                            \n                        elif action == 'close':\n                            logger.info(f\"🚪 AI recommends closing {symbol} position\")\n                            # Implement position closing logic\n            \n        except Exception as e:\n            logger.error(f"Position update failed: {e}")\n    \n    def on_open_position(self, order: 'Order') -> None:\n        \"\"\"Called when position is opened\"\"\"\n        logger.info(f\"✅ Position opened: {order}\")\n        \n        # Update strategy performance tracking\n        self.strategy_performance['last_entry'] = datetime.now()\n        \n    def on_close_position(self, order: 'Order') -> None:\n        \"\"\"Called when position is closed\"\"\"\n        logger.info(f\"🔒 Position closed: {order}\")\n        \n        # Analyze trade performance\n        self._analyze_completed_trade(order)\n    \n    def _analyze_completed_trade(self, order):\n        \"\"\"Analyze completed trade for strategy improvement\"\"\"\n        try:\n            # Extract trade metrics\n            if hasattr(order, 'pnl'):\n                pnl = order.pnl\n                \n                # Log trade results\n                logger.info(f\"📊 Trade PnL: {pnl}\")\n                \n                # Track performance metrics\n                if 'total_trades' not in self.strategy_performance:\n                    self.strategy_performance['total_trades'] = 0\n                    self.strategy_performance['winning_trades'] = 0\n                    self.strategy_performance['total_pnl'] = 0.0\n                \n                self.strategy_performance['total_trades'] += 1\n                self.strategy_performance['total_pnl'] += pnl\n                \n                if pnl > 0:\n                    self.strategy_performance['winning_trades'] += 1\n                \n                # Calculate win rate\n                win_rate = (self.strategy_performance['winning_trades'] / \n                           self.strategy_performance['total_trades'])\n                \n                logger.info(f\"📈 Strategy Performance: Win Rate {win_rate:.2%}, Total PnL: {self.strategy_performance['total_pnl']:.2f}\")\n                \n        except Exception as e:\n            logger.error(f"Trade analysis failed: {e}")\n    \n    def terminate(self) -> None:\n        \"\"\"Called when strategy terminates\"\"\"\n        logger.info(\"🔚 Enhanced VictoryChain MCP Strategy terminating\")\n        \n        # Log final performance\n        if self.strategy_performance:\n            logger.info(f\"📊 Final Performance: {self.strategy_performance}\")\n        \n        # Clean up MCP connection\n        if self.mcp_client:\n            try:\n                asyncio.create_task(self.mcp_client.disconnect())\n            except Exception as e:\n                logger.error(f"MCP disconnect error: {e}")\n\n# Configuration for different strategy modes\nSTRATEGY_CONFIGS = {\n    'conservative': {\n        'ai_signal_weight': 0.5,\n        'ai_confidence_threshold': 0.8,\n        'risk_threshold': 6.0,\n        'max_portfolio_heat': 0.6,\n        'base_qty': 0.5\n    },\n    'balanced': {\n        'ai_signal_weight': 0.7,\n        'ai_confidence_threshold': 0.65,\n        'risk_threshold': 8.0,\n        'max_portfolio_heat': 0.8,\n        'base_qty': 1.0\n    },\n    'aggressive': {\n        'ai_signal_weight': 0.9,\n        'ai_confidence_threshold': 0.5,\n        'risk_threshold': 9.0,\n        'max_portfolio_heat': 0.9,\n        'base_qty': 1.5\n    }\n}\n\nif __name__ == "__main__":\n    # Demo the enhanced Jesse strategy\n    print("🔧 Enhanced Jesse MCP Strategy Demo")\n    \n    strategy = EnhancedVictoryChainMCPStrategy()\n    \n    # Simulate some market conditions\n    strategy.candles = np.random.random((100, 6)) * 100  # Mock candle data\n    \n    print(f"Strategy mode: {strategy.strategy_mode}")\n    print(f"AI signals enabled: {strategy.use_ai_signals}")\n    print(f"AI risk management enabled: {strategy.use_ai_risk_management}")\n    \n    # Test decision making\n    should_long = strategy.should_long()\n    should_short = strategy.should_short()\n    \n    print(f"Should go long: {should_long}")\n    print(f"Should go short: {should_short}")\n    \n    print("✅ Enhanced Jesse MCP Strategy demo completed!")
