from crewai import Crew, Agent, Task
from crewai.tools import tool
from crewai_tools import (FileReadTool, JSONSearchTool)
from openai import OpenAI
import pyupbit
import json
from langchain_openai import ChatOpenAI
import yfinance as yf
import time
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




#GPT 모델, API설정

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY")) #OpenAI api키
OPENAI_MODEL_NAME = "gpt-4o-mini"

gpt = ChatOpenAI(api_key=OPENAI_API_KEY, model=OPENAI_MODEL_NAME, temperature=0.8, max_completion_tokens=5000)


#비트코인에 대한 뉴스를 확인하여 news.json으로 반환하는 함수
def bitcoin_news(ticker_symbol: str):
    """Provide the latest news for a given ticker. The ticker_symbol is the name of a cryptocurrency news. example : "BTC-KRW" """
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        
        if news:
            with open("news.json", "w", encoding="utf-8") as file:
                json.dump(news, file, ensure_ascii=False, indent=4)
            return "뉴스가 'news.json' 파일에 저장되었습니다."
        else:
            return "해당 티커에 대한 뉴스가 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"
    

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

marketAnalyist                  = Agent(
                            role="Market News Analyst",
                            goal="""
                            Monitor real-time news, regulatory updates, and major industry events daily, swiftly collecting and analyzing crucial information related to the three assigned cryptocurrencies.
                            Evaluate market sentiment by analyzing elements such as FUD (Fear, Uncertainty, Doubt) and FOMO (Fear of Missing Out), ensuring the team is well-prepared to respond to rapid market changes driven by external events.
                            """,
                            backstory="""
                            An expert with over 5 years of industry experience, known for carefully reading and analyzing financial and blockchain-related news.
                            Leverages a diverse range of sources—including Twitter, CoinDesk, exchange announcements, and government releases—to ensure no breaking news is missed, and excels at understanding the nuance and deeper implications behind each news item.
                            Goes beyond mere news aggregation by forecasting the potential impact of news on market prices, providing the team with actionable strategies to respond promptly to shifts in market sentiment.
                            """,
                            verbose=True,
                            llm=gpt,
                            tools=[json_tool],
                        
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

                            Translated with DeepL.com (free version)
                            """,
                            verbose=True,
                            llm=gpt
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


marketAnalysis          = Task(
                            description="""
The News Analyst tracks the latest 24-hour news, regulatory updates, and macroeconomic events affecting the crypto market.
This report helps assess the impact of news on price movements and investor sentiment.
                            """,
                            agent=marketAnalyist,
                            expected_output="""
Read the news articles in the JSON file and analyze them, focusing on the following questions.
The data should be analyzed with the "shortnews.json" file included in the context.

Analyzing market psychology:
FOMO (fear of missing out) vs. FUD (fear, uncertainty, doubt) metrics
Social media trends, search volume spikes
News impact assessment:
How a specific news event affects prices in the short and long term
Comparison to similar events in the past
Strategic response planning:
Identifying buying opportunities following positive news
Risk management strategies for negative news
Short-term volatility forecasting and contingency planning
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
Provides detailed investment information about a Cryptocurrency based on reports from 'dayweekSpecialist', 'shortMinSpecialist', 'marketAnalyist', 'fundAnalyist', and 'riskManagement'. 
                        """,
                        agent=headManager,
                        expected_output="""
Your final answer must be a detailed recommendation, choosing between buying, selling, or holding the cryptocurrency. Provide a clear rationale for your recommendation.
You should also remember that there is a "0.05%" commission on trades, and you should take this into account when deciding on your trading plan.
You MUST should output the report as a json file in the following format. No specification is allowed except for the following format.
{"decision":"buy or sell or hold", "reason":"some technical reason"}
                        """,
                        context=[
                            shortSpecial,
                            marketAnalysis,
                            riskManage
                        ],
                        output_file="shortcoin_recommendation.json"
                        )


def excute_analysis():
    global decision

    crew = Crew(
        agents=[
            shortMinSpecialist,
            marketAnalyist,
            riskManagement,
            headManager
        ],
        tasks=[
            shortSpecial,
            marketAnalysis,
            riskManage,
            headManage
        ],
        verbose=True
    )
    result = crew.kickoff()

    # 파일을 열고 JSON 데이터 읽기
    with open("shortcoin_recommendation.json", "r") as file:
        data = json.load(file)

    decision = data.get("decision")

    # 결과 출력
    print(decision)


def run_every_10_minutes():
    while True:
        # 비트코인 뉴스, 가격 정보, 분석 및 매매 실행
        bitcoin_news("BTC")  # 비트코인 뉴스 모음
        bitcoin_price("minute1", 180, "shortminprice")  # 분봉데이터 확인

        excute_analysis()  # 분석 시작
        upbit_trading()  # 매매 실행
        
        # 10분마다 (600초) 동안 대기
        time.sleep(600)  # 900초 = 15분



if __name__ == "__main__":
    run_every_10_minutes()