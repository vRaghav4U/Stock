import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Sensibull Options Strategy Screener")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")

def determine_strategy(row):
    fut = row['FuturePrice']
    maxpain = row['MaxPain']
    pcr = row['PCR']

    strategy = "Long Call/Put"
    entry = fut
    exit_ = fut
    potential_points = 0
    comments = "Neutral, low edge"
    trade_details = f"Buy ATM at {fut}"

    if fut < maxpain and pcr < 0.6:
        strategy = "Bull Call Spread"
        entry = fut
        exit_ = maxpain
        potential_points = exit_ - entry
        comments = "Bullish bias: PCR low, Max Pain above FutPrice"
        trade_details = f"Buy Call at {fut}, Sell Call at {maxpain}"
    elif fut > maxpain and pcr > 0.7:
        strategy = "Bear Put Spread"
        entry = fut
        exit_ = maxpain
        potential_points = entry - exit_
        comments = "Bearish bias: PCR high, Max Pain below FutPrice"
        trade_details = f"Buy Put at {fut}, Sell Put at {maxpain}"

    return pd.Series([strategy, entry, exit_, comments, potential_points, trade_details])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        # Ensure numeric types
        numeric_cols = ['FuturePrice', 'MaxPain', 'PCR']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Insert NIFTY and BANKNIFTY at top if not already
        nifty_row = {'Instrument':'NIFTY','FuturePrice':24890,'MaxPain':24950,'PCR':0.69}
        banknifty_row = {'Instrument':'BANKNIFTY','FuturePrice':55260,'MaxPain':55500,'PCR':0.57}
        df = pd.concat([pd.DataFrame([nifty_row, banknifty_row]), df], ignore_index=True)

        # Apply strategy function
        df[['Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails']] = df.apply(determine_strategy, axis=1)

        # Reorder columns
        cols_sequence = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                         'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange',
                         'IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']
        df = df[[col for col in cols_sequence if col in df.columns]]

        # Styling
        def highlight_strategy(row):
            if "Bull" in row['Strategy']:
                return ['background-color: #b6fcb6']*len(row)
            elif "Bear" in row['Strategy']:
                return ['background-color: #ffb3b3']*len(row)
            else:
                return ['']*len(row)

        st.subheader("All Strategies")
        st.dataframe(df.style.apply(highlight_strategy, axis=1).set_table_attributes('style="width:100%"'))

        # Top 10 trades by PotentialPoints
        top_trades = df.sort_values(by='PotentialPoints', ascending=False).head(10)
        st.subheader("Top 10 Trades by Potential Points")
        st.dataframe(top_trades.style.apply(highlight_strategy, axis=1).set_table_attributes('style="width:100%"'))

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info("Please upload a Sensibull CSV to see strategies.")
