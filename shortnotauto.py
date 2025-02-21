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
    balance_current("KRW-BTC")
    variable_names()
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
            print("전량 매수")
            upbit.buy_market_order("KRW-BTC", krw_balance - 100)
        else:
            print("진입시점이 아닙니다. 보류합니다.")

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

    print("데이터가 'current_balances_info.json' 파일로 저장되었습니다.")


    



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
 - 'RSI': Relative Strength Index (RSI, 2 minute timeframe) 
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
    if not data_file or not isinstance(data_file, list):
        print("⚠️ 데이터 파일이 없거나 올바른 형식이 아닙니다.")
        return "No data available"

    # ✅ 최근 10개 데이터만 사용
    recent_data = data_file[-10:]
    data_str = json.dumps(recent_data, indent=4, ensure_ascii=False) if data_file else "No data available"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": """
You are an expert in short-term KRW-BTC scalping
. You analyze KRW-BTC's price, RSI, SMA, EMA, Bollinger Bands, etc. to determine where to buy, sell, or hold KRW-BTC.
"""},
                  {"role": "user", "content": f"""
You need to read the data in {data_str} and make a judgment based on the price, RSI, SMA, EMA, and Bollinger Bands for 10 minutes of every minute. 
You should select 'buy' if you think the price is likely to go up at this time, 'sell' if you think the price is likely to go down, or 'hold' if you think there is a reason to hold.

Here's how to read the data

{data_description}

Once you've completed your analysis, please answer only in the following format

{{"decision":"buy or sell or hold", "reason":"the basis and reason for your decision", "timestamp":"{timestamp}}}"
               
"""}],
        temperature = 0.5,
        max_tokens = 2000
    )
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
        investmentData.process_data()
        analyze_market()
        pyupbit_trading()
        investmentJsonAppend.append_to_report_data("./shortnotauto_data/current_recommendation.json", "./shortnotauto_data/notauto_Reported_Data.json")
        investmentJsonAppend.delete_old_data(3, "./shortnotauto_data/notauto_Reported_Data.json")

        time.sleep(180)
