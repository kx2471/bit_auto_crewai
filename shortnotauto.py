import openai
import pyupbit
import json
from langchain_openai import ChatOpenAI
import investmentData
import time
import re
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

openai.api_key = (os.getenv("OPENAI_API_KEY"))





#ai에게 현재 상황을 인식시킴. 예를들면 최신거래내역이 매수면 비트코인을 가지고 있고, 매도이면 원화를 가지고있음. 
#최신거래내역은 tading_info.json에서 trade_history 항목의 created_at 이 가장 최신시간인 것이 최신거래내역임. 매수, 매도 판단은 side 값이 bid면 매수, ask면 매도임.
#이번에는 AI에게 buy / sell / hold의 판단은 내리지 않고 오로지 기술적으로 수익률이 5%이상이면 팔고, 손실률이 5%이하이더라도 팔도록 지시함.
#ai가 해야 할 일은 비트코인을 가지고 있지 않을 때 오를것같다고 판단되는 시기에 비트코인을 시장가로 all buy하도록 결정하는 것 뿐임.
#ai는 그렇게해서 손실이 났을 때는 이전 판단에 대한 반성을 해야함.



sample_data = """
    {
        "timestamp":"2025-02-21T13:33:00.000",
        "open":145025000.0,
        "high":145110000.0,
        "low":145025000.0,
        "close":145061000.0,
        "volume":0.13091492,
        "value":18990991.4528600015,
        "SMA_5":145032400.0,
        "EMA_1":145061000.0,
        "RSI":97.3684210526,
        "BB_Middle_5min":145032400.0,
        "BB_Upper_5min":145064387.4975576401,
        "BB_Lower_5min":145000412.5024423599
    }
"""
data_description = """This data contains a number of technical indicators related to the price of Bitcoin. 
 Each key has the following meanings

- 'timestamp': The time of the corresponding data point (in ISO 8601 format)
 - 'open': The opening price at the given time
 - 'high': The highest price during the given time
 - 'low': Lowest price during the given time
 - 'close': The closing price for the given time
 - 'volume': Volume traded during the given time
 - 'value': Total value traded (price x volume)
 - 'SMA_5': 5 minute simple moving average
 - 'EMA_1': 1-minute exponential moving average
 - 'RSI': Relative Strength Index (RSI, 5 minute timeframe) 
 - 'BB_Middle_5min': Midline of the 5 minute Bollinger Bands
 - 'BB_Upper_5min': The upper line of the 5-minute bullinger band
 - 'BB_Lower_5min': The lower line of the 5-minute bullinger bands

 Sample data:
 {sample_data}
 
 Based on this 
 data, please analyze the price trend of Bitcoin and predict the likely price increase/decrease in the next time. 
 Make a buy/sell decision based on the given indicators.
"""
data_file = "processed_data.json"

def analyze_market():
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": """
You are an expert in short-term KRW-BTC scalping
. You analyze KRW-BTC's latest price, RSI, SMA, EMA, Bollinger Bands, etc. to determine where to buy, sell, or hold KRW-BTC.
"""},
                  {"role": "user", "content": """
Read the data in {data_file} and look at the price, RSI, SMA, EMA, and Bollinger Bands every minute to determine if you should buy, sell, or hold at the current time.

Here's how to read the data

{data_description}

Also, please write a brief reason for each decision.                   
"""}],
        temperature=0.2,
        max_tokens = 1000
    )
    
    return response["choices"][0]["message"]["content"]



response = analyze_market()
print(response)  # 전체 JSON 응답 출력
print(response["choices"][0]["message"]["content"])  # AI의 응답 내용만 출력