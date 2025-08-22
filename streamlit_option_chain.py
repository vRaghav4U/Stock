# streamlit_option_chain.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Option Trade Signals", layout="wide")

# =========================
# Indicator Functions
# =========================
def compute_rsi(series, length=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(length, min_periods=1).mean()
    avg_loss = loss.rolling(length, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_atr(df, length=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(length, min_periods=1).mean()
    return atr

# =========================
# Main Signal Calculation
# =========================
def calculate_signals(symbol, rsi_length=14, break_len=20, atr_len=14, atr_mult=1.5):
    # Download data (Yahoo fallback)
    try:
        ticker = symbol+".NS" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else "^NSEI"
        df = yf.download(ticker, period="60d", interval="15m")
    except:
        return pd.DataFrame()
    
    # Minimum rows check
    min_rows_needed = max(rsi_length, break_len, atr_len, 50)
    if df.empty or df.shape[0] < min_rows_needed:
        return pd.DataFrame()
    
    # Compute indicators
    df['RSI'] = compute_rsi(df['Close'], rsi_length)
    df['HighestHigh'] = df['High'].rolling(break_len, min_periods=1).max()
    df['LowestLow'] = df['Low'].rolling(break_len, min_periods=1).min()
    df['MA'] = df['Close'].rolling(50, min_periods=1).mean()
    df['ATR'] = compute_atr(df, atr_len)
    
    # Ensure numeric
    for col in ['Close','HighestHigh','LowestLow','MA','RSI','ATR']:
        if col not in df.columns:
            return pd.DataFrame()
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filter NaNs
    df = df.dropna(subset=['Close','HighestHigh','LowestLow','MA','RSI','ATR'])
    if df.empty:
        return pd.DataFrame()
    
    # Generate signals
    df['Signal'] = ''
    df['StopLoss'] = np.nan
    
    long_mask  = (df['Close'] > df['HighestHigh']) & (df['RSI'] > 50) & (df['Close'] > df['MA'])
    short_mask = (df['Close'] < df['LowestLow']) & (df['RSI'] < 50) & (df['Close'] < df['MA'])
    
    df.loc[long_mask, ['Signal','StopLoss']]  = ['CALL', df['Close'] - atr_mult * df['ATR']]
    df.loc[short_mask, ['Signal','StopLoss']] = ['PUT',  df['Close'] + atr_mult * df['ATR']]
    
    # Prepare final table
    signals = df[df['Signal'] != ''][['Signal','StopLoss','Close']]
    signals.reset_index(inplace=True)
    signals.rename(columns={'index':'Datetime','Close':'Price'}, inplace=True)
    
    return signals

# =========================
# Streamlit UI
# =========================
st.title("📊 Option Trade Signals")
st.write("This app calculates CALL/PUT signals for stocks and indices using RSI, MA, ATR, and breakout levels.")

# User input
symbol = st.text_input("Enter Stock/Index Symbol (e.g., RELIANCE, NIFTY, BANKNIFTY)", value="NIFTY")
atr_mult = st.slider("ATR Stop Loss Multiplier", min_value=0.5, max_value=5.0, value=1.5, step=0.1)

# Run calculation
if st.button("Generate Signals"):
    with st.spinner("Fetching data and calculating signals..."):
        signals = calculate_signals(symbol, atr_mult=atr_mult)
    
    if signals.empty:
        st.warning("No signals found or not enough data to calculate indicators.")
    else:
        # Color-code CALL/PUT
        def color_row(row):
            if row.Signal == 'CALL':
                return ['background-color: #b6fcb6']*len(row)
            else:
                return ['background-color: #fcb6b6']*len(row)
        
        st.subheader(f"Signals for {symbol.upper()}")
        st.dataframe(signals.style.apply(color_row, axis=1))
