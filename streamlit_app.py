# streamlit_app.py

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Live Option Signals", layout="wide")
st.title("Live Options Screener Signals from Sensibull")

# -----------------------------
# Function to fetch table data
# -----------------------------
@st.cache_data(ttl=60)
def fetch_sensibull_data():
    url = "https://web.sensibull.com/options-screener?view=table"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find table
    table = soup.find("table")
    if not table:
        st.warning("Could not find the table on the page. Sensibull may have blocked requests.")
        return pd.DataFrame()

    # Read HTML table into pandas
    df = pd.read_html(str(table))[0]
    return df

# -----------------------------
# Function to generate signals
# -----------------------------
def generate_signals(df):
    df = df.copy()
    df['Signal'] = 'HOLD'

    # Ensure numeric columns
    numeric_cols = ['Fut Price','ATM IV','IV Chg','IVP','OI % Chg','PCR','Max Pain']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # CALL conditions
    call_cond = (df['Fut Price'] > df['Max Pain']) & (df['OI % Chg'] > 0) & (df['PCR'] < 0.8)
    df.loc[call_cond, 'Signal'] = 'CALL'

    # PUT conditions
    put_cond = (df['Fut Price'] < df['Max Pain']) & (df['OI % Chg'] > 0) & (df['PCR'] > 1.2)
    df.loc[put_cond, 'Signal'] = 'PUT'

    return df

# -----------------------------
# Main
# -----------------------------
df = fetch_sensibull_data()
if df.empty:
    st.warning("No data available. Sensibull may have blocked the request or table structure changed.")
else:
    df_signals = generate_signals(df)
    st.dataframe(df_signals, use_container_width=True)
