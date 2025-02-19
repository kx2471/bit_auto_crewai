from crewai import Crew, Agent, Task
from crewai.tools import tool
from crewai_tools import (JSONSearchTool)
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
            if krw_balance is None: # 잔액을 가져오는데 실패한 경우
                print("Error: Could not retrieve KRW balance.")
                return

            buy_amount = krw_balance - 100
            if buy_amount < 0: # 매수 금액이 0보다 작은 경우
                print("Error: 잔액이 없어 구매할 수 없습니다.")
                return

            upbit.buy_market_order("KRW-BTC", buy_amount)
            print(f"Buy order placed for {buy_amount} KRW")

        elif decision == "sell":
            btc_balance = upbit.get_balance("BTC")
            if btc_balance is None: # 잔액을 가져오는데 실패한 경우
                print("Error: Could not retrieve BTC balance.")
                return
            if btc_balance == 0: # 잔액이 0인 경우
                print("Error: 잔액이 없어 판매할 수 없습니다.")
                return
            upbit.sell_market_order("KRW-BTC", btc_balance)
            print(f"Sell order placed for {btc_balance} BTC")

        elif decision is None: # decision이 None인 경우
            print("No decision made yet.")

        else:
            print(f"Hold 합니다.: {decision}")

    except Exception as e:
        print(f"Error occurred in upbit_trading: {type(e)}, {e}")

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
    profit_loss_percent = f"{round(profit_loss_percent, 3)}%"

    # 거래 내역 조회
    # "done" 상태 주문과 "cancel" 상태 주문을 각각 가져오기
    done_order_history = upbit.get_order("KRW-BTC", state="done", limit=15)
    cancel_order_history = upbit.get_order("KRW-BTC", state="cancel", limit=15)

    # 두 리스트 합치기
    combined_order_history = done_order_history + cancel_order_history

    # "created_at" 기준으로 최신순으로 정렬 (내림차순)
    sorted_order_history = sorted(combined_order_history, key=lambda x: x["created_at"], reverse=True)

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
        },
        "trade_history": sorted_order_history
    }

    # JSON 파일로 저장
    with open("trading_info.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("데이터가 JSON 파일로 저장되었습니다.")



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
report_data_tool = JSONSearchTool(json_path='./ReportData.json')
minPrice_tool = JSONSearchTool(json_path='./shortminprice.json')
trading_information_tool = JSONSearchTool(json_path='./trading_info.json')



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
                            tools=[report_data_tool]
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
                            tools=[trading_information_tool],
                        )




#task
shortSpecial            = Task(
                            description="""
View and analyze 1-hour price chart data of Bitcoin to analyze the market, evaluate opportunities, recommend strategies, and formulate opinions.


Analyze the past trading decisions stored in 'shortminprice.json'. 
The JSON file contains price data for the last 60 minutes at 1-minute intervals.
The structure of the data is as follows :

1.timestamp: The exact time when the trade occurred. The format is ISO 8601, which includes both the date and time.
2.open: The price at which the trading period began. This is the first trade price in the given time interval.
3.high: The highest price during the given time interval. It represents the peak price reached during that period.
4.low: The lowest price during the given time interval. It represents the bottom price reached during that period.
5.close: The last trade price of the given time interval. This is the price at the end of the trading period.
6.volume: The total amount of assets (such as stocks or contracts) traded during that time period. It represents the volume of trades in that interval.
7.value: The total value of the trades during that time period, calculated as volume * close. It represents the monetary value of the trades in the given interval.

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

You can check the headmanager's judgment records in 'ReportData.json'.
The structure of each data in ReportData.json is as follows.

"decision":
Explanation: The trader's final decision or action taken in relation to the trade.

"reason":
Explanation: The reasoning behind the decision made by the trader. For example, if the market is in a sideways trend with no clear momentum, the trader might decide to "hold" and wait for a breakout or reversal.

"decision_factors":
Explanation: The key factors influencing the trader's decision.
"market_trend": The overall trend of the market. For example, "Sideways trend" indicates the market is moving horizontally, with no strong upward or downward movement.
    "volatility": The level of market volatility. For example, "Medium" suggests a moderate level of market fluctuation.
    "shortMinSpecialist_signal": A signal from a short-term market specialist. For example, "No clear momentum" means there is no discernible market momentum.
    "reflectiveExperts_analysis": The analysis provided by reflective experts. For example, "Cautious approach advised" suggests waiting for a breakout or reversal before making a move.

"trade_outcome":
Explanation: Information regarding the outcome of the trade.
    "price_change": The percentage change in price after the trade. For example, "0%" indicates no change in price.
    "PNL": The profit or loss generated from the trade. For example, "0 KRW" means there was no profit or loss from the trade.
    "net_profit_after_fee": The net profit after deducting any trading fees. For example, "0 KRW" means no net profit after fees.

"psychological_factors":
Explanation: The psychological and emotional state of the trader that could influence the decision.
    "confidence_level": The trader's level of confidence in the market. For example, "Medium" suggests moderate confidence.
    "market_uncertainty": The level of uncertainty in the market. For example, "High" indicates significant uncertainty in the market conditions.
    "emotional_state": The trader's emotional state based on current market conditions. For example, "Cautious due to current market indecision" means the trader is feeling cautious due to the market's indecisive nature.
"timestamp": When you made the judgment

                            """,
                            agent=reflectiveExperts,
                            expected_output="""
1. Analyze the thought process
If the decision was right: what factors were valid?
If the decision was wrong: What factors did not work and why?
Recurring strengths and weaknesses in the head manager's decision-making patterns

2. Improvements and optimization strategies
Ways to improve to get closer to the right answer in the next analysis
Adjust how data is interpreted and refine decision-making frameworks
Suggestions for removing psychological biases and better thought processes
                            """,
                            )


headManage              = Task(
                            description="""
The starting amount is 100000 KRW.
Based on the reports of 'shortMinSpecialist' and 'reflectiveExperts', you decide to buy, sell, or hold for short-term scalping Bitcoin. You know that you can only buy all, sell all, or hold, and you remember that the fee for each trade is “0.05%”. You check your current balance, see how much you bought, how much it went up, and how much it went down, and your goal is to make a profit, not lose money.
Then, you analyze the chart and calculate the price change since the previous trade was executed, the percentage loss, and the percentage loss including the commission (trade_outcome), and submit the psychological factors to the report (psychological_factors).  

You can look at your previous transaction history to determine if you're holding Bitcoin now or not. For example, if the “side” value of the most recent transaction is bid, you have bitcoin, and if it is ask, you don't have bitcoin.

In 'trading_info.json' you can see your current holdings, average bid price, drawdown, etc. and your trading history.
 The structure of each data in 'trading_info.json' is as follows:

"my_balances":
    "currency": The trading pair being used. It refers to the two assets being traded (e.g., KRW-BTC).
    "balance": The amount of the asset currently held.
    "avg_buy_price": The average price at which the asset was purchased.
    "buy_amount": The total amount spent to purchase the asset.
    "est_value": The estimated value of the asset based on the current market price.
    "profit_loss": The current profit or loss from the asset trade.
    "profit_loss_percent": The percentage of profit or loss.

"trade_history" (an array that can include multiple trade records)
    "uuid": A unique identifier for the trade.
    "side": Indicates the direction of the trade. For example, "ask" represents a sell order, while "bid" would represent a buy order.
    "ord_type": Specifies the type of order, such as "market" for a market order.
    "avg_price": The average price at which the trade was executed.
    "state": Represents the status of the order. "done" indicates that the order has been completed.
    "market": Denotes the market or trading pair where the trade took place.
    "created_at": The date and time when the order was created, formatted in ISO 8601.
    "volume": The total volume of the asset included in the order.
    "remaining_volume": The volume of the order that has not yet been executed.
    "reserved_fee": The fee amount that has been reserved for the trade.
    "remaining_fee": The fee amount that has not yet been charged or deducted.
    "paid_fee": The fee amount that has already been paid.
    "locked": The amount of funds that are locked due to the trade.
    "executed_volume": The volume of the asset that was actually executed in the trade.
    "trades_count": The number of individual trades that were involved in filling the order.
    "application_name": The name of the application or API that initiated the order.
    "thirdparty": A Boolean value indicating whether the trade was executed via a third-party service.
    "is_cancel_and_newable": A Boolean value that shows whether the order can be canceled and replaced with a new one.

""",
                        agent=headManager,
                        expected_output="""
example:
{
  "decision": "The final decision made by the head manager based on the analysis. Possible values: "buy", "sell", "hold"
",
  "reason": "The rationale behind the decision made. It explains the thought process or market conditions that led to the decision.",
  "decision_factors": {
    "market_trend": "Describes the overall market movement (e.g., "uptrend", "downtrend", "sideways").",
    "volatility": "Represents the level of price fluctuations (e.g., "high", "medium", "low").",
    "shortMinSpecialist_signal": "The signal or analysis from the short-term scalping expert (e.g., "No clear momentum", "Buy signal detected").",
    "reflectiveExperts_analysis": "Insights provided by the reflective experts, which may suggest a cautious approach or a particular market condition to be aware of. (e.g, 78%)"
  },
  "trade_outcome": {
    "price_change": "The percentage of profit or loss from the starting amount to the current price. (((est_value(If est_value is 0, the value of KRW_balance in my_balances) - 100000(starting amount)) / starting amount) * 100 ). Denoted by +,- symbols.",
    "PNL": "The current profit or loss from the asset trade. Equal to the value of “profit_loss” in the “trading_info.json” file. but Denoted by +,- symbols.
    "net_profit_after_fee": "“PNL” to limit the fee to the price. The amount of realized profit after the trade. ("PNL" - fee)"
  },
  "psychological_factors": {
    "confidence_level": "The trader's confidence in the current decision and market outlook (e.g., "high", "medium", "low").",
    "market_uncertainty": "The level of uncertainty in the market (e.g., "high", "medium", "low").",
    "emotional_state": "The emotional condition of the trader (e.g., "cautious", "aggressive", "calm"), often influenced by market conditions and previous trades."
  }
}

                        """,
                        context=[
                            shortSpecial,
                            reflective
                        ],
                        output_file="shortcoin_recommendation.txt"
                        )


def jsonkey():  #shortcoin_recommendation 을 current_recommendation.json으로 변환하는 함수
    # 원본 TXT 파일과 저장할 JSON 파일 경로
    source_file = "shortcoin_recommendation.txt"
    destination_file = "current_recommendation.json"

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

        print(f"데이터가 {destination_file}에 저장되었습니다!")
    except json.JSONDecodeError as e:
        print(f"JSON 변환 오류: {e}")

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

def get_decision():
    global decision
    try:
        with open("current_recommendation.json", "r") as file:
            data = json.load(file)
            decision_value = data.get("decision")

            if decision_value is None:
                print("Warning: 'decision' key not found in current_recommendation.json")
                decision = None  # 또는 다른 기본값 설정
            else:
                decision = str(decision_value)  # 문자열로 명시적 형변환
                print(f"Decision: {decision}")

    except FileNotFoundError:
        print("Error: current_recommendation.json not found.")
        decision = None  # 파일이 없을 경우 decision을 None으로 설정
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        decision = None  # JSON 파싱 오류 시 decision을 None으로 설정
    except Exception as e: # 그 외의 에러
        print(f"Error occurred in get_decision: {e}")
        decision = None    


def run_every_5_minutes():
    while True:
        try:
            # 비트코인 뉴스, 가격 정보, 분석 및 매매 실행
            bitcoin_price("minute1", 30, "shortminprice")  # 분봉데이터 확인
            balance_current("KRW-BTC")
            excute_analysis()  # 분석 시작
            jsonkey() #cuurent decision값 확인하는과정
            get_decision()
            upbit_trading()  # 매매 실행
            investmentJsonAppend.append_to_report_data() #Report.json 에 headmanger의 보고서 데이터 축적
            investmentJsonAppend.delete_old_data() #Report.json에서 7일지난 데이터 삭제
        except Exception as e:
            print(f"Error occurred during execution: {type(e)}, {e}")

        # 5분마다 (300초) 동안 대기
        time.sleep(300)


if __name__ == "__main__":
    run_every_5_minutes()