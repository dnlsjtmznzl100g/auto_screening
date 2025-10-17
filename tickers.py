import FinanceDataReader as fdr
ticker_flag = False
ticker_list = ['NASDAQ','NYSE','AMEX','S&P500','KOSPI','KOSDAQ' ]

def tickers(idx: str):
    if idx not in ticker_list:
        print("please enter right index",ticker_list)
    return False

    # NASDAQ 상장사 전체 불러오기
    df = fdr.StockListing(idx)

    # 티커(symbol)만 추출
    tickers = df['Symbol'].tolist()

    # 파일로 저장
    with open("tickers.txt", "w") as f:
        for ticker in tickers:
            f.write(ticker + "\n")

    print(f"✅ {len(tickers)}개의 NASDAQ 종목을 tickers.txt로 저장했습니다.")
    return True
#======================================
df = fdr.StockListing(idx)

    # 티커(symbol)만 추출
tickers = df['Symbol'].tolist()

    # 파일로 저장
with open("tickers.txt", "w") as f:
        for ticker in tickers:
            f.write(ticker + "\n")

    print(f"✅ {len(tickers)}개의 NASDAQ 종목을 tickers.txt로 저장했습니다.")
