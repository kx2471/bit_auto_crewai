import openai
import pyupbit
import json
import investmentData
import investmentJsonAppend
import os 
import re
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o-mini"
open_api_key = os.getenv("OPENAI_API_KEY")

upbit_acc_key = os.getenv("UPBIT_ACCESS_KEY")  # 업비트 액세스 키
upbit_sec_Key = os.getenv("UPBIT_SECRET_KEY")  # 업비트 시크릿 키

if not upbit_acc_key or not upbit_sec_Key:
    print("API 키가 설정되지 않았습니다.")
else:
    upbit = pyupbit.Upbit(upbit_acc_key, upbit_sec_Key)

client = openai.Client(api_key=open_api_key)

decision = None #AI결정값. 전역변수

currency = None
krw_balance = None
btc_balance = None
avg_buy_price = None
buy_amount = None
est_value = None
profit_loss = None
profit_loss_percent = None



def variable_names():
    global currency, krw_balance, btc_balance, avg_buy_price, buy_amount, est_value, profit_loss, profit_loss_percent
    with open("./shortnotauto_data/current_balances_info.json", 'r') as file:
        data = json.load(file)
    currency = data["my_balances"]["currency"]
    krw_balance = data["my_balances"]["KRW_balance"]
    btc_balance = data["my_balances"]["balance"]
    avg_buy_price = data["my_balances"]["avg_buy_price"]
    buy_amount = data["my_balances"]["buy_amount"]
    est_value = data["my_balances"]["est_value"]
    profit_loss = data["my_balances"]["profit_loss"]
    profit_loss_percent = data["my_balances"]["profit_loss_percent"]





def pyupbit_trading():
    if btc_balance > 0:  # BTC를 보유하고 있을 때
        
        # 손익률 계산
        pl = profit_loss_percent
        
        if decision == "sell":
            # AI 전량 매도
            print("AI 판단으로 전량 매도")
            upbit.sell_market_order("KRW-BTC", btc_balance)

        elif pl <= -3:
            # 손실 전량 매도
            print("3% 손실으로 전량 매도")
            upbit.sell_market_order("KRW-BTC", btc_balance)
        
        elif pl >= 3:
            # 이득 전량 매도
            print("3% 이익으로 전량 매도")
            upbit.sell_market_order("KRW-BTC", btc_balance)
        
        elif decision == "hold":
            print("매도/매수 없이 보유 중")

    else:  # BTC를 보유하지 않을 때
        if decision == "buy":
            # 전량 매수 (KRW 잔고로 BTC 구매)
            print("AI 진입 시점으로 판단하여 전량 매수")
            upbit.buy_market_order("KRW-BTC", krw_balance - 100)
        else:
            print("진입 시점이 아닙니다. 보류합니다.")

    return



def balance_current(ticker):
    # 보유 자산 정보 조회
    balance_info = upbit.get_balance(ticker)  # 보유 자산 정보 (예시로 KRW-BTC)
    avg_buy_price = upbit.get_avg_buy_price(ticker)  # 매수 평균가 (예시로 KRW-BTC)
    # 현재 가격 조회
    current_price = pyupbit.get_current_price(ticker)

    # 매수 금액과 평가 금액 계산
    buy_amount = balance_info * avg_buy_price  # 매수 금액
    est_value = balance_info * current_price  # 평가 금액
    
    profit_loss = est_value - buy_amount

    profit_loss_percent = 0.0
    if buy_amount != 0:
        profit_loss_percent = (profit_loss / buy_amount) * 100 
    

    KRW_balance = upbit.get_balance(ticker="KRW")

    # 원하는 JSON 형식으로 데이터 구성
    data = {
        "my_balances": {
            "currency": ticker, #코인이름
            "KRW_balance": KRW_balance, #보유원화
            "balance": balance_info, #보유량
            "avg_buy_price": avg_buy_price, #매수평균가
            "buy_amount": buy_amount, #매수금액
            "est_value": est_value, #평가금액
            "profit_loss": profit_loss, #손실 (원화)
            "profit_loss_percent": profit_loss_percent  # 손실률
        }
    }

    # JSON 파일로 저장
    with open("./shortnotauto_data/current_balances_info.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    
    variable_names()

    print("데이터가 'current_balances_info.json' 파일로 저장되었습니다.")


    

my_balances_description = """
currency: The name of the instrument (e.g. "KRW-BTC")
KRW_balance: The amount of Korean won (KRW) you have
balance: The amount of Bitcoin you have
avg_buy_price: The average buy price of the coin
buy_amount: The amount you spent to buy the coin (buy_amount * buy_price)
est_value: The current estimate value of the coin (current price * amount held)
profit_loss: profit or loss (in KRW) - estimate value minus buy amount
profit_loss_percent: profit or loss percentage (%) - profit or loss divided by buy amount, expressed as a percentage
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
 - 'SMA_2': 2 minute simple moving average
 - 'EMA_1': 1-minute exponential moving average
 - 'RSI': Relative Strength Index (RSI, 3 minute timeframe) 
 - 'BB_Middle_3min': Midline of the 3 minute Bollinger Bands
 - 'BB_Upper_3min': The upper line of the 3-minute bullinger band
 - 'BB_Lower_3min': The lower line of the 3-minute bullinger bands

 
 Based on this 
 data, please analyze the price trend of Bitcoin and predict the likely price increase/decrease in the next time. 
 Make a buy/sell decision based on the given indicators.
"""

def load_json_data(file_path):
    """JSON 파일을 읽고 Python 딕셔너리로 변환"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)  # JSON을 Python 딕셔너리로 변환
        return data
    except Exception as e:
        print(f"⚠️ 파일을 읽는 중 오류 발생: {e}")
        return None
data_file = load_json_data("./shortnotauto_data/processed_data.json")




def extract_json_from_response(response_text):
    try:
        # '### Response:' 이후의 JSON 부분만 추출
        json_part = response_text.split('### Response:')[-1].strip()

        # 만약 JSON 형식으로 시작하고 끝나는지 확인하고 파싱
        if json_part.startswith('[') and json_part.endswith(']'):
            response_data = json.loads(json_part)
            return response_data
        else:
            print("응답에 유효한 JSON이 없습니다.")
            return None
    except Exception as e:
        print(f"오류 발생: {e}")
        return None




def analyze_market():
    investmentData.process_data()
    balance_current("KRW-BTC")
     # 파일을 올바르게 읽고 처리
    try:
        with open("./shortnotauto_data/processed_data.json", 'r', encoding='utf-8') as file:
            data_file = json.load(file)
    except FileNotFoundError:
        print("⚠️ 파일을 찾을 수 없습니다: ./shortnotauto_data/processed_data.json")
        return "No data available"
    except json.JSONDecodeError:
        print("⚠️ JSON 파일을 파싱하는 중 오류가 발생했습니다.")
        return "No data available"

    # 데이터 파일이 없거나 올바른 형식이 아닐 경우
    if not data_file or not isinstance(data_file, list):
        print("⚠️ 데이터 파일이 없거나 올바른 형식이 아닙니다.")
        print("data_file 상태:", data_file)  # data_file 상태 확인
        return "No data available"

    # ✅ 최근 10개 데이터만 사용
    recent_data = data_file[-3:]
    data_str = json.dumps(recent_data, indent=4, ensure_ascii=False) if data_file else "No data available"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
     #내 잔액 파일 읽기
    try:
        with open("./shortnotauto_data/current_balances_info.json", 'r', encoding='utf-8') as file:
            my_balances = json.load(file)
    except FileNotFoundError:
        print("⚠️ 잔액 파일을 찾을 수 없습니다: ./shortnotauto_data/current_balances_info.json")
        return "No data available"
    except json.JSONDecodeError:
        print("⚠️ 잔액 파일을 파싱하는 중 오류가 발생했습니다.")
        return "No data available"

    yes = "Yes"
    no = "No"
    balance_prompt = upbit.get_balance("KRW-BTC")
    print(balance_prompt)

    if balance_prompt <= 0: #BTC를 보유하지 않은 상태
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": """
    You are an expert in short-term KRW-BTC scalping.
    You analyze KRW-BTC's price, RSI, SMA, EMA, Bollinger Bands, etc. to determine where to buy, sell, or hold KRW-BTC.
    Make a decision based on both short-term trends and longer-term signals. Pay close attention to oversold and overbought conditions in RSI and price proximity to Bollinger Bands.
        ### **Trading Guidelines**
    - **Consider market trends across multiple timeframes, not just the latest data.**
    - Always analyze the **past 5 minutes of data**, including:
    - Price trends (higher highs/lows, lower highs/lows)
    - RSI movements (oversold <40, overbought >70)
    - SMA & EMA trends (crossovers, divergence)
    - Bollinger Band positioning (breakouts, mean reversion)
    - **Trading volume increase** as confirmation
    """},
                    {"role": "user", "content": f"""
            Analyze the following data: {data_str}.
            You need to read the data and make a judgment based on the price, RSI, SMA, EMA, and Bollinger Bands for the past 5 minutes.
            **Additional Considerations for BUY signal, Conditions that must be met:**
            - Consider buy if RSI is greater than or equal to 50.
            - Check for an upward trend in EMA and SMA.
            - If the price is near or below the middle Bollinger Band and RSI is above 50, consider a buy.
            - If the current price shows upward momentum and crosses above the previous high, consider a buy.          
            - If the RSI value is between 60 and 75, make sure to buy MUST now.
            
            **Trading Decision:**
            - **"buy"** if the price is likely to go up based on the conditions mentioned above.
            - **"sell"** if the price is likely to go down based on overbought conditions (RSI > 70) or price near the upper Bollinger Band.
            - **"hold"** if the situation is uncertain or prices are in a neutral zone.


    ### **How to Interpret the Data**
    {data_description}

    ### **Response Format**
    Please respond **ONLY** in the following format:

    {{"decision": "buy or sell or hold", "reason": "the basis and reason for your decision", "whether bitcoin is held": "{no}", "timestamp": "{timestamp}"}} 
                
    """}],
            temperature = 0.3,
            max_tokens = 2000
        )
    else: #BTC를 보유한 상태
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": """
    You are an expert in short-term KRW-BTC scalping.
    You analyze KRW-BTC's price, RSI, SMA, EMA, Bollinger Bands, etc. to determine where to sell, or hold KRW-BTC.
    Make a decision based on both short-term trends and longer-term signals. Pay close attention to oversold and overbought conditions in RSI and price proximity to Bollinger Bands.
    """},
                    {"role": "user", "content": f"""
    You are holding BTC. Your current assets, balances, are in {my_balances}. 
    Here's how to read your balance data:

    {my_balances_description}

    You need to read the data in {data_str} and make a judgment based on the price, RSI, SMA, EMA, and Bollinger Bands for 5 minutes of every minute. 
    You need to decide whether to sell or hold BTC based solely on the current rate of return, the expected outcome of BTC, and any risk management factors. If the current market conditions suggest volatility or the potential for a reversal, take those factors into account in your decision. 
    Make sure to consider the impact of potential losses, and provide strategies for mitigating them if necessary (e.g., stop-loss or trailing stops).

    Once you've completed your analysis, please answer only in the following format

    {{"decision":"sell or hold", "reason":"the basis and reason for your decision", "whether bitcoin is held": "{yes}", "timestamp":"{timestamp}}}"
                
    """}],
            temperature = 0.2,
            max_tokens = 2000)
    
    # ✅ 응답 내용
    response_text = response.choices[0].message.content
    save_response_to_file(response_text)
    jsonkey()
    get_decision("./shortnotauto_data/current_recommendation.json")

    # ✅ 사용된 토큰 정보 확인
    prompt_tokens = response.usage.prompt_tokens  # 입력(prompt)에 사용된 토큰 수
    completion_tokens = response.usage.completion_tokens  # 출력(response)에 사용된 토큰 수
    total_tokens = response.usage.total_tokens  # 전체 토큰 수

    print(f" **응답 내용:**\n{response_text}")
    print(f"\n **토큰 사용량:**")
    print(f"    입력(prompt) 토큰: {prompt_tokens}")
    print(f"    출력(completion) 토큰: {completion_tokens}")
    print(f"    총 사용 토큰: {total_tokens}")
    return response_text

def save_response_to_file(txt, file_path="./shortnotauto_data/response.txt"):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(txt)
        #print(f"응답 내용이 {file_path}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")


def jsonkey():  #response.txt 을 current_recommendation.json으로 변환하는 함수
    # 원본 TXT 파일과 저장할 JSON 파일 경로
    source_file = "./shortnotauto_data/response.txt"
    destination_file = "./shortnotauto_data/current_recommendation.json"

    # 파일 읽기
    with open(source_file, "r", encoding="utf-8") as file:
        data = file.read()

    # JSON 부분만 추출 (백틱이나 불필요한 문자 제거)
    data_cleaned = re.sub(r'```json|```', '', data).strip()

    try:
        # JSON 형식으로 변환
        json_data = json.loads(data_cleaned)

        # JSON 파일로 저장
        with open(destination_file, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, indent=2, ensure_ascii=False)

        #print(f"데이터가 {destination_file}에 저장되었습니다!")
    except json.JSONDecodeError as e:
        print(f"JSON 변환 오류: {e}")


def get_decision(file_name):
    global decision
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
            decision_value = data.get("decision")

            if decision_value is None:
                print(f"Warning: 'decision' key not found in {file_name}")
                decision = None  # 또는 다른 기본값 설정
            else:
                decision = str(decision_value)  # 문자열로 명시적 형변환
                print(f"Decision: {decision}")

    except FileNotFoundError:
        print(f"Error: {file_name} not found.")
        decision = None  # 파일이 없을 경우 decision을 None으로 설정
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        decision = None  # JSON 파싱 오류 시 decision을 None으로 설정
    except Exception as e: # 그 외의 에러
        print(f"Error occurred in get_decision: {e}")
        decision = None    

if __name__ == "__main__":
    while True:       
        analyze_market()
        pyupbit_trading()
        investmentJsonAppend.append_to_report_data("./shortnotauto_data/current_recommendation.json", "./shortnotauto_data/notauto_Reported_Data.json")
        investmentJsonAppend.delete_old_data(3, "./shortnotauto_data/notauto_Reported_Data.json")

        time.sleep(70)
