import streamlit as st
import pandas as pd
import pytz
import time
import numpy as np
from datetime import datetime, time as dtime

st.set_page_config(page_title="Gold AutoTrader", layout="wide")
st.title("🥇 Gold AutoTrader - London Killzone")

# --- TRY CONNECT MT5 ---
MT5_AVAILABLE = False
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        MT5_AVAILABLE = True
        account = mt5.account_info()
        st.sidebar.success("MT5 CONNECTED - REAL TRADING ✅")
        st.sidebar.metric("Balance", f"${account.balance:.2f}")
    else:
        st.sidebar.error("MT5 Not Logged In")
except:
    st.sidebar.warning("Demo Mode - No MT5 Found")

# --- SETTINGS ---
symbol = "XAUUSD"
lot_size = 0.01
sl_pips = 150  # 15 pips
tp_pips = 300  # 30 pips
daily_loss_limit = 10.0  # $10
magic_number = 12345

# --- TRADING FUNCTIONS ---
def get_demo_data():
    dates = pd.date_range(end=datetime.now(), periods=300, freq='1min')
    price = 4400 + np.cumsum(np.random.randn(300) * 0.8)
    df = pd.DataFrame({'time': dates, 'close': price})
    df['vwap'] = df['close'].rolling(50).mean()
    df['rsi'] = 50 + np.random.randn(300) * 10
    return df

def get_mt5_data():
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 300)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain/loss))
    return df

def in_london_session():
    gmt = pytz.timezone('GMT')
    now = datetime.now(gmt).time()
    return dtime(8,0) <= now <= dtime(11,0)

def place_trade(order_type):
    if not MT5_AVAILABLE:
        st.info("DEMO: Would place trade here")
        return
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    sl = price - sl_pips * 0.1 if order_type == mt5.ORDER_TYPE_BUY else price + sl_pips * 0.1
    tp = price + tp_pips * 0.1 if order_type == mt5.ORDER_TYPE_BUY else price - tp_pips * 0.1
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol, "volume": lot_size, "type": order_type,
        "price": price, "sl": sl, "tp": tp, "magic": magic_number,
        "comment": "London Killzone Bot",
    }
    result = mt5.order_send(request)
    return result

# --- MAIN LOGIC ---
data = get_mt5_data() if MT5_AVAILABLE else get_demo_data()
last = data.iloc[-1]
positions = mt5.positions_get(symbol=symbol) if MT5_AVAILABLE else []

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Session", "LONDON OPEN" if in_london_session() else "CLOSED")
with col2:
    st.metric("Open Trades", len(positions))
with col3:
    st.metric("Mode", "REAL" if MT5_AVAILABLE else "DEMO")

st.subheader("Live Chart")
st.line_chart(data, x='time', y='close')

# TRADING RULES
can_trade = len(positions) == 0 and in_london_session()

if can_trade:
    if last['close'] > last['vwap'] and last['rsi'] > 50:
        st.success("BUY SIGNAL!")
        place_trade(mt5.ORDER_TYPE_BUY if MT5_AVAILABLE else 0)
    elif last['close'] < last['vwap'] and last['rsi'] < 50:
        st.error("SELL SIGNAL!")
        place_trade(mt5.ORDER_TYPE_SELL if MT5_AVAILABLE else 1)
else:
    st.info("Waiting for London session 8-11am GMT")

time.sleep(10)
st.rerun()
