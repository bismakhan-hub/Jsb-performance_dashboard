import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PERSISTENCE & PRIVACY ---
DATA_FILE = "executive_memory.csv"
ADMIN_PASSWORD = "your_chosen_password" # Use Streamlit Secrets for better security

st.set_page_config(page_title="Performance Excellence Board", layout="wide")

# --- SIDEBAR: SECURE ADMIN ---
with st.sidebar:
    st.header("🔐 Admin Controls")
    pwd = st.text_input("Enter Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Admin Access Granted")
        m = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        y = st.selectbox("Year", [2024, 2025, 2026])
        month_label = f"{m} {y}"
        perf_file = st.file_uploader("Upload Activity Report", type=["xls", "xlsx"])
        str_file = st.file_uploader("Upload STR List", type=["xls", "xlsx"])
    else:
        perf_file, str_file, month_label = None, None, ""

# --- DATA ENGINE (Fixes KeyError) ---
if perf_file and str_file:
    df_perf = pd.read_excel(perf_file, header=2).fillna(0)
    df_str = pd.read_excel(str_file).fillna(0)
    df_perf.columns = df_perf.columns.str.strip()
    df_str.columns = df_str.columns.str.strip()
    
    # Maker/Checker scoring
    maker_cols = ['SEND RFI', 'RECOMMEND CLOSE WITHOUT SAR', 'RECOMMEND CLOSE AND GENERATE SAR']
    checker_cols = ['CLOSE WITHOUT SAR', 'CLOSE AND GENERATE SAR', 'LINK AND CLOSE AS MERGE']
    df_perf['Maker_Vol'] = df_perf[maker_cols].sum(axis=1)
    df_perf['Checker_Vol'] = df_perf[[c for c in checker_cols if c in df_perf.columns]].sum(axis=1)
    
    # SMART JOIN KEY: Automatically finds 'Team Member' or 'OWNER ID'
    str_key = next((col for col in df_str.columns if col.lower() in ['team member', 'owner id']), df_str.columns[0])
    
    master = pd.merge(df_perf, df_str, left_on='OWNER ID', right_on=str_key, how='left').fillna(0)
    master['Total_Score'] = master['Maker_Vol'] + master['Checker_Vol'] + (master.get('STR', 0) * 20) + (master.get('PRI STR', 0) * 4)

    if st.button(f"🚀 Publish {month_label}"):
        master['Report_Month'] = month_label
        master.to_csv(DATA_FILE, index=False)
        st.rerun()

# --- DISPLAY BOARD ---
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE)
    current_month = data['Report_Month'].iloc[0]
    st.markdown(f"<h1 style='text-align: center;'>🏆 Performance Excellence Board</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: orange;'>{current_month}</h3>", unsafe_allow_html=True)
    
    tab_rank, tab_tl, tab_explorer = st.tabs(["👑 Top Rankings", "👑 Team Lead Rankings", "🔍 Team Explorer"])

    with tab_rank:
        top_5 = data[data['Maker_Vol'] > 0].nlargest(5, 'Total_Score').reset_index(drop=True)
        # 2ndndndnd-1st-3rd podium logic here using st.markdown flexbox
        # Use star emojis for Rank 4 and 5 in st.columns

    with tab_tl:
        tl_data = data[data['Checker_Vol'] > 0].nlargest(5, 'Total_Score').reset_index(drop=True)
        st.plotly_chart(px.bar(tl_data, x='OWNER ID', y='Total_Score', text_auto=True), use_container_width=True)

    with tab_explorer:
        st.dataframe(data[['OWNER ID', 'Total_Score']].sort_values('Total_Score', ascending=False), use_container_width=True)
