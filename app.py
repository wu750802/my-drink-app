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
            fee_rate = 0.03 if pay_method in ["街口", "Line Pay"] else 0.0
            
            for item in st.session_state.cart:
                order_fee = item['小計'] * fee_rate
                global_data["history"].append({
                    "類別": "訂單", "訂單編號": order_id, "時間": now_time,
                    "品項": item["品項"], "規格": item["規格"], "付款": pay_method,
                    "杯數": int(item["杯數"]), "金額": item["小計"], "手續費": order_fee,
                    "利潤": item["小計"] - item["成本小計"] - order_fee, "狀態": "製作中"
                })
            st.session_state.cart = [] 
            st.success("訂單已送出！")
            st.rerun()
        
        if st.button("🗑️ 取消整單"):
            st.session_state.cart = []
            st.rerun()

    st.divider()
    st.subheader("📝 營業雜支紀錄")
    exp_name = st.text_input("項目 (如: 買冰塊)")
    exp_amount = st.number_input("支出金額", min_value=0, value=0, step=1)
    if st.button("💸 紀錄支出", use_container_width=True):
        if exp_name and exp_amount > 0:
            tw_now = get_taiwan_time()
            global_data["expenses"].append({
                "類別": "雜支", "時間": tw_now.strftime("%H:%M"), "品項": exp_name,
                "金額": -exp_amount, "利潤": -exp_amount, "付款": "現金支出", "狀態": "已完成", "杯數": 0
            })
            st.success(f"已記錄支出: {exp_name}")
            st.rerun()

# --- 4. 主畫面顯示與統計 ---
ALL_COLS = ['類別', '訂單編號', '時間', '品項', '規格', '付款', '杯數', '金額', '手續費', '利潤', '狀態']
df_history = pd.DataFrame(global_data["history"], columns=ALL_COLS)
df_expenses = pd.DataFrame(global_data["expenses"])
df_full = pd.concat([df_history, df_expenses], ignore_index=True).fillna(0)

# 強制數值轉換
num_cols = ['金額', '手續費', '利潤', '杯數']
for col in num_cols:
    if col in df_full.columns:
        df_full[col] = pd.to_numeric(df_full[col], errors='coerce').fillna(0)
df_full['杯數'] = df_full['杯數'].astype(int)

col_main, col_stat = st.columns([3, 2])

with col_main:
    st.subheader("📋 安泰穂 - 待處理訂單")
    if st.button("🔄 刷新清單"):
        st.rerun()

    pending = df_history[df_history['狀態'] == "製作中"]
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
                        st.write(f"🔹 {row['品項']} ({row['規格']}) x {int(row['杯數'])}")
                if c_btn.button("✅ 完成製作", key=f"btn_{oid}", use_container_width=True):
                    for item in global_data["history"]:
                        if item.get('訂單編號') == oid:
                            item['狀態'] = '已完成'
                    st.rerun()
    
    if not df_expenses.empty:
        st.divider()
        st.subheader("🧾 今日雜支明細")
        st.table(df_expenses[['時間', '品項', '金額']])

with col_stat:
    st.subheader("📊 安泰穂 - 營運看板")
    if len(global_data["history"]) > 0 or len(global_data["expenses"]) > 0:
        orders_only = df_full[df_full['類別'] == "訂單"]
        rev = int(orders_only['金額'].sum())
        cups = int(orders_only['杯數'].sum())
        profit = int(df_full['利潤'].sum())
        
        m1, m2 = st.columns(2)
        m1.metric("今日總營收", f"${rev}")
        m1.metric("總銷售杯數", f"{cups} 杯")
        m2.metric("預估淨獲利 (總利潤)", f"${profit}")
        
        st.divider()
        if not orders_only.empty:
            st.write("📦 **品項銷量明細**")
            item_summary = orders_only.groupby("品項").agg({"杯數": "sum", "金額": "sum"}).sort_values(by="杯數", ascending=False)
            item_summary['杯數'] = item_summary['杯數'].astype(int)
            st.table(item_summary)
        
        if st.button("📥 下載今日總報表"):
            tw_date = get_taiwan_time().strftime('%Y%m%d')
            output = io.StringIO()
            # 寫入明細
            df_full.to_csv(output, index=False, encoding='utf-8-sig')
            
            # 寫入分隔與統計總結
            output.write("\n\n--- 營運總結 ---\n")
            output.write(f"今日總營收,${rev}\n")
            output.write(f"今日總杯數,{cups}\n")
            output.write(f"今日總利潤,${profit}\n")
            
            if not orders_only.empty:
                output.write("\n--- 品項銷量明細 ---\n")
                item_summary.to_csv(output, encoding='utf-8-sig')
            
            csv_data = output.getvalue().encode('utf-8-sig')
            st.download_button("確認下載 CSV", csv_data, f"安泰穂_報表_{tw_date}.csv", "text/csv")
            
        if st.button("🧹 結帳清空紀錄"):
            global_data["history"] = []
            global_data["expenses"] = []
            st.rerun()
    else:
        st.write("⏳ 等待資料錄入...")
