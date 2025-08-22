# streamlit_option_chain.py

import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import numpy as np
from time import sleep

# =========================
# Helper functions
# =========================

def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rsi = 100 - (100/(1 + ma_up/ma_down))
    return rsi

def compute_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = high_low.combine(high_close, max).combine(low_close, max)
    atr = tr.rolling(period).mean()
    return atr

def get_optionable_stocks():
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    url_eq = "https://www.nseindia.com/api/live-equity-derivatives?index=optstock"
    try:
        response = session.get(url_eq, headers=headers).json()
        stocks = [x['symbol'] for x in response['data']]
    except:
        stocks = []
    return stocks

def fetch_option_chain(symbol):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers).json()
    
    data = []
    records = response['records']['data']
    for rec in records:
        ce = rec.get('CE')
        pe = rec.get('PE')
        strikePrice = rec['strikePrice']
        if ce:
            data.append({'Type':'CE','Strike':strikePrice,'LTP':ce['lastPrice'],'OI':ce['openInterest'],'Volume':ce['totalTradedVolume']})
        if pe:
            data.append({'Type':'PE','Strike':strikePrice,'LTP':pe['lastPrice'],'OI':pe['openInterest'],'Volume':pe['totalTradedVolume']})
    df = pd.DataFrame(data)
    return df

def calculate_signals(symbol, rsi_length=14, break_len=20, atr_len=14, atr_mult=1.5):
    try:
        df = yf.download(symbol+".NS", period="60d", interval="15m")
    except:
        return pd.DataFrame()
    
    df['RSI'] = compute_rsi(df['Close'], rsi_length)
    df['HighestHigh'] = df['High'].rolling(break_len).max()
    df['LowestLow'] = df['Low'].rolling(break_len).min()
    df['MA'] = df['Close'].rolling(50).mean()
    df['ATR'] = compute_atr(df, atr_len)
    
    signals = []
    for idx, row in df.iterrows():
        longCond  = row['Close'] > row['HighestHigh'] and row['RSI'] > 50 and row['Close'] > row['MA']
        shortCond = row['Close'] < row['LowestLow'] and row['RSI'] < 50 and row['Close'] < row['MA']
        longSL = row['Close'] - atr_mult * row['ATR']
        shortSL = row['Close'] + atr_mult * row['ATR']
        
        if longCond:
            signals.append({'Datetime': idx, 'Symbol': symbol, 'Signal': 'CALL', 'StopLoss': longSL, 'Close': row['Close']})
        elif shortCond:
            signals.append({'Datetime': idx, 'Symbol': symbol, 'Signal': 'PUT', 'StopLoss': shortSL, 'Close': row['Close']})
    return pd.DataFrame(signals)

# =========================
# Streamlit UI
# =========================
st.title("NSE Option Chain & Trading Signals")

# Dropdown for stocks
optionable_stocks = get_optionable_stocks()
optionable_stocks += ["NIFTY","BANKNIFTY"]

symbol = st.selectbox("Select Symbol", optionable_stocks)

if st.button("Fetch Option Chain & Signals"):
    with st.spinner("Fetching data..."):
        oc = fetch_option_chain(symbol)
        signals = calculate_signals(symbol)
        sleep(1)
    
    st.subheader("Option Chain")
    st.dataframe(oc)  # interactive table
    
    st.subheader("Generated Signals")
    st.dataframe(signals)
