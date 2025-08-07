import datetime as dt, os

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from dotenv import load_dotenv
load_dotenv() 

client = StockHistoricalDataClient(os.getenv("alpaca_key"), os.getenv("alpaca_secret"))

def get_price_bars(symbols, start, end, tf=TimeFrame.Day):

    req = StockBarsRequest(symbol_or_symbols=symbols,
    timeframe=tf, # type: ignore
    start=start,
    end=end)

    bars = client.get_stock_bars(req).df # type: ignore
    # Multi‑index → column pivot
    return bars.close.unstack(level=0)

if __name__ == "__main__":
    today = dt.date.today()
    prices = get_price_bars(["AAPL", "MSFT"], today - dt.timedelta(days=30), today)

    print(prices.tail())