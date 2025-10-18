import asyncio
from binance import AsyncClient, BinanceSocketManager
from victory_bot.utils.price_cache import update_price


async def stream_all_usdt_prices(symbols):
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client)
    # Binance expects lowercase and no slash, e.g. btcusdt
    streams = [bm.symbol_ticker_socket(s.replace("/", "").lower()) for s in symbols]
    tasks = []
    for stream, symbol in zip(streams, symbols):

        async def listen(stream=stream, symbol=symbol):
            async with stream as s:
                while True:
                    res = await s.recv()
                    if "c" in res:  # 'c' is the last price in Binance stream
                        await update_price(symbol, float(res["c"]))

        tasks.append(asyncio.create_task(listen()))
    await asyncio.gather(*tasks)
