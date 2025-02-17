from crewai import Crew, Agent, Task
import crewai_tools
from openai import OpenAI
import pyupbit
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
    balance = upbit.get_balance()
    print("계좌 잔고:", balance)


openAI_key = (os.getenv("OPENAI_API_KEY")) #OpenAI api키


#업비트에서 일봉30일치 가져옴
dailyPriceBTC = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")

#업비트에서 주봉 10주치 가져옴
wekeelyPriceBTC = pyupbit.get_ohlcv("KRW-BTC", count=10, interval="week")

#업비트에서 1분봉 데이터를 5시간치 가져옴
minPriceBTC = pyupbit.get_ohlcv("KRW-BTC", interval="minute1", count=300)





#CrewAi Agent 생성
class dayAnalyst(Agent):
    def run(self):
        return "분석결과"

class weekAnalyst(Agent):
    def run()