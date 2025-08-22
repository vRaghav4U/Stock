import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.title("Sensibull Options Strategy Screener")
uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def generate_strategy(row):
    """
    Simple logic to generate entry, exit, comments, potential profit.
    """
    strategy = ""
    entry = ""
    exit_ = ""
    comments = ""
    potential_profit = 0.0

    # Use simple heuristics based on IV, PCR, Max Pain
    fut_price = row['FuturePrice']
    atm_iv = row['ATMIV']
    pcr = row['PCR']
    max_pain = row['MaxPain']

    # CALL strategy
    if fut_price < max_pain and pcr < 0.7:
        strategy = "CALL"
        entry = f"Buy Call at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Bullish setup based on Max Pain & PCR"
        potential_profit = max_pain - fut_price
    # PUT strategy
    elif fut_price > max_pain and pcr > 0.8:
        strategy = "PUT"
        entry = f"Buy Put at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Bearish setup based on Max Pain & PCR"
        potential_profit = fut_price - max_pain
    else:
        strategy = "Neutral"
        entry = f"Hold"
        exit_ = f"N/A"
        comments = "No clear bias"
        potential_profit = 0.0

    return pd.Series([strategy, entry, exit_, comments, potential_profit])

def highlight_strategy(row):
    if row['Strategy'] == "CALL":
        return ['background-color: lightgreen']*len(row)
    elif row['Strategy'] == "PUT":
        return ['background-color: lightcoral']*len(row)
    else:
        return ['']*len(row)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        required_cols = ['Instrument','FuturePrice','ATMIV','PCR','MaxPain']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Column '{col}' not found in file!")
                st.stop()
        # Generate strategy columns
        df[['Strategy','Entry','Exit','Comments','PotentialProfit']] = df.apply(generate_strategy, axis=1)

        # Sort by PotentialProfit and take top 10
        df_top = df.sort_values(by='PotentialProfit', ascending=False).head(10)

        st.write("Top 10 Option Strategies based on Potential Profit")
        st.dataframe(
            df_top.style.apply(highlight_strategy, axis=1),
            width=1400,
            height=600
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
