import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIG & SECRETS ---
DATA_FILE = "executive_memory.csv"
GRADING_FILE = "grading_data.csv"

try:
    ADMIN_PWD = st.secrets["ADMIN_PASSWORD"]
    TL_PWD = st.secrets.get("TL_PASSWORD", "tl123")
    HEAD_AML_PWD = st.secrets.get("HEAD_AML_PASSWORD", "head123")
    HEAD_CFT_PWD = st.secrets.get("HEAD_CFT_PASSWORD", "cft123")
except:
    ADMIN_PWD, TL_PWD, HEAD_AML_PWD, HEAD_CFT_PWD = "admin_access_123", "tl123", "head123", "cft123"

st.set_page_config(page_title="JSB Trade Audit", layout="wide")

# --- HIERARCHY DATA ---
HIERARCHY = {
    "BASIT.RAHIM": ["DAWAR.IMAM", "BISMA.KHAN", "AMNAH.KHAN", "K.MEHDI"],
    "IRFAN.HASAN": ["SHAHZAIB.QURESHI", "MARYAM.TAHIR", "MSALMAN.K", "MUJEEB.ARIF", "RIMSHA.IQBAL"],
    "HASSAN.WASEEM": ["FABIHA.IRSHAD", "RIZA.ALI", "A.ASLAM", "MUHAMMAD.AHMER"],
    "REHAN.SYED": ["SHABBIR.SHAH", "AREEB.ALI", "WAQAR.AHMAD20374", "AMRA.SIDDIQUI"]
}
TEAM_LEADS = list(HIERARCHY.keys())
GRADE_POINTS = {"1": 30, "2": 25, "3": 20, "4": 15}

# --- HELPER FUNCTIONS ---
def load_data(file):
    return pd.read_csv(file) if os.path.exists(file) else None

def save_data(df, file):
    df.to_csv(file, index=False)

# --- SIDEBAR LOGIN ---
with st.sidebar:
    st.header("🔐 Secure Access")
    role = st.radio("Select Role", ["Viewer", "Admin", "Team Lead", "Head AML", "Head AML/CFT"])
    pwd = st.text_input("Password", type="password")

# --- ADMIN: FILE UPLOAD ---
if role == "Admin" and pwd == ADMIN_PWD:
    st.subheader("Admin: Data Management")
    m = st.selectbox("Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    y = st.selectbox("Year", [2024, 2025, 2026])
    month_label = f"{m} {y}"
    
    perf_file = st.file_uploader("Activity Report", type=["xls", "xlsx"])
    str_file = st.file_uploader("STR List", type=["xls", "xlsx"])

    if perf_file and str_file:
        # Note: 'xlrd' and 'openpyxl' must be in requirements.txt
        df_perf = pd.read_excel(perf_file, header=2).fillna(0)
        df_str = pd.read_excel(str_file).fillna(0)
        
        # Logic: AMRA.SIDDIQUI 5:1 Ratio
        def adjust_vol(row):
            vol = row['Maker_Vol']
            if row['OWNER ID'] == "AMRA.SIDDIQUI":
                return vol / 5
            return vol

        # Standard Processing
        df_perf.columns = df_perf.columns.str.strip()
        maker_cols = ['SEND RFI', 'RECOMMEND CLOSE WITHOUT SAR', 'RECOMMEND CLOSE AND GENERATE SAR']
        df_perf['Maker_Vol'] = df_perf[[c for c in maker_cols if c in df_perf.columns]].sum(axis=1)
        df_perf['Adjusted_Vol'] = df_perf.apply(adjust_vol, axis=1)
        
        # Merge STRs
        master = pd.merge(df_perf, df_str, left_on='OWNER ID', right_on=df_str.columns[0], how='left').fillna(0)
        
        # Case Points (70% Weighting)
        master['Case_Points'] = (master['Adjusted_Vol'] + (master.get('STR', 0) * 20) + (master.get('PRI STR', 0) * 4)) * 0.7
        master['Report_Month'] = month_label
        
        if st.button("🚀 Publish Raw Data"):
            save_data(master, DATA_FILE)
            st.success("Data Published!")

# --- TEAM LEAD: GRADING ---
elif role == "Team Lead" and pwd == TL_PWD:
    tl_name = st.selectbox("Identify Yourself", TEAM_LEADS)
    analysts = HIERARCHY[tl_name]
    st.subheader(f"Grading for Team: {tl_name}")
    
    gradings = load_data(GRADING_FILE) or pd.DataFrame(columns=["Name", "Grade", "Points", "Status"])
    
    for a in analysts:
        col1, col2 = st.columns(2)
        with col1: st.write(a)
        with col2: grade = st.selectbox(f"Grade {a}", ["1", "2", "3", "4"], key=a)
        # Update logic here to save gradings
    
    if st.button("Submit Gradings"):
        st.info("Gradings submitted for Head AML review.")

# --- HEAD AML: REVIEW & TL GRADING ---
elif role == "Head AML" and pwd == HEAD_AML_PWD:
    st.subheader("Head AML: Review Analyst Grades & Grade Team Leads")
    # Show Pending Analyst Grades
    # Option to Grade the 4 Team Leads
    st.write("Reviewing TLs: " + ", ".join(TEAM_LEADS))

# --- HEAD AML/CFT: FINAL ENDORSEMENT ---
elif role == "Head AML/CFT" and pwd == HEAD_CFT_PWD:
    st.subheader("Head AML/CFT: Final Approval")
    st.warning("Pending Approval: Final Performance Scores")

# --- DASHBOARD VIEW ---
raw_data = load_data(DATA_FILE)
if raw_data is not None:
    st.title("🏆 Performance Excellence Board")
    
    # Calculate Final Score (Case Points + Grading Points)
    # For now, showing based on Case Points until gradings approved
    top_5 = raw_data.nlargest(5, 'Case_Points')
    
    # Podium (Visual Representation)
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: flex-end; gap: 20px;">
        <div style="text-align: center;">🥈<br><div style="background:#e5e4e2; padding:20px; border-radius:10px;">{top_5.iloc[1]['OWNER ID']}</div></div>
        <div style="text-align: center;">🥇<br><div style="background:#ffd700; padding:40px; border-radius:10px;">{top_5.iloc[0]['OWNER ID']}</div></div>
        <div style="text-align: center;">🥉<br><div style="background:#cd7f32; padding:15px; border-radius:10px;">{top_5.iloc[2]['OWNER ID']}</div></div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("Dashboard waiting for Admin data upload.")