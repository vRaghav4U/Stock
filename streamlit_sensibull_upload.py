import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.title("Option Strategy Screener")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")
st.markdown("**By Ketan**")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def generate_strategy(row):
    fut_price = float(row['FuturePrice'])
    max_pain = float(row['MaxPain'])
    pcr = float(row['PCR'])
    
    # Basic logic for bullish/bearish trades
    strategy, entry, exit_, comments = "", "", "", ""
    potential_points = 0
    trade_details = ""

    # Nifty / BankNifty default
    if row['Instrument'].upper() == "NIFTY" or row['Instrument'].upper() == "BANKNIFTY":
        if fut_price < max_pain or pcr < 0.6:
            strategy = "CALL / Bull Call Spread"
            entry = fut_price
            exit_ = max_pain
            comments = f"Bullish bias: PCR low, Max Pain above Fut Price"
            potential_points = exit_ - entry
        else:
            strategy = "PUT / Bear Call Spread"
            entry = fut_price
            exit_ = max_pain
            comments = f"Bearish bias: PCR high, Max Pain below Fut Price"
            potential_points = entry - exit_
        trade_details = f"Buy {strategy.split('/')[0]} at {entry}, Target: {exit_}"
    else:
        # Other instruments based on PCR and Max Pain
        if pcr < 0.6 and fut_price < max_pain:
            strategy = "CALL / Bull Call Spread"
            entry = fut_price
            exit_ = max_pain
            comments = "Bullish bias: PCR low, Max Pain above Fut Price"
            potential_points = exit_ - entry
            trade_details = f"Buy Call at {entry}, Target: {exit_}"
        elif pcr > 0.6 and fut_price > max_pain:
            strategy = "PUT / Bear Call Spread"
            entry = fut_price
            exit_ = max_pain
            comments = "Bearish bias: PCR high, Max Pain below Fut Price"
            potential_points = entry - exit_
            trade_details = f"Buy Put at {entry}, Target: {exit_}"
        else:
            strategy = "Neutral / No clear signal"
            entry = fut_price
            exit_ = fut_price
            comments = "No clear bullish or bearish bias"
            potential_points = 0
            trade_details = "Hold / Avoid Trade"

    return pd.Series([strategy, entry, exit_, comments, potential_points, trade_details])

def highlight_row(row):
    if 'CALL' in str(row['Strategy']):
        return ['background-color: #d4edda']*len(row)  # Green
    elif 'PUT' in str(row['Strategy']):
        return ['background-color: #f8d7da']*len(row)  # Red
    else:
        return ['']*len(row)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric
        numeric_cols = ['FuturePrice','MaxPain','PCR']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Generate strategy columns
        df[['Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails']] = df.apply(generate_strategy, axis=1)

        # Arrange display columns
        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','Event',
                        'VolumeMultiple','FutureOIPercentChange']

        # Separate NIFTY and BANKNIFTY
        nifty_df = df[df['Instrument'].str.upper() == 'NIFTY'].reset_index(drop=True)
        banknifty_df = df[df['Instrument'].str.upper() == 'BANKNIFTY'].reset_index(drop=True)

        # Top 10 trades based on PotentialPoints
        top10_df = df.drop(nifty_df.index.union(banknifty_df.index)).nlargest(10, 'PotentialPoints').reset_index(drop=True)

        # Remaining
        rest_df = df.drop(nifty_df.index.union(banknifty_df.index).union(top10_df.index)).reset_index(drop=True)

        # Concatenate for all trades
        full_df = pd.concat([nifty_df, banknifty_df, top10_df, rest_df]).reset_index(drop=True)

        st.subheader("Top Trades")
        st.dataframe(pd.concat([nifty_df, banknifty_df, top10_df]).reset_index(drop=True)[display_cols]
                     .style.apply(highlight_row, axis=1), use_container_width=True)

        st.subheader("All Trades")
        st.dataframe(full_df[display_cols].style.apply(highlight_row, axis=1), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
