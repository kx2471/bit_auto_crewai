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
            # 필터링된 뉴스 데이터
            filtered_news = []
            for article in news:
                filtered_article = {
                    "id": article.get("id"),
                    "contentType": article.get("contentType"),
                    "title": article.get("title"),
                    "summary": article.get("summary"),
                    "pubDate": article.get("pubDate"),
                    "provider": article.get("provider"),
                    "canonicalUrl": article.get("canonicalUrl")
                }
                filtered_news.append(filtered_article)
            
            # JSON 파일로 저장
            with open("news.json", "w", encoding="utf-8") as file:
                json.dump(filtered_news, file, ensure_ascii=False, indent=4)
            
            return "뉴스가 'news.json' 파일에 저장되었습니다."
        else:
            return "해당 티커에 대한 뉴스가 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"
    
bitcoin_news("BTC")

    
def bitcoin_price(intervalName, countNum, filename):
    # OHLCV 데이터 가져오기
    bit_Price = pyupbit.get_ohlcv(ticker="KRW-BTC", interval=intervalName, count=countNum)

    if bit_Price is not None:
        # 인덱스(시간)를 컬럼으로 변환
        bit_Price = bit_Price.reset_index()

        # "index" 컬럼 이름을 "timestamp"로 변경
        bit_Price.rename(columns={"index": "timestamp"}, inplace=True)

        # 확장자 .json 자동 추가
        if not filename.endswith(".json"):
            filename += ".json"

        # JSON 파일로 저장 (사용자가 지정한 파일명)
        bit_Price.to_json(filename, orient="records", date_format="iso")

    return bit_Price


