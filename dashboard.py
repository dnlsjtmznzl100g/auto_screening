# dashboard.py
"""
Streamlit 대시보드 for Yahoo Finance 스크리닝 결과
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Stock Screener Dashboard", layout="wide")

st.title("📈 주식 자동 스크리닝 대시보드 (Yahoo Finance 기반)")

# Load data
@st.cache_data
def load_data(path="results.csv"):
    df = pd.read_csv(path)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ results.csv 파일을 불러올 수 없습니다. 먼저 screen_yahoo_finance.py를 실행해주세요.\n{e}")
    st.stop()

# Sidebar filters
st.sidebar.header("📋 필터 설정")

roce_min = st.sidebar.slider("ROCE 최소값 (%)", 0, 50, 13)
rev_min = st.sidebar.slider("매출 YoY 최소값 (%)", 0, 100, 15)
op_min = st.sidebar.slider("영업이익 YoY 최소값 (%)", 0, 100, 10)
only_pass = st.sidebar.checkbox("스크리닝 통과 기업만 보기", True)

# Apply filters
filtered = df[
    (df["roce_pct"] >= roce_min)
    & (df["revenue_yoy_pct"] >= rev_min)
    & (df["op_income_yoy_pct"] >= op_min)
]
if only_pass:
    filtered = filtered[filtered["pass_all"] == True]

st.markdown(f"### 🎯 필터링된 기업 수: {len(filtered)} / {len(df)}")

# Display table
st.dataframe(
    filtered[
        [
            "ticker",
            "name",
            "roce_pct",
            "revenue_yoy_pct",
            "op_income_yoy_pct",
        ]
    ].sort_values(by="roce_pct", ascending=False),
    use_container_width=True,
)

# Top N chart
st.markdown("### 🏆 상위 10개 기업 (ROCE 기준)")
top_n = filtered.sort_values(by="roce_pct", ascending=False).head(10)

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(top_n["ticker"], top_n["roce_pct"], color="skyblue")
ax.set_xlabel("ROCE (%)")
ax.set_ylabel("Ticker")
ax.invert_yaxis()
st.pyplot(fig)

# Revenue & Operating Profit growth comparison
st.markdown("### 📊 매출 & 영업이익 YoY 비교 (Top 10)")
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.bar(top_n["ticker"], top_n["revenue_yoy_pct"], label="Revenue YoY", alpha=0.7)
ax2.bar(top_n["ticker"], top_n["op_income_yoy_pct"], label="Operating Income YoY", alpha=0.7)
ax2.set_ylabel("YoY Growth (%)")
ax2.legend()
st.pyplot(fig2)

# Download option
st.download_button(
    label="💾 필터링된 결과 다운로드 (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="filtered_results.csv",
    mime="text/csv",
)

st.success("✅ 데이터 로드 완료! 필터를 조정하며 조건에 맞는 기업을 분석해보세요.")
