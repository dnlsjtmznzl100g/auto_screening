import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

# -----------------------------
# 1️⃣ Helper functions 왜 커밋이 안돼
# -----------------------------

def load_tickers(filename="tickers.txt", limit=100):
    """tickers.txt에서 티커 불러오기 (기본 5개 테스트용)"""
    with open(filename, "r") as f:
        tickers = [line.strip() for line in f.readlines()]
    return tickers[:limit]  # 너무 많으면 API 제한 걸릴 수 있으므로 제한

def get_financial_data(ticker):
    """
        ticker: 티커명
        return { # dataFrame으로 저장
            "Ticker": ticker,
            "Latest_Cross_day": cross_days[-1].index.date,
        }
    """
    
    try:
        t = yf.Ticker(ticker)
        df = yf.download(ticker, start="2025-01-01")# 주가 자료
        
        # 이동평균 계산
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # 어제와 오늘의 이동평균선 비교로 '골든크로스' 탐지
        df['Cross'] = (df['MA20'].shift(1) < df['MA60'].shift(1)) & (df['MA20'] > df['MA60'])


        # 골든크로스 발생일 출력
        cross_days = df[(df['Cross'] == True)]
        print("\n📈 골든크로스 발생일:")
        a = str(cross_days.tail(1).index.date)
        a = (a[15:len(a)-2])
        
        return {
            "Ticker": ticker,
            "Latest_Cross_day": a
        }

    except Exception as e:
        print(f"{t}의 이동평균선 계산 과정에서 문제가 발생했습니다.")
        print(e)
        return None

# -----------------------------
# 2️⃣ Streamlit App
# -----------------------------

st.set_page_config(page_title="NASDAQ 자동 스크리너", layout="wide")
st.title("📈 NASDAQ 자동 주식 스크리너")
st.caption("조건: 20일이 60일을 역전")

if st.button("데이터 수집 및 스크리닝 실행"):
    tickers = load_tickers("tickers.txt", limit=3)  # 초기엔 20개만 시도
    st.write(f"총 {len(tickers)}개 종목 수집 중...")

    results = []
    progress = st.progress(0)

    for i, ticker in enumerate(tickers):
        data = get_financial_data(ticker)
        
        if data:
            results.append(data)
        progress.progress((i + 1) / len(tickers))

    df = pd.DataFrame(results)
    if not df.empty:
        filtered = df
        print(filtered)

        st.success(f"✅ 스크리닝 완료 — 골드 크로스 주가 {len(filtered)}개 발견")
        st.dataframe(filtered, use_container_width=True)


        # CSV 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"screening_result_{timestamp}.csv"
        filtered.to_csv(filename, index=False)
        #st.download_button("📥 결과 CSV 다운로드", data=filtered.to_csv(index=False), file_name=filename)
    else:
        st.error("❌ 데이터를 불러오지 못했습니다.")

