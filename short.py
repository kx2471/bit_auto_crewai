from crewai import Crew, Agent, Task
from crewai.tools import tool
from crewai_tools import (FileReadTool, JSONSearchTool)
from openai import OpenAI
import pyupbit
import json
from langchain_openai import ChatOpenAI
import investmentJsonAppend
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

def masu_avg(ticker):

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
                            Analyze minute-by-minute charts of the past hour in real-time to spot short-term price movements and detect spikes or dips.
Develop and execute scalping trading strategies by identifying optimal entry and exit points to generate quick profits.
View charts and submit reports solely for profit.
                            """,
                            backstory="",
                            verbose=True,
                            llm=gpt,
                            tools=[minPrice_tool]
                                               
                        )



reflectiveExperts                  = Agent(
                            role="Self-reflective experts",
                            goal="""
                            The goal is for teams to analyze data on previous decisions they've made and analyze the expected and actual outcomes of those decisions to find ways to do things better if they met expectations, and to self-reflect on why they didn't, and to strengthen their thinking so they can improve.
                            """,
                            backstory="""With over 10 years of experience in behavioral finance and decision-making psychology, this expert specializes in analyzing trading outcomes and cognitive biases. Having worked with hedge funds and proprietary trading firms, they refine strategies by comparing expected vs. actual results. Proficient in data analytics and performance reviews, they drive continuous improvement. Their structured self-reflection approach strengthens traders' strategic thinking and adaptability.
                            """,
                           
                            verbose=True,
                            llm=gpt,
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
                            tools=[masu_tool],
                        )




#task
shortSpecial            = Task(
                            description="""
View and analyze 1-hour price chart data of Bitcoin to analyze the market, evaluate opportunities, recommend strategies, and formulate opinions.
""",
                            agent=shortMinSpecialist,
                            expected_output="""
1. market analysis (based on 1-hour chart)
Current BTC price and key volatility indicators (e.g. ATR, Bollinger Bands)
Key support/resistance levels and trend direction (up/down/sideways)
Volume changes and liquidity conditions

2. evaluate trading opportunities
Buy/Sell entry signals (e.g. momentum, breakout, reversal signals)
Estimated target price and stop loss (including Risk-Reward Ratio)
Other indicators to check (funding rate, open interest, etc.)

3. recommended strategies and opinions
The best trading strategy for the current market (e.g. scalping, breakout trading, counter-trend trading)
Recommended action, whether buy/sell/wait-and-see, and the rationale behind it
Success rate and reliability assessment of recent strategies                        
""",
                            )



                            

reflective              = Task(
                            description="""
Gather feedback on the head manager's buy, sell, and hold decisions and rationale over the past seven days, analyze them, and if you made a profit, analyze how you can do it better next time for greater profit, and if you lost money, self-reflect and come up with a better way to avoid losing money next time.
                            """,
                            agent=reflectiveExperts,
                            expected_output="""
1. Evaluate decisions
List of buy/sell/hold decisions made by the head manager in the last 7 days
Key data and market conditions on which the decision was based
Expected vs. actual outcome

2. Analyze the thought process
If the decision was right: what factors were valid?
If the decision was wrong: What factors did not work and why?
Recurring strengths and weaknesses in the head manager's decision-making patterns

3. Improvements and optimization strategies
Ways to improve to get closer to the right answer in the next analysis
Adjust how data is interpreted and refine decision-making frameworks
Suggestions for removing psychological biases and better thought processes
                            """,
                            )


headManage              = Task(
                            description="""
Based on the reports of 'shortMinSpecialist' and 'reflectiveExperts', you decide to buy, sell, or hold for short-term scalping Bitcoin. You know that you can only buy all, sell all, or hold, and you remember that the fee for each trade is “0.05%”. You check your current balance, see how much you bought, how much it went up, and how much it went down, and your goal is to make a profit, not lose money.
Then, you analyze the chart and calculate the price change since the previous trade was executed, the percentage loss, and the percentage loss including the commission (trade_outcome), and submit the psychological factors to the report (psychological_factors).  
""",
                        agent=headManager,
                        expected_output="""
example:
{
  "decision": "buy or sell or hold",
  "reason": "According to the ShortMinSpecialist report, BTC shows strong upward momentum and a high probability of breaking key resistance. The ReflectiveExperts report also indicates that breakout trades have had a 78% success rate recently. Current balance: 50,000 USDT, estimated BTC purchase: 0.98 (including fee).",
  "decision_factors": {
    "market_trend": "Strong uptrend",
    "volatility": "Medium",
    "shortMinSpecialist_signal": "Buy signal detected",
    "reflectiveExperts_analysis": "Recent breakout trade success rate: 78%"
  },
  "trade_outcome": {
    "price_change": "+0.5%",
    "PNL": "+250 KRW",
    "net_profit_after_fee": "+240 KRW"
  },
  "psychological_factors": {
    "confidence_level": "High",
    "market_uncertainty": "Low",
    "emotional_state": "More aggressive due to previous successful trade"
  }
}

                        """,
                        context=[
                            shortSpecial,
                            reflective
                        ],
                        output_file="shortcoin_recommendation.json"
                        )


def excute_analysis():
    global decision

    crew = Crew(
        agents=[
            shortMinSpecialist,
            reflectiveExperts,
            headManager
        ],
        tasks=[
            shortSpecial,
            reflective,
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
            masu_avg("KRW-BTC")
            excute_analysis()  # 분석 시작
            investmentJsonAppend.append_to_report_data() #Report.json 에 headmanger의 보고서 데이터 축적
            investmentJsonAppend.delete_old_data() #Report.json에서 7일지난 데이터 삭제
            upbit_trading()  # 매매 실행
        except Exception as e:
            print(f"Error occurred during execution: {e}")

        # 10분마다 (300초) 동안 대기
        time.sleep(300)


if __name__ == "__main__":
    run_every_10_minutes()