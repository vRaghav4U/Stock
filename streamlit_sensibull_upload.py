import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.title("Sensibull Options Strategy Screener")

# File upload
uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"], help="Upload CSV from Sensibull")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Ensure numeric columns
        num_cols = ['FuturePrice','ATMIV','ATMIVChange','IVPercentile','FutureOIPercentChange','PCR','MaxPain']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Strategy determination function
        def determine_strategy(row):
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']
            atmiv = row['ATMIV']

            # Default
            strategy = "Long Call"
            entry = fut
            exit_ = fut
            comments = ""
            potential_points = 0

            # Bullish if MaxPain above FutPrice & PCR low
            if fut < maxpain and pcr < 0.6:
                strategy = "Bull Call Spread"
                entry = fut  # buy ATM call
                exit_ = maxpain  # sell OTM call near MaxPain
                potential_points = exit_ - entry
                comments = f"Bullish bias: PCR low, Max Pain above FutPrice"

            # Bearish if MaxPain below FutPrice & PCR high
            elif fut > maxpain and pcr > 0.7:
                strategy = "Bear Put Spread"
                entry = fut  # buy ATM put
                exit_ = maxpain  # sell OTM put near MaxPain
                potential_points = entry - exit_
                comments = f"Bearish bias: PCR high, Max Pain below FutPrice"

            # Neutral / ATM
            else:
                strategy = "Long Call/Put"
                entry = fut
                exit_ = fut
                potential_points = 0
                comments = "Neutral, low edge"

            return pd.Series([strategy, entry, exit_, comments, potential_points])

        df[['Strategy','Entry','Exit','Comments','PotentialPoints']] = df.apply(determine_strategy, axis=1)

        # Bring NIFTY and BANKNIFTY to top
        nifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        other_df = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        df = pd.concat([nifty_df, other_df], ignore_index=True)

        # Style function for bullish/bearish
        def highlight_strategy(row):
            color = ""
            if "Bull" in row['Strategy']:
                color = 'background-color: #b6d7a8'  # light green
            elif "Bear" in row['Strategy']:
                color = 'background-color: #f4cccc'  # light red
            else:
                color = 'background-color: #fff2cc'  # light yellow
            return [color]*len(row)

        # Display full width
        styled_df = df.style.apply(highlight_strategy, axis=1).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center')]},
            {'selector': 'td', 'props': [('text-align', 'center')]} 
        ]).format({'FuturePrice':'{:.2f}','Entry':'{:.2f}','Exit':'{:.2f}','PotentialPoints':'{:.2f}'})

        st.write("### Top Option Strategies (NIFTY & BANKNIFTY always on top)")
        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
