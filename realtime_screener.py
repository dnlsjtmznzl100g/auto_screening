# realtime_stock_screener.py
"""
📈 Yahoo Finance 실시간 스크리너 + 대시보드
버튼 클릭 → 데이터 수집 → 조건 필터링 → 시각화까지 자동 수행
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# -------------------------------------
# 🔧 기본 설정
# -------------------------------------
st.set_page_config(page_title="Realtime Stock Screener", layout="wide")
st.title("📊 실시간 주식 자동 스크리너 (Yahoo Finance API 기반)")

# 대상 티커 (예시로 미국 주요 종목)
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "UNH", "JNJ", "XOM",
    "PG", "HD", "PFE", "KO", "V", "MA", "PEP", "DIS", "INTC", "NFLX"
]

# -------------------------------------
# 🧮 데이터 수집 함수
# -------------------------------------
def get_financial_data(tickers):
    results = []
    for t in tickers:
        try:
            ticker = yf.Ticker(t)
            info = ticker.info
            financials = ticker.financials
            revenues = financials.loc["Total Revenue"]
            op_income = financials.loc["Operating Income"]

            # 최근 2개 연도 YoY 계산
            if len(revenues) >= 2 and len(op_income) >= 2:
                rev_yoy = (revenues[0] - revenues[1]) / revenues[1] * 100
                op_yoy = (op_income[0] - op_income[1]) / op_income[1] * 100
            else:
                rev_yoy = None
                op_yoy = None

            roce = info.get("returnOnCapitalEmployed", None)
            if roce:
                roce *= 100  # 비율로 변환

            results.append({
                "ticker": t,
                "name": info.get("longName", ""),
                "roce_pct": roce,
                "revenue_yoy_pct": rev_yoy,
                "op_income_yoy_pct": op_yoy
            })
        except Exception as e:
            print(f"{t} 오류: {e}")
    df = pd.DataFrame(results)
    df["pass_all"] = (
        (df["roce_pct"] >= 13)
        & (df["revenue_yoy_pct"] >= 15)
        & (df["op_income_yoy_pct"] >= 10)
    )
    return df

# -------------------------------------
# ⚙️ 사이드바 설정
# -------------------------------------
st.sidebar.header("⚙️ 설정")

tickers_input = st.sidebar.text_area(
    "대상 티커 리스트 (쉼표로 구분)",
    ", ".join(DEFAULT_TICKERS)
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

roce_min = st.sidebar.slider("ROCE 최소값 (%)", 0, 50, 13)
rev_min = st.sidebar.slider("매출 YoY 최소값 (%)", 0, 100, 15)
op_min = st.sidebar.slider("영업이익 YoY 최소값 (%)", 0, 100, 10)

# -------------------------------------
# 🚀 실행 버튼
# -------------------------------------
if st.button("🔍 실시간 스크리닝 실행"):
    with st.spinner("📡 Yahoo Finance에서 데이터를 수집 중입니다..."):
        df = get_financial_data(tickers)

    st.success(f"✅ {len(df)}개 기업 데이터 수집 완료!")
    st.session_state["data"] = df

# -------------------------------------
# 📊 결과 시각화
# -------------------------------------
if "data" in st.session_state:
    df = st.session_state["data"]

    # 필터 적용
    filtered = df[
        (df["roce_pct"] >= roce_min)
        & (df["revenue_yoy_pct"] >= rev_min)
        & (df["op_income_yoy_pct"] >= op_min)
    ]

    st.markdown(f"### 🎯 필터링된 기업 수: {len(filtered)} / {len(df)}")

    # 데이터프레임 표시
    st.dataframe(
        filtered[
            ["ticker", "name", "roce_pct", "revenue_yoy_pct", "op_income_yoy_pct"]
        ].sort_values(by="roce_pct", ascending=False),
        use_container_width=True,
    )

    # 상위 10개 ROCE 차트
    st.markdown("### 🏆 ROCE 상위 10개 기업")
    top_n = filtered.sort_values(by="roce_pct", ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top_n["ticker"], top_n["roce_pct"], color="skyblue")
    ax.set_xlabel("ROCE (%)")
    ax.invert_yaxis()
    st.pyplot(fig)

    # 매출 & 영업이익 YoY 비교
    st.markdown("### 📊 매출 & 영업이익 YoY 비교 (Top 10)")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(top_n["ticker"], top_n["revenue_yoy_pct"], label="Revenue YoY", alpha=0.7)
    ax2.bar(top_n["ticker"], top_n["op_income_yoy_pct"], label="Operating Income YoY", alpha=0.7)
    ax2.legend()
    st.pyplot(fig2)

    # CSV 다운로드
    st.download_button(
        label="💾 CSV로 저장",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="realtime_filtered_results.csv",
        mime="text/csv",
    )
else:
    st.info("👆 좌측 조건을 조정하고 [🔍 실시간 스크리닝 실행] 버튼을 눌러주세요.")
