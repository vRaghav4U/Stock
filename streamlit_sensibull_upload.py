import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# Title with "by Ketan" on next line
st.markdown("""
# Option Strategy Screener  
<span style='font-size:20px; color:gray;'>by Ketan</span>
""", unsafe_allow_html=True)

# Sensibull link as a button
st.markdown("[Go to Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

# Function to generate strategy signals
def generate_strategy(df):
    strategies = []
    entries = []
    exits = []
    comments = []
    potential = []
    trade_details = []

    # Ensure NIFTY and BANKNIFTY are at top
    df = df.sort_values(by='Instrument', key=lambda x: x.map(lambda y: 0 if y in ['NIFTY','BANKNIFTY'] else 1))

    for idx, row in df.iterrows():
        fut_price = row['FuturePrice']
        pcr = row['PCR']
        max_pain = row['MaxPain']

        # Default values
        strategy = ""
        entry = ""
        exit_ = ""
        comment = ""
        potential_points = ""
        trade_detail = ""

        # NIFTY and BANKNIFTY as special cases
        if row['Instrument'] == 'NIFTY':
            strategy = "CALL / Bull Call Spread"
            entry = fut_price
            exit_ = max_pain
            comment = f"Bullish bias: PCR low, Max Pain above Fut Price"
            potential_points = max_pain - fut_price
            trade_detail = f"Buy Call at {fut_price}, Target: {max_pain}"
        elif row['Instrument'] == 'BANKNIFTY':
            strategy = "CALL / Bull Call Spread"
            entry = fut_price
            exit_ = max_pain
            comment = f"Bullish bias: PCR low, Max Pain above Fut Price"
            potential_points = max_pain - fut_price
            trade_detail = f"Buy Call at {fut_price}, Target: {max_pain}"
        else:
            # Based on PCR and Max Pain
            if fut_price < max_pain and pcr < 0.7:
                strategy = "CALL / Bull Call Spread"
                entry = fut_price
                exit_ = max_pain
                comment = "Bullish bias: PCR low, Max Pain above Fut Price"
                potential_points = max_pain - fut_price
                trade_detail = f"Buy Call at {fut_price}, Target: {max_pain}"
            elif fut_price > max_pain and pcr > 0.7:
                strategy = "PUT / Bear Call Spread"
                entry = fut_price
                exit_ = max_pain
                comment = "Bearish bias: PCR high, Max Pain below Fut Price"
                potential_points = fut_price - max_pain
                trade_detail = f"Buy Put at {fut_price}, Target: {max_pain}"
            else:
                strategy = "NEUTRAL / Iron Condor"
                entry = fut_price
                exit_ = max_pain
                comment = "Neutral strategy: PCR moderate, near Max Pain"
                potential_points = abs(fut_price - max_pain)/2
                trade_detail = f"Sell Spread around {fut_price}"

        strategies.append(strategy)
        entries.append(entry)
        exits.append(exit_)
        comments.append(comment)
        potential.append(potential_points)
        trade_details.append(trade_detail)

    df['Strategy'] = strategies
    df['Entry'] = entries
    df['Exit'] = exits
    df['Comments'] = comments
    df['PotentialPoints'] = potential
    df['TradeDetails'] = trade_details

    # Arrange columns
    display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                    'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange',
                    'IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
    df = df[display_cols]
    return df

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric conversion
        numeric_cols = ['FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','VolumeMultiple','FutureOIPercentChange']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df_strategy = generate_strategy(df)

        # Highlight bullish green, bearish red
        def highlight_strategy(row):
            color = ''
            if 'Bull' in row['Strategy']:
                color = 'background-color: lightgreen'
            elif 'Bear' in row['Strategy']:
                color = 'background-color: lightcoral'
            return [color]*len(row)

        st.dataframe(df_strategy.style.apply(highlight_strategy, axis=1).set_precision(2), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
