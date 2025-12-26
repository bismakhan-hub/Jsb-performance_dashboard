import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. GLOBAL SHARED STORAGE ---
# This @st.cache_resource creates a memory space shared by ALL users.
@st.cache_resource
def get_global_store():
    return {
        "mtd_data": None,
        "submitted_ratings": set(),
        "pending_tl_ratings": [],
        "pending_head_aml_ratings": [],
        "approved_ratings": {}
    }

global_store = get_global_store()

# Helper to push updates to the shared memory
def save_to_global():
    global_store["mtd_data"] = st.session_state.mtd_data
    global_store["submitted_ratings"] = st.session_state.submitted_ratings
    global_store["pending_tl_ratings"] = st.session_state.pending_tl_ratings
    global_store["pending_head_aml_ratings"] = st.session_state.pending_head_aml_ratings
    global_store["approved_ratings"] = st.session_state.approved_ratings

# --- 2. INITIALIZATION ---
if 'role' not in st.session_state: st.session_state.role = None
if 'user_name' not in st.session_state: st.session_state.user_name = None

# Automatically load the shared data for the current user
st.session_state.mtd_data = global_store["mtd_data"]
st.session_state.submitted_ratings = global_store["submitted_ratings"]
st.session_state.pending_tl_ratings = global_store["pending_tl_ratings"]
st.session_state.pending_head_aml_ratings = global_store["pending_head_aml_ratings"]
st.session_state.approved_ratings = global_store["approved_ratings"]

st.set_page_config(layout="wide", page_title="AML Performance Board")

# --- 3. STYLING ---
st.markdown("""
    <style>
    .comparison-box { background-color: #0d1117; border: 2px solid #30363d; border-radius: 15px; padding: 20px; height: 100%; }
    .vertical-line { border-left: 2px dashed #444; height: 550px; margin: 0 auto; }
    .rank-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; text-align: center; color: white; margin: 5px; }
    .rank-star { color: #FFD700; font-size: 20px; }
    .rank-name { font-weight: bold; font-size: 16px; margin-top: 5px; }
    .rank-pts { color: #4CAF50; font-weight: bold; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- HIERARCHY ---
TEAM_STRUCTURE = {
    "BASIT.RAHIM": ["DAWAR.IMAM", "BISMA.KHAN", "AMNAH.KHAN", "K.MEHDI"],
    "IRFAN.HASAN": ["SHAHZAIB.QURESHI", "MARYAM.TAHIR", "MSALMAN.K", "MUJEEB.ARIF"],
    "HASSAN.WASEEM": ["FABIHA.IRSHAD", "RIZA.ALI", "A.ASLAM", "MUHAMMAD.AHMER", "RIMSHA.IQBAL"],
    "REHAN.SYED": ["SHABBIR.SHAH", "AREEB.ALI", "WAQAR.AHMAD20374", "AMRA.SIDDIQUI"]
}

PASSWORDS = {
    "Admin": st.secrets.get("ADMIN_PASSWORD", "admin_access_123"),
    "Head AML/CFT": "CFT@Head2025",
    "Head AML": "HeadAML!123", 
    "Team Lead": "TL@AML2025", 
    "Analyst": "AMLView"
}

# --- 4. LOGIN SYSTEM ---
if not st.session_state.role:
    st.title("🛡️ AML Portal Secure Login")
    r = st.selectbox("Select Role", ["Viewer"] + list(PASSWORDS.keys()))
    selected_name = st.selectbox("Select Your Name", list(TEAM_STRUCTURE.keys())) if r == "Team Lead" else r
    p = st.text_input("Password", type="password") if r != "Viewer" else ""
    
    if st.button("Login"):
        if r == "Viewer" or p == PASSWORDS[r]:
            st.session_state.role, st.session_state.user_name = r, selected_name
            st.rerun()
        else: st.error("Access Denied")
else:
    # --- 5. TOP BAR ---
    st.sidebar.info(f"User: {st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

    st.title("🏆 Performance Excellence Board")
    c1, c2 = st.columns(2)
    with c1: sel_year = st.selectbox("Select Year", [2024, 2025], index=1)
    with c2:
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        sel_month_name = st.selectbox("Select Month", months, index=10)
        sel_month = months.index(sel_month_name) + 1

    # --- 6. CALCULATION ENGINE ---
    def calculate_performance(fccm_df, str_df, month):
        fccm_df.columns = [str(c).upper().strip() for c in fccm_df.columns]
        str_df.columns = [str(c).upper().strip() for c in str_df.columns]
        df = pd.merge(fccm_df, str_df.rename(columns={"TEAM MEMBER": "OWNER ID"}), on="OWNER ID", how="outer").fillna(0)
        
        amra_row = df[df['OWNER ID'].str.contains("AMRA.SIDDIQUI", na=False, case=False)]
        amra_raw_fccm = (amra_row.iloc[0].get('SEND RFI', 0) + amra_row.iloc[0].get('RECOMMEND CLOSE WITHOUT SAR', 0)) if not amra_row.empty else 0

        def apply_logic(row):
            oid = str(row.get('OWNER ID', 'UNKNOWN')).upper()
            a_vol = (row.get('SEND RFI', 0) + row.get('RECOMMEND CLOSE WITHOUT SAR', 0) + row.get('RECOMMEND CLOSE AND GENERATE SAR', 0))
            tl_vol = (row.get('CLOSE WITHOUT SAR', 0) + row.get('REJECT RECOMMENDATION', 0) + row.get('LINK AND CLOSE AS MERGE', 0) + row.get('CLOSE AND GENERATE SAR', 0))
            str_v, pri_str = row.get('STR', 0), row.get('PRI STR', 0)
            
            if ("IRFAN.HASAN" in oid and month <= 11) or ("REHAN.SYED" in oid and month == 12):
                final_vol, role, target = (tl_vol - amra_raw_fccm) + (amra_raw_fccm * 0.2) + (str_v * 20) + (pri_str * 2), "Team Lead", 40
            elif "AMRA.SIDDIQUI" in oid:
                final_vol, role, target = (a_vol * 0.2) + (str_v * 0.33), "Analyst", 200
            elif tl_vol > 0:
                final_vol, role, target = tl_vol + (str_v * 20) + (pri_str * 2), "Team Lead", 40
            else:
                final_vol, role, target = a_vol + (str_v * 20) + (pri_str * 2), "Analyst", 40

            system_score = round(((final_vol / target) * 70) + 30, 2)
            rating_val = st.session_state.approved_ratings.get(oid, 3) 
            revised_total = round((system_score * 0.7) + ((rating_val * 25) * 0.3), 2)
            return pd.Series([final_vol, system_score, revised_total, role])

        df[['Eff_Vol', 'System_Score', 'Final_Score', 'Role']] = df.apply(apply_logic, axis=1)
        return df

    def refresh_scores_inplace():
        if st.session_state.mtd_data is not None:
            def update_row(row):
                oid = str(row['OWNER ID']).upper()
                sys = row['System_Score']
                rat = st.session_state.approved_ratings.get(oid, 3)
                return round((sys * 0.7) + ((rat * 25) * 0.3), 2)
            st.session_state.mtd_data['Final_Score'] = st.session_state.mtd_data.apply(update_row, axis=1)
            save_to_global()

    # --- 7. RANKING RENDERER ---
    def render_snapshot_rankings(df, score_col, title, is_pending=False):
        st.subheader(title)
        if is_pending:
            st.info("⚠️ Ratings Pending / Approval Awaited")
            return
        top_5 = df.sort_values(score_col, ascending=False).head(5)
        st.dataframe(top_5[['OWNER ID', score_col]], use_container_width=True)

    # --- 8. TABS & LOGIC ---
    tab_list = ["🏆 Analyst Excellence", "🎖️ TL Excellence", "📊 Scoreboard Explorer"]
    if st.session_state.role in ["Team Lead", "Head AML"]: tab_list.append("⭐ Rating Panel")
    if st.session_state.role in ["Admin", "Head AML", "Head AML/CFT"]: tab_list.append("⚙️ Management & Approvals")
    tabs = st.tabs(tab_list)

    if "⚙️ Management & Approvals" in tab_list:
        with tabs[-1]: 
            if st.session_state.role == "Admin":
                f1 = st.file_uploader("FCCM MTD (.xls)", type=['xls'])
                f2 = st.file_uploader("STR MTD (.xlsx)", type=['xlsx'])
                if st.button("Process Reports"):
                    if f1 and f2: 
                        st.session_state.mtd_data = calculate_performance(pd.read_excel(f1, skiprows=2, engine='xlrd'), pd.read_excel(f2), sel_month)
                        st.session_state.submitted_ratings = set()
                        st.session_state.pending_tl_ratings = []
                        st.session_state.pending_head_aml_ratings = []
                        st.session_state.approved_ratings = {}
                        save_to_global() # SAVE DATA TO ALL USERS
                        st.success("Data Updated for Everyone!")
                        st.rerun()
            
            if st.session_state.role == "Head AML":
                for i, entry in enumerate(st.session_state.pending_tl_ratings):
                    if st.button(f"Approve {entry.get('TL')}", key=f"aa_{i}"):
                        st.session_state.approved_ratings.update(entry['Grades'])
                        st.session_state.pending_tl_ratings.pop(i)
                        refresh_scores_inplace()
                        save_to_global()
                        st.rerun()

    if "⭐ Rating Panel" in tab_list:
        with tabs[3]: 
            if st.session_state.role == "Team Lead":
                my_team = TEAM_STRUCTURE.get(st.session_state.user_name, [])
                with st.form("tl_form"):
                    grades = {oid: st.slider(f"Rating {oid}", 1, 5, 3) for oid in my_team}
                    if st.form_submit_button("Submit"):
                        st.session_state.pending_tl_ratings.append({"TL": st.session_state.user_name, "Grades": grades})
                        st.session_state.submitted_ratings.add(st.session_state.user_name)
                        save_to_global()
                        st.rerun()

    # --- 9. DISPLAY VIEWS ---
    if st.session_state.mtd_data is not None:
        with tabs[0]: 
            df_a = st.session_state.mtd_data[st.session_state.mtd_data['Role'] == "Analyst"]
            render_snapshot_rankings(df_a, 'System_Score', "System Productivity")