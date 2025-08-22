import streamlit as st
import pandas as pd

st.set_page_config(page_title="Options Strategy Screener by Ketan", layout="wide")

st.markdown("""
# Sensibull Options Strategy Screener
[View Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)  
_by Ketan_
""")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Convert numeric columns to float
        numeric_cols = ['FuturePrice','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'FutureOIPercentChange','PCR','MaxPain']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Define strategy logic
        strategies = []
        entries = []
        exits = []
        comments = []
        potential = []
        trade_details = []

        for idx, row in df.iterrows():
            fut = row['FuturePrice']
            pcr = row['PCR']
            maxpain = row['MaxPain']

            # Simple Bullish / Bearish detection
            if fut < maxpain and pcr < 0.7:  # price below Max Pain and PCR low → Bullish
                strategy = "CALL / Bullish Trade"
                entry = fut
                exit_ = maxpain
                comment = f"Bullish bias: PCR low, Max Pain above Fut Price"
                potential_points = exit_ - entry
                trade_detail = f"Buy Call at {entry:.2f}"
            elif fut > maxpain and pcr > 0.7:  # price above Max Pain and PCR high → Bearish
                strategy = "PUT / Bearish Trade"
                entry = fut
                exit_ = maxpain
                comment = f"Bearish bias: PCR high, Max Pain below Fut Price"
                potential_points = entry - exit_
                trade_detail = f"Buy Put at {entry:.2f}"
            else:
                strategy = "Neutral / No Clear Bias"
                entry = fut
                exit_ = fut
                comment = f"PCR: {pcr:.2f}, Max Pain: {maxpain:.2f}"
                potential_points = 0
                trade_detail = "No Trade"
            
            strategies.append(strategy)
            entries.append(round(entry,2))
            exits.append(round(exit_,2))
            comments.append(comment)
            potential.append(round(potential_points,2))
            trade_details.append(trade_detail)

        # Insert new columns
        df.insert(1, "Strategy", strategies)
        df.insert(2, "Entry", entries)
        df.insert(3, "Exit", exits)
        df.insert(4, "Comments", comments)
        df.insert(5, "PotentialPoints", potential)
        df.insert(6, "TradeDetails", trade_details)

        # Separate NIFTY / BANKNIFTY for top table
        top_index = df['Instrument'].isin(['NIFTY','BANKNIFTY'])
        st.subheader("Major Indices")
        st.dataframe(df[top_index].style.applymap(lambda x: 'color: green' if 'Bullish' in str(x) else ('color: red' if 'Bearish' in str(x) else ''), subset=['Strategy']), use_container_width=True)

        # Top 10 trades excluding indices
        st.subheader("Top 10 Trades")
        df_trades = df[~top_index].copy()
        df_trades = df_trades.sort_values(by='PotentialPoints', ascending=False).head(10)
        st.dataframe(df_trades.style.applymap(lambda x: 'color: green' if 'Bullish' in str(x) else ('color: red' if 'Bearish' in str(x) else ''), subset=['Strategy']), use_container_width=True)

        # All trades table
        st.subheader("All Trades")
        st.dataframe(df.style.applymap(lambda x: 'color: green' if 'Bullish' in str(x) else ('color: red' if 'Bearish' in str(x) else ''), subset=['Strategy']), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
