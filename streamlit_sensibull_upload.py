import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sensibull Options Strategy Screener", layout="wide")
st.title("Sensibull Options Strategy Screener")
st.markdown("by **Ketan**")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")

uploaded_file = st.file_uploader("Upload Sensibull CSV", type="csv")
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric columns
        numeric_cols = ["FuturePrice","FuturePercentChange","ATMIV","ATMIVChange","IVPercentile",
                        "VolumeMultiple","FutureOIPercentChange","PCR","MaxPain"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Strategy logic
        strategies = []
        entries = []
        exits = []
        comments = []
        potential_points = []
        trade_details = []

        for idx, row in df.iterrows():
            fut_price = row['FuturePrice']
            max_pain = row['MaxPain']
            pcr = row['PCR']

            # Default
            strategy = "No Trade"
            entry = fut_price
            exit_price = fut_price
            comment = ""
            potential = 0
            trade_detail = ""

            # Example logic
            if fut_price < max_pain and pcr < 0.7:
                strategy = "CALL / Bull Call Spread"
                entry = fut_price
                exit_price = max_pain
                comment = f"Bullish bias: PCR low, Max Pain above Fut Price"
                potential = exit_price - entry
                trade_detail = f"Buy Call at {entry:.2f}"
            elif fut_price > max_pain and pcr > 0.7:
                strategy = "PUT / Bear Call Spread"
                entry = fut_price
                exit_price = max_pain
                comment = f"Bearish bias: PCR high, Max Pain below Fut Price"
                potential = entry - exit_price
                trade_detail = f"Buy Put at {entry:.2f}"

            strategies.append(strategy)
            entries.append(entry)
            exits.append(exit_price)
            comments.append(comment)
            potential_points.append(potential)
            trade_details.append(trade_detail)

        df['Strategy'] = strategies
        df['Entry'] = entries
        df['Exit'] = exits
        df['Comments'] = comments
        df['PotentialPoints'] = potential_points
        df['TradeDetails'] = trade_details

        # Reorder columns
        full_df = df[['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                      'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange',
                      'IVPercentile','Event','VolumeMultiple','FutureOIPercentChange']]

        # Move NIFTY and BANKNIFTY to top
        top_indices = full_df[full_df['Instrument'].isin(['NIFTY','BANKNIFTY'])].index
        top_df = full_df.loc[top_indices]
        other_df = full_df.drop(top_indices)
        full_df = pd.concat([top_df, other_df], ignore_index=True)

        # Highlight strategy colors
        def highlight_strategy(row):
            if "CALL" in row['Strategy']:
                return ['background-color: #d4fcd4']*len(row)
            elif "PUT" in row['Strategy']:
                return ['background-color: #fcd4d4']*len(row)
            else:
                return ['']*len(row)

        # Format numbers to 2 decimals
        styled_df = full_df.style.apply(highlight_strategy, axis=1)\
                                 .format({"PotentialPoints": "{:.2f}",
                                          "Entry": "{:.2f}",
                                          "Exit": "{:.2f}",
                                          "FuturePrice": "{:.2f}",
                                          "MaxPain": "{:.2f}",
                                          "PCR": "{:.2f}",
                                          "FuturePercentChange":"{:.2f}",
                                          "ATMIV":"{:.2f}",
                                          "ATMIVChange":"{:.2f}",
                                          "IVPercentile":"{:.2f}",
                                          "VolumeMultiple":"{:.2f}",
                                          "FutureOIPercentChange":"{:.2f}"})

        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
