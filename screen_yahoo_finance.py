# screen_yahoo_finance.py
"""
요구사항:
 - ROCE >= 13%
 - revenue YoY >= 15% AND operating income YoY >= 10%

사용법:
 1) 가상환경에서: pip install yfinance pandas numpy requests lxml
 2) 실행: python screen_yahoo_finance.py
    (동일 폴더에 tickers.txt 가 있으면 그걸 사용합니다. 없으면 S&P500 목록을 위키에서 가져옵니다.)
출력:
 - results.csv (스크리닝 결과)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from io import StringIO
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------------------------
# 설정 (필요시 변경)
# -------------------------
OUTPUT_CSV = "results.csv"
MIN_ROCE_PCT = 13.0
MIN_REV_YOY_PCT = 15.0
MIN_OP_YOY_PCT = 10.0

# User can supply tickers.txt (one ticker per line). If not present, script fetches S&P500 list from Wikipedia.
TICKERS_FILE = "tickers.txt"

# -------------------------
# 헬퍼: S&P500 리스트 가져오기 (위키)
# -------------------------
def fetch_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    logging.info("Fetching S&P500 tickers from Wikipedia...")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    tables = pd.read_html(r.text)
    # 첫 번째 테이블이 구성종목 표
    df = tables[0]
    tickers = df['Symbol'].tolist()
    # 몇몇 티커에 '.' 포함된 경우 yfinance가 '-'로 처리할 때가 있음. yfinance는 일반적으로 '.' 허용하지만 예외있음.
    tickers = [t.replace('.', '-') for t in tickers]
    logging.info(f"Fetched {len(tickers)} tickers.")
    return tickers

# -------------------------
# 헬퍼: 안전하게 여러 라벨 시도하여 항목 뽑기
# -------------------------
def get_row_safe(df, candidates):
    """
    df: pandas DataFrame with index labels (strings)
    candidates: list of possible label names in preferred order
    returns: pd.Series (the row) or None
    """
    if df is None or df.empty:
        return None
    for c in candidates:
        if c in df.index:
            return df.loc[c]
    # try case-insensitive contains
    idx_lower = [i.lower() for i in df.index.astype(str)]
    for c in candidates:
        c_l = c.lower()
        for i, il in enumerate(idx_lower):
            if c_l == il or c_l in il or il in c_l:
                return df.iloc[i]
    return None

# -------------------------
# 메인: 티커 하나 처리
# -------------------------
def analyze_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        # 회사명
        name = t.info.get('shortName') or t.info.get('longName') or ""
    except Exception as e:
        logging.warning(f"{ticker}: yfinance Ticker init failed: {e}")
        return None

    # financials: annual (columns are years as Timestamp or str; rows are items like 'Total Revenue', 'Operating Income')
    try:
        fin = t.financials  # DataFrame: rows = items, cols = years (newest col usually left)
        bs = t.balance_sheet
    except Exception as e:
        logging.warning(f"{ticker}: failed to fetch financials/balance_sheet: {e}")
        return None

    # if empty -> skip
    if fin is None or fin.empty or bs is None or bs.empty:
        logging.info(f"{ticker}: missing financials or balance sheet, skipping.")
        return None

    # Normalize columns order by chronological (old -> new) using column names (which are Timestamps or strings)
    try:
        # columns might be Timestamp; convert to str of year
        cols = [str(c.year) if hasattr(c, "year") else str(c) for c in fin.columns]
        fin.columns = cols
        bs_cols = [str(c.year) if hasattr(c, "year") else str(c) for c in bs.columns]
        bs.columns = bs_cols
        # choose the latest two years present
        years = sorted([int(c) for c in fin.columns if c.isdigit()])
        if len(years) < 2:
            logging.info(f"{ticker}: less than 2 years of financials, skipping.")
            return None
        latest = str(years[-1])
        prev = str(years[-2])
    except Exception as e:
        logging.debug(f"{ticker}: column parsing issue: {e}")
        # fallback: use original order (take first two columns)
        try:
            cols = list(fin.columns)
            latest = str(cols[0])
            prev = str(cols[1]) if len(cols) > 1 else None
        except Exception:
            return None

    # fetch revenue row (try multiple label variants)
    revenue_row = get_row_safe(fin, ['Total Revenue', 'Revenue', 'Revenues', 'Total revenues', 'TotalRevenue'])
    opinc_row = get_row_safe(fin, ['Operating Income', 'Operating income', 'Income From Continuing Operations', 'OperatingIncome', 'OperatingProfit'])
    if revenue_row is None or opinc_row is None:
        logging.info(f"{ticker}: revenue or operating income row not found, skipping.")
        return None

    # get latest and prev numeric values (some series may have NaN)
    try:
        rev_latest = revenue_row.get(latest, np.nan)
        rev_prev = revenue_row.get(prev, np.nan)
        op_latest = opinc_row.get(latest, np.nan)
        op_prev = opinc_row.get(prev, np.nan)
    except Exception as e:
        logging.info(f"{ticker}: error extracting numbers: {e}")
        return None

    # Check numeric validity
    if pd.isna(rev_latest) or pd.isna(rev_prev) or pd.isna(op_latest) or pd.isna(op_prev):
        logging.info(f"{ticker}: missing latest/prev values for rev/op. skipping.")
        return None

    # compute YoY %
    try:
        rev_yoy = (float(rev_latest) - float(rev_prev)) / abs(float(rev_prev)) * 100.0
    except Exception:
        rev_yoy = None
    try:
        op_yoy = (float(op_latest) - float(op_prev)) / abs(float(op_prev)) * 100.0
    except Exception:
        op_yoy = None

    # Balance sheet: get Total Assets and Total Current Liabilities (latest year)
    # bs rows examples: 'Total Assets', 'Total assets', 'TotalCurrentLiabilities', 'Current Liabilities'
    assets_row = get_row_safe(bs, ['Total Assets', 'Assets', 'totalAssets', 'Total assets'])
    curr_liab_row = get_row_safe(bs, ['Total Current Liabilities', 'Current Liabilities', 'Total current liabilities', 'Current Liabilities & Short Term Debt', 'currentLiabilities'])
    if assets_row is None or curr_liab_row is None:
        logging.info(f"{ticker}: balance sheet rows missing -> can't compute ROCE. skipping.")
        return None

    # extract latest values from bs (bs columns aligned similar to fin)
    try:
        assets_latest = assets_row.get(latest, np.nan)
        curr_liab_latest = curr_liab_row.get(latest, np.nan)
    except Exception:
        logging.info(f"{ticker}: unable to read bs latest values.")
        return None

    if pd.isna(assets_latest) or pd.isna(curr_liab_latest):
        logging.info(f"{ticker}: bs latest asset/liab missing, skipping.")
        return None

    # compute ROCE = Operating Income / (Total Assets - Current Liabilities) *100
    try:
        capital_employed = float(assets_latest) - float(curr_liab_latest)
        if capital_employed == 0:
            logging.info(f"{ticker}: capital employed zero -> skip.")
            return None
        roce = float(op_latest) / capital_employed * 100.0
    except Exception as e:
        logging.info(f"{ticker}: ROCE calc error: {e}")
        return None

    # assemble result
    result = {
        "ticker": ticker,
        "name": name,
        "year_latest": latest,
        "year_prev": prev,
        "revenue_latest": float(rev_latest),
        "revenue_prev": float(rev_prev),
        "revenue_yoy_pct": rev_yoy,
        "op_income_latest": float(op_latest),
        "op_income_prev": float(op_prev),
        "op_income_yoy_pct": op_yoy,
        "total_assets_latest": float(assets_latest),
        "current_liabilities_latest": float(curr_liab_latest),
        "capital_employed": capital_employed,
        "roce_pct": roce
    }
    # rule pass?
    result["pass_roce"] = roce >= MIN_ROCE_PCT
    # ensure revenue/op yoy not None
    result["pass_revenue_yoy"] = (rev_yoy is not None) and (rev_yoy >= MIN_REV_YOY_PCT)
    result["pass_op_yoy"] = (op_yoy is not None) and (op_yoy >= MIN_OP_YOY_PCT)
    result["pass_all"] = result["pass_roce"] and result["pass_revenue_yoy"] and result["pass_op_yoy"]

    return result

# -------------------------
# 루프: 모든 티커 처리
# -------------------------
def main():
    # get tickers
    try:
        with open(TICKERS_FILE, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        logging.info(f"Using {len(tickers)} tickers from {TICKERS_FILE}.")
    except FileNotFoundError:
        tickers = fetch_sp500_tickers()

    logging.info(f"Start analyzing {len(tickers)} tickers. This may take some minutes.")
    results = []
    # optionally rate-limit so we don't get blocked
    for i, tk in enumerate(tickers):
        logging.info(f"[{i+1}/{len(tickers)}] Processing {tk} ...")
        try:
            r = analyze_ticker(tk)
            if r:
                results.append(r)
        except Exception as e:
            logging.warning(f"{tk} -> exception: {e}")
        # light sleep to be polite to remote
        time.sleep(0.5)

    if not results:
        logging.info("No results collected.")
        return

    df = pd.DataFrame(results)
    # sort by pass_all then by roce desc
    df_sorted = df.sort_values(by=["pass_all", "roce_pct"], ascending=[False, False])
    df_sorted.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved {len(df_sorted)} rows to {OUTPUT_CSV}.")
    logging.info("Sample passing companies:")
    passing = df_sorted[df_sorted['pass_all'] == True]
    if not passing.empty:
        logging.info(passing[['ticker','name','roce_pct','revenue_yoy_pct','op_income_yoy_pct']].head(20).to_string(index=False))
    else:
        logging.info("No tickers passed all rules.")

if __name__ == "__main__":
    main()
