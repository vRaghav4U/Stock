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
        exit = S
        potential = 'High (Buy Call + Put ATM)'
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
        exit = S
        potential = 0
        comment = 'Neutral market, consider Iron Condor'

    return pd.Series([strategy, entry, exit, potential, comment])

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Sensibull Option Strategy Analyzer")
st.write("Upload Sensibull CSV and get strategy recommendations (CALL, PUT, Spreads, Iron Condor).")

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
        df[['Strategy','Entry','Exit','PotentialProfit','Comment']] = df.apply(recommend_strategy, axis=1)

        # Sort by PotentialProfit descending if numeric
        numeric_mask = df['PotentialProfit'].apply(lambda x: isinstance(x, (int, float)))
        df_sorted = df[numeric_mask].sort_values(by='PotentialProfit', ascending=False)
        df_non_numeric = df[~numeric_mask]

        # Merge numeric and non-numeric potential
        df_final = pd.concat([df_sorted, df_non_numeric])

        # Show top 10 strategies
        st.subheader("Top 10 Option Strategies")
        st.dataframe(df_final.head(10))

    except Exception as e:
        st.error(f"Error processing file: {e}")
