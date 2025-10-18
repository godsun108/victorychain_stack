import asyncio
from binance import AsyncClient, BinanceSocketManager
from victory_bot.utils.price_cache import update_price, update_candle


async def stream_all_usdt_prices_and_candles(symbols, interval="1m"):
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    # Price streams
    price_streams = [
        bm.symbol_ticker_socket(s.replace("/", "").lower()) for s in symbols
    ]
    # Candle streams
    candle_streams = [
        bm.kline_socket(s.replace("/", "").lower(), interval=interval) for s in symbols
    ]
    tasks = []
    # Price listeners
    for stream, symbol in zip(price_streams, symbols):

        async def listen_price(stream=stream, symbol=symbol):
            async with stream as s:
                while True:
                    res = await s.recv()
                    if "c" in res:
                        await update_price(symbol, float(res["c"]))

        tasks.append(asyncio.create_task(listen_price()))
    # Candle listeners
    for stream, symbol in zip(candle_streams, symbols):

        async def listen_candle(stream=stream, symbol=symbol):
            async with stream as s:
                while True:
                    res = await s.recv()
                    if "k" in res:
                        await update_candle(symbol, res["k"])

        tasks.append(asyncio.create_task(listen_candle()))
    await asyncio.gather(*tasks)
