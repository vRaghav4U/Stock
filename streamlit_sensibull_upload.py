import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# Helper functions
# -----------------------------

def recommend_strategy(row):
    """
    Basic option strategy recommendation logic based on Sensibull CSV columns.
    This is illustrative and uses simple rules:
    - CALL if ATMIV is rising, PCR < 0.7, Price < MaxPain
    - PUT if ATMIV is rising, PCR > 0.7, Price > MaxPain
    """
    S = row['FuturePrice']
    PCR = row['PCR']
    MaxPain = row['MaxPain']
    iv_change = row['ATMIVChange']

    strategy = 'Neutral'
    entry = S
    exit = S
    potential = 0
    comment = ''

    # Call signal
    if iv_change > 0 and PCR < 0.7 and S < MaxPain:
        strategy = 'CALL'
        exit = MaxPain
        potential = exit - entry
        comment = 'Buy Call, IV rising, PCR low, Price below MaxPain'
    # Put signal
    elif iv_change > 0 and PCR > 0.7 and S > MaxPain:
        strategy = 'PUT'
        exit = MaxPain
        potential = entry - exit
        comment = 'Buy Put, IV rising, PCR high, Price above MaxPain'
    # Iron Condor / Neutral suggestion
    elif PCR >= 0.5 and PCR <= 0.7:
        strategy = 'NEUTRAL'
        exit = S
        potential = 0
        comment = 'Neutral market, consider Iron Condor or short strangle'
    else:
        strategy = 'HOLD'
        exit = S
        potential = 0
        comment = 'Market unclear, hold position'

    return pd.Series([strategy, entry, exit, potential, comment])

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Sensibull Option Screener Strategy Analyzer")
st.write("Upload your Sensibull options CSV and get strategy recommendations.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric columns
        numeric_cols = ['FuturePrice','ATMIV','ATMIVChange','PCR','MaxPain']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Drop rows with missing crucial data
        df.dropna(subset=numeric_cols, inplace=True)

        # Apply strategy recommendation
        df[['Strategy','Entry','Exit','PotentialProfit','Comment']] = df.apply(recommend_strategy, axis=1)

        # Sort by potential profit descending
        df_sorted = df.sort_values(by='PotentialProfit', ascending=False)

        # Show top 10 strategies
        st.subheader("Top 10 Option Strategies")
        st.dataframe(df_sorted.head(10))

    except Exception as e:
        st.error(f"Error processing file: {e}")
