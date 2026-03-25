import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="安泰穂飲品 POS", layout="wide")
st.title("🥤 安泰穂飲品 - 多機同步點單系統")

# --- 關鍵：使用 @st.cache_resource 建立一個「所有裝置共享」的資料庫 ---
@st.cache_resource
def get_global_data():
    return {"history": []}

global_data = get_global_data()

# 選項定義
DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 側邊欄：點單員 ---
with st.sidebar:
    st.header("🛒 新增點單")
    drink = st.selectbox("品項", DRINKS)
    ice = st.radio("冰塊", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1, step=1)
    
    if st.button("➕ 加入暫存", use_container_width=True):
        st.session_state.cart.append({"品項": drink, "規格": f"{ice}/{sugar}", "杯數": int(qty)})
        st.rerun()

    if st.session_state.cart:
        st.divider()
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']}")
        
        if st.button("🚀 確認送出整單", type="primary", use_container_width=True):
            order_id = datetime.now().strftime("%H%M%S")
            for item in st.session_state.cart:
                # 這裡寫入「全域共享」的資料
                global_data["history"].append({
                    "訂單編號": order_id,
                    "時間": datetime.now().strftime("%H:%M"),
                    "品項": item["品項"],
                    "規格": item["規格"],
                    "杯數": item["杯數"],
                    "狀態": "製作中"
                })
            st.session_state.cart = []
            st.success("送單成功！所有裝置皆可同步。")
            st.rerun()

# --- 主畫面：製作員 ---
df = pd.DataFrame(global_data["history"])

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📋 待處理訂單")
    if st.button("🔄 刷新清單"):
        st.rerun()

    if not df.empty:
        pending = df[df['狀態'] == "製作中"]
        for oid, group in pending.groupby('訂單編號'):
            with st.container(border=True):
                c_info, c_btn = st.columns([4, 1])
                with c_info:
                    st.write(f"**訂單 #{oid}**")
                    for _, row in group.iterrows():
                        st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                if c_btn.button("完成", key=f"done_{oid}"):
                    # 更新全域資料中的狀態
                    for item in global_data["history"]:
                        if item['訂單編號'] == oid:
                            item['狀態'] = "已完成"
                    st.rerun()

with col_right:
    st.subheader("📊 今日銷量")
    if not df.empty:
        st.metric("總杯數", int(df['杯數'].sum()))
        stats = df.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(stats)
        
        if st.button("🗑️ 清除所有紀錄 (關店結帳)"):
            global_data["history"] = []
            st.rerun()
