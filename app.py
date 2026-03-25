import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime


st.set_page_config(page_title="泰式飲品 POS 系統", layout="wide")
st.title("🥤 泰式飲品 - 雲端同步點單系統")


SHEET_URL = "https://docs.google.com/spreadsheets/d/1apQ3JzTtEaFniD896dkOwDNfc4pxOy8DSzY5S4yLglA/edit?gid=0#gid=0"

conn = st.connection("gsheets", type=GSheetsConnection)


def load_data():
    try:
        return conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2,3,4,5], ttl="0s")
    except:
        return pd.DataFrame(columns=['訂單編號', '時間', '品項', '規格', '杯數', '狀態'])


def save_data(df):
    conn.update(spreadsheet=SHEET_URL, data=df)
    st.cache_data.clear()


DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

if 'cart' not in st.session_state:
    st.session_state.cart = []


with st.sidebar:
    st.header("🛒 快速點單")
    drink = st.selectbox("品項", DRINKS)
    ice = st.radio("冰塊", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1)
    
    if st.button("➕ 加入購物車", use_container_width=True):
        st.session_state.cart.append({"品項": drink, "規格": f"{ice}/{sugar}", "杯數": qty})

    if st.session_state.cart:
        st.divider()
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']}")
        
        if st.button("🚀 確認送出訂單", type="primary", use_container_width=True):
            current_df = load_data()
            order_id = datetime.now().strftime("%H%M%S")
            new_rows = []
            for item in st.session_state.cart:
                new_rows.append({
                    "訂單編號": order_id,
                    "時間": datetime.now().strftime("%H:%M"),
                    "品項": item["品項"],
                    "規格": item["規格"],
                    "杯數": item["杯數"],
                    "狀態": "製作中"
                })
            updated_df = pd.concat([current_df, pd.DataFrame(new_rows)], ignore_index=True)
            save_data(updated_df)
            st.session_state.cart = []
            st.success("訂單已同步至 Google Sheets！")
            st.rerun()


df = load_data()

col_list, col_stat = st.columns([3, 2])

with col_list:
    st.subheader("📋 待處理訂單")
    # 定時自動重新整理按鈕 (Streamlit Cloud 建議手動按或加自動重新整理)
    if st.button("🔄 重新整理訂單"):
        st.rerun()

    if not df.empty:
        pending = df[df['狀態'] == "製作中"]
        if pending.empty:
            st.success("✨ 目前沒有待辦訂單")
        else:
            for oid, group in pending.groupby('訂單編號'):
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.write(f"**訂單 #{oid}**")
                        for _, row in group.iterrows():
                            st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                    if c2.button("完成", key=f"done_{oid}"):
                        df.loc[df['訂單編號'] == oid, '狀態'] = "已完成"
                        save_data(df)
                        st.rerun()

with col_stat:
    st.subheader("📊 今日銷量統計")
    if not df.empty:
        st.metric("今日總杯數", f"{df['杯數'].astype(int).sum()} 杯")
        stats = df.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(stats)
