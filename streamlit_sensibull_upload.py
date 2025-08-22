import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.markdown("<h1 style='text-align:center;'>Options Strategy Screener</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center;'>by Ketan</h4>", unsafe_allow_html=True)
st.markdown('<div style="text-align:center;"><a href="https://web.sensibull.com/options-screener?view=table" target="_blank">Sensibull Options Screener</a></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def calculate_strategy(row):
    fut = row['FuturePrice']
    maxpain = row['MaxPain']
    pcr = row['PCR']
    iv = row['ATMIV']
    
    strategy = "N/A"
    entry = fut
    exit_price = maxpain
    stop_loss = 0
    potential = 0
    rr = 0
    trade_details = ""
    comments = ""

    # Long Call
    if pcr < 0.6 and fut < maxpain:
        strategy = "CALL / Long Call"
        trade_details = f"Buy CE at {entry:.2f}"
        potential = abs(maxpain - fut)
        stop_loss = fut - 0.5 * potential
        rr = potential / max(1, abs(fut - stop_loss))
        comments = "Bullish bias: PCR low, Max Pain above Fut Price"
    # Bull Call Spread
    elif pcr < 0.6 and fut < maxpain and 10 < iv < 40:
        strategy = "CALL / Bull Call Spread"
        trade_details = f"Buy CE at {entry:.2f}, Sell CE above"
        potential = abs(maxpain - fut)
        stop_loss = fut - 0.5 * potential
        rr = potential / max(1, abs(fut - stop_loss))
        comments = "Bullish bias: PCR low, Max Pain above Fut Price"
    # Long Put
    elif pcr > 0.8 and fut > maxpain:
        strategy = "PUT / Long Put"
        trade_details = f"Buy PE at {entry:.2f}"
        potential = abs(fut - maxpain)
        stop_loss = fut + 0.5 * potential
        rr = potential / max(1, abs(stop_loss - fut))
        comments = "Bearish bias: PCR high, Max Pain below Fut Price"
    # Bear Call Spread
    elif pcr > 0.8 and fut > maxpain and 10 < iv < 40:
        strategy = "PUT / Bear Call Spread"
        trade_details = f"Sell CE at {entry:.2f}, Buy CE above"
        potential = abs(fut - maxpain)
        stop_loss = fut + 0.5 * potential
        rr = potential / max(1, abs(stop_loss - fut))
        comments = "Bearish bias: PCR high, Max Pain below Fut Price"
    # Straddle (High IV)
    elif iv > 40:
        strategy = "Straddle"
        trade_details = f"Buy ATM CE & PE at {entry:.2f}"
        potential = 0
        stop_loss = 0
        rr = 0
        comments = "High IV, potential for large move"
    # Strangle (High IV)
    elif iv > 35:
        strategy = "Strangle"
        trade_details = f"Buy OTM CE & PE around {entry:.2f}"
        potential = 0
        stop_loss = 0
        rr = 0
        comments = "High IV, potential for large move"

    return pd.Series([strategy, round(entry,2), round(exit_price,2), round(stop_loss,2), round(rr,2), comments, round(potential,2), trade_details])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        # Ensure numeric columns
        num_cols = ['FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','VolumeMultiple','FutureOIPercentChange']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Calculate strategy
        df[['Strategy','Entry','Exit','StopLoss','RiskReward','Comments','PotentialPoints','TradeDetails']] = df.apply(calculate_strategy, axis=1)

        # Order columns
        columns_order = ['Instrument','Strategy','Entry','Exit','StopLoss','RiskReward','Comments','PotentialPoints','TradeDetails',
                         'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
        df = df[columns_order]

        # Separate NIFTY & BANKNIFTY
        index_top = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])].index
        df_top = df.loc[index_top]
        df_rest = df.drop(index_top)

        # Top 10 trades by PotentialPoints
        df_top10 = df_rest.sort_values('PotentialPoints', ascending=False).head(10)

        # All other trades
        df_all = df_rest.sort_values('Instrument')

        # Color coding
        def highlight_row(row):
            if 'CALL' in row['Strategy']:
                return ['background-color: #b6fcd5']*len(row)
            elif 'PUT' in row['Strategy']:
                return ['background-color: #ffb3b3']*len(row)
            else:
                return ['']*len(row)

        st.markdown("### NIFTY & BANKNIFTY")
        st.dataframe(df_top.style.apply(highlight_row, axis=1).format("{:.2f}", subset=['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','RiskReward']))

        st.markdown("### Top 10 Trades")
        st.dataframe(df_top10.style.apply(highlight_row, axis=1).format("{:.2f}", subset=['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','RiskReward']))

        st.markdown("### All Trades")
        st.dataframe(df_all.style.apply(highlight_row, axis=1).format("{:.2f}", subset=['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','RiskReward']))

    except Exception as e:
        st.error(f"Error processing file: {e}")
