import streamlit as st
import pandas as pd
import numpy as np

# ---------- App chrome ----------
st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.markdown("<h1 style='text-align:center;'>Options Strategy Screener</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>by Ketan</h4>", unsafe_allow_html=True)
st.markdown('<div style="text-align:center;"><a href="https://web.sensibull.com/options-screener?view=table" target="_blank">Sensibull Options Screener</a></div>', unsafe_allow_html=True)
st.write("Upload the raw CSV exported from Sensibull (same headers as your sample).")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

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
    """Derive generic directional target/SL using distance to Max Pain as anchor."""
    dist = abs(maxpain - fut)
    # guard for tiny/NaN
    if not np.isfinite(dist) or dist < 1e-6:
        dist = max(1.0, fut * 0.005)  # 0.5% fallback
    # 50% of the distance as risk, full distance as reward proxy
    long_sl  = fut - 0.5 * dist
    short_sl = fut + 0.5 * dist
    tgt      = maxpain
    potential = abs(maxpain - fut)  # proxy points
    return tgt, long_sl, short_sl, potential

def neutral_range(fut: float, maxpain: float, ivp: float):
    """Return a neutral range around fut; wider when IVP is high."""
    base = max(1.0, fut * 0.004)  # base 0.4%
    widen = 1.0 + (ivp/100.0)     # 1x to 2x of base as IVP grows 0->100
    half_width = base * widen
    return fut - half_width, fut + half_width, half_width

def bucket_iv(ivr: float, iv: float):
    """Classify implied volatility regime."""
    # prefer percentile if present; otherwise fall back to absolute ATM IV
    if np.isfinite(ivr):
        if ivr >= 70: return "HIGH"
        if ivr <= 30: return "LOW"
        return "MEDIUM"
    else:
        if iv >= 30: return "HIGH"
        if iv <= 15: return "LOW"
        return "MEDIUM"

def bias_from_pcr_maxpain(pcr: float, fut: float, maxpain: float):
    """Heuristic directional bias using PCR + relationship to Max Pain."""
    # PCR < ~0.6 often bullish, > ~0.8 bearish; maxpain as magnet/anchor
    if np.isfinite(pcr) and np.isfinite(fut) and np.isfinite(maxpain):
        if pcr < 0.6 and maxpain > fut: return "BULLISH"
        if pcr > 0.8 and maxpain < fut: return "BEARISH"
    # fallback using only distance to max pain
    if maxpain > fut: return "BULLISH"
    if maxpain < fut: return "BEARISH"
    return "NEUTRAL"

def add_strategy(rows, instrument, cat, name, entry, exit_price, sl, potential, rr, details, comments):
    rows.append({
        "Instrument": instrument,
        "Category": cat,              # CALL/PUT/NEUTRAL/LONGVOL/SHORTVOL
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
    """Return a list of dicts (one per strategy) for a single instrument."""
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

    # ----------------------- Directional (Bullish) -----------------------
    if bias == "BULLISH":
        # Long Call (debit) - best when IV LOW/MED
        if iv_regime in ("LOW", "MEDIUM"):
            rr = safe_rr(potential, abs(fut - long_sl))
            add_strategy(
                rows, i, "CALL",
                "Long Call",
                entry=fut, exit_price=tgt, sl=long_sl, potential=potential, rr=rr,
                details=f"Buy ATM CE ~{fut:.2f}",
                comments="Bullish bias (PCR/MaxPain). Debit favored when IV not high."
            )
        # Bull Call Spread (debit)
        if iv_regime in ("LOW", "MEDIUM"):
            spread_potential = potential * 0.6  # conservative cap for verticals
            rr = safe_rr(spread_potential, 0.5 * abs(fut - long_sl))
            add_strategy(
                rows, i, "CALL",
                "Bull Call Spread",
                entry=fut, exit_price=tgt, sl=long_sl, potential=spread_potential, rr=rr,
                details=f"Buy ATM CE, Sell OTM CE (~{tgt:.2f})",
                comments="Debit vertical caps risk; useful when IV not elevated."
            )
        # Bull Put Spread (credit) - best when IV HIGH
        if iv_regime == "HIGH":
            credit_potential = potential * 0.4  # credit spreads earn smaller but safer
            rr = safe_rr(credit_potential, 0.5 * abs(fut - long_sl))
            add_strategy(
                rows, i, "PUT",
                "Bull Put Spread (Credit)",
                entry=fut, exit_price=n_hi, sl=n_lo, potential=credit_potential, rr=rr,
                details=f"Sell OTM PE, Buy lower PE; hold if > {n_lo:.2f}.",
                comments="Bullish + high IV → sell puts for premium."
            )

    # ----------------------- Directional (Bearish) -----------------------
    if bias == "BEARISH":
        # Long Put (debit)
        if iv_regime in ("LOW", "MEDIUM"):
            rr = safe_rr(potential, abs(short_sl - fut))
            add_strategy(
                rows, i, "PUT",
                "Long Put",
                entry=fut, exit_price=tgt, sl=short_sl, potential=potential, rr=rr,
                details=f"Buy ATM PE ~{fut:.2f}",
                comments="Bearish bias (PCR/MaxPain). Debit favored when IV not high."
            )
        # Bear Put Spread (debit)
        if iv_regime in ("LOW", "MEDIUM"):
            spread_potential = potential * 0.6
            rr = safe_rr(spread_potential, 0.5 * abs(short_sl - fut))
            add_strategy(
                rows, i, "PUT",
                "Bear Put Spread",
                entry=fut, exit_price=tgt, sl=short_sl, potential=spread_potential, rr=rr,
                details=f"Buy ATM PE, Sell lower PE (~{tgt:.2f})",
                comments="Debit vertical improves RR; works with moderate IV."
            )
        # Bear Call Spread (credit)
        if iv_regime == "HIGH":
            credit_potential = potential * 0.4
            rr = safe_rr(credit_potential, 0.5 * abs(short_sl - fut))
            add_strategy(
                rows, i, "CALL",
                "Bear Call Spread (Credit)",
                entry=fut, exit_price=n_lo, sl=n_hi, potential=credit_potential, rr=rr,
                details=f"Sell OTM CE, Buy higher CE; hold if < {n_hi:.2f}.",
                comments="Bearish + high IV → sell calls for premium."
            )

    # ----------------------- Neutral / Volatility -----------------------
    # If fut is close to max pain (within 0.4%-0.8%), consider neutral setups
    close_to_mp = (abs(maxpain - fut) <= 0.008 * fut)

    # Long Straddle/Strangle: when IV LOW and expecting move away from MP
    if iv_regime == "LOW":
        lv_pot = max(potential, fut * 0.005)  # modest move proxy
        rr = safe_rr(lv_pot, 0.5 * lv_pot)
        add_strategy(
            rows, i, "LONGVOL",
            "Long Straddle",
            entry=fut, exit_price=tgt, sl=np.nan, potential=lv_pot, rr=rr,
            details="Buy ATM CE + ATM PE",
            comments="Low IV → buy vol; profit from move/expansion."
        )
        add_strategy(
            rows, i, "LONGVOL",
            "Long Strangle",
            entry=fut, exit_price=tgt, sl=np.nan, potential=lv_pot*0.9, rr=rr,
            details="Buy OTM CE + OTM PE",
            comments="Cheaper than straddle; needs larger move."
        )

    # Short Straddle/Strangle & Iron structures: when IV HIGH (sell premium)
    if iv_regime == "HIGH":
        # Short Straddle
        credit = half_w * 2.0
        rr = safe_rr(credit, half_w)  # risk proxy using break-even half-width
        add_strategy(
            rows, i, "SHORTVOL",
            "Short Straddle (ATM)",
            entry=fut, exit_price=fut, sl=fut + 2*half_w, potential=credit, rr=rr,
            details=f"Sell ATM CE + ATM PE; manage ±{2*half_w:.2f}",
            comments="High IV → mean reversion & theta; manage risk actively."
        )
        # Short Strangle
        credit = half_w * 1.6
        rr = safe_rr(credit, half_w)
        add_strategy(
            rows, i, "SHORTVOL",
            "Short Strangle (OTM)",
            entry=fut, exit_price=fut, sl=fut + 2.5*half_w, potential=credit, rr=rr,
            details=f"Sell OTM CE + OTM PE; cushion up to ~±{2.5*half_w:.2f}",
            comments="Higher safety than straddle; less credit."
        )
        # Iron Condor (when neutral & near MP helps)
        if close_to_mp:
            credit = half_w * 1.2
            rr = safe_rr(credit, half_w)
            add_strategy(
                rows, i, "NEUTRAL",
                "Iron Condor",
                entry=fut, exit_price=fut, sl=fut + 3*half_w, potential=credit, rr=rr,
                details="Sell OTM CE & PE; buy far OTM wings.",
                comments="High IV + near Max Pain → premium capture."
            )
        # Iron Butterfly (ATM short body)
        if close_to_mp:
            credit = half_w * 1.4
            rr = safe_rr(credit, half_w)
            add_strategy(
                rows, i, "NEUTRAL",
                "Iron Butterfly",
                entry=fut, exit_price=fut, sl=fut + 2.5*half_w, potential=credit, rr=rr,
                details="Short ATM straddle + buy far OTM wings.",
                comments="High IV + price pinned near MP → best payoff."
            )

    return rows

# ---------- Styling ----------
def highlight_row(row):
    cat = row.get('Category', '')
    if cat == 'CALL':
        return ['background-color: #b6fcd5'] * len(row)     # mint for bullish
    if cat == 'PUT':
        return ['background-color: #ffb3b3'] * len(row)     # soft red for bearish
    if cat == 'NEUTRAL':
        return ['background-color: #c9d7ff'] * len(row)     # soft blue for neutral
    if cat == 'LONGVOL':
        return ['background-color: #f7e7a9'] * len(row)     # yellow for long vol
    if cat == 'SHORTVOL':
        return ['background-color: #e6d4ff'] * len(row)     # lilac for short vol
    return [''] * len(row)

# ---------- Main run ----------
if uploaded_file:
    try:
        raw = pd.read_csv(uploaded_file)
        df = to_num(raw.copy())

        # Generate all strategies (one-to-many → explode)
        all_rows = []
        for _, r in df.iterrows():
            all_rows.extend(generate_strategies(r))
        out = pd.DataFrame(all_rows)

        # If no strategies produced (e.g., bad CSV), bail gracefully
        if out.empty:
            st.warning("No strategies generated. Please check the CSV columns/values.")
            st.stop()

        # Join back some original columns for reference
        keep_cols = ['Instrument','FuturePrice','MaxPain','PCR','FuturePercentChange',
                     'ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
        ref = df[keep_cols].drop_duplicates(subset=['Instrument'])
        out = out.merge(ref, on='Instrument', how='left')

        # Order columns
        columns_order = [
            'Instrument','Category','Strategy','TradeDetails','Comments',
            'Entry','Exit','StopLoss','RiskReward','PotentialPoints',
            'FuturePrice','MaxPain','PCR','FuturePercentChange',
            'ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange'
        ]
        out = out[columns_order]

        # Top rows: NIFTY & BANKNIFTY (all strategies)
        df_top = out[out['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()

        # Non-index universe
        df_rest = out[~out['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()

        # Top 10 trades by PotentialPoints (excluding NaNs)
        df_top10 = df_rest.dropna(subset=['PotentialPoints']).sort_values(
            'PotentialPoints', ascending=False
        ).head(10)

        # All other trades (sorted)
        df_all = df_rest.sort_values(['Instrument','Category','Strategy'])

        # Display
        st.markdown("### NIFTY & BANKNIFTY")
        st.dataframe(
            df_top.style.apply(highlight_row, axis=1).format({
                'Entry': '{:.2f}','Exit':'{:.2f}','StopLoss':'{:.2f}',
                'RiskReward':'{:.2f}','PotentialPoints':'{:.2f}',
                'FuturePrice':'{:.2f}','MaxPain':'{:.2f}',
                'FuturePercentChange':'{:.2f}','ATMIV':'{:.2f}',
                'ATMIVChange':'{:.2f}','IVPercentile':'{:.0f}'
            }, na_rep="-")
        )

        st.markdown("### Top 10 Trades (by Potential Points)")
        st.dataframe(
            df_top10.style.apply(highlight_row, axis=1).format({
                'Entry': '{:.2f}','Exit':'{:.2f}','StopLoss':'{:.2f}',
                'RiskReward':'{:.2f}','PotentialPoints':'{:.2f}',
                'FuturePrice':'{:.2f}','MaxPain':'{:.2f}',
                'FuturePercentChange':'{:.2f}','ATMIV':'{:.2f}',
                'ATMIVChange':'{:.2f}','IVPercentile':'{:.0f}'
            }, na_rep="-")
        )

        st.markdown("### All Trades (every strategy for every symbol)")
        st.dataframe(
            df_all.style.apply(highlight_row, axis=1).format({
                'Entry': '{:.2f}','Exit':'{:.2f}','StopLoss':'{:.2f}',
                'RiskReward':'{:.2f}','PotentialPoints':'{:.2f}',
                'FuturePrice':'{:.2f}','MaxPain':'{:.2f}',
                'FuturePercentChange':'{:.2f}','ATMIV':'{:.2f}',
                'ATMIVChange':'{:.2f}','IVPercentile':'{:.0f}'
            }, na_rep="-")
        )

        # Downloads
        st.download_button(
            "Download full results (CSV)",
            data=out.to_csv(index=False).encode('utf-8'),
            file_name="options_strategy_screener_results.csv",
            mime="text/csv"
        )

        # Notes for users
        with st.expander("Notes / Assumptions"):
            st.write("""
- **Heuristics only**: Without option-chain premiums, spreads/credits are **proxies**. 
  *PotentialPoints* uses distance to **MaxPain** and IV bands as anchors.
- **IV logic**: 
  - IVP ≤ 30 → debit (long options/verticals) favored.
  - IVP ≥ 70 → credit (short premium, condors, fly) favored.
- **Risk/Reward**: Risk proxies use a fraction of distance to Max Pain or neutral half-width. 
  Adjust to your risk model (ATR, stdev, or option greeks) if you later add the chain.
- **Neutral setups** prefer instruments trading **near Max Pain**.
- **Manage actively**: Credit strategies need strict risk management and exits on IV crush/mean reversion.
""")

    except Exception as e:
        st.error(f"Error processing file: {e}")
