import asyncio
from collections import deque

price_cache = {}
candle_cache = {}
price_cache_lock = asyncio.Lock()


async def update_price(symbol: str, price: float):
    async with price_cache_lock:
        price_cache[symbol] = price


async def get_price(symbol: str) -> float:
    async with price_cache_lock:
        return price_cache.get(symbol)


async def update_candle(symbol: str, candle: dict, maxlen=100):
    async with price_cache_lock:
        if symbol not in candle_cache:
            candle_cache[symbol] = deque(maxlen=maxlen)
        candle_cache[symbol].append(candle)


async def get_candles(symbol: str) -> list:
    async with price_cache_lock:
        return list(candle_cache.get(symbol, []))
