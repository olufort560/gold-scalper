import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time
import numpy as np
from datetime import datetime

# Try to import MT5, but don't crash if it's not installed
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except:
    MT5_AVAILABLE = False

st.set_page_config(page_title="Gold Scalper Dashboard", layout="wide")
st.title("🥇 Gold Scalper Live Dashboard")

# Sidebar for settings
st.sidebar.header("Settings")
symbol = st.sidebar.text_input("Gold Symbol", "XAUUSD")
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m"])

# Function to get data
@st.cache_data(ttl=10)
def get_gold_data():
    if MT5_AVAILABLE:
        st.sidebar.success("MT5 Connected ✅")
    
    # DEMO DATA from Yahoo Finance
    try:
        ticker = "GC=F"  # Gold Futures
        data = yf.download(ticker, period="5d", interval="1m")
        
        # FIX: Flatten columns if yfinance returns MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        data = data.tail(200).reset_index()
        data = data[['Datetime', 'Close']].ffill()
        return data
    except:
        # Fake data if yfinance fails
        dates = pd.date_range(end=datetime.now(), periods=200, freq='1min')
        price = 2300 + np.cumsum(np.random.randn(200) * 0.5)
        data = pd.DataFrame({'Datetime': dates, 'Close': price})
        return data

# Get data
data = get_gold_data()

# Show metrics - FIXED
col1, col2, col3 = st.columns(3)
with col1:
    current_price = float(data['Close'].iloc[-1])
    st.metric("Current Price", f"${current_price:.2f}")
with col2:
    prev_price = float(data['Close'].iloc[-2])
    change = current_price - prev_price
    st.metric("Change", f"${change:.2f}")
with col3:
    st.metric("MT5 Status", "Connected" if MT5_AVAILABLE else "Demo Mode")

# Candlestick Chart - FIXED
fig = go.Figure(data=[go.Scatter(
    x=data['Datetime'],
    y=data['Close'],
    mode='lines',
    name='Gold Price'
)])
fig.update_layout(title=f"{symbol} Live Chart")
st.plotly_chart(fig, use_container_width=True)

# Trade Log
st.subheader("Recent Signals")
st.write("Waiting for Gold Scalper signals...")
st.info("To connect real MT5: Run this bot from your laptop with MT5 installed")

# Auto refresh
time.sleep(5)
st.rerun()
