import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- SETTINGS & STORAGE ---
DATA_FILE = "executive_memory.csv"
ADMIN_PASSWORD = "admin_access_123" 

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
    if pwd == ADMIN_PASSWORD:
        st.success("Access Granted")
        
        # Month Picker
        m = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        y = st.selectbox("Year", [2024, 2025, 2026])
        month_label = f"{m} {y}"
        
        perf_file = st.file_uploader("Upload Activity Report", type=["xls", "xlsx"])
        str_file = st.file_uploader("Upload STR List", type=["xls", "xlsx"])
        
        if st.button("🗑️ Wipe Dashboard"):
            if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
            st.rerun()
    else:
        perf_file, str_file, month_label = None, None, ""

# --- DATA ENGINE ---
if perf_file and str_file:
    df_perf = pd.read_excel(perf_file, header=2).fillna(0)
    df_str = pd.read_excel(str_file).fillna(0)
    df_perf.columns = df_perf.columns.str.strip()
    df_str.columns = df_str.columns.str.strip()
    
    maker_cols = ['SEND RFI', 'RECOMMEND CLOSE WITHOUT SAR', 'RECOMMEND CLOSE AND GENERATE SAR']
    checker_cols = ['CLOSE WITHOUT SAR', 'CLOSE AND GENERATE SAR', 'LINK AND CLOSE AS MERGE']
    
    df_perf['Maker_Vol'] = df_perf[maker_cols].sum(axis=1)
    df_perf['Checker_Vol'] = df_perf[[c for c in checker_cols if c in df_perf.columns]].sum(axis=1)
    
    str_key = 'Team Member' if 'Team Member' in df_str.columns else df_str.columns[0]
    master = pd.merge(df_perf, df_str, left_on='OWNER ID', right_on=str_key, how='left').fillna(0)
    master['Total_Score'] = master['Maker_Vol'] + master['Checker_Vol'] + (master['STR'] * 20) + (master['PRI STR'] * 4)

    if st.button(f"🚀 Publish {month_label}"):
        save_data(master, month_label)
        st.success("Dashboard Updated!")
        st.rerun()

# --- THE VIEW ---
data = load_data()

if data is not None:
    current_month = data['Report_Month'].iloc[0]
    st.markdown(f"<h1 style='text-align: center;'>🏆 Performance Excellence Board</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #FFD700;'>{current_month} Performance</h3>", unsafe_allow_html=True)
    
    tab_analyst, tab_tl, tab_explorer = st.tabs(["📊 Analyst Rankings", "👑 Team Lead Rankings", "🔍 Full Explorer"])

    with tab_analyst:
        top_5 = data[data['Maker_Vol'] > 0].nlargest(5, 'Total_Score').reset_index(drop=True)
        
        # CLEAN PODIUM (2-1-3) - Emoji Removed from Rank 1
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: flex-end; gap: 30px; margin-top: 40px; margin-bottom: 40px;">
            <div style="text-align: center;">
                <div style="font-size: 45px;">🥈</div>
                <div style="background: #e5e4e2; border-radius: 50%; width: 110px; height: 110px; display: flex; align-items: center; justify-content: center; margin: auto; color: black; font-weight: bold; font-size: 12px; border: 3px solid #c0c0c0;">{top_5.iloc[1]['OWNER ID']}</div>
                <p><b>Rank 2</b><br>{int(top_5.iloc[1]['Total_Score'])} Pts</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 55px; margin-bottom: 5px;">🥇</div>
                <div style="background: #ffd700; border: 5px solid #b8860b; border-radius: 50%; width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; margin: auto; color: black; font-weight: bold; box-shadow: 0px 10px 20px rgba(0,0,0,0.3); font-size: 14px;">{top_5.iloc[0]['OWNER ID']}</div>
                <p style="font-size: 18px;"><b>Winner</b><br>{int(top_5.iloc[0]['Total_Score'])} Pts</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 45px;">🥉</div>
                <div style="background: #cd7f32; border-radius: 50%; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; margin: auto; color: black; font-weight: bold; font-size: 11px; border: 3px solid #8b4513;">{top_5.iloc[2]['OWNER ID']}</div>
                <p><b>Rank 3</b><br>{int(top_5.iloc[2]['Total_Score'])} Pts</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # RANK 4 & 5 BADGES
        c4, c5 = st.columns(2)
        with c4:
            st.markdown(f"""<div style="text-align: center; padding: 15px; border: 2px solid #555; border-radius: 15px; background-color: rgba(255,255,255,0.05);">
                <span style="font-size: 30px;">⭐</span><br><b>Rank 4</b><br><span style="font-size: 18px;">{top_5.iloc[3]['OWNER ID']}</span><br><span style="color: #4CAF50; font-weight: bold;">{int(top_5.iloc[3]['Total_Score'])} Pts</span>
            </div>""", unsafe_allow_html=True)
        with c5:
            st.markdown(f"""<div style="text-align: center; padding: 15px; border: 2px solid #555; border-radius: 15px; background-color: rgba(255,255,255,0.05);">
                <span style="font-size: 30px;">⭐</span><br><b>Rank 5</b><br><span style="font-size: 18px;">{top_5.iloc[4]['OWNER ID']}</span><br><span style="color: #4CAF50; font-weight: bold;">{int(top_5.iloc[4]['Total_Score'])} Pts</span>
            </div>""", unsafe_allow_html=True)

    with tab_tl:
        # Team Lead logic (Checker Volume)
        tl_data = data[data['Checker_Vol'] > 0].nlargest(5, 'Total_Score').reset_index(drop=True)
        if not tl_data.empty:
            st.markdown("<h4 style='text-align: center;'>👑 Top Performing Team Leads</h4>", unsafe_allow_html=True)
            fig = px.bar(tl_data, x='OWNER ID', y='Total_Score', color='Total_Score', 
                         color_continuous_scale='Viridis', text_auto=True)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(tl_data[['OWNER ID', 'Total_Score', 'Checker_Vol']], use_container_width=True, hide_index=True)
        else:
            st.info("No Team Lead data available for this month.")

    with tab_explorer:
        st.subheader("🕵️ Detailed Performance Explorer")
        search = st.multiselect("Filter by Analyst Name:", options=sorted(data['OWNER ID'].unique()))
        filtered = data[data['OWNER ID'].isin(search)] if search else data
        st.dataframe(filtered[['OWNER ID', 'Maker_Vol', 'Checker_Vol', 'STR', 'PRI STR', 'Total_Score']].sort_values('Total_Score', ascending=False), 
                     use_container_width=True, hide_index=True)

else:
    st.info("📢 The Dashboard is ready. Admin: Please login to publish the latest monthly report.")