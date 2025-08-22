import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sensibull Option Strategy Screener by Ketan", layout="wide")
st.title("Sensibull Options Strategy Screener")
st.markdown("[Sensibull Options Screener](https://web.sensibull.com/options-screener?view=table)  \nby Ketan", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Sensibull CSV", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Ensure numeric columns
        num_cols = ['FuturePrice','MaxPain','PCR','FuturePercentChange','ATMIV','ATMIVChange',
                    'IVPercentile','VolumeMultiple','FutureOIPercentChange']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Generate strategy, entry, exit, stoploss, potential points
        strategies = []
        entry = []
        exit_ = []
        stoploss = []
        potential_points = []
        trade_details = []
        comments = []

        for idx, row in df.iterrows():
            fp = row['FuturePrice']
            mp = row['MaxPain']
            pcr = row['PCR']
            iv = row['ATMIV']

            strat = ""
            ent = 0
            ex = 0
            sl = 0
            pp = 0
            td = ""
            cmnt = ""

            if row['Instrument'] in ['NIFTY','BANKNIFTY']:
                if fp < mp:
                    strat = "CALL / Bull Call Spread"
                    ent = fp
                    ex = mp
                    sl = fp - 0.5*(ex-ent)
                    pp = ex - ent
                    td = f"Buy Call at {ent:.2f}"
                    cmnt = f"Bullish bias: PCR low, Max Pain above Fut Price"
                else:
                    strat = "PUT / Bear Call Spread"
                    ent = fp
                    ex = mp
                    sl = ent + 0.5*(ent-ex)
                    pp = ent - ex
                    td = f"Buy Put at {ent:.2f}"
                    cmnt = f"Bearish bias: PCR high, Max Pain below Fut Price"
            else:
                # Simple rules for top trades
                if fp < mp:
                    strat = "CALL / Bull Call Spread"
                    ent = fp
                    ex = mp
                    sl = fp - 0.5*(ex-ent)
                    pp = ex - ent
                    td = f"Buy Call at {ent:.2f}"
                    cmnt = "Bullish bias"
                else:
                    strat = "PUT / Bear Call Spread"
                    ent = fp
                    ex = mp
                    sl = ent + 0.5*(ent-ex)
                    pp = ent - ex
                    td = f"Buy Put at {ent:.2f}"
                    cmnt = "Bearish bias"

            strategies.append(strat)
            entry.append(ent)
            exit_.append(ex)
            stoploss.append(sl)
            potential_points.append(pp)
            trade_details.append(td)
            comments.append(cmnt)

        df['Strategy'] = strategies
        df['Entry'] = entry
        df['Exit'] = exit_
        df['StopLoss'] = stoploss
        df['PotentialPoints'] = potential_points
        df['TradeDetails'] = trade_details
        df['Comments'] = comments

        # Separate NIFTY and BANKNIFTY
        nifty_df = df[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]
        top10_df = df.drop(df.index[df['Instrument'].isin(['NIFTY','BANKNIFTY'])]).sort_values(by='PotentialPoints', ascending=False).head(10)
        all_df = df.copy()

        # Function for colour coding
        def style_rows(row):
            color = ''
            if 'CALL' in row['Strategy']:
                color = 'background-color: #d4edda'  # green
            elif 'PUT' in row['Strategy']:
                color = 'background-color: #f8d7da'  # red
            else:
                color = ''
            return [color]*len(row)

        # Display tables
        st.subheader("NIFTY and BANKNIFTY")
        st.dataframe(
            nifty_df.style.apply(style_rows, axis=1)
            .format({col: "{:.2f}" for col in ['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','PCR']}),
            use_container_width=True
        )

        st.subheader("Top 10 Trades")
        st.dataframe(
            top10_df.style.apply(style_rows, axis=1)
            .format({col: "{:.2f}" for col in ['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','PCR']}),
            use_container_width=True
        )

        st.subheader("All Trades")
        st.dataframe(
            all_df.style.apply(style_rows, axis=1)
            .format({col: "{:.2f}" for col in ['Entry','Exit','StopLoss','PotentialPoints','FuturePrice','MaxPain','PCR']}),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
