import streamlit as st
import pandas as pd
import MetaTrader5 as mt5
import pytz
import time
from datetime import datetime, time as dtime

st.set_page_config(page_title="Gold AutoTrader", layout="wide")
st.title("🥇 Gold AutoTrader - London Killzone")

# --- SETTINGS ---
symbol = "XAUUSD"
lot_size = 0.01
sl_pips = 150  # 15 pips
tp_pips = 300  # 30 pips
daily_loss_limit = 10.0  # $10
magic_number = 12345

# --- CONNECT MT5 ---
if not mt5.initialize():
    st.error("MT5 NOT CONNECTED! Open MT5 on your PC first")
    st.stop()
else:
    st.sidebar.success("MT5 CONNECTED ✅")

account = mt5.account_info()
st.sidebar.metric("Balance", f"${account.balance:.2f}")
st.sidebar.metric("Equity", f"${account.equity:.2f}")

# --- TRADING FUNCTIONS ---
def get_data():
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 300)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
    df['rsi'] = 100 - (100 / (1 + df['close'].pct_change().rolling(14).mean() / df['close'].pct_change().rolling(14).std()))
    return df

def in_london_session():
    gmt = pytz.timezone('GMT')
    now = datetime.now(gmt).time()
    return dtime(8,0) <= now <= dtime(11,0)

def place_trade(order_type):
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    sl = price - sl_pips * 0.1 if order_type == mt5.ORDER_TYPE_BUY else price + sl_pips * 0.1
    tp = price + tp_pips * 0.1 if order_type == mt5.ORDER_TYPE_BUY else price - tp_pips * 0.1
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": magic_number,
        "comment": "London Killzone Bot",
    }
    result = mt5.order_send(request)
    return result

# --- MAIN LOGIC ---
daily_pnl = 0
positions = mt5.positions_get(symbol=symbol)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Session", "LONDON OPEN" if in_london_session() else "CLOSED")
with col2:
    st.metric("Open Trades", len(positions))
with col3:
    st.metric("Daily P&L", f"${daily_pnl:.2f}")

data = get_data()
last = data.iloc[-1]

# TRADING RULES
can_trade = len(positions) == 0 and in_london_session() and daily_pnl > -daily_loss_limit

if can_trade:
    # BUY RULE: Price > VWAP AND RSI > 50
    if last['close'] > last['vwap'] and last['rsi'] > 50:
        st.warning("BUY SIGNAL! Placing order...")
        res = place_trade(mt5.ORDER_TYPE_BUY)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            st.success(f"BUY ORDER PLACED! Ticket: {res.order}")
    
    # SELL RULE: Price < VWAP AND RSI < 50
    elif last['close'] < last['vwap'] and last['rsi'] < 50:
        st.warning("SELL SIGNAL! Placing order...")
        res = place_trade(mt5.ORDER_TYPE_SELL)
        if res.retcode == mt5.TRADE_RETCODE_DONE:
            st.success(f"SELL ORDER PLACED! Ticket: {res.order}")
else:
    st.info("Waiting for London session 8-11am GMT or Daily limit reached")

# Auto refresh every 10 seconds
time.sleep(10)
st.rerun()
