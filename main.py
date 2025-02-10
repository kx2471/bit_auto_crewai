import crewai
import crewai_tools
from openai import OpenAI
import pyupbit
import os 
from dotenv import load_dotenv
load_dotenv()

upbit_acc_key = (os.getenv("UPBIT_ACCESS_KEY")) #업비트 액세스키
upbit_sec_Key = (os.getenv("UPBIT_SECRET_KEY")) #업비트 시크릿키
upbit = pyupbit.Upbit(upbit_acc_key, upbit_sec_Key)

openAI_key = (os.getenv("OPENAI_API_KEY")) #OpenAI api키


#업비트에서 일봉30일치 가져옴
dailyPriceBTC = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")

#업비트에서 주봉 10주치 가져옴
wekeelyPriceBTC = pyupbit.get_ohlcv("KRW-BTC", count=10, interval="week")

#업비트에서 1분봉 데이터를 5시간치 가져옴
minPriceBTC = pyupbit.get_ohlcv("KRW-BTC", interval="minute1", count=300)
print(minPriceBTC)