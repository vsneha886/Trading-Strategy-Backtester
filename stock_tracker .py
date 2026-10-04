#Stock price tracker
#Sneha Anudeep Verma
#09/04/2026


#import libraries
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#functions

#creating a cache 
stock_data_cache = {}  # lives outside any function, at the top of your file



#function ensuring we can get any stock we want
def get_current_price(ticker):
    """gets the current price and the closing price of a chosen stock"""
    stock = yf.Ticker(ticker)#assign stock 
    info = stock.info  # fetch stock info 
    price = info["currentPrice"] #get current price
    prev_close = info["previousClose"] #get yesterdays closing price 
    return price, prev_close #return both values 


#function getting one month history of stock 
def get_stock_history(ticker, period="6mo"):
    """gets price history for a ticker, using a cached copy if already fetched"""
    if ticker in stock_data_cache :
        return _cache[ticker]  # already have it, skip the API call
    
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    _cache[ticker] = data  # remember it for next time
    return data
#function getting one month close history of stock 
def get_stock_history_close(ticker, period = "6mo"):
    """gets the six month close history of the chosen stock """
    stock = yf.Ticker(ticker)
    data = stock.history(period = period)
    return data["Close"]

#function calculating percent change (returns) of a stock over a month
def get_daily_percent_change(ticker):
    """calculates the day-over-day percent change from a price history DataFrame"""
    returns = get_stock_history_close(ticker).pct_change()
    return returns
#function calculating the volatility of a stock
def get_volatility(ticker, window = 20):
    """calculates the volatility of a stock"""
    returns = get_daily_percent_change(ticker)
    volatility = returns.rolling(window).std()
    return volatility

def get_annualized_volatility(ticker, window=20):
    """calculates rolling volatility of daily returns, annualized to a yearly scale"""
    daily_vol = get_volatility(ticker, window)  
    annualized_vol = daily_vol * np.sqrt(252)
    return annualized_vol
#Get shapre ratio for analysis 
def get_sharpe_ratio(ticker, risk_free_rate=0.04):
    """calculates the annualized Sharpe ratio for a Close price Series"""
    mean_returns = get_daily_percent_change(ticker).mean() * 252
    sharpeValue  = (mean_returns - risk_free_rate)/(get_daily_percent_change(ticker).std()* np.sqrt(252))
    return sharpeValue

def get_moving_average(ticker, window=20):
    """calculates the rolling moving average of Close prices"""
    returns = get_stock_history_close(ticker)
    moving_avg = returns.rolling(window).mean()
    return moving_avg
def get_crossover_signal(ticker, short_window=10, long_window=50):
    """
    Computes short and long moving averages and detects crossover points.
    Returns a DataFrame with columns: short_ma, long_ma, signal, crossover
    """
    short_ma = get_moving_average(ticker, short_window)
    long_ma = get_moving_average(ticker, long_window)

    signal = (short_ma > long_ma).astype(int)  # 1 = short above long, 0 = short below
    crossover = signal.diff()  # 1 = fresh buy signal, -1 = fresh sell signal, 0 = no change

    result = pd.DataFrame({
        "short_ma": short_ma,
        "long_ma": long_ma,
        "signal": signal,
        "crossover": crossover
    })
    return result      


def backtest_crossover(ticker, short_window=10, long_window=50):
    """Simulates returns from following the crossover signal vs. buy-and-hold."""
    data = get_crossover_signal(ticker, short_window, long_window)
    daily_returns = get_daily_percent_change(ticker)

    # Use yesterday's signal to avoid lookahead bias
    position = data["signal"].shift(1)

    strategy_returns = daily_returns * position
    buy_hold_returns = daily_returns

    strategy_cumulative = (1 + strategy_returns).cumprod()
    buy_hold_cumulative = (1 + buy_hold_returns).cumprod()

    return strategy_cumulative, buy_hold_cumulative, strategy_returns

def get_max_drawdown(cumulative_returns):
    """
    Calculates the maximum peak-to-trough decline in a cumulative returns series.
    cumulative_returns: a Series like the ones from backtest_crossover
    (e.g., strategy_cumulative or buy_hold_cumulative)
    """

    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max)/running_max

    return  drawdown.min()

def get_win_rate(strategy_returns):
    """
    Calculates the percentage of active trading days with positive returns.
    strategy_returns: the Series from backtest_crossover (daily_returns * position)
    """
    active_days = strategy_returns[strategy_returns != 0]
    win_rate = (active_days>0).mean()
    return win_rate
def plot_backtest(ticker):
    strategy, buy_hold, _  = backtest_crossover(ticker)
    
    plt.plot(strategy, label="Strategy")
    plt.plot(buy_hold, label="Buy & Hold")
    
    plt.title(f"Equity Curve: {ticker} ")
    plt.xlabel("Month")
    plt.ylabel("Net Growth ")
    plt.legend()
    plt.show()

def display_stock_summary(ticker):
    """Prints a clean summary for one stock using the functions you already built."""
    price, prev_close = get_current_price(ticker)
    change = price - prev_close
    pct_change = (change / prev_close) * 100
    vol = get_annualized_volatility(ticker).iloc[-1]  # most recent value only
    sharpe = get_sharpe_ratio(ticker)
    strategy_cumulative, buy_hold_cumulative, strategy_returns = backtest_crossover(ticker_input)

    print("=" * 40)
    print(f"  {ticker} Summary")
    print("=" * 40)
    print(f"  Price:         ${price:.2f}")
    print(f"  Change:        ${change:+.2f} ({pct_change:+.2f}%)")
    print(f"  Ann. Vol:      {vol:.2%}")
    print(f"  Sharpe Ratio:  {sharpe:.2f}") 
    print(f"Strategy final return: {(strategy_cumulative.iloc[-1] - 1) * 100:.2f}%")
    print(f"Buy & Hold final return: {(buy_hold_cumulative.iloc[-1] - 1) * 100:.2f}%")
    print(f"Strategy Max Drawdown: {get_max_drawdown(strategy_cumulative):.2%}")
    print(f"Buy & Hold Max Drawdown: {get_max_drawdown(buy_hold_cumulative):.2%}")
    print(f"Win Rate: {get_win_rate(strategy_returns):.2%}\n")
    print("=" * 40)
    plot_backtest(ticker)
  


while True:
    ticker_input = input("Enter a stock ticker (or 'quit' to exit): ").upper()
    
    if ticker_input == "QUIT":
        print("Goodbye!")
        break

    
    try:
        display_stock_summary(ticker_input)
        

    except (KeyError, IndexError):
        print(f"Couldn't find data for '{ticker_input}' — check the ticker symbol and try again.\n")


'''
#testing
AAPL_price, AAPL_prev_close = get_current_price("AAPL") #assigns values

AAPL_data = get_stock_history("AAPL")
AAPL_data_close = get_stock_history_close("AAPL")

print(AAPL_data_close)
AAPL_returns = get_daily_percent_change("AAPL")
print(f"APPL percent change {AAPL_returns}%")
print (f"AAPL Volatility: {get_volatility('AAPL')}")

print (f"AAPL annual Volatility: {get_annualized_volatility('AAPL')}")

print(f"AAPL price: ${AAPL_price}, previous close: ${AAPL_prev_close}")#display values

print(f"AAPL sharpe Ratio: {get_sharpe_ratio('AAPL')}")
print(f"AAPL moving  average: {get_moving_average('AAPL')}")

print()
print(f"AAPL Crossover signal {get_crossover_signal('AAPL')}")


crossover_data = get_crossover_signal("AAPL")
actual_crosses = crossover_data.dropna()
actual_crosses = actual_crosses[actual_crosses["crossover"] != 0]
print(actual_crosses)'''
