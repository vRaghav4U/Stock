import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Sensibull Options Strategy Screener by Ketan")

st.markdown("<h1 style='text-align:center'>Options Strategy Screener</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center'>by Ketan</h3>", unsafe_allow_html=True)
st.markdown("[View Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric columns are converted
        num_cols = ['FuturePrice','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','FutureOIPercentChange','MaxPain']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Function to generate strategy, entry, exit, comments
        def generate_trade(row):
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']
            if fut < maxpain and pcr < 0.6:
                strategy = 'CALL / Bull Call Spread'
                entry = fut
                exit_price = maxpain
                stop_loss = fut * 0.02
                comments = f"Bullish bias: PCR low, Max Pain above Fut Price"
                trade_detail = f"Buy CE at {entry:.2f}"
            elif fut > maxpain and pcr > 0.6:
                strategy = 'PUT / Bear Call Spread'
                entry = fut
                exit_price = maxpain
                stop_loss = fut * 0.02
                comments = f"Bearish bias: PCR high, Max Pain below Fut Price"
                trade_detail = f"Buy PE at {entry:.2f}"
            else:
                strategy = 'NEUTRAL / Straddle'
                entry = fut
                exit_price = fut
                stop_loss = fut * 0.01
                comments = f"Neutral bias: PCR moderate, Max Pain near Fut Price"
                trade_detail = f"Buy CE & PE at {entry:.2f}"
            potential_points = abs(exit_price - entry)
            risk_reward = round(potential_points / stop_loss if stop_loss != 0 else 0,2)
            return pd.Series([strategy, entry, exit_price, stop_loss, comments, potential_points, risk_reward, trade_detail])

        df[['Strategy','Entry','Exit','StopLoss','Comments','PotentialPoints','RiskReward','TradeDetails']] = df.apply(generate_trade, axis=1)

        # Separate NIFTY and BANKNIFTY
        nifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()
        other_df = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])].copy()

        # Top 10 trades based on PotentialPoints
        top10_df = other_df.nlargest(10, 'PotentialPoints')

        # Function to color code
        def highlight_strategy(row):
            if 'CALL' in row['Strategy']:
                return ['background-color: #b6fcd5']*len(row)
            elif 'PUT' in row['Strategy']:
                return ['background-color: #fcb6b6']*len(row)
            else:
                return ['background-color: #fff7b6']*len(row)

        st.markdown("### NIFTY / BANKNIFTY")
        st.dataframe(nifty_df.style.apply(highlight_strategy, axis=1).format({
            'FuturePrice':'{:.2f}',
            'Entry':'{:.2f}',
            'Exit':'{:.2f}',
            'StopLoss':'{:.2f}',
            'PotentialPoints':'{:.2f}',
            'RiskReward':'{:.2f}'
        }), use_container_width=True)

        st.markdown("### Top 10 Trades")
        st.dataframe(top10_df.style.apply(highlight_strategy, axis=1).format({
            'FuturePrice':'{:.2f}',
            'Entry':'{:.2f}',
            'Exit':'{:.2f}',
            'StopLoss':'{:.2f}',
            'PotentialPoints':'{:.2f}',
            'RiskReward':'{:.2f}'
        }), use_container_width=True)

        st.markdown("### All Trades")
        st.dataframe(other_df.style.apply(highlight_strategy, axis=1).format({
            'FuturePrice':'{:.2f}',
            'Entry':'{:.2f}',
            'Exit':'{:.2f}',
            'StopLoss':'{:.2f}',
            'PotentialPoints':'{:.2f}',
            'RiskReward':'{:.2f}'
        }), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
