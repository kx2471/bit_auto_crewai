from crewai.tools import tool
import pyupbit
import json
import yfinance as yf

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
    
def aaa(ticker):
    # 보유 자산 정보 조회
    balance_info = upbit.get_balance(ticker)  # 보유 자산 정보 (예시로 KRW-BTC)
    avg_buy_price = upbit.get_avg_buy_price(ticker)  # 매수 평균가 (예시로 KRW-BTC)
    # 현재 가격 조회
    current_price = pyupbit.get_current_price(ticker)

    # 매수 금액과 평가 금액 계산
    buy_amount = balance_info * avg_buy_price  # 매수 금액
    est_value = balance_info * current_price  # 평가 금액
    
    profit_loss = est_value - buy_amount
    profit_loss_percent = (profit_loss / buy_amount) * 100 
    profit_loss_percent = f"{round(profit_loss_percent, 3)}%"

    # 거래 내역 조회
    order_history = upbit.get_order(ticker, state="done", limit=50)

    # 원하는 JSON 형식으로 데이터 구성
    data = {
        "my_balances": {
            "currency": ticker, #코인이름
            "balance": balance_info, #보유량
            "avg_buy_price": avg_buy_price, #매수평균가
            "buy_amount": buy_amount, #매수금액
            "est_value": est_value, #평가금액
            "profit_loss": profit_loss, #손실 (원화)
            "profit_loss_percent": profit_loss_percent  # 손실률
        },
        "trade_history": order_history
    }

    # JSON 파일로 저장
    with open("asset_and_trade_history.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("데이터가 JSON 파일로 저장되었습니다.")

aaa("KRW-BTC")