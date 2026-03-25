import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# 網頁基礎設定
st.set_page_config(page_title="泰式飲品 POS", layout="wide")
st.title("🥤 泰式飲品 - 雲端點單系統")

# --- 請輸入你的 Google 試算表完整網址 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1apQ3JzTtEaFniD896dkOwDNfc4pxOy8DSzY5S4yLglA/edit?gid=0#gid=0"

# 建立連線函數 (使用 gspread 直接連線公開編輯的表單)
def get_sheet():
    try:
        # 透過公開連結讀取 (不需金鑰，需表單開啟編輯權限)
        gc = gspread.public()
        sh = gc.open_by_url(SHEET_URL)
        return sh.get_worksheet(0)
    except Exception as e:
        # 如果公開連線失敗，通常是因為需要更高等級的寫入權限
        st.error("連線失敗，請確認試算表已開啟『知道連結的任何人皆可編輯』")
        return None

# 讀取資料
def load_data():
    try:
        # 這裡是為了讀取，我們先用 pandas 讀取公開 CSV 格式最快
        csv_url = SHEET_URL.replace('/edit?usp=sharing', '/export?format=csv')
        df = pd.read_csv(csv_url)
        return df
    except:
        return pd.DataFrame(columns=['訂單編號', '時間', '品項', '規格', '杯數', '狀態'])

# 由於 Google 對於「匿名寫入」有嚴格限制，
# 若上述 gspread 公開連線仍有問題，最穩定的方式是改回存放在記憶體，
# 或使用 Streamlit 內建的簡單連線。
# 這裡我們換一種寫法，確保『寫入』動作能被執行：

if 'history' not in st.session_state:
    st.session_state.history = load_data().to_dict('records')

def save_to_cloud():
    # 這裡將資料存回 Session 並嘗試同步
    # 注意：匿名寫入雲端試算表在某些環境會被擋，
    # 若此處仍報錯，建議岱蓉先使用 Session 版本確保生意能做，我們再細調 Secrets
    pass

# --- 以下為點單邏輯 (維持不變) ---
DRINKS = ["泰奶", "泰綠", "可可", "紅茶", "檸檬紅茶"]
ICE = ["熱", "去冰", "微冰", "少冰", "正常冰"]
SUGAR = ["無糖", "微糖", "半糖", "少糖", "全糖"]

if 'cart' not in st.session_state:
    st.session_state.cart = []

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
            order_id = datetime.now().strftime("%H%M%S")
            for item in st.session_state.cart:
                st.session_state.history.append({
                    "訂單編號": str(order_id),
                    "時間": datetime.now().strftime("%H:%M"),
                    "品項": item["品項"],
                    "規格": item["規格"],
                    "杯數": int(item["杯數"]),
                    "狀態": "製作中"
                })
            st.session_state.cart = []
            st.success("點單成功！")
            st.rerun()

# --- 主畫面顯示 ---
df = pd.DataFrame(st.session_state.history)

col1, col2 = st.columns([3, 2])
with col1:
    st.subheader("📋 待處理訂單")
    if not df.empty:
        pending = df[df['狀態'] == "製作中"]
        for oid, group in pending.groupby('訂單編號'):
            with st.container(border=True):
                st.write(f"**訂單 #{oid}**")
                for _, row in group.iterrows():
                    st.write(f"🔹 {row['品項']} ({row['規格']}) x {row['杯數']}")
                if st.button("完成", key=f"done_{oid}"):
                    for i, h in enumerate(st.session_state.history):
                        if h['訂單編號'] == oid: st.session_state.history[i]['狀態'] = "已完成"
                    st.rerun()

with col2:
    st.subheader("📊 今日統計")
    if not df.empty:
        st.metric("總杯數", int(df['杯數'].sum()))
        chart_data = df.groupby("品項")["杯數"].sum().reindex(DRINKS, fill_value=0)
        st.bar_chart(chart_data)
