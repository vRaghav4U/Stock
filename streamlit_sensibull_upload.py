import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("Options Strategy Screener")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")
st.markdown("**By Ketan**")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def generate_strategy(row):
    fut = row['FuturePrice']
    max_pain = row['MaxPain']
    pcr = row['PCR']
    
    # Simple heuristics for demo
    if fut < max_pain:
        strategy = "CALL / Bull Call Spread"
        entry = fut
        exit_price = max_pain
        trade_detail = f"Buy CE at {entry:.2f}"
        stop_loss = entry * 0.98
        comments = f"Bullish bias: PCR low, Max Pain above Fut Price"
    elif fut > max_pain:
        strategy = "PUT / Bear Call Spread"
        entry = fut
        exit_price = max_pain
        trade_detail = f"Buy PE at {entry:.2f}"
        stop_loss = entry * 1.02
        comments = f"Bearish bias: PCR high, Max Pain below Fut Price"
    else:
        strategy = "Neutral"
        entry = fut
        exit_price = fut
        trade_detail = "N/A"
        stop_loss = fut
        comments = "Market at Max Pain"
    
    potential_points = abs(exit_price - entry)
    
    return pd.Series([strategy, entry, exit_price, stop_loss, trade_detail, comments, potential_points])

def style_rows(row):
    if 'CALL' in str(row['Strategy']):
        return ['background-color: #d4f4dd']*len(row)  # Green for bullish
    elif 'PUT' in str(row['Strategy']):
        return ['background-color: #f4d4d4']*len(row)  # Red for bearish
    else:
        return ['']*len(row)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Ensure numeric columns
        num_cols = ['FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','VolumeMultiple','FutureOIPercentChange']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Generate strategy columns
        df[['Strategy','Entry','Exit','StopLoss','TradeDetails','Comments','PotentialPoints']] = df.apply(generate_strategy, axis=1)
        
        # Columns order
        cols_order = ['Instrument','Strategy','Entry','Exit','StopLoss','TradeDetails','Comments','PotentialPoints',
                      'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
        df = df[cols_order]
        
        # Separate NIFTY and BANKNIFTY
        nifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        other_df = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        
        # Top 10 trades based on PotentialPoints
        top10_df = other_df.sort_values(by='PotentialPoints', ascending=False).head(10)
        all_trades_df = other_df.sort_values(by='PotentialPoints', ascending=False)
        
        st.subheader("NIFTY and BANKNIFTY")
        st.dataframe(nifty_df.style.apply(style_rows, axis=1).format("{:.2f}"), use_container_width=True)
        
        st.subheader("Top 10 Trades")
        st.dataframe(top10_df.style.apply(style_rows, axis=1).format("{:.2f}"), use_container_width=True)
        
        st.subheader("All Trades")
        st.dataframe(all_trades_df.style.apply(style_rows, axis=1).format("{:.2f}"), use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
