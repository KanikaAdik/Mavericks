import random

class MarketMaker:
    def __init__(self):
        self.stocks = ["AAPL", "MSFT", "GOOG", "AMZN", "FB", "TSLA", "NVDA", "NFLX", "PYPL", "INTC", 
                       "CSCO", "ADBE", "AVGO", "TXN", "QCOM", "CRM", "ACN", "IBM", "V", "MA"]
        self.bids = {}
        self.asks = {}

    def update_quote(self, stock, bid_price, ask_price):
        self.bids[stock] = bid_price
        self.asks[stock] = ask_price

    def make_quotes(self):
        for stock in self.stocks:
            mid_price = (self.bids.get(stock, 0) + self.asks.get(stock, 0)) / 2
            bid_price = mid_price - random.uniform(0, 0.5)
            ask_price = mid_price + random.uniform(0, 0.5)
            self.update_quote(stock, bid_price, ask_price)
# create a MarketMaker object
mm = MarketMaker()

# make the initial quotes
mm.make_quotes()

# print the initial quotes
for stock in mm.stocks:
    print(f"{stock}: bid={mm.bids[stock]}, ask={mm.asks[stock]}")

# update the quotes every second
import time
while True:
    time.sleep(1)
    mm.make_quotes()
    for stock in mm.stocks:
        print(f"{stock}: bid={mm.bids[stock]}, ask={mm.asks[stock]}")

