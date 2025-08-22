import streamlit as st
import pandas as pd

# Assuming df is your processed DataFrame with strategy signals
# Example columns: ['Instrument', 'Strategy', 'Entry', 'Exit', 'PotentialProfit', 'PotentialPercent', 'Comment']

# Color function for bullish/bearish strategy
def highlight_strategy(row):
    color = ''
    if row['Strategy'].lower() in ['call', 'bullish', 'bull spread']:
        color = 'background-color: #d4f4dd'  # light green
    elif row['Strategy'].lower() in ['put', 'bearish', 'bear spread']:
        color = 'background-color: #f4d4d4'  # light red
    return [color]*len(row)

# Style the DataFrame
styled_df = df.style.apply(highlight_strategy, axis=1)\
    .format({
        'PotentialProfit': '{:.2f} pts',
        'PotentialPercent': '{:.2f} %'
    })\
    .set_table_styles([
        {'selector': 'th', 'props': [('text-align','center'), ('min-width','120px')]},
        {'selector': 'td', 'props': [('text-align','center'), ('min-width','120px')]}
    ])\
    .background_gradient(subset=['PotentialProfit'], cmap='RdYlGn', low=0, high=1)

# Display full-width table in Streamlit
st.dataframe(styled_df, use_container_width=True)
