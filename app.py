import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 網頁基礎設定
st.set_page_config(page_title="泰式飲品 POS", layout="wide")
st.title("🥤 泰式飲品 - 雲端點單系統")

# --- 1. 請在此處輸入你的 Google 試算表完整網址 ---
# 確認你的試算表已開啟「知道連結的任何人」皆可「編輯」
SHEET_URL = "https://docs.google.com/spreadsheets/d/1apQ3JzTtEaFniD896dkOwDNfc4pxOy8DSzY5S4yLglA/edit?gid=0#gid=0"

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取資料函數
def load_data():
    try:
        # 讀取工作表，若為空則回傳預設結構
        data = conn.read(spreadsheet=SHEET_URL, ttl="0s")
        if data.empty:
            return pd.DataFrame(columns=['訂單編號', '時間', '品項', '規格', '杯數', '狀態'])
        return data
    except Exception:
        return pd.DataFrame(columns=['訂單編號', '時間', '品項', '規格', '杯數', '狀態'])

# 寫入資料函數
def save_data(df):
    conn.update(spreadsheet=SHEET_URL, data=df)
    st.cache_data.clear()

# 選項定義
DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

# 初始化購物車
if 'cart' not in st.session_state:
    st.session_state.cart = []

# --- 2. 側邊欄：點單 (手機端) ---
with st.sidebar:
    st.header("🛒 新增點單")
    drink = st.selectbox("品項", DRINKS)
    ice = st.radio("冰塊", ICE, horizontal=True, index=2)
    sugar = st.radio("甜度", SUGAR, horizontal=True, index=2)
    qty = st.number_input("杯數", min_value=1, value=1, step=1)
    
    if st.button("➕ 加入暫存", use_container_width=True):
        st.session_state.cart.append({"品項": drink, "規格": f"{ice}/{sugar}", "杯數": qty})
        st.rerun()

    if st.session_state.cart:
        st.divider()
        st.write("📝 目前暫存：")
        for i, item in enumerate(st.session_state.cart):
            st.write(f"{i+1}. {item['品項']} x {item['杯數']}")
        
        if st.button("🚀 確認送出整單", type="primary", use_container_width=True):
            with st.spinner('正在同步至雲端...'):
                current_df = load_data()
                order_id = datetime.now().strftime("%H%M%S")
                new_entries = []
                for item in st.session_state.cart:
                    new_entries.append({
                        "訂單編號": str(order_id),
                        "時間": datetime.now().strftime("%H:%M"),
                        "品項": item["品項"],
                        "規格": item["規格"],
                        "杯數": int(item["杯數"]),
                        "狀態": "製作中"
                    })
                new_df = pd.DataFrame(new_entries)
                # 確保欄位順序一致
                updated_df = pd.concat([current_df, new_df], ignore_index=True)
                save_data(updated_df)
                st.session_state.cart = []
                st.success("點單成功！")
                st.rerun()
        
        if st.button("🗑️ 清空暫存"):
            st.session_state.cart = []
            st.rerun()

# --- 3. 主畫面：顯示與統計 (平板端) ---
df = load_data()

col_list, col_stat = st.columns([3, 2])

with col_list:
    st.subheader("📋 待處理訂單")
    if st.button("🔄 刷新清單"):
        st.rerun()

    if not df.empty and '狀態' in df.columns:
        pending = df[df['狀態'] == "製作中"]
        if pending.empty:
            st.info("✨ 目前沒有待辦訂單")
        else:
            for oid, group in pending.groupby('訂單編號'):
                with st.container(border=True):
                    c_info, c_btn = st.columns([4, 1])
                    with c_info:
                        st.write(f"**訂單 #{oid}**")
                        for _, row in group.iterrows():
                            st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                    if c_btn.button("完成", key=f"btn_{oid}"):
                        # 更新狀態
                        idx = df[df['訂單編號'] == oid].index
                        df.loc[idx, '狀態'] = "已完成"
                        save_data(df)
                        st.rerun()
    else:
        st.info("尚未有任何訂單紀錄")

with col_stat:
    st.subheader("📊 今日銷量")
    if not df.empty and '品項' in df.columns:
        # 轉換杯數為數字避免錯誤
        df['杯數'] = pd.to_numeric(df['杯數'], errors='coerce').fillna(0)
        total = int(df['杯數'].sum())
        st.metric("總點單量", f"{total} 杯")
        
        chart_data = df.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(chart_data)
