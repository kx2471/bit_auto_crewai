from crewai.tools import tool
import yfinance as yf
import pyupbit

@tool("가격 가져오기")
def get_price_data(intervalname, countnum):
    """Tool to retrieve the price at each interval for a ticker.
intreval has "day", "week", and "minute1", which are the daily, weekly, and minute1 timeframes, respectively.
The value entered in count is the number of data from the current to the previous time. ex) In the case of daily 30 days, data from 30 days ago.
"""
    return pyupbit.get_ohlcv(ticker="KRW-BTC", interval=intervalname, count=countnum)


# 🔹 수정된 실행 코드
print(get_price_data.run("day", 5))

