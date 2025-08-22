import pandas as pd
import numpy as np
import yfinance as yf

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

def calculate_signals(symbol, rsi_length=14, break_len=20, atr_len=14, atr_mult=1.5):
    # Download data (Yahoo fallback for NIFTY/BANKNIFTY)
    try:
        ticker = symbol+".NS" if symbol.upper() not in ["NIFTY","BANKNIFTY"] else "^NSEI"
        df = yf.download(ticker, period="60d", interval="15m")
    except:
        return pd.DataFrame()
    
    # Ensure we have enough rows
    min_rows_needed = max(rsi_length, break_len, atr_len, 50)
    if df.empty or df.shape[0] < min_rows_needed:
        return pd.DataFrame()
    
    # Compute indicators
    df['RSI'] = compute_rsi(df['Close'], rsi_length)
    df['HighestHigh'] = df['High'].rolling(break_len, min_periods=1).max()
    df['LowestLow'] = df['Low'].rolling(break_len, min_periods=1).min()
    df['MA'] = df['Close'].rolling(50, min_periods=1).mean()
    df['ATR'] = compute_atr(df, atr_len)
    
    # Convert all necessary columns to numeric
    for col in ['Close','HighestHigh','LowestLow','MA','RSI','ATR']:
        if col not in df.columns:
            return pd.DataFrame()
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filter out rows with any NaNs
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
    
    # Return only the rows with signals
    signals = df[df['Signal'] != ''][['Signal','StopLoss','Close']]
    signals.reset_index(inplace=True)
    signals.rename(columns={'index':'Datetime','Close':'Price'}, inplace=True)
    
    return signals
