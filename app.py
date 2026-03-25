import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# 網頁基礎設定
st.set_page_config(page_title="安泰穂 POS 系統", layout="wide")
st.title("🥤 安泰穂 - 專屬點單與財務管理系統")

# --- 1. 飲品數據設定 ---
DRINK_DATA = {
    "泰奶": {"成本": 28, "賣價": 70},
    "泰綠": {"成本": 32, "賣價": 70},
    "可可": {"成本": 24, "賣價": 60},
    "紅茶": {"成本": 11, "賣價": 50},
    "檸檬紅茶": {"成本": 20, "賣價": 60}
}
DRINKS = list(DRINK_DATA.keys())
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]
PAYMENTS = ["現金", "街口", "Line Pay"]

# --- 定義台灣時間函數 ---
def get_taiwan_time():
    return datetime.utcnow() + timedelta(hours=8)

# --- 2. 建立共享資料庫 ---
@st.cache_resource
def get_global_data():
    return {"history": [], "expenses": []}

global_data = get_global_data()

if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 3. 側邊欄：點單與雜支 ---
with st.sidebar:
    st.markdown("## 🏪 安泰穂 - 點單櫃檯")
    st.subheader("第一步：挑選飲品")
    drink = st.selectbox("選擇品項", DRINKS)
    price = DRINK_DATA[drink]["賣價"]
    st.info(f"💰 單價: ${price}")
    
    ice = st.radio("冰塊選擇", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度選擇", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1, step=1)
    
    if st.button("➕ 加入暫存", use_container_width=True):
        cost = DRINK_DATA[drink]["成本"]
        st.session_state.cart.append({
            "品項": drink, "規格": f"{ice}/{sugar}", "杯數": int(qty),
            "單價": price, "小計": price * int(qty), "成本小計": cost * int(qty)
        })
        st.rerun()

    if st.session_state.cart:
        st.divider()
        st.subheader("第二步：結帳確認")
        temp_total = sum(item['小計'] for item in st.session_state.cart)
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {int(item['杯數'])} — **${item['小計']}**")
        
        st.markdown(f"### 🚩 需付款總計: :red[${temp_total}]")
        pay_method = st.selectbox("選擇付款方式", PAYMENTS)
        
        if st.button("🚀 確認收款並送出訂單", type="primary", use_container_width=True):
            tw_now = get_taiwan_time()
            order_id = tw_now.strftime("%H%M%S")
            now_time = tw_now.strftime("%H:%M")
            fee_rate = 0.03 if pay_method in ["街口", "Line Pay"]
