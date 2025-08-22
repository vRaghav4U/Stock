# streamlit_sensibull_upload.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sensibull Option Signals", layout="wide")
st.title("Option Signals from Sensibull CSV")

st.markdown("""
Upload your Sensibull options CSV file below. The app will calculate simple CALL/PUT/HOLD signals based on the data.
""")

# -----------------------------
# Upload CSV
# -----------------------------
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Data")
        st.dataframe(df, use_container_width=True)

        # -----------------------------
        # Clean numeric columns
        # -----------------------------
        numeric_cols = ['Fut Price','ATM IV','IV Chg','IVP','OI % Chg','PCR','Max Pain']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # -----------------------------
        # Generate Signals
        # -----------------------------
        df['Signal'] = 'HOLD'

        # CALL if Futures Price > Max Pain AND PCR < 0.8
        call_cond = (df['Fut Price'] > df['Max Pain']) & (df['PCR'] < 0.8)
        df.loc[call_cond, 'Signal'] = 'CALL'

        # PUT if Futures Price < Max Pain AND PCR > 1.2
        put_cond = (df['Fut Price'] < df['Max Pain']) & (df['PCR'] > 1.2)
        df.loc[put_cond, 'Signal'] = 'PUT'

        st.subheader("Option Signals")
        st.dataframe(df[['Stock','Fut Price','Max Pain','PCR','Signal']], use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a CSV file exported from Sensibull to calculate signals.")
