import streamlit as st
import pandas as pd
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ---------- App setup ----------
st.set_page_config(page_title="Ketan Verma- Options Strategy Screener", layout="wide")
st.markdown("<h1 style='text-align:center;'>Options Strategy Screener</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>by Ketan</h4>", unsafe_allow_html=True)
st.markdown('<div style="text-align:center;"><a href="https://web.sensibull.com/options-screener?view=table" target="_blank">Sensibull Options Screener</a></div>', unsafe_allow_html=True)

# ---------- Utility helpers ----------
NUM_COLS = [
    'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV',
    'ATMIVChange','IVPercentile','VolumeMultiple','FutureOIPercentChange'
]

def to_num(df: pd.DataFrame) -> pd.DataFrame:
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def safe_rr(potential: float, risk_pts: float) -> float:
    risk_pts = abs(risk_pts)
    if risk_pts <= 0 or np.isnan(risk_pts):
        return 0.0
    return round(potential / risk_pts, 2)

def directional_levels(fut: float, maxpain: float):
    dist = abs(maxpain - fut)
    if not np.isfinite(dist) or dist < 1e-6:
        dist = max(1.0, fut * 0.005)
    long_sl  = fut - 0.5 * dist
    short_sl = fut + 0.5 * dist
    tgt      = maxpain
    potential = abs(maxpain - fut)
    return tgt, long_sl, short_sl, potential

def neutral_range(fut: float, maxpain: float, ivp: float):
    base = max(1.0, fut * 0.004)
    widen = 1.0 + (ivp/100.0)
    half_width = base * widen
    return fut - half_width, fut + half_width, half_width

def bucket_iv(ivr: float, iv: float):
    if np.isfinite(ivr):
        if ivr >= 70: return "HIGH"
        if ivr <= 30: return "LOW"
        return "MEDIUM"
    else:
        if iv >= 30: return "HIGH"
        if iv <= 15: return "LOW"
        return "MEDIUM"

def bias_from_pcr_maxpain(pcr: float, fut: float, maxpain: float):
    if np.isfinite(pcr) and np.isfinite(fut) and np.isfinite(maxpain):
        if pcr < 0.6 and maxpain > fut: return "BULLISH"
        if pcr > 0.8 and maxpain < fut: return "BEARISH"
    if maxpain > fut: return "BULLISH"
    if maxpain < fut: return "BEARISH"
    return "NEUTRAL"

def add_strategy(rows, instrument, cat, name, entry, exit_price, sl, potential, rr, details, comments):
    rows.append({
        "Instrument": instrument,
        "Category": cat,
        "Strategy": name,
        "Entry": round(entry, 2),
        "Exit": round(exit_price, 2),
        "StopLoss": round(sl, 2) if np.isfinite(sl) else 0.0,
        "RiskReward": round(rr, 2),
        "PotentialPoints": round(potential, 2),
        "TradeDetails": details,
        "Comments": comments
    })

def generate_strategies(row):
    i = row['Instrument']
    fut = row['FuturePrice']
    maxpain = row['MaxPain']
    pcr = row['PCR']
    iv = row['ATMIV']
    ivp = row['IVPercentile']

    rows = []
    if not np.isfinite(fut) or not np.isfinite(maxpain):
        return rows

    iv_regime = bucket_iv(ivp, iv)
    bias = bias_from_pcr_maxpain(pcr, fut, maxpain)
    tgt, long_sl, short_sl, potential = directional_levels(fut, maxpain)
    n_lo, n_hi, half_w = neutral_range(fut, maxpain, ivp if np.isfinite(ivp) else 50.0)

    if iv_regime in ("LOW", "MEDIUM"):
        if bias == "BULLISH":
            add_strategy(rows, i, "CALL", "Bull Call Spread", fut, tgt, long_sl,
                         potential*0.6, safe_rr(potential*0.6, 0.5*abs(fut-long_sl)),
                         f"Buy ATM CE ~{fut:.0f}, Sell OTM CE ~{tgt:.0f}",
                         "Low IV + bullish bias → debit spread.")
        elif bias == "BEARISH":
            add_strategy(rows, i, "PUT", "Bear Put Spread", fut, tgt, short_sl,
                         potential*0.6, safe_rr(potential*0.6, 0.5*abs(short_sl-fut)),
                         f"Buy ATM PE ~{fut:.0f}, Sell OTM PE ~{tgt:.0f}",
                         "Low IV + bearish bias → debit spread.")
        else:
            add_strategy(rows, i, "LONGVOL", "Long Straddle", fut, tgt, np.nan,
                         max(potential, fut*0.005),
                         safe_rr(potential, 0.5*potential),
                         "Buy ATM CE + ATM PE",
                         "Low IV + neutral bias → buy vol for breakout.")
    elif iv_regime == "HIGH":
        if bias == "BULLISH":
            add_strategy(rows, i, "PUT", "Bull Put Spread (Credit)", fut, n_hi, n_lo,
                         potential*0.4, safe_rr(potential*0.4, half_w),
                         f"Sell OTM PE ~{n_lo:.0f}, Buy lower PE",
                         "High IV + bullish bias → sell puts for premium.")
        elif bias == "BEARISH":
            add_strategy(rows, i, "CALL", "Bear Call Spread (Credit)", fut, n_lo, n_hi,
                         potential*0.4, safe_rr(potential*0.4, half_w),
                         f"Sell OTM CE ~{n_hi:.0f}, Buy higher CE",
                         "High IV + bearish bias → sell calls for premium.")
        else:
            add_strategy(rows, i, "NEUTRAL", "Iron Condor", fut, fut, fut,
                         potential*0.3, safe_rr(potential*0.3, half_w),
                         "Sell OTM CE & PE, hedge with wings",
                         "High IV + near MaxPain → condor best.")
    return rows

def highlight_row(row):
    cat = row.get('Category', '')
    if cat == 'CALL':
        return ['background-color: #b6fcd5'] * len(row)
    if cat == 'PUT':
        return ['background-color: #ffb3b3'] * len(row)
    if cat == 'NEUTRAL':
        return ['background-color: #c9d7ff'] * len(row)
    if cat == 'LONGVOL':
        return ['background-color: #f7e7a9'] * len(row)
    if cat == 'SHORTVOL':
        return ['background-color: #e6d4ff'] * len(row)
    return [''] * len(row)

# ---------- Fetch live table ----------
def fetch_live_sensibull_table():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get("https://web.sensibull.com/options-screener?view=table")

    st.info("Please log in manually in the browser window that opens...")
    time.sleep(30)  # give time to login manually
    time.sleep(10)  # wait for table to load fully

    tables = pd.read_html(driver.page_source)
    driver.quit()
    return tables[0]

# ---------- Main Run ----------
if st.button("Fetch Live Options Data"):
    try:
        raw = fetch_live_sensibull_table()
        st.success("Data fetched successfully!")
        df = to_num(raw.copy())

        # Generate all strategies
        all_rows = []
        for _, r in df.iterrows():
            all_rows.extend(generate_strategies(r))
        out = pd.DataFrame(all_rows)

        if out.empty:
            st.warning("No strategies generated. Please check the data.")
            st.stop()

        keep_cols = ['Instrument','FuturePrice','MaxPain','PCR','FuturePercentChange',
                     'ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
        ref = df[keep_cols].drop_duplicates(subset=['Instrument'])
        out = out.merge(ref, on='Instrument', how='left')

        columns_order = [
            'Instrument','Category','Strategy','TradeDetails','Comments',
            'Entry','Exit','StopLoss','RiskReward','PotentialPoints',
            'FuturePrice','MaxPain','PCR','FuturePercentChange',
            'ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange'
        ]
        out = out[columns_order]

        df_top = out[out['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()
        df_rest = out[~out['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()
        df_top10 = df_rest.dropna(subset=['PotentialPoints']).sort_values('PotentialPoints', ascending=False).head(10)
        df_all = df_rest.sort_values(['Instrument','Category','Strategy'])

        st.markdown("### NIFTY & BANKNIFTY")
        st.dataframe(df_top.style.apply(highlight_row, axis=1))

        st.markdown("### Top 10 Trades (by Potential Points)")
        st.dataframe(df_top10.style.apply(highlight_row, axis=1))

        st.markdown("### All Trades (every strategy for every symbol)")
        st.dataframe(df_all.style.apply(highlight_row, axis=1))

        st.download_button(
            "Download full results (CSV)",
            data=out.to_csv(index=False).encode('utf-8'),
            file_name="options_strategy_screener_results.csv",
            mime="text/csv"
        )

        with st.expander("Notes / Assumptions"):
            st.write("""
- Heuristics only: PotentialPoints uses distance to MaxPain and IV bands.
- IV logic: IVP ≤ 30 → debit; IVP ≥ 70 → credit.
- Risk/Reward uses fraction of distance to MaxPain or neutral half-width.
- Neutral setups prefer instruments near MaxPain.
- Credit strategies need active management.
""")

    except Exception as e:
        st.error(f"Error fetching or processing data: {e}")
