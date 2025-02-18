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

# def bitcoin_news(ticker_symbol: str):
#     """Provide the latest news for a given ticker. The ticker_symbol is the name of a cryptocurrency news. example : "BTC-KRW" """
#     try:
#         ticker = yf.Ticker(ticker_symbol)
#         news = ticker.news
        
#         if news:
#             # 필터링된 뉴스 데이터
#             filtered_news = []
#             for article in news:
#                 filtered_article = {
#                     "id": article.get("id"),
#                     "contentType": article.get("contentType"),
#                     "title": article.get("title"),
#                     "summary": article.get("summary"),
#                     "pubDate": article.get("pubDate"),
#                     "provider": article.get("provider"),
#                     "canonicalUrl": article.get("canonicalUrl")
#                 }
#                 filtered_news.append(filtered_article)
            
#             # JSON 파일로 저장
#             with open("news.json", "w", encoding="utf-8") as file:
#                 json.dump(filtered_news, file, ensure_ascii=False, indent=4)
            
#             return "뉴스가 'news.json' 파일에 저장되었습니다."
#         else:
#             return "해당 티커에 대한 뉴스가 없습니다."
#     except Exception as e:
#         return f"오류 발생: {str(e)}"
    
# bitcoin_news("BTC")

    
# def bitcoin_price(intervalName, countNum, filename):
#     # OHLCV 데이터 가져오기
#     bit_Price = pyupbit.get_ohlcv(ticker="KRW-BTC", interval=intervalName, count=countNum)

#     if bit_Price is not None:
#         # 인덱스(시간)를 컬럼으로 변환
#         bit_Price = bit_Price.reset_index()

#         # "index" 컬럼 이름을 "timestamp"로 변경
#         bit_Price.rename(columns={"index": "timestamp"}, inplace=True)

#         # 확장자 .json 자동 추가
#         if not filename.endswith(".json"):
#             filename += ".json"

#         # JSON 파일로 저장 (사용자가 지정한 파일명)
#         bit_Price.to_json(filename, orient="records", date_format="iso")

#     return bit_Price

import time
import os 
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o-mini"

upbit_acc_key = os.getenv("UPBIT_ACCESS_KEY")  # 업비트 액세스 키
upbit_sec_Key = os.getenv("UPBIT_SECRET_KEY")  # 업비트 시크릿 키

if not upbit_acc_key or not upbit_sec_Key:
    print("API 키가 설정되지 않았습니다.")
else:
    upbit = pyupbit.Upbit(upbit_acc_key, upbit_sec_Key)
    # 계좌 확인
    

    
def masu_avg():
    ticker = "KRW-BTC"

    # 평균 매수가
    avg_buy_price = upbit.get_avg_buy_price(ticker)

    # 보유 수량
    balance = upbit.get_balance(ticker)

    # 매수금액 (총 투자금)
    buy_amount = avg_buy_price * balance

    # 현재 가격
    current_price = pyupbit.get_orderbook(ticker)["orderbook_units"][0]["ask_price"]

    # 현재 평가금액
    eval_amount = current_price * balance

    # 평가손익
    profit_loss = eval_amount - buy_amount

    balances = upbit.get_balances()

    # 데이터 저장할 JSON 구조
    data = {
        "Buy Amount": buy_amount,
        "Est. Value": eval_amount,
        "P/L": profit_loss,
        "balance" : balances,
    }

    # JSON 파일로 저장
    with open("trading_info.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("📁 JSON 파일 저장 완료: trading_info.json")

masu_avg()
