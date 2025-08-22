import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Options Strategy Screener by Ketan", layout="wide")

# Page Header
st.markdown("<h1>Options Strategy Screener</h1>", unsafe_allow_html=True)
st.markdown('<p style="font-size:16px;">by Ketan</p>', unsafe_allow_html=True)
st.markdown('<a href="https://web.sensibull.com/options-screener?view=table" target="_blank">Sensibull Options Screener</a>', unsafe_allow_html=True)
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Ensure numeric columns
        numeric_cols = ['FuturePrice','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'FutureOIPercentChange','MaxPain']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Calculate Strategy, Entry, Exit, Comments, Potential Points
        def determine_strategy(row):
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']
            if fut < maxpain:
                strategy = 'CALL / Bull Call Spread'
                entry = fut
                exit_ = maxpain
                comments = f'Bullish bias: PCR low, Max Pain above Fut Price'
                potential = exit_ - entry
            else:
                strategy = 'PUT / Bear Call Spread'
                entry = fut
                exit_ = maxpain
                comments = f'Bearish bias: PCR high, Max Pain below Fut Price'
                potential = entry - exit_
            row['Strategy'] = strategy
            row['Entry'] = round(entry,2)
            row['Exit'] = round(exit_,2)
            row['Comments'] = comments
            row['PotentialPoints'] = round(potential,2)
            row['TradeDetails'] = f"Buy at {entry:.2f}"
            return row
        
        df = df.apply(determine_strategy, axis=1)

        # Separate NIFTY & BANKNIFTY
        nifty_bnifty = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        df_rest = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        
        # Top 10 trades by PotentialPoints
        top_trades = df_rest.sort_values(by='PotentialPoints', ascending=False).head(10)
        
        # Remaining trades
        all_trades = df_rest.copy()

        # Row coloring function
        def highlight_row(row):
            if 'Bullish' in row['Strategy']:
                return ['background-color: #d4f4dd']*len(row)
            elif 'Bearish' in row['Strategy']:
                return ['background-color: #f4d4d4']*len(row)
            else:
                return ['']*len(row)
        
        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'Event','VolumeMultiple','FutureOIPercentChange']

        # Display tables
        st.subheader("NIFTY & BANKNIFTY")
        st.dataframe(nifty_bnifty[display_cols].style.apply(highlight_row, axis=1).format(precision=2), use_container_width=True)

        st.subheader("Top 10 Trades")
        st.dataframe(top_trades[display_cols].style.apply(highlight_row, axis=1).format(precision=2), use_container_width=True)

        st.subheader("All Trades")
        st.dataframe(all_trades[display_cols].style.apply(highlight_row, axis=1).format(precision=2), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
