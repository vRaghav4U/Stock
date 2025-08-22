# streamlit_option_chain_final.py

import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import numpy as np
import time

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
    if df.shape[0] < period + 1:
        return pd.Series([np.nan]*len(df), index=df.index)
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    
    # Safe calculation for single-row or small DataFrames
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def get_optionable_stocks():
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers)
        url_eq = "https://www.nseindia.com/api/live-equity-derivatives?index=optstock"
        response = session.get(url_eq, headers=headers).json()
        stocks = [x['symbol'] for x in response['data']]
    except:
        stocks = []
    return stocks

def fetch_option_chain(symbol):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com"
    }
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=headers)
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        
        for _ in range(3):
            try:
                response = session.get(url, headers=headers, timeout=5)
                data = response.json()
                break
            except:
                time.sleep(2)
        else:
            st.warning(f"NSE blocked requests for {symbol}, falling back to Yahoo Finance.")
            return fetch_option_chain_yf(symbol)
        
        data_list = []
        records = data['records']['data']
        for rec in records:
            ce = rec.get('CE')
            pe = rec.get('PE')
            strikePrice = rec['strikePrice']
            if ce:
                data_list.append({'Type':'CE','Strike':strikePrice,'LTP':ce['lastPrice'],'OI':ce['openInterest'],'Volume':ce['totalTradedVolume']})
            if pe:
                data_list.append({'Type':'PE','Strike':strikePrice,'LTP':pe['lastPrice'],'OI':pe['openInterest'],'Volume':pe['totalTradedVolume']})
        return pd.DataFrame(data_list)
    
    except Exception as e:
        st.warning(f"Failed to fetch from NSE: {e}. Using Yahoo Finance fallback.")
        return fetch_option_chain_yf(symbol)

def fetch_option_chain_yf(symbol):
    df = yf.download(symbol+".NS" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else "^NSEI", period="5d")
    if df.empty:
        return pd.DataFrame()
    last_close = df['Close'].iloc[-1]
    data_list = [
        {'Type':'CE','Strike':last_close,'LTP':last_close,'OI':0,'Volume':0},
        {'Type':'PE','Strike':last_close,'LTP':last_close,'OI':0,'Volume':0}
    ]
    return pd.DataFrame(data_list)

def calculate_signals(symbol, rsi_length=14, break_len=20, atr_len=14, atr_mult=1.5):
    try:
        df = yf.download(symbol+".NS" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else "^NSEI",
                         period="60d", interval="15m")
    except:
        return pd.DataFrame()
    
    if df.empty or df.shape[0] < max(rsi_length, break_len, atr_len, 50):
        st.warning(f"Not enough data to calculate signals for {symbol}.")
        return pd.DataFrame()
    
    df['RSI'] = compute_rsi(df['Close'], rsi_length)
    df['HighestHigh'] = df['High'].rolling(break_len).max()
    df['LowestLow'] = df['Low'].rolling(break_len).min()
    df['MA'] = df['Close'].rolling(50).mean()
    df['ATR'] = compute_atr(df, atr_len)
    
    signals = []
    for idx in df.index:
        row = df.loc[idx]
        # Skip if any rolling value is NaN
        if pd.isna(row['ATR']) or pd.isna(row['HighestHigh']) or pd.isna(row['LowestLow']) or pd.isna(row['MA']) or pd.isna(row['RSI']):
            continue
        
        longCond  = (row['Close'] > row['HighestHigh']) and (row['RSI'] > 50) and (row['Close'] > row['MA'])
        shortCond = (row['Close'] < row['LowestLow']) and (row['RSI'] < 50) and (row['Close'] < row['MA'])
        
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

st.title("NSE Option Chain & Robust Signals")

optionable_stocks = get_optionable_stocks()
optionable_stocks += ["NIFTY","BANKNIFTY"]

symbol = st.selectbox("Select Symbol", optionable_stocks)

if st.button("Fetch Option Chain & Signals"):
    with st.spinner("Fetching data..."):
        oc = fetch_option_chain(symbol)
        signals = calculate_signals(symbol)
        time.sleep(1)
    
    st.subheader("Option Chain")
    if oc.empty:
        st.info("No option chain data available.")
    else:
        st.dataframe(oc)
    
    st.subheader("Generated Signals")
    if signals.empty:
        st.info("No signals generated due to insufficient data.")
    else:
        st.dataframe(signals)



