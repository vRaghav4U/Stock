import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.title("Sensibull Options Strategy Screener")
st.write("Upload your Sensibull CSV file to see strategy suggestions")

# File uploader
uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Ensure numeric columns are correct
        numeric_cols = ['FuturePrice', 'ATMIV', 'ATMIVChange', 'IVPercentile', 
                        'FutureOIPercentChange', 'PCR', 'MaxPain']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with missing FuturePrice or PCR
        df = df.dropna(subset=['FuturePrice', 'PCR'])
        
        # Strategy assignment function
        def assign_strategy(row):
            try:
                # Bullish strategy
                if row['PCR'] < 0.7 and row['FuturePercentChange'] >= 0:
                    return "Buy Call / Bullish Spread"
                # Bearish strategy
                elif row['PCR'] > 1.0 and row['FuturePercentChange'] <= 0:
                    return "Buy Put / Bearish Spread"
                # Neutral / high IV
                elif row['IVPercentile'] > 75:
                    return "Iron Condor / Short Straddle"
                else:
                    return "Neutral / Wait"
            except:
                return "Unknown"

        df['Strategy'] = df.apply(assign_strategy, axis=1)
        
        # Simple profit/loss estimation (in points)
        def estimate_profit(row):
            try:
                if "Bullish" in row['Strategy']:
                    return max(row['MaxPain'] - row['FuturePrice'], 0)
                elif "Bearish" in row['Strategy']:
                    return max(row['FuturePrice'] - row['MaxPain'], 0)
                elif "Iron" in row['Strategy']:
                    return row['ATMIV']  # rough estimate for premium collected
                else:
                    return 0
            except:
                return 0

        df['PotentialProfit'] = df.apply(estimate_profit, axis=1)

        # Highlight strategy
        def highlight_strategy(row):
            if "Bullish" in row['Strategy']:
                return ['background-color: #b6fcd5']*len(row)
            elif "Bearish" in row['Strategy']:
                return ['background-color: #ffb3b3']*len(row)
            elif "Iron" in row['Strategy']:
                return ['background-color: #f7f7b3']*len(row)
            else:
                return ['background-color: #f0f0f0']*len(row)

        st.write("Top Option Strategies")
        st.dataframe(
            df.style.apply(highlight_strategy, axis=1),
            width=1400,
            height=600
        )
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
