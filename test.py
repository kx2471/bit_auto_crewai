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

import json
import yfinance as yf

def bitcoin_news(ticker_symbol: str):
    """Provide the latest news for a given ticker. The ticker_symbol is the name of a cryptocurrency news. example : "BTC-KRW" """
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        
        if news:
            with open("news.json", "w", encoding="utf-8") as file:
                json.dump(news, file, ensure_ascii=False, indent=4)
            return "뉴스가 'news.json' 파일에 저장되었습니다."
        else:
            return "해당 티커에 대한 뉴스가 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"

# 🔹 수정된 실행 코드
bitcoin_news("BTC-KRW")

