import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sensibull Options Strategy Screener by Ketan", layout="wide")

st.title("Option Strategy Screener")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)")
st.markdown("by **Ketan**", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Ensure numeric columns
        num_cols = ['FuturePrice','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                    'FutureOIPercentChange','PCR','MaxPain']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Define strategy logic
        strategies = []
        entries = []
        exits = []
        comments = []
        potential_points = []
        trade_details = []

        for idx, row in df.iterrows():
            fut = row['FuturePrice']
            pcr = row['PCR']
            maxpain = row['MaxPain']
            atmiv = row['ATMIV']

            strategy = "-"
            entry = "-"
            exit_price = "-"
            comment = "-"
            points = 0.0
            trade_detail = "-"

            # Simple logic for demonstration
            if fut < maxpain and pcr < 0.6:
                strategy = "CALL / Bull Call Spread"
                entry = fut
                exit_price = maxpain
                comment = f"Bullish bias: PCR low, Max Pain above Fut Price"
                points = maxpain - fut
                trade_detail = f"Buy Call at {fut:.2f}"
            elif fut > maxpain and pcr > 0.6:
                strategy = "PUT / Bear Call Spread"
                entry = fut
                exit_price = maxpain
                comment = f"Bearish bias: PCR high, Max Pain below Fut Price"
                points = fut - maxpain
                trade_detail = f"Buy Put at {fut:.2f}"
            else:
                strategy = "Neutral / Iron Condor"
                entry = fut
                exit_price = maxpain
                comment = "Sideways / low opportunity"
                points = 0.0
                trade_detail = "-"

            strategies.append(strategy)
            entries.append(entry)
            exits.append(exit_price)
            comments.append(comment)
            potential_points.append(round(points,2))
            trade_details.append(trade_detail)

        df['Strategy'] = strategies
        df['Entry'] = entries
        df['Exit'] = exits
        df['Comments'] = comments
        df['PotentialPoints'] = potential_points
        df['TradeDetails'] = trade_details

        # Reorder columns
        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'Event','VolumeMultiple','FutureOIPercentChange']
        df = df[display_cols]

        # Move Nifty and BankNifty to top
        nifty_banknifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        rest_df = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        top10_df = rest_df.sort_values(by='PotentialPoints', ascending=False).head(10)
        other_df = rest_df.drop(top10_df.index)
        final_df = pd.concat([nifty_banknifty_df, top10_df, other_df], ignore_index=True)

        # Style table
        def highlight_strategy(row):
            color = ''
            if 'CALL' in row['Strategy']:
                color = 'background-color: #d4f8d4'  # light green
            elif 'PUT' in row['Strategy']:
                color = 'background-color: #f8d4d4'  # light red
            else:
                color = ''
            return [color]*len(row)

        styled_df = final_df.style.apply(highlight_strategy, axis=1)\
                                  .format(precision=2)\
                                  .set_table_styles([{'selector':'th','props':[('text-align','center')]}])\
                                  .set_properties(**{'text-align':'center'})

        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
