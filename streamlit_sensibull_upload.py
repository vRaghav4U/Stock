import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Option Strategy Screener")
st.markdown("by Ketan")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")

# Upload CSV
uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Convert numeric columns
        numeric_cols = ['FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile','FutureOIPercentChange']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Generate sample strategy, entry, exit, comments, potential points
        strategies = []
        entries = []
        exits = []
        comments = []
        potential_points = []
        trade_details = []

        for idx, row in df.iterrows():
            fut = row['FuturePrice']
            maxpain = row['MaxPain']
            pcr = row['PCR']

            if fut < maxpain:  # Bearish
                strategy = "Bear Call Spread / Put"
                entry = fut
                exit_val = maxpain
                comment = f"Bearish bias: PCR high, Max Pain above"
                potential = abs(maxpain - fut)
                trade_detail = f"Buy Put at {fut}, Target {exit_val}"
            else:  # Bullish
                strategy = "Bull Call Spread / Call"
                entry = fut
                exit_val = maxpain
                comment = f"Bullish bias: PCR low, Max Pain below"
                potential = abs(maxpain - fut)
                trade_detail = f"Buy Call at {fut}, Target {exit_val}"

            strategies.append(strategy)
            entries.append(entry)
            exits.append(exit_val)
            comments.append(comment)
            potential_points.append(potential)
            trade_details.append(trade_detail)

        df['Strategy'] = strategies
        df['Entry'] = entries
        df['Exit'] = exits
        df['Comments'] = comments
        df['PotentialPoints'] = potential_points
        df['TradeDetails'] = trade_details

        # Separate NIFTY and BANKNIFTY
        nifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        others_df = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]

        # Top 10 trades
        top10_df = others_df.sort_values(by='PotentialPoints', ascending=False).head(10)
        rest_df = others_df.sort_values(by='Instrument')

        # Columns to display
        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'Event','VolumeMultiple','FutureOIPercentChange']

        st.subheader("NIFTY & BANKNIFTY Strategies")
        st.dataframe(nifty_df[display_cols], use_container_width=True)

        st.subheader("Top 10 Trades")
        st.dataframe(top10_df[display_cols], use_container_width=True)

        st.subheader("All Trades")
        st.dataframe(pd.concat([nifty_df, top10_df, rest_df])[display_cols], use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
