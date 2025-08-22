import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# Helper function
# -----------------------------
def recommend_strategy(row):
    S = row['FuturePrice']
    PCR = row['PCR']
    MaxPain = row['MaxPain']
    iv_change = row['ATMIVChange']
    iv_level = row['ATMIV']

    strategy = 'HOLD'
    entry = S
    exit = S
    potential = 0
    comment = ''

    # High volatility / Straddle
    if iv_level > 40 and iv_change > 0:
        strategy = 'STRADDLE'
        potential = 0
        comment = 'Expect high volatility, consider ATM Call & Put'

    # Long Call
    elif iv_change > 0 and PCR < 0.7 and S < MaxPain:
        strategy = 'LONG CALL'
        exit = MaxPain
        potential = exit - entry
        comment = 'Buy ATM Call, IV rising, Price below MaxPain'

    # Long Put
    elif iv_change > 0 and PCR > 0.7 and S > MaxPain:
        strategy = 'LONG PUT'
        exit = MaxPain
        potential = entry - exit
        comment = 'Buy ATM Put, IV rising, Price above MaxPain'

    # Bull Call Spread
    elif S < MaxPain and 0.5 < PCR < 0.7:
        strategy = 'BULL CALL SPREAD'
        exit = MaxPain
        potential = exit - entry
        comment = 'Buy ATM Call & Sell OTM Call'

    # Bear Put Spread
    elif S > MaxPain and 0.3 < PCR < 0.5:
        strategy = 'BEAR PUT SPREAD'
        exit = MaxPain
        potential = entry - exit
        comment = 'Buy ATM Put & Sell OTM Put'

    # Neutral / Iron Condor
    elif 0.5 <= PCR <= 0.7 and abs(iv_change) < 2:
        strategy = 'IRON CONDOR'
        potential = 0
        comment = 'Neutral market, consider Iron Condor'

    potential_percent = (potential / entry * 100) if entry != 0 else 0

    return pd.Series([strategy, entry, exit, potential, potential_percent, comment])

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Sensibull Option Strategy Analyzer")
st.write("Upload Sensibull CSV and get strategy recommendations with color-coded bullish/bearish signals.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Convert numeric columns
        numeric_cols = ['FuturePrice','ATMIV','ATMIVChange','PCR','MaxPain']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows with missing crucial data
        df.dropna(subset=numeric_cols, inplace=True)

        # Apply strategy recommendation
        df[['Strategy','Entry','Exit','PotentialProfit','PotentialPercent','Comment']] = df.apply(recommend_strategy, axis=1)

        # Color coding
        def highlight_strategy(row):
            color = ''
            if row['Strategy'] in ['LONG CALL', 'BULL CALL SPREAD']:
                color = 'background-color: lightgreen'
            elif row['Strategy'] in ['LONG PUT', 'BEAR PUT SPREAD']:
                color = 'background-color: salmon'
            elif row['Strategy'] in ['IRON CONDOR', 'STRADDLE']:
                color = 'background-color: lightyellow'
            else:
                color = ''
            return [color]*len(row)

        # Full-width dataframe
        st.subheader("Top 10 Option Strategies")
        styled_df = df.head(10).style.apply(highlight_strategy, axis=1).format({
            'PotentialProfit': '{:.2f} pts',
            'PotentialPercent': '{:.2f} %'
        })
        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
