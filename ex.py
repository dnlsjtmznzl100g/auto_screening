"""
import FinanceDataReader as fdr
stocks = fdr.StockListing('Nasdaq')# dataframe type

import FinanceDataReader as fdr

# Apple(AAPL)의 2020년 주식 가격 데이터 로드
df = fdr.DataReader('AAPL', '2020')

# KOSPI 지수 데이터 로드
kospi = fdr.DataReader('KS11', '2020')

print(df.head())  # 데이터의 처음 몇 줄을 출력
print(kospi.head())
#=========================================================================
"""
"""
import pandas as pd
pd.set_option('display.max_rows', None)
# col 생략 없이 출력
pd.set_option('display.max_columns', None)

tk_list = ['NVDA','AAPL',"MSFT"]
import yfinance as yf
for ticker in tk_list:
    t = yf.Ticker(ticker)
    fin = t.financials  # 손익계산서 (annual)
    bs = t.balance_sheet  # 재무상태표
    print("===========================================================")
    #print("fin",type(fin))
    print("===========================================================")
    #print("bs",bs),

    # roce 구하기 =============================================================
    ebit = fin.loc["EBIT"].iloc[0]
    print("ebit",ebit)
    
    total_assets = bs.loc["Total Assets"].iloc[0]
    print("total_assets",total_assets)
    
    current_liabilities = bs.loc["Current Liabilities"].iloc[0]
    print("current_liabilities",current_liabilities)

    roce = (ebit / (total_assets - current_liabilities)) * 100
    print("roce:",roce)
"""

# =============== 이평선 골든 크로스 날짜 출력하기 ========================
import pandas as pd
import yfinance as yf

# 예시: 삼성전자 (005930.KS)
ticker = "AAPL"
df = yf.download(ticker, start="2025-01-01")

# 이동평균 계산
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA60'] = df['Close'].rolling(window=60).mean()

# 어제와 오늘의 이동평균선 비교로 '골든크로스' 탐지
df['Cross'] = (df['MA20'].shift(1) < df['MA60'].shift(1)) & (df['MA20'] > df['MA60'])

# 골든크로스 발생일 출력
cross_days = df[df['Cross'] == True]

print("\n📈 골든크로스 발생일:")
print(cross_days.tail(1).index.date)
a = str(cross_days.tail(1).index.date)
a = (a[15:len(a)-2])
y,m,d = a.split(",")
print(y,m,d)
#============================================================
