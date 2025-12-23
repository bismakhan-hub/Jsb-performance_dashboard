import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- SETTINGS & STORAGE ---
DATA_FILE = "executive_memory.csv"

# FIXED: This now looks at your Streamlit "Secrets" vault
# Make sure you have ADMIN_PASSWORD = "admin_access_123" saved in your App Settings!
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except:
    ADMIN_PASSWORD = "admin_access_123" # Fallback for local testing

st.set_page_config(page_title="Performance Dashboard", layout="wide")

def save_data(df, month_label):
    df['Report_Month'] = month_label
    df.to_csv(DATA_FILE, index=False)

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return None

# --- SIDEBAR: ADMIN CONTROLS ---
with st.sidebar:
    st.header("🔐 Admin Access")
    pwd = st.text_input("Password", type="password")
    
    # Initialize these as None so the app doesn't crash
    perf_file, str_file, month_label = None, None, ""
    
    if pwd == ADMIN_PASSWORD:
        st.success("Access Granted")
        
        # Month Picker
        m = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        y = st.selectbox("Year", [2024, 2025, 2026])
        month_label = f"{m} {y}"
        
        perf_file = st.file_uploader("Upload Activity Report", type=["xls", "xlsx"])
        str_file = st.file_uploader("Upload STR List", type=["xls", "xlsx"])
        
        if st.button("🗑️ Wipe Dashboard"):
            if os.path.exists(DATA_FILE): 
                os.remove(DATA_FILE)
            st.rerun()

# --- DATA ENGINE ---
# This part only runs if the Admin is logged in and files are uploaded
if perf_file and str_file:
    try:
        df_perf = pd.read_excel(perf_file, header=2).fillna(0)
        df_str = pd.read_excel(str_file).fillna(0)
        
        df_perf.columns = df_perf.columns.str.strip()
        df_str.columns = df_str.columns.str.strip()
        
        maker_cols = ['SEND RFI', 'RECOMMEND CLOSE WITHOUT SAR', 'RECOMMEND CLOSE AND GENERATE SAR']
        checker_cols = ['CLOSE WITHOUT SAR', 'CLOSE AND GENERATE SAR', 'LINK AND CLOSE AS MERGE']
        
        # Calculate Scores
        df_perf['Maker_Vol'] = df_perf[[c for c in maker_cols if c in df_perf.columns]].sum(axis=1)
        df_perf['Checker_Vol'] = df_perf[[c for c in checker_cols if c in df_perf.columns]].sum(axis=1)
        
        str_key = 'Team Member' if 'Team Member' in df_str.columns else df_str.columns[0]
        master = pd.merge(df_perf, df_str, left_on='OWNER ID', right_on=str_key, how='left').fillna(0)
        
        # Formula: Maker + Checker + (STR * 20) + (PRI STR * 4)
        master['Total_Score'] = master['Maker_Vol'] + master['Checker_Vol'] + (master.get('STR', 0) * 20) + (master.get('PRI STR', 0) * 4)

        if st.button(f"🚀 Publish {month_label}"):
            save