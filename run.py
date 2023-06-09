import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
import pandas as pd
# NOTE: for documentation on the different classes and methods used to interact with the SHIFT system, 
# see: https://github.com/hanlonlab/shift-python/wiki

def cancel_orders(trader, ticker):
    # cancel all the remaining orders
    for order in trader.get_waiting_list():
        if (order.symbol == ticker):
            trader.submit_cancellation(order)
            sleep(1)  # the order cancellation needs a little time to go through


def close_positions(trader, ticker):
    # NOTE: The following orders may not go through if:
    # 1. You do not have enough buying power to close your short postions. Your strategy should be formulated to ensure this does not happen.
    # 2. There is not enough liquidity in the market to close your entire position at once. You can avoid this either by formulating your
    #    strategy to maintain a small position, or by modifying this function to close ur positions in batches of smaller orders.

    # close all positions for given ticker
    print(f"running close positions function for {ticker}")

    item = trader.get_portfolio_item(ticker)

    # close any long positions
    long_shares = item.get_long_shares()
    if long_shares > 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, int(long_shares/100))  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        sleep(1)  # we sleep to give time for the order to process

    # close any short positions
    short_shares = item.get_short_shares()
    if short_shares > 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, int(short_shares/100))
        trader.submit_order(order)
        sleep(1)

#def market_trend(trader: shift.Trader):

        
def nno_of_lots(risk_type, funds_available):
    if risk_type == 'high':
        lot_size = 0.05 * funds_available
    elif risk_type == 'medium':
        lot_size = 0.15 * funds_available
    elif risk_type == 'low':
        lot_size = 0.2 * funds_available
    else:
        print('Invalid risk type!')
        return None
    
    return lot_size

def no_of_lots(risk_type, funds_available, current_price):
    if risk_type == 'high':
        if current_price > 1000:
            lot_size = 0.02 * funds_available / current_price
        else:
            lot_size = 0.05 * funds_available / current_price
    elif risk_type == 'medium':
        if current_price > 1000:
            lot_size = 0.1 * funds_available / current_price
        else:
            lot_size = 0.15 * funds_available / current_price
    elif risk_type == 'low':
        lot_size = 0.2 * funds_available / current_price
    else:
        print('Invalid risk type!')
        return None

    return lot_size


def risk_type(stock_df):
    price_std = stock_df[['ask_price', 'bid_price']].std().mean()
    
    if price_std > 0.05:
        risk = 'high'
    elif price_std > 0.02:
        risk = 'medium'
    else:
        risk = 'low'
    return risk

def book_profits(initial_investment, current_value):
    profit_percentage = (current_value - initial_investment) / initial_investment * 100
    if profit_percentage >= 5:
        return "Sell"
    else:
        return "Hold"


def strategy(trader: shift.Trader, ticker: str, endtime):
    # know market trend
    current = trader.get_last_trade_time()
    end_time = current + timedelta(minutes=10)
    data_list=[]
    df = pd.DataFrame()
    #market_trend(trader)
    t_end = current + timedelta(minutes=5)
    while trader.get_last_trade_time() < t_end:
        current_price = trader.get_last_price(ticker)    
        best_price = trader.get_best_price(ticker)
        best_bid = best_price.get_bid_price()
        best_ask = best_price.get_ask_price()
        previous_price = (best_bid + best_ask) / 2
        data_dict = {'timestamp': trader.get_last_trade_time(), 'ticker': ticker,  'ask_price': best_ask, 'bid_price': best_bid, 'mid_price': previous_price}
    	# append the dictionary to the list
        data_list.append(data_dict)
    df = pd.DataFrame(data_list)
    print("\nDATAFRAME:::", df.head())
    risk = risk_type(df[df['ticker']==ticker])
    print("\nRISK:::::", risk)
     
    mid_price = (best_bid + best_ask) / 2
    while (trader.get_last_trade_time() < endtime):
        # cancel unfilled orders from previous time-step
        cancel_orders(trader, ticker)
        funds_available = trader.get_portfolio_summary().get_total_bp()
        current_price = best_ask
        nolot = no_of_lots(risk, funds_available,current_price )
        no_lot = int(str(int(nolot))[0])
        print("\n noof lot :", no_lot)
	# place order
        order_buy = shift.Order(shift.Order.Type.LIMIT_BUY, ticker, no_lot, mid_price)
        trader.submit_order(order_buy)
        order_sell = shift.Order(shift.Order.Type.LIMIT_SELL, ticker, no_lot, mid_price)
        trader.submit_order(order_sell)
        for order in trader.get_submitted_orders():
            if order.symbol == ticker and  order.status == shift.Order.Status.FILLED:
                price = order.executed_price
                size = order.executed_size
                type = order.type
                print("\n Executed : Price m Size", price, size) 
                print("Track if profit")
                current_price = trader.get_last_price(ticker)
                state= book_profits(price,current_price)
                if state=='Sell':
                     if type == 'shift.Order.Type.LIMIT_BUY':
                         order = shift.Order(shift.Order.Type.MARKET_SELL, ticker, size, price)
                     elif type == 'shift.Order.Type.LIMIT_SELL':
                         order = shift.Order(shift.Order.Type.MARKET_BUY, ticker, size, price)
                     trader.submit_order(order)
                else:
                     continue
    return      


def strategyyyy(trader: shift.Trader, ticker: str, endtime):
    # NOTE: Unlike the following sample strategy, it is highly reccomended that you track and account for your buying power and
    # position sizes throughout your algorithm to ensure both that have adequite captial to trade throughout the simulation and
    # that you are able to close your position at the end of the strategy without incurring major losses.
    #track buying power check capital and close position without loss 
    #position size ot lot
    #check loss

    initial_pl = trader.get_portfolio_item(ticker).get_realized_pl()
    
    print( "Ticker last price:", ticker ,"::: ",   trader.get_last_price(ticker))
    # strategy parameters
    check_freq = 1
    order_size = 5  # NOTE: this is 5 lots which is 500 shares.

    # strategy variables
    best_price = trader.get_best_price(ticker)
    best_bid = best_price.get_bid_price()
    best_ask = best_price.get_ask_price()
    previous_price = (best_bid + best_ask) / 2

    while (trader.get_last_trade_time() < endtime):
        # cancel unfilled orders from previous time-step
        cancel_orders(trader, ticker)

        # get necessary data
        best_price = trader.get_best_price(ticker)
        best_bid = best_price.get_bid_price()
        best_ask = best_price.get_ask_price()
        midprice = (best_bid + best_ask) / 2

        # place order
        if (midprice > previous_price):  # price has increased since last timestep
            # we predict price will continue to go up
            order = shift.Order(
                shift.Order.Type.MARKET_BUY, ticker, order_size)
            trader.submit_order(order)
        elif (midprice < previous_price):  # price has decreased since last timestep
            # we predict price will continue to go down
            order = shift.Order(
                shift.Order.Type.MARKET_SELL, ticker, order_size)
            trader.submit_order(order)

            # NOTE: If you place a sell order larger than your current long position, it will result in a short sale, which
            # requires buying power both for the initial short_sale and to close your short position.For example, if we short
            # sell 1 lot of a stock trading at $100, it will consume 100*100 = $10000 of our buying power. Then, in order to
            # close that position, assuming the price has not changed, it will require another $10000 of buying power, after
            # which our pre short-sale buying power will be restored, minus any transaction costs. Therefore, it requires
            # double the buying power to open and close a short position than a long position.

        previous_price = midprice
        sleep(check_freq)

    # cancel unfilled orders and close positions for this ticker
    cancel_orders(trader, ticker)
    close_positions(trader, ticker)

    print(
        f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - initial_pl}")


def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    current = trader.get_last_trade_time()
    start_time = datetime.combine(current, dt.time(9, 30, 0))
    end_time = datetime.combine(current, dt.time(15, 50, 0))
    #start_time = current
    #end_time = start_time + timedelta(minutes=15)
    print(start_time, end_time)
    while trader.get_last_trade_time() < start_time:
        print("still waiting for market open")
        sleep(check_frequency)

    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads = []

    # in this example, we simultaneously and independantly run our trading alogirthm on two tickers
    tickers = trader.get_stock_list() #["AAPL", "MSFT"]
    print(tickers)
    print("START")

    for ticker in tickers:
        # initializes threads containing the strategy for each ticker
        threads.append(
            Thread(target=strategy, args=(trader, ticker, end_time)))

    for thread in threads:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time:
        sleep(check_frequency)

    # wait for all threads to finish
    for thread in threads:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join()

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    print(
        f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")


if __name__ == '__main__':
    with shift.Trader("market_mavericks") as trader:
    #with shift.Trader("market_mavericks_test01") as trader:
        trader.connect("initiator.cfg", "1n5Yj51a10")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)
        main(trader)
