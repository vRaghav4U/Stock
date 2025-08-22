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
                        'FutureOIPercentChange','MaxPain','PCR']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Determine strategy
        def determine_strategy(row):
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']
            atmiv = row['ATMIV']
            strat = ''
            entry = fut
            exit_ = maxpain
            comments = ''
            potential = 0

            # Bullish strategies
            if fut < maxpain and pcr < 0.8:
                if atmiv > 40:
                    strat = 'Long Call / Straddle'
                    comments = f'Bullish with high IV: consider long call or straddle'
                else:
                    strat = 'CALL / Bull Call Spread'
                    comments = f'Bullish bias: PCR low, Max Pain above Fut Price'
                exit_ = maxpain
                potential = exit_ - entry

            # Bearish strategies
            elif fut > maxpain and pcr > 1.2:
                if atmiv > 40:
                    strat = 'Long Put / Straddle'
                    comments = f'Bearish with high IV: consider long put or straddle'
                else:
                    strat = 'PUT / Bear Call Spread'
                    comments = f'Bearish bias: PCR high, Max Pain below Fut Price'
                exit_ = maxpain
                potential = entry - exit_

            # Neutral / volatility plays
            else:
                if 0.9 <= pcr <= 1.1 and 20 <= atmiv <= 40:
                    strat = 'Iron Condor / Neutral'
                    comments = 'Neutral bias: consider Iron Condor'
                    potential = abs(entry - exit_)  # approximate

            row['Strategy'] = strat
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

        # Row coloring function for Styler
        def highlight_row(row):
            color = ''
            if 'Bull' in row['Strategy']:
                color = '#d4f4dd'
            elif 'Bear' in row['Strategy']:
                color = '#f4d4d4'
            elif 'Neutral' in row['Strategy']:
                color = '#f4f0d4'
            return ['background-color: {}'.format(color) for _ in row]

        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'Event','VolumeMultiple','FutureOIPercentChange']

        # Display tables
        st.subheader("NIFTY & BANKNIFTY")
        st.write(nifty_bnifty[display_cols].style.apply(highlight_row, axis=1).format(precision=2), unsafe_allow_html=True)

        st.subheader("Top 10 Trades")
        st.write(top_trades[display_cols].style.apply(highlight_row, axis=1).format(precision=2), unsafe_allow_html=True)

        st.subheader("All Trades")
        st.write(all_trades[display_cols].style.apply(highlight_row, axis=1).format(precision=2), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
