import json
import pandas as pd
import numpy as np
import pyupbit
import os 
from dotenv import load_dotenv
load_dotenv()

upbit_acc_key = os.getenv("UPBIT_ACCESS_KEY")  # 업비트 액세스 키
upbit_sec_Key = os.getenv("UPBIT_SECRET_KEY")  # 업비트 시크릿 키

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


def load_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return pd.DataFrame(data)

def calculate_sma(df, window=2): #SMA 2분간격
    df[f'SMA_{window}'] = df['close'].rolling(window=window).mean()

def calculate_ema(df, window=1): #EMA 1분간격
    df[f'EMA_{window}'] = df['close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(df, window=2):  # RSI를 2분 간격으로 계산
    # 가격 변화량 (Delta)
    delta = df['close'].diff()
    
    # 상승 부분 (Gain)과 하락 부분 (Loss)을 각각 추출
    gain = (delta.where(delta > 0, 0))  # 상승은 그대로 두고, 하락은 0으로
    loss = (-delta.where(delta < 0, 0))  # 하락은 그대로 두고, 상승은 0으로

    # 상승 평균과 하락 평균 계산 (rolling 윈도우를 사용)
    avg_gain = gain.rolling(window=window).mean()  # 상승 평균
    avg_loss = loss.rolling(window=window).mean()  # 하락 평균

    # 상대 강도 (RS) 계산
    rs = avg_gain / avg_loss
    
    # RSI 계산
    df['RSI'] = 100 - (100 / (1 + rs))  # RSI 공식 적용

def calculate_bollinger_bands(df, window=3, num_std=2):   #3분단위 불린저밴드 계산
    df[f'BB_Middle_{window}min'] = df['close'].rolling(window=window).mean()
    df[f'BB_Upper_{window}min'] = df[f'BB_Middle_{window}min'] + num_std * df['close'].rolling(window=window).std()
    df[f'BB_Lower_{window}min'] = df[f'BB_Middle_{window}min'] - num_std * df['close'].rolling(window=window).std()





def process_data(output_filename="./shortnotauto_data/processed_data.json"):
    # 데이터를 로드하고 지표들을 계산
    bitcoin_price("minute1", 180, "./shortnotauto_data/shortminprice.json")
    file_path = './shortnotauto_data/shortminprice.json'
    df = load_data(file_path)
    calculate_sma(df)
    calculate_ema(df)
    calculate_rsi(df)
    calculate_bollinger_bands(df)

    # 데이터를 시간순 또는 원하는 다른 기준으로 정렬
    df = df.sort_values(by='timestamp')  # 예시: 'timestamp' 열을 기준으로 정렬
    
    # 계산된 데이터프레임을 JSON 파일로 저장
    if not output_filename.endswith(".json"):
        output_filename += ".json"
        
    df.to_json(output_filename, orient="records", date_format="iso", indent=4)
    return df








