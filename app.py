import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="安泰穂點單系統", layout="wide")
st.title("🥤 安泰穂飲品 - 每日點單管理")

# --- 2. 飲料與規格定義 ---
DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

# --- 3. 初始化雲端記憶體資料 (只要不重啟 App，資料都在) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 4. 側邊欄：手機點單員 ---
with st.sidebar:
    st.header("🛒 新增點單")
    drink = st.selectbox("品項", DRINKS)
    ice = st.radio("冰塊", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1, step=1)
    
    if st.button("➕ 加入暫存", use_container_width=True):
        st.session_state.cart.append({
            "品項": drink, 
            "規格": f"{ice}/{sugar}", 
            "杯數": int(qty)
        })
        st.rerun()

    if st.session_state.cart:
        st.divider()
        st.write("📝 目前暫存：")
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']}")
        
        if st.button("🚀 確認送出整單", type="primary", use_container_width=True):
            order_id = datetime.now().strftime("%H%M%S")
            now_time = datetime.now().strftime("%H:%M")
            for item in st.session_state.cart:
                st.session_state.history.append({
                    "訂單編號": order_id,
                    "時間": now_time,
                    "品項": item["品項"],
                    "規格": item["規格"],
                    "杯數": item["杯數"],
                    "狀態": "製作中"
                })
            st.session_state.cart = []
            st.success("送單成功！")
            st.rerun()
        
        if st.button("🗑️ 清空暫存"):
            st.session_state.cart = []
            st.rerun()

# --- 5. 主畫面：製作員與統計 ---
df = pd.DataFrame(st.session_state.history)

col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📋 待處理訂單")
    if st.button("🔄 刷新清單"):
        st.rerun()

    if not df.empty:
        pending = df[df['狀態'] == "製作中"]
        if pending.empty:
            st.info("✨ 目前沒有待辦訂單，休息一下吧！")
        else:
            # 依照訂單編號分組顯示
            for oid, group in pending.groupby('訂單編號'):
                with st.container(border=True):
                    c_info, c_btn = st.columns([4, 1])
                    with c_info:
                        st.write(f"**訂單 #{oid}** (時間: {group['時間'].iloc[0]})")
                        for _, row in group.iterrows():
                            st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                    if c_btn.button("完成", key=f"done_{oid}"):
                        for i, item in enumerate(st.session_state.history):
                            if item['訂單編號'] == oid:
                                st.session_state.history[i]['狀態'] = "已完成"
                        st.rerun()
    else:
        st.info("尚未有任何訂單，請從左側下單。")

with col_right:
    st.subheader("📊 今日銷量統計")
    if not df.empty:
        total_cups = int(df['杯數'].sum())
        st.metric("今日總杯數", f"{total_cups} 杯")
        
        # 繪製統計圖
        stats = df.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(stats)
        
        st.divider()
        # 下載報表功能
        st.subheader("📥 每日總表匯出")
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下載今日訂單明細 (CSV)",
            data=csv_data,
            file_name=f"drinks_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            use_container_width=True
        )
        
        if st.button("⚠️ 清除所有紀錄 (關店結帳用)", type="secondary", use_container_width=True):
            st.session_state.history = []
            st.rerun()
