import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("Sensibull Options Strategy Screener")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)  \nby Ketan", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip() for c in df.columns]

        # Convert necessary columns to numeric
        num_cols = ['FuturePrice','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','FutureOIPercentChange','PCR','MaxPain']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Function to determine strategy
        def determine_strategy(row):
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']
            atmiv = row['ATMIV']

            # Defaults
            strategy = "N/A"
            entry = fut
            exit_ = maxpain
            stop_loss = None
            potential = abs(fut - maxpain)
            trade_detail = ""
            comments = ""

            if pd.isna(fut) or pd.isna(maxpain) or pd.isna(pcr):
                return pd.Series([strategy, entry, exit_, stop_loss, comments, potential, trade_detail])

            # Bullish strategies
            if fut < maxpain and pcr < 0.8:
                strategy = "CALL / Bull Call Spread"
                trade_detail = f"Buy CE at {fut:.2f}, Sell CE at {maxpain:.2f}"
                comments = "Bullish bias: PCR low, Max Pain above Fut Price"
                stop_loss = fut - 0.5 * potential

            elif fut < maxpain and 0.8 <= pcr <= 1.2:
                strategy = "PUT / Bull Put Spread"
                trade_detail = f"Sell PE at {fut:.2f}, Buy PE at {maxpain:.2f}"
                comments = "Moderately bullish: PCR moderate, Max Pain above Fut Price"
                stop_loss = fut - 0.5 * potential

            # Bearish strategies
            elif fut > maxpain and pcr > 1.2:
                strategy = "PUT / Bear Call Spread"
                trade_detail = f"Buy PE at {fut:.2f}, Sell PE at {maxpain:.2f}"
                comments = "Bearish bias: PCR high, Max Pain below Fut Price"
                stop_loss = fut + 0.5 * potential

            elif fut > maxpain and 0.8 <= pcr <= 1.2:
                strategy = "CALL / Bear Put Spread"
                trade_detail = f"Buy CE at {fut:.2f}, Sell CE at {maxpain:.2f}"
                comments = "Moderately bearish: PCR moderate, Max Pain below Fut Price"
                stop_loss = fut + 0.5 * potential

            # Neutral / volatility strategies
            elif abs(fut - maxpain)/fut < 0.02 and atmiv > 20:
                strategy = "Straddle / Strangle"
                trade_detail = f"Buy CE & PE at {fut:.2f}"
                comments = "Expect big move, directional neutral"
                stop_loss = None

            else:
                strategy = "Iron Condor"
                trade_detail = f"Sell OTM CE & PE, Buy farther OTM CE & PE"
                comments = "Neutral strategy, low IV"
                stop_loss = None

            return pd.Series([strategy, entry, exit_, stop_loss, comments, potential, trade_detail])

        df[['Strategy','Entry','Exit','StopLoss','Comments','PotentialPoints','TradeDetails']] = df.apply(determine_strategy, axis=1)

        # Order NIFTY and BANKNIFTY on top
        nifty_rows = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        other_rows = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        top10_rows = other_rows.sort_values('PotentialPoints', ascending=False).head(10)
        all_trades = pd.concat([other_rows]).sort_values('PotentialPoints', ascending=False)

        def highlight_strategy(row):
            if 'Bull' in row['Strategy']:
                return ['background-color: #c6f5c6']*len(row)
            elif 'Bear' in row['Strategy']:
                return ['background-color: #f5c6c6']*len(row)
            else:
                return ['background-color: #c6d9f5']*len(row)

        # Columns sequence
        columns_seq = ['Instrument','Strategy','Entry','Exit','StopLoss','Comments','PotentialPoints','TradeDetails',
                       'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']

        st.subheader("NIFTY / BANKNIFTY")
        st.dataframe(nifty_rows[columns_seq].style.apply(highlight_strategy, axis=1).format(precision=2), use_container_width=True)

        st.subheader("Top 10 Trades")
        st.dataframe(top10_rows[columns_seq].style.apply(highlight_strategy, axis=1).format(precision=2), use_container_width=True)

        st.subheader("All Trades")
        st.dataframe(all_trades[columns_seq].style.apply(highlight_strategy, axis=1).format(precision=2), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
