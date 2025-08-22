import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")
st.title("Sensibull Options Strategy Screener")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def option_strategy(row):
    fut_price = row['FuturePrice']
    pcr = row['PCR']
    max_pain = row['MaxPain']

    strategy = ""
    entry = ""
    exit_ = ""
    comments = ""
    potential_profit = 0.0

    # Logic for multiple strategies
    if fut_price < max_pain and pcr < 0.7:
        # Bullish strategies
        strategy = "CALL / Bull Call Spread"
        entry = f"Buy Call at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Bullish bias: PCR low, Max Pain above Fut Price"
        potential_profit = max_pain - fut_price
    elif fut_price > max_pain and pcr > 0.8:
        # Bearish strategies
        strategy = "PUT / Bear Call Spread"
        entry = f"Buy Put at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Bearish bias: PCR high, Max Pain below Fut Price"
        potential_profit = fut_price - max_pain
    elif fut_price < max_pain and 0.7 <= pcr <= 0.8:
        strategy = "Bull Put Spread"
        entry = f"Sell Put at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Neutral to bullish range-bound"
        potential_profit = max_pain - fut_price
    elif fut_price > max_pain and 0.7 <= pcr <= 0.8:
        strategy = "Bear Put Spread"
        entry = f"Sell Put at {fut_price}"
        exit_ = f"Target: {max_pain}"
        comments = "Neutral to bearish range-bound"
        potential_profit = fut_price - max_pain
    else:
        strategy = "Neutral / No Trade"
        entry = "Hold"
        exit_ = "N/A"
        comments = "No clear bias or low profit potential"
        potential_profit = 0.0

    return pd.Series([strategy, entry, exit_, comments, potential_profit])

def highlight_strategy(row):
    if "CALL" in row['Strategy']:
        return ['background-color: lightgreen']*len(row)
    elif "PUT" in row['Strategy']:
        return ['background-color: lightcoral']*len(row)
    else:
        return ['']*len(row)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        required_cols = ['Instrument','FuturePrice','ATMIV','PCR','MaxPain']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Column '{col}' not found in file!")
                st.stop()

        # Generate strategies
        df[['Strategy','Entry','Exit','Comments','PotentialProfit']] = df.apply(option_strategy, axis=1)
        df_top = df.sort_values(by='PotentialProfit', ascending=False).head(10)

        st.write("Top 10 Option Strategies based on Potential Profit")
        st.dataframe(
            df_top.style.apply(highlight_strategy, axis=1),
            width=1600,
            height=600
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
