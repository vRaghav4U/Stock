import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")

st.title("Option Strategy Screener")
st.markdown("by Ketan")
st.markdown("[View Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")

# Upload CSV
uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure column names are consistent
        df.columns = [col.strip() for col in df.columns]

        # Define function to calculate strategies
        def generate_strategy(row):
            fut_price = row['FuturePrice']
            pcr = row['PCR']
            maxpain = row['MaxPain']
            atm_iv = row['ATMIV']
            fut_change = row['FuturePercentChange']

            # Default values
            strategy, entry, exit, comments, potential_points, trade_details = '', '', '', '', 0, ''

            # Nifty/BankNifty
            if row['Instrument'] in ['NIFTY', 'BANKNIFTY']:
                if fut_price < maxpain:
                    strategy = 'CALL / Bull Call Spread'
                    entry = fut_price
                    exit = maxpain
                    comments = f'Bullish bias: PCR low, Max Pain above Fut Price'
                    potential_points = round(exit - entry, 2)
                    trade_details = f'Buy Call at {entry}, Target {exit}'
                else:
                    strategy = 'PUT / Bear Call Spread'
                    entry = fut_price
                    exit = maxpain
                    comments = f'Bearish bias: PCR high, Max Pain below Fut Price'
                    potential_points = round(entry - exit, 2)
                    trade_details = f'Buy Put at {entry}, Target {exit}'
            else:
                # Other instruments based on PCR
                if pcr < 0.5:
                    strategy = 'CALL / Bull Call Spread'
                    entry = fut_price
                    exit = maxpain if maxpain > fut_price else fut_price + 50
                    comments = f'Bullish: PCR low, Max Pain above Fut Price'
                    potential_points = round(exit - entry,2)
                    trade_details = f'Buy Call at {entry}, Target {exit}'
                elif pcr > 0.6:
                    strategy = 'PUT / Bear Call Spread'
                    entry = fut_price
                    exit = maxpain if maxpain < fut_price else fut_price - 50
                    comments = f'Bearish: PCR high, Max Pain below Fut Price'
                    potential_points = round(entry - exit,2)
                    trade_details = f'Buy Put at {entry}, Target {exit}'
                else:
                    strategy = 'Straddle / Neutral'
                    entry = fut_price
                    exit = fut_price
                    comments = f'Market neutral, watch volatility'
                    potential_points = 0
                    trade_details = f'Buy Call & Put at {entry}'

            return pd.Series([strategy, entry, exit, comments, potential_points, trade_details])

        # Generate strategy columns
        df[['Strategy', 'Entry', 'Exit', 'Comments', 'PotentialPoints', 'TradeDetails']] = df.apply(generate_strategy, axis=1)

        # Reorder columns
        column_order = ['Instrument', 'Strategy', 'Entry', 'Exit', 'Comments', 'PotentialPoints', 'TradeDetails'] + \
                       [col for col in df.columns if col not in ['Instrument', 'Strategy', 'Entry', 'Exit', 'Comments', 'PotentialPoints', 'TradeDetails']]
        df = df[column_order]

        # Highlight bullish and bearish
        def highlight_strategy(row):
            if 'Bull' in row['Strategy']:
                color = 'background-color: lightgreen'
            elif 'Bear' in row['Strategy']:
                color = 'background-color: lightcoral'
            elif 'Neutral' in row['Strategy']:
                color = 'background-color: lightyellow'
            else:
                color = ''
            return [color]*len(row)

        # Display table
        st.dataframe(
            df.style
            .apply(highlight_strategy, axis=1)
            .format("{:.2f}"),  # numeric formatting
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload a Sensibull CSV file to get option strategy signals.")
