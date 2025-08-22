import streamlit as st
import pandas as pd
import numpy as np
from math import exp, sqrt, log
from scipy.stats import norm

st.set_page_config(page_title="Top Option Strategies", layout="wide")
st.title("Top Option Strategies from Sensibull CSV with P/L")

# --- Black-Scholes for ATM Option Premium with safety ---
def bs_option_price(S, K, T=30/365, r=0.05, sigma=0.3, option_type='call'):
    """Black-Scholes Option Price with safety checks"""
    if sigma <= 0 or T <= 0:
        return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if option_type=='call':
        return S*norm.cdf(d1) - K*exp(-r*T)*norm.cdf(d2)
    else:
        return K*exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

st.markdown("Upload your Sensibull CSV to calculate top 10 option strategies with potential profit/loss.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        # Convert numeric columns safely
        numeric_cols = ['FuturePrice','ATMIV','ATMIVChange','IVPercentile','FutureOIPercentChange','PCR','MaxPain']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Initialize strategy columns
        df['Signal'] = 'HOLD'
        df['Comments'] = ''
        df['Entry'] = df['FuturePrice']
        df['Exit'] = df['MaxPain']
        df['Premium'] = 0.0
        df['MaxProfit'] = 0.0
        df['MaxLoss'] = 0.0
        df['RewardRisk'] = 0.0

        # Strategy logic
        if all(x in df.columns for x in ['FuturePrice','MaxPain','PCR','ATMIV']):
            # CALL signal: FuturePrice > MaxPain & low PCR
            call_cond = (df['FuturePrice'] > df['MaxPain']) & (df['PCR'] < 0.8)
            df.loc[call_cond, 'Signal'] = 'CALL'
            df.loc[call_cond, 'Comments'] = "Bullish: Future > Max Pain & low PCR"

            # PUT signal: FuturePrice < MaxPain & high PCR
            put_cond = (df['FuturePrice'] < df['MaxPain']) & (df['PCR'] > 1.2)
            df.loc[put_cond, 'Signal'] = 'PUT'
            df.loc[put_cond, 'Comments'] = "Bearish: Future < Max Pain & high PCR"

            # Calculate ATM Premium & P/L
            for idx, row in df.iterrows():
                if row['Signal'] != 'HOLD':
                    S = row['FuturePrice']
                    K = round(S/50)*50  # Approx ATM strike rounded to nearest 50
                    sigma = row['ATMIV']/100 if row['ATMIV'] > 0 else 0.01
                    option_type = row['Signal'].lower()
                    premium = bs_option_price(S, K, sigma=sigma, option_type=option_type)
                    df.at[idx,'Premium'] = round(premium,2)

                    # MaxProfit / MaxLoss assuming simple exit at MaxPain
                    if row['Signal'] == 'CALL':
                        df.at[idx,'MaxProfit'] = max(row['Exit'] - S - premium,0)
                    else:
                        df.at[idx,'MaxProfit'] = max(S - row['Exit'] - premium,0)
                    df.at[idx,'MaxLoss'] = premium
                    if df.at[idx,'MaxLoss']>0:
                        df.at[idx,'RewardRisk'] = round(df.at[idx,'MaxProfit']/df.at[idx,'MaxLoss'],2)

        # Top 10 strategies by Reward/Risk
        top_strategies = df[df['Signal'] != 'HOLD'].sort_values(by='RewardRisk', ascending=False).head(10)

        st.subheader("Top 10 Option Strategies with Potential P/L")
        st.dataframe(top_strategies[['Instrument','Signal','Entry','Exit','Premium','MaxProfit','MaxLoss','RewardRisk','Comments']].fillna('N/A'), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a CSV file exported from Sensibull.")
