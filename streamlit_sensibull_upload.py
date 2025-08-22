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

        # Compute PotentialPoints and Strategy
        df['Strategy'] = "-"
        df['Entry'] = np.nan
        df['Exit'] = np.nan
        df['Comments'] = "-"
        df['PotentialPoints'] = 0.0
        df['TradeDetails'] = "-"

        for idx, row in df.iterrows():
            fut = row['FuturePrice']
            pcr = row['PCR']
            maxpain = row['MaxPain']

            if fut < maxpain and pcr < 0.6:
                df.at[idx,'Strategy'] = "CALL / Bull Call Spread"
                df.at[idx,'Entry'] = fut
                df.at[idx,'Exit'] = maxpain
                df.at[idx,'Comments'] = "Bullish bias: PCR low, Max Pain above Fut Price"
                df.at[idx,'PotentialPoints'] = round(maxpain - fut,2)
                df.at[idx,'TradeDetails'] = f"Buy Call at {fut:.2f}"
            elif fut > maxpain and pcr > 0.6:
                df.at[idx,'Strategy'] = "PUT / Bear Call Spread"
                df.at[idx,'Entry'] = fut
                df.at[idx,'Exit'] = maxpain
                df.at[idx,'Comments'] = "Bearish bias: PCR high, Max Pain below Fut Price"
                df.at[idx,'PotentialPoints'] = round(fut - maxpain,2)
                df.at[idx,'TradeDetails'] = f"Buy Put at {fut:.2f}"
            else:
                df.at[idx,'Strategy'] = "Neutral / Iron Condor"
                df.at[idx,'Entry'] = fut
                df.at[idx,'Exit'] = maxpain
                df.at[idx,'Comments'] = "Sideways / low opportunity"
                df.at[idx,'PotentialPoints'] = 0.0
                df.at[idx,'TradeDetails'] = "-"

        # Reorder columns
        display_cols = ['Instrument','Strategy','Entry','Exit','Comments','PotentialPoints','TradeDetails',
                        'FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                        'Event','VolumeMultiple','FutureOIPercentChange']
        df = df[display_cols]

        # Separate Nifty and BankNifty
        nifty_banknifty = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        others = df[~df['Instrument'].isin(['NIFTY','BANKNIFTY'])]

        # Top 10 trades from remaining
        top10 = others.sort_values(by='PotentialPoints', ascending=False).head(10)
        rest = others.drop(top10.index)

        # Final dataframe
        final_df = pd.concat([nifty_banknifty, top10, rest], ignore_index=True)

        # Styling
        def highlight_strategy(row):
            if 'CALL' in row['Strategy']:
                color = 'background-color: #d4f8d4'
            elif 'PUT' in row['Strategy']:
                color = 'background-color: #f8d4d4'
            else:
                color = ''
            return [color]*len(row)

        styled_df = final_df.style.apply(highlight_strategy, axis=1)\
                                  .format("{:.2f}", subset=['Entry','Exit','PotentialPoints','FuturePrice','MaxPain',
                                                             'PCR','FuturePercentChange','ATMIV','ATMIVChange','IVPercentile',
                                                             'FutureOIPercentChange'])\
                                  .set_properties(**{'text-align':'center'})\
                                  .set_table_styles([{'selector':'th','props':[('text-align','center')]}])

        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
