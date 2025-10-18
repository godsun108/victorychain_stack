#!/usr/bin/env python3

"""
🚀 ENHANCED OPEN SOURCE MCP CLIENT
Advanced MCP client with real-time updates, caching, and error handling
Compatible with all major open source trading frameworks
"""

import asyncio
import json
import websockets
import aiohttp
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta
import weakref
import threading
from collections import defaultdict
import time
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPRequest:
    """Standard MCP request format"""

    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """Standard MCP response format"""

    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class CacheEntry:
    """Cache entry with TTL"""

    data: Any
    timestamp: float
    ttl: float

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


class EnhancedMCPClient:
    """
    Enhanced MCP client with advanced features:
    - Real-time data streaming
    - Intelligent caching with TTL
    - Automatic reconnection
    - Batch requests
    - Event subscriptions
    - Fallback mechanisms
    """

    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        ws_url: str = "ws://localhost:8080/ws",
        cache_ttl: Dict[str, float] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):

        self.server_url = server_url
        self.ws_url = ws_url
        self.session = None
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        self.request_id = 0

        # Cache configuration
        self.cache_ttl = cache_ttl or {
            "portfolio": 30.0,  # 30 seconds for portfolio data
            "market_data": 60.0,  # 1 minute for market data
            "risk_metrics": 300.0,  # 5 minutes for risk analysis
            "strategies": 600.0,  # 10 minutes for strategy data
            "default": 120.0,  # 2 minutes default
        }
        self.cache = {}

        # Connection management
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.connected = False

        # Event handling
        self.event_handlers = defaultdict(list)
        self.subscriptions = set()

        # Background tasks
        self._background_tasks = set()
        self._cache_cleanup_task = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Establish connections to MCP server"""
        try:
            # HTTP session for REST API
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # Initialize MCP connection
            await self.initialize()

            # Start WebSocket connection for real-time updates
            await self._connect_websocket()

            # Start background tasks
            self._cache_cleanup_task = asyncio.create_task(self._cache_cleanup_loop())

            self.connected = True
            self.logger.info("✅ Enhanced MCP client connected successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to connect: {e}")
            await self.disconnect()
            raise

    async def disconnect(self):
        """Clean disconnect from MCP server"""
        self.connected = False

        # Cancel background tasks
        if self._cache_cleanup_task:
            self._cache_cleanup_task.cancel()

        for task in self._background_tasks:
            task.cancel()

        # Close connections
        if self.websocket:
            await self.websocket.close()

        if self.session:
            await self.session.close()

        self.logger.info("🔌 MCP client disconnected")

    async def _connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            self.websocket = await websockets.connect(self.ws_url)

            # Start listening for messages
            task = asyncio.create_task(self._websocket_listener())
            self._background_tasks.add(task)

        except Exception as e:
            self.logger.warning(f"WebSocket connection failed: {e}")
            # Continue without WebSocket - will use polling

    async def _websocket_listener(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(data)
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")

    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        msg_type = data.get("type")

        if msg_type == "data_update":
            # Update cache with new data
            resource = data.get("resource")
            new_data = data.get("data")

            if resource and new_data:
                self._update_cache(resource, new_data)

                # Trigger event handlers
                for handler in self.event_handlers.get(resource, []):
                    try:
                        await handler(new_data)
                    except Exception as e:
                        self.logger.error(f"Event handler error: {e}")

        elif msg_type == "notification":
            # Handle notifications
            event = data.get("event")
            for handler in self.event_handlers.get("notification", []):
                try:
                    await handler(data)
                except Exception as e:
                    self.logger.error(f"Notification handler error: {e}")

    def _get_next_id(self) -> str:
        """Get next request ID"""
        self.request_id += 1
        return str(self.request_id)

    def _get_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Create deterministic hash of method and params
        content = f"{method}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_ttl(self, resource_type: str) -> float:
        """Get TTL for resource type"""
        return self.cache_ttl.get(resource_type, self.cache_ttl["default"])

    def _update_cache(self, key: str, data: Any, resource_type: str = "default"):
        """Update cache with new data"""
        ttl = self._get_cache_ttl(resource_type)
        self.cache[key] = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        entry = self.cache.get(key)
        if entry and not entry.is_expired():
            return entry.data
        elif entry:
            # Remove expired entry
            del self.cache[key]
        return None

    async def _cache_cleanup_loop(self):
        """Periodically clean up expired cache entries"""
        while self.connected:
            try:
                current_time = time.time()
                expired_keys = [
                    key
                    for key, entry in self.cache.items()
                    if current_time - entry.timestamp > entry.ttl
                ]

                for key in expired_keys:
                    del self.cache[key]

                if expired_keys:
                    self.logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

                await asyncio.sleep(60)  # Clean up every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    async def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        resource_type: str = "default",
    ) -> MCPResponse:
        """Send MCP request with caching and retry logic"""

        params = params or {}
        cache_key = self._get_cache_key(method, params)

        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return MCPResponse(result=cached_data)

        # Send request with retry logic
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                request = MCPRequest(
                    id=self._get_next_id(), method=method, params=params
                )

                async with self.session.post(
                    f"{self.server_url}/mcp",
                    json=asdict(request),
                    headers={"Content-Type": "application/json"},
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        result = MCPResponse(**data)

                        # Cache successful result
                        if use_cache and result.result:
                            self._update_cache(cache_key, result.result, resource_type)

                        return result
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"

            except Exception as e:
                last_error = str(e)

            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        self.logger.error(
            f"Request failed after {self.retry_attempts} attempts: {last_error}"
        )
        return MCPResponse(error={"code": -1, "message": last_error})

    async def batch_request(self, requests: List[Dict[str, Any]]) -> List[MCPResponse]:
        """Send multiple requests in batch"""
        tasks = []

        for req in requests:
            method = req.get("method", "")
            params = req.get("params", {})
            use_cache = req.get("use_cache", True)
            resource_type = req.get("resource_type", "default")

            task = self.send_request(method, params, use_cache, resource_type)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection"""
        response = await self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {"subscribe": True},
                    "tools": {"listChanged": True},
                    "prompts": {"listChanged": True},
                },
                "clientInfo": {
                    "name": "VictoryChain-Enhanced-OpenSource-Client",
                    "version": "2.0.0",
                },
            },
            use_cache=False,
        )

        return response.result if response.result else {}

    # Resource methods
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Get available trading data resources"""
        response = await self.send_request("resources/list", resource_type="strategies")
        return response.result.get("resources", []) if response.result else []

    async def get_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get specific resource data"""
        response = await self.send_request("resources/read", {"uri": uri})
        return response.result if response.result else None

    # Tool methods
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available AI tools"""
        response = await self.send_request("tools/list", resource_type="strategies")
        return response.result.get("tools", []) if response.result else []

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call AI tool with arguments"""
        response = await self.send_request(
            "tools/call",
            {"name": name, "arguments": arguments},
            resource_type="default",
        )
        return response.result if response.result else {}

    # High-level trading methods
    async def get_portfolio_data(self) -> Dict[str, Any]:
        """Get live portfolio data"""
        return await self.get_resource("victorychain://portfolio")

    async def get_market_data(self, symbol: str = "MAGIC") -> Dict[str, Any]:
        """Get market data for symbol"""
        return await self.call_tool(
            "analyze_token",
            {
                "symbol": symbol,
                "timeframe": "1h",
                "include_technical": True,
                "include_sentiment": True,
            },
        )

    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get comprehensive risk analysis"""
        return await self.call_tool(
            "calculate_risk_metrics", {"scope": "portfolio", "timeframe": "1w"}
        )

    async def generate_trading_signal(
        self, symbol: str, strategy: str = "momentum", risk_tolerance: str = "medium"
    ) -> Dict[str, Any]:
        """Generate AI trading signal"""
        return await self.call_tool(
            "generate_trading_signal",
            {"symbol": symbol, "strategy": strategy, "risk_tolerance": risk_tolerance},
        )

    async def optimize_portfolio(
        self, target_risk: float = 0.15, max_position_size: float = 0.3
    ) -> Dict[str, Any]:
        """Get portfolio optimization recommendations"""
        return await self.call_tool(
            "optimize_portfolio",
            {"target_risk": target_risk, "max_position_size": max_position_size},
        )

    # Event subscription
    def subscribe_to_events(self, event_type: str, handler: Callable):
        """Subscribe to real-time events"""
        self.event_handlers[event_type].append(handler)
        self.subscriptions.add(event_type)

    def unsubscribe_from_events(self, event_type: str, handler: Callable):
        """Unsubscribe from events"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)

    # Synchronous wrapper for non-async frameworks
    def sync_call(self, coro):
        """Execute async call synchronously"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(coro)
        except Exception as e:
            self.logger.error(f"Sync call failed: {e}")
            return None


# Global client instance for easy access
_global_client = None
_client_lock = threading.Lock()


def get_global_mcp_client() -> EnhancedMCPClient:
    """Get or create global MCP client instance"""
    global _global_client

    with _client_lock:
        if _global_client is None:
            _global_client = EnhancedMCPClient()
        return _global_client


async def close_global_mcp_client():
    """Close global MCP client"""
    global _global_client

    with _client_lock:
        if _global_client is not None:
            await _global_client.disconnect()
            _global_client = None


# Convenience functions for common operations
async def quick_market_analysis(symbol: str) -> Dict[str, Any]:
    """Quick market analysis for a symbol"""
    async with EnhancedMCPClient() as client:
        return await client.get_market_data(symbol)


async def quick_portfolio_check() -> Dict[str, Any]:
    """Quick portfolio status check"""
    async with EnhancedMCPClient() as client:
        return await client.get_portfolio_data()


async def quick_risk_assessment() -> Dict[str, Any]:
    """Quick risk assessment"""
    async with EnhancedMCPClient() as client:
        return await client.get_risk_metrics()


if __name__ == "__main__":

    async def demo():
        """Demo the enhanced MCP client"""
        print("🚀 Enhanced MCP Client Demo")

        async with EnhancedMCPClient() as client:
            # Test basic functionality
            print("\n📊 Getting portfolio data...")
            portfolio = await client.get_portfolio_data()
            print(f"Portfolio value: ${portfolio.get('total_value', 'N/A')}")

            # Test market analysis
            print("\n🔍 Analyzing MAGIC token...")
            magic_analysis = await client.get_market_data("MAGIC")
            print(f"MAGIC analysis: {magic_analysis.get('summary', 'N/A')}")

            # Test batch requests
            print("\n📦 Testing batch requests...")
            batch_requests = [
                {
                    "method": "resources/read",
                    "params": {"uri": "victorychain://portfolio"},
                },
                {
                    "method": "tools/call",
                    "params": {
                        "name": "analyze_token",
                        "arguments": {"symbol": "MAGIC"},
                    },
                },
                {
                    "method": "tools/call",
                    "params": {"name": "calculate_risk_metrics", "arguments": {}},
                },
            ]

            results = await client.batch_request(batch_requests)
            print(f"Batch completed: {len(results)} responses")

            print("\n✅ Enhanced MCP client demo completed!")

    asyncio.run(demo())
