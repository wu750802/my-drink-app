with open('app.py', 'w', encoding='utf-8') as f:
    f.write("""
import streamlit as st
import pandas as pd
from datetime import datetime

# 網頁設定
st.set_page_config(page_title="飲料點單系統", layout="wide")
st.title("🥤 雲端飲料點單與統計 (手機/平板同步版)")

# 選項
DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

# 初始化 Session (存放在雲端記憶體中)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 側邊欄：手機點單區 ---
with st.sidebar:
    st.header("🛒 新增點單")
    drink = st.selectbox("品項", DRINKS)
    ice = st.radio("冰塊", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1)
    
    if st.button("➕ 加入暫存", use_container_width=True):
        st.session_state.cart.append({"品項": drink, "規格": f"{ice}/{sugar}", "杯數": qty})

    if st.session_state.cart:
        st.divider()
        st.write("📝 暫存清單：")
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']}")
        
        if st.button("🚀 確認送出整單", type="primary", use_container_width=True):
            order_id = datetime.now().strftime("%H%M%S")
            for item in st.session_state.cart:
                item['ID'] = order_id
                item['時間'] = datetime.now().strftime("%H:%M")
                item['狀態'] = "製作中"
                st.session_state.history.append(item)
            st.session_state.cart = []
            st.success("訂單已送出！")
            st.rerun()
        
        if st.button("🗑️ 清空暫存"):
            st.session_state.cart = []
            st.rerun()

# --- 主畫面：平板統計區 ---
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📋 待處理訂單")
    if not st.session_state.history:
        st.info("目前沒有訂單")
    else:
        df = pd.DataFrame(st.session_state.history)
        pending = df[df['狀態'] == "製作中"]
        
        if pending.empty:
            st.success("✨ 所有訂單已完成！")
        else:
            for oid, group in pending.groupby('ID'):
                with st.container(border=True):
                    c_info, c_btn = st.columns([4, 1])
                    with c_info:
                        st.write(f"**訂單 #{oid}** (時間: {group['時間'].iloc[0]})")
                        for _, row in group.iterrows():
                            st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                    if c_btn.button("完成", key=oid):
                        for i, h in enumerate(st.session_state.history):
                            if h['ID'] == oid: st.session_state.history[i]['狀態'] = "已完成"
                        st.rerun()

with col2:
    st.subheader("📊 今日統計")
    if st.session_state.history:
        df_all = pd.DataFrame(st.session_state.history)
        st.metric("總杯數", f"{df_all['杯數'].sum()} 杯")
        
        stats = df_all.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(stats)
    else:
        st.write("尚無統計數據")
""")
