from crewai import Crew, Agent, Task
import crewai_tools
from openai import OpenAI
import pyupbit
import os 
from dotenv import load_dotenv
load_dotenv()

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
dayweekSpecialist             = Agent(
                            role="Daily & Weekly Chart Specialist",
                            goal="""
                            Every morning, meticulously analyze 90 days of daily charts and 10 weeks of weekly charts to grasp the overall market trend and momentum.
                            Identify trends, momentum, key support/resistance levels and, based on these insights, propose mid-to-long-term trading strategies to set the team's investment direction.
                            """,
                            backstory="""
                            A veteran with over 5 years of experience in technical analysis, holding a background in financial engineering and having worked with various investment institutions.
                            Each morning, digs deep into the charts using various technical indicators such as moving averages, candlestick patterns, RSI, and MACD to uncover hidden patterns and minute price changes.
                            Drawing on past experiences at major investment firms, excels at reading the unique volatility and complex patterns inherent in the cryptocurrency market, ensuring the team never misses a major market trend.
                            """,
                        )


shortMinSpecialist             = Agent(
                            role="Short-Term Scalping Specialist",
                            goal="""
                            In real-time, analyze the last 5 hours of minute-based charts to capture short-term price fluctuations and detect sudden spikes or drops.
                            Develop and execute scalping trading strategies by identifying optimal entry and exit points to generate rapid profits.
                            """,
                            backstory="",
                            verbose=True,
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
                        )

fundAnalyist                    = Agent(
                            role="Crypto Fundamental Analyst",
                            goal="""
                            Conduct in-depth analyses of the economic value, technological capabilities, and market positioning of the three assigned cryptocurrencies, assessing their long-term growth potential and intrinsic value.
                            Evaluate key factors such as the development team, roadmap, tokenomics, and on-chain data to devise a stable investment strategy that remains robust against short-term market fluctuations.
                            """,
                            backstory="""
                            A specialist with over 7 years of research experience in blockchain and cryptocurrency, meticulously scrutinizing whitepapers, partnerships, and technical progress across various projects.
                            Combines academic research with hands-on experience to focus on the intrinsic value and real-world utility of coins, using on-chain data and network activity as indicators of overall market health.
                            Diligently tracks whale movements and large-scale investor trends to propose long-term investment strategies based on fundamental value rather than mere price volatility.
                            """,
                            verbose=True,
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
                        )                         


#crewai Task설정
dayweekSpecial          = Task(
                            description="",
                            agent=dayweekSpecialist
                            expected_output="",
                            )

shortSpecial            = Task(
                            description="",
                            agent=shortMinSpecialist
                            expected_output="",
                            )

marketAnalysis          = Task(
                            description="",
                            agent=marketAnalyist
                            expected_output="",
                            )

fundAnalysis            = Task(
                            description="",
                            agent=fundAnalyist
                            expected_output="",
                            )

riskManage              = Task(
                            description="",
                            agent=riskManagement
                            expected_output="",
                            )