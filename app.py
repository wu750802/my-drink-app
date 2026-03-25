import streamlit as st
import pandas as pd
from datetime import datetime

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

# --- 2. 建立共享資料庫 ---
@st.cache_resource
def get_global_data():
    return {"history": []}

global_data = get_global_data()

# 初始化暫存購物車
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 3. 側邊欄：點單員 ---
with st.sidebar:
    st.markdown(f"## 🏪 安泰穂 - 點單櫃檯")
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
            "品項": drink,
            "規格": f"{ice}/{sugar}",
            "杯數": int(qty),
            "單價": price,
            "小計": price * int(qty),
            "成本小計": cost * int(qty)
        })
        st.rerun()

    if st.session_state.cart:
        st.divider()
        st.subheader("第二步：結帳確認")
        temp_total = sum(item['小計'] for item in st.session_state.cart)
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']} — **${item['小計']}**")
        
        st.markdown(f"### 🚩 需付款總計: :red[${temp_total}]")
        pay_method = st.selectbox("選擇付款方式", PAYMENTS)
        
        if st.button("🚀 確認收款並送出訂單", type="primary", use_container_width=True):
            order_id = datetime.now().strftime("%H%M%S")
            now_time = datetime.now().strftime("%H:%M")
            fee_rate = 0.03 if pay_method in ["街口", "Line Pay"] else 0
            
            for item in st.session_state.cart:
                order_fee = item['小計'] * fee_rate
                global_data["history"].append({
                    "訂單編號": order_id,
                    "時間": now_time,
                    "品項": drink, # 修正變數名稱
                    "規格": item["規格"],
                    "付款": pay_method,
                    "杯數": item["杯數"],
                    "金額": item["小計"],
                    "手續費": order_fee,
                    "利潤": item["小計"] - item["成本小計"] - order_fee,
                    "狀態": "製作中"
                })
            st.session_state.cart = [] 
            st.success("訂單送出成功！")
            st.rerun()
        
        if st.button("🗑️ 取消整單"):
            st.session_state.cart = []
            st.rerun()

# --- 4. 主畫面：顯示與統計 ---
# 強制定義欄位結構，避免任何 KeyError
columns = ['訂單編號', '時間', '品項', '規格', '付款', '杯數', '金額', '手續費', '利潤', '狀態']
df = pd.DataFrame(global_data["history"], columns=columns)

col_main, col_stat = st.columns([3, 2])

with col_main:
    st.subheader("📋 安泰穂 - 待處理訂單")
    if st.button("🔄 刷新清單"):
        st.rerun()

    pending = df[df['狀態'] == "製作中"]
    if pending.empty:
        st.info("✨ 目前沒有待辦訂單。")
    else:
        for oid, group in pending.groupby('訂單編號'):
            with st.container(border=True):
                c_info, c_btn = st.columns([4, 1.5])
                with c_info:
                    t_price = group['金額'].sum()
                    t_pay = group['付款'].iloc[0]
                    st.write(f"**訂單 #{oid}** | 付款: :blue[{t_pay}] | **總額: ${t_price}**")
                    for _, row in group.iterrows():
                        st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                if c_btn.button("✅ 完成", key=f"btn_{oid}", use_container_width=True):
                    for item in global_data["history"]:
                        if item['訂單編號'] == oid:
                            item['狀態'] = "已完成"
                    st.rerun()

with col_stat:
    st.subheader("📊 今日營運統計")
    # 使用 try
