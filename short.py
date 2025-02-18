from crewai import Crew, Agent, Task
from crewai.tools import tool
from crewai_tools import (FileReadTool, JSONSearchTool)
from openai import OpenAI
import pyupbit
import json
from langchain_openai import ChatOpenAI
import yfinance as yf
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
    # 계좌 확인
    


decision = None #AI결정값. 전역변수

#upbit 매수,매도 설정
def upbit_trading():
    try:
        if decision == "buy":
            krw_balance = upbit.get_balance("KRW")
            upbit.buy_market_order("KRW-BTC", krw_balance-100)
        elif decision == "sell":
            btc_balance = upbit.get_balance("BTC")
            upbit.sell_market_order("KRW-BTC", btc_balance)
        else:
            pass
    except Exception as e:
        print(f"Error occurred: {e}")
        pass

    return

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



#GPT 모델, API설정

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY")) #OpenAI api키
OPENAI_MODEL_NAME = "gpt-4o-mini"

gpt = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL_NAME, temperature=0.5, max_completion_tokens=8000)



#get ohlcv로 비트코인 분봉, 주봉, 월봉등 가져오는 함수
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



#crewai tool

#tool모음
json_tool = JSONSearchTool(json_path='./shortnews.json')
minPrice_tool = JSONSearchTool(json_path='./shortminprice.json')
masu_tool = JSONSearchTool(json_path='./trading_info.json')



shortMinSpecialist             = Agent(
                            role="Short-Term Scalping Specialist",
                            goal="""
                            In real-time, analyze the last 3 hours of minute-based charts to capture short-term price fluctuations and detect sudden spikes or drops.
                            Develop and execute scalping trading strategies by identifying optimal entry and exit points to generate rapid profits.
                            """,
                            backstory="",
                            verbose=True,
                            llm=gpt,
                            tools=[minPrice_tool]
                                               
                        )



riskManagement                  = Agent(
                            role="Risk Management Specialist",
                            goal="""
                            Systematically evaluate and monitor various risks inherent in market and trading strategies, including market risk, liquidity risk, and credit risk.
                            Develop effective stop-loss criteria, position sizing strategies, and hedging tactics to minimize overall risk exposure and ensure the team can respond swiftly to unexpected market volatility.
                            Collaborate with other team experts to maintain portfolio stability and continuously enhance the efficiency of risk management processes.
                            """,
                            backstory="""
                            A seasoned professional with over 7 years of experience in the finance and investment sectors, adept at managing risks across diverse market conditions through proven real-world strategies.
                            Proficient in leveraging quantitative analysis tools and advanced risk management software to evaluate risks in real-time and tailor risk management strategies specific to the team's needs.
                            With a solid background from working in the risk management departments of major investment institutions, this specialist has built a comprehensive risk management framework that accounts for both market uncertainties and investor psychology, ensuring a stable and secure investment environment for the entire team.
                            """,
                            verbose=True,
                            llm=gpt
                        )                         

headManager                     =Agent(
                            role="Haed Manager",
                            goal="""
                            Synthesize reports from all experts to create optimal trading strategies in real-time
                            Automatically generate strategies that minimize risk and maximize returns
                            Act as a key decision maker to make final investment decisions quickly and accurately
                            """,
                            backstory="""
                            A general manager is not just a data analyst; he or she is a professional who has weathered a lot of volatility in the past and realized huge returns.
                            His ability to make sound judgments and calmly formulate strategies in the midst of extreme market fluctuations has resulted in returns of hundreds and thousands of percent.
                            But his success isn't just luck, it's a well-calculated strategy that combines technical analysis, news flow, fundamental data, and risk management.
                            """,
                            verbose=True,
                            llm=gpt,
                            tools=[masu_tool]
                        )




#task
shortSpecial            = Task(
                            description="""
The High-Frequency Trader analyzes intraday price movements over the last 3 hours using 1-minute to 30-minute candlestick data to detect short-term trading opportunities. The pricing chart uses a JSON file.
This report focuses on scalping and day trading strategies.
""",
                            agent=shortMinSpecialist,
                            expected_output="""
Market Volatility Analysis (Last 3 Hours):
Price swings and rapid movements
Trading volume and liquidity assessment
The data should be analyzed with the "shortminprice.json" file included in the context.

Short-Term Technical Indicator Analysis:
Bollinger Bands, Stochastic Oscillator
Moving Averages (5, 10, 20)
Short-term support & resistance levels
Key Trading Signals & Patterns:
Recent buy/sell signals (Overbought/Oversold, Breakouts, Reversals)
Short-term candlestick pattern recognition
Trading Strategy:
Projected price action for the next 1-6 hours
Entry & exit strategies for short-term trades
Risk-reward analysis & emergency exit plans                           
""",
                            )



                            

riskManage              = Task(
                            description="""
The Risk Management Specialist monitors market volatility, portfolio risk, and specific cryptocurrency risks to maintain a secure trading environment.
This report provides early warnings, risk indicators, and defensive strategies to minimize potential losses.
                            """,
                            agent=riskManagement,
                            expected_output="""
Portfolio Risk Assessment:
Current risk level of held positions
Risk indicators (VaR, maximum potential loss)
Market Volatility Analysis:
Last 24-hour volatility and unusual price swings
Liquidity concerns and spread widening
Potential Risk Detection & Evaluation:
Risk of price crashes in specific assets
External threats (regulatory risks, large sell-offs)
Risk Mitigation Strategies:
Stop-loss levels & trigger points
Hedging strategies and position adjustments
Emergency alerts for high-risk situations
                            """,
                            )


headManage              = Task(
                            description="""
Provides detailed investment information about a Cryptocurrency based on reports from  'shortMinSpecialist', 'marketAnalyist', and 'riskManagement'. 
                        """,
                        agent=headManager,
                        expected_output="""
The starting amount is 100000KRW.
Your final answer must be a detailed recommendation, choosing between buying, selling, or holding the cryptocurrency. Provide a clear rationale for your recommendation.
The current balance of your account, the amount of cryptocurrency you own, the purchase price, the valuation, and the profit/loss of your account are in the “trading_info.json” file. You MUST check this file to determine the current situation. 
Also, you should not forget that there is a "0.05%" commission. All trades are executed in KRW or BTC.
You MUST should output the report as a json file in the following format. No specification is allowed except for the following format. There shouldn't be any characters outside of this format.
{"decision":"buy or sell or hold", "reason":"some technical reason and Provide a clear rationale for your recommendation."} 
                        """,
                        context=[
                            shortSpecial,
                            riskManage
                        ],
                        output_file="shortcoin_recommendation.json"
                        )


def excute_analysis():
    global decision

    crew = Crew(
        agents=[
            shortMinSpecialist,
            riskManagement,
            headManager
        ],
        tasks=[
            shortSpecial,
            riskManage,
            headManage
        ],
        verbose=True
    )
    result = crew.kickoff()

     # 파일을 열고 JSON 데이터 읽기
    with open("shortcoin_recommendation.json", "r") as file:
        data = file.read()

    # 백틱이 포함된 불필요한 문자가 있는지 확인
    if "```json" in data:
        # 불필요한 문자가 있으면 정규식을 사용하여 백틱 제거
        data_cleaned = re.sub(r'```json|```', '', data)

        try:
            # 정리된 데이터를 JSON으로 변환
            json_data = json.loads(data_cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON 디코딩 오류: {e}")
            return
    else:
        # 불필요한 문자가 없으면 그대로 JSON 파싱
        json_data = json.loads(data)

    # decision 값 추출
    decision = json_data.get("decision")

    # 결과 출력
    print(decision)


def run_every_10_minutes():
    while True:
        try:
            # 비트코인 뉴스, 가격 정보, 분석 및 매매 실행
            bitcoin_price("minute1", 180, "shortminprice")  # 분봉데이터 확인
            masu_avg()

            excute_analysis()  # 분석 시작
            upbit_trading()  # 매매 실행
        except Exception as e:
            print(f"Error occurred during execution: {e}")

        # 10분마다 (300초) 동안 대기
        time.sleep(300)


if __name__ == "__main__":
    run_every_10_minutes()