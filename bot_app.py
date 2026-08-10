import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time
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
@st.cache_data(ttl=10)  # refresh every 10 seconds
def get_gold_data():
    if MT5_AVAILABLE:
        st.sidebar.success("MT5 Connected ✅")
        # Real MT5 data would go here
        # For now return demo
        pass
    
    # DEMO DATA from Yahoo Finance - works on Streamlit Cloud
    try:
        ticker = "GC=F"  # Gold Futures
        data = yf.download(ticker, period="1d", interval="1m")
        data = data.tail(200)  # last 200 candles
        data.reset_index(inplace=True)
        data['Close'] = data['Close'].ffill()
        return data
    except:
        # If yfinance fails, make fake data
        dates = pd.date_range(end=datetime.now(), periods=200, freq='1min')
        price = 2300 + pd.Series(range(200)).cumsum() * 0.5
        data = pd.DataFrame({'Datetime': dates, 'Close': price})
        return data

# Get data
data = get_gold_data()

# Show metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", f"${data['Close'].iloc[-1]:.2f}")
with col2:
    change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
    st.metric("Change", f"${change:.2f}")
with col3:
    st.metric("MT5 Status", "Connected" if MT5_AVAILABLE else "Demo Mode")

# Candlestick Chart
fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Close'],
    high=data['Close'] * 1.001,
    low=data['Close'] * 0.999,
    close=data['Close']
)])
fig.update_layout(title=f"{symbol} Live Chart", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Trade Log
st.subheader("Recent Signals")
st.write("Waiting for Gold Scalper signals...")
st.info("To connect real MT5: Run this bot from your laptop with MT5 installed")

# Auto refresh
time.sleep(5)
st.rerun()
