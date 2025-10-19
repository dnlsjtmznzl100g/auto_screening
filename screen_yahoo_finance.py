# stock_screening_dashboard.py
import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

# -----------------------------
# 1️⃣ Helper functions
# -----------------------------

def load_tickers(filename="tickers.txt", limit=5):
    """tickers.txt에서 티커 불러오기 (기본 5개 테스트용)"""
    with open(filename, "r") as f:
        tickers = [line.strip() for line in f.readlines()]
    return tickers[:limit]  # 너무 많으면 API 제한 걸릴 수 있으므로 제한

def get_financial_data(ticker: str):
    """
    ticker: ticker 명 (ex:"AAPL")
    return # dataFrame으로 받기 위함
        {
            "Ticker": ticker,
            "ROCE": round(roce, 2),
            "Revenue YoY": round(revenue_yoy, 2),
            "Operating YoY": round(op_yoy, 2),
        }
    """
    print(ticker)
    try:
        t = yf.Ticker(ticker)
        fin = t.financials  # 손익계산서 (annual)
        bs = t.balance_sheet  # 재무상태표

        if fin.empty or bs.empty:
            print(f"{t}의 손익계산서 or 재무상태표가 비어있습니다.")
            return None

        # 필요한 지표 계산
        ebit = fin.loc["EBIT"].iloc[0]
        #print("ebit",ebit)
    
        total_assets = bs.loc["Total Assets"].iloc[0]
        #print("total_assets",total_assets)
    
        current_liabilities = bs.loc["Current Liabilities"].iloc[0]
        #print("current_liabilities",current_liabilities)

        roce = (ebit / (total_assets - current_liabilities)) * 100
        #print("roce:",roce)

        # YoY 계산
        # YoY 계산 (연도 명시)
        rev = fin.loc["Total Revenue"]
        op_income = fin.loc["Operating Income"]

        if len(rev) >= 2 and len(op_income) >= 2:
            years = rev.index.to_list()
            revenue_yoy = ((rev[years[0]] - rev[years[1]]) / rev[years[1]]) * 100
            op_yoy = ((op_income[years[0]] - op_income[years[1]]) / op_income[years[1]]) * 100
        else:
            revenue_yoy, op_yoy = None, None

        return {
            "Ticker": ticker,
            "ROCE": round(roce, 2),
            "Revenue YoY": round(revenue_yoy, 2),
            "Operating YoY": round(op_yoy, 2),
        }

    except Exception:
        print(f"{t}의 roce 및 yoy 계산 과정에서 문제가 발생했습니다.")
        return None

# -----------------------------
# 2️⃣ Streamlit App
# -----------------------------

st.set_page_config(page_title="NASDAQ 자동 스크리너", layout="wide")
st.title("📈 NASDAQ 자동 주식 스크리너")
st.caption("조건: ROCE ≥ 13%, 매출 YoY ≥ 15%, 영업이익 YoY ≥ 10%")

if st.button("데이터 수집 및 스크리닝 실행"):
    tickers = load_tickers("tickers.txt", limit=5)  # 초기엔 100개만 시도
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
        filtered = df[
            (df["ROCE"] >= 13) & # bitwise 연산
            (df["Revenue YoY"] >= 15) &
            (df["Operating YoY"] >= 10)
        ]
        unfiltered = df[
            (df["ROCE"] >= 13) & # bitwise 연산
            (df["ROCE"] < 13) | 
            (df["Revenue YoY"] < 15) |
            (df["Operating YoY"] < 10)
        ]

        st.success(f"✅ 스크리닝 완료 — 조건 충족 기업 {len(filtered)}개 발견")
        st.dataframe(filtered, use_container_width=True)

        st.success(f"✅ 스크리닝 완료 — 조건 불충족 기업 {len(unfiltered)}개 발견")
        st.dataframe(unfiltered, use_container_width=True)

        # CSV 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"screening_result_{timestamp}.csv"
        filtered.to_csv(filename, index=False)
        #st.download_button("📥 결과 CSV 다운로드", data=filtered.to_csv(index=False), file_name=filename)
    else:
        st.error("❌ 데이터를 불러오지 못했습니다.")
