import streamlit as st
import pandas as pd

st.title("Sensibull Options Strategy Screener")

# Upload CSV
uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

if uploaded_file is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Example: Add Strategy, Entry, Exit, PotentialProfit, Comment columns
        # Here you would normally calculate signals based on FuturePrice, ATMIV, PCR etc.
        # For demonstration, we'll create dummy strategy data
        df['Strategy'] = ['Call' if x%2==0 else 'Put' for x in range(len(df))]
        df['Entry'] = df['FuturePrice'] * 0.99
        df['Exit'] = df['FuturePrice'] * 1.01
        df['PotentialProfit'] = df['Exit'] - df['Entry']
        df['PotentialPercent'] = df['PotentialProfit'] / df['Entry'] * 100
        df['Comment'] = ['Bullish' if s=='Call' else 'Bearish' for s in df['Strategy']]

        # Color coding function
        def highlight_strategy(row):
            color = ''
            if row['Strategy'].lower() in ['call', 'bullish', 'bull spread']:
                color = 'background-color: #d4f4dd'  # light green
            elif row['Strategy'].lower() in ['put', 'bearish', 'bear spread']:
                color = 'background-color: #f4d4d4'  # light red
            return [color]*len(row)

        # Apply styling
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

        # Show table in Streamlit
        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
