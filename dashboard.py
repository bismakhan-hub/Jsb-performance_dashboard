import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- FILE PATHS ---
DATA_FILE = "executive_memory.csv"
GRADING_FILE = "grading_data.csv"

# --- ALL PASSWORDS CONFIG ---
# Set these in your Streamlit Advanced Settings > Secrets
ADMIN_PWD = st.secrets.get("ADMIN_PASSWORD", "admin_123")
TL_PWD = st.secrets.get("TL_PASSWORD", "tl_pass_456")
HEAD_AML_PWD = st.secrets.get("HEAD_AML_PASSWORD", "aml_head_789")
HEAD_CFT_PWD = st.secrets.get("HEAD_CFT_PASSWORD", "cft_head_000")

st.set_page_config(page_title="Performance Dashboard", layout="wide")

# --- HIERARCHY DATA ---
HIERARCHY = {
    "BASIT.RAHIM": ["DAWAR.IMAM", "BISMA.KHAN", "AMNAH.KHAN", "K.MEHDI"],
    "IRFAN.HASAN": ["SHAHZAIB.QURESHI", "MARYAM.TAHIR", "MSALMAN.K", "MUJEEB.ARIF", "RIMSHA.IQBAL"],
    "HASSAN.WASEEM": ["FABIHA.IRSHAD", "RIZA.ALI", "A.ASLAM", "MUHAMMAD.AHMER"],
    "REHAN.SYED": ["SHABBIR.SHAH", "AREEB.ALI", "WAQAR.AHMAD20374", "AMRA.SIDDIQUI"]
}
GRADE_POINTS = {"1": 30, "2": 25, "3": 20, "4": 15}

# --- 70% CALCULATION LOGIC ---
def calculate_system_score(row):
    owner = str(row.get('OWNER ID', '')).strip()
    # Targets for 70% achievement
    if owner == "AMRA.SIDDIQUI":
        t_cases, t_strs, t_pri = 200, 6, 20 
    else:
        t_cases, t_strs, t_pri = 40, 2, 10

    # Actuals
    a_cases = row.get('SEND RFI', 0) + row.get('RECOMMEND CLOSE WITHOUT SAR', 0) + row.get('RECOMMEND CLOSE AND GENERATE SAR', 0)
    a_strs = row.get('STR', 0)
    a_pri = row.get('PRI STR', 0)

    # Capped Achievement Ratios
    case_perf = min(a_cases / t_cases, 1.0) if t_cases > 0 else 0
    str_perf = min(a_strs / t_strs, 1.0) if t_strs > 0 else 0
    pri_perf = min(a_pri / t_pri, 1.0) if t_pri > 0 else 0

    return max(case_perf, str_perf, pri_perf) * 70

# --- SIDEBAR LOGIN ---
with st.sidebar:
    st.header("🔐 Access Control")
    role = st.radio("Select Role", ["Viewer", "Admin", "Team Lead", "Head AML", "Head AML/CFT"])
    pwd = st.text_input("Enter Password", type="password")

# --- 1. ADMIN PORTAL: FILE UPLOAD & YEAR SELECTION ---
if role == "Admin" and pwd == ADMIN_PWD:
    st.subheader("🛠️ Admin: Publish Performance Data")
    
    # Selection Controls
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Select Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    with col2:
        year = st.selectbox("Select Year", [2024, 2025, 2026])
    
    # File Uploaders
    st.markdown("---")
    perf_file = st.file_uploader("Upload Activity Report (Excel)", type=["xls", "xlsx"])
    str_file = st.file_uploader("Upload STR List (Excel)", type=["xls", "xlsx"])

    if perf_file and str_file:
        if st.button("🚀 Calculate & Publish Dashboard"):
            try:
                # Process Excel Files
                df_p = pd.read_excel(perf_file, header=2).fillna(0)
                df_s = pd.read_excel(str_file).fillna(0)
                df_p.columns = df_p.columns.str.strip()
                
                # Merge Data
                master = pd.merge(df_p, df_s, left_on='OWNER ID', right_on=df_s.columns[0], how='left').fillna(0)
                
                # Apply 70% Calculation Engine
                master['Case_Points'] = master.apply(calculate_system_score, axis=1)
                master['Final_Score'] = master['Case_Points'] # Initial value before TL Grading
                master['Report_Month'] = f"{month} {year}"
                
                # Save to memory to prevent KeyErrors
                master.to_csv(DATA_FILE, index=False)
                st.success(f"Successfully published data for {month} {year}!")
            except Exception as e:
                st.error(f"Error processing files: {e}")

# --- 2. TEAM LEAD PORTAL: GRADING ---
elif role == "Team Lead" and pwd == TL_PWD:
    tl_name = st.selectbox("Select Your Name", list(HIERARCHY.keys()))
    st.subheader(f"Grading Portal: {tl_name}")
    
    analysts = HIERARCHY[tl_name]
    new_grades = []
    for a in analysts:
        g = st.selectbox(f"Grade for {a}", ["1", "2", "3", "4"], key=a)
        new_grades.append({"Analyst": a, "Grade": g, "Points": GRADE_POINTS[g], "Status": "Pending Head AML"})
    
    if st.button("Submit Gradings"):
        pd.DataFrame(new_grades).to_csv(GRADING_FILE, index=False)
        st.success("Gradings submitted for approval.")

# --- 3. HEAD AML / HEAD AML/CFT: APPROVAL ---
elif role in ["Head AML", "Head AML/CFT"] and pwd in [HEAD_AML_PWD, HEAD_CFT_PWD]:
    st.subheader(f"{role}: Review & Final Endorsement")
    if os.path.exists(GRADING_FILE):
        grades = pd.read_csv(GRADING_FILE)
        st.dataframe(grades)
        if st.button("Endorse All & Update Dashboard"):
            data = pd.read_csv(DATA_FILE)
            for _, row in grades.iterrows():
                data.loc[data['OWNER ID'] == row['Analyst'], 'Final_Score'] = data['Case_Points'] + row['Points']
            data.to_csv(DATA_FILE, index=False)
            st.success("Final Scores published to Dashboard!")
    else:
        st.info("No pending gradings found.")

# --- 4. DASHBOARD VIEW (VIEWER ROLE) ---
if os.path.exists(DATA_FILE):
    data = pd.read_csv(DATA_FILE).sort_values("Final_Score", ascending=False).reset_index(drop=True)
    st.title("🏆 Performance Excellence Board")
    st.markdown(f"<h3 style='text-align: center;'>{data['Report_Month'].iloc[0]}</h3>", unsafe_allow_html=True)
    
    # Rankings Display
    st.dataframe(data[['OWNER ID', 'Final_Score']], use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ No data published yet. Admin must upload files.")