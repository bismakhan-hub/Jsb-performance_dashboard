import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. INITIALIZATION & SESSION STATE ---
if 'role' not in st.session_state: st.session_state.role = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'mtd_data' not in st.session_state: st.session_state.mtd_data = None
if 'submitted_ratings' not in st.session_state: st.session_state.submitted_ratings = set()
if 'pending_tl_ratings' not in st.session_state: st.session_state.pending_tl_ratings = []
if 'pending_head_aml_ratings' not in st.session_state: st.session_state.pending_head_aml_ratings = []
if 'approved_ratings' not in st.session_state: st.session_state.approved_ratings = {}

st.set_page_config(layout="wide", page_title="AML Performance Board")

# --- 2. STYLING ---
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

# --- PASSWORDS (ADMIN HIDDEN IN SECRETS) ---
PASSWORDS = {
    "Admin": st.secrets.get("ADMIN_PASSWORD", "admin_access_123"),
    "Head AML/CFT": "CFT@Head2025",
    "Head AML": "HeadAML!123", 
    "Team Lead": "TL@AML2025", 
    "Analyst": "AMLView"
}

# --- 3. LOGIN SYSTEM ---
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
    # --- 4. TOP BAR ---
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

    st.markdown(f"### <div style='text-align: center; color: #FFD700;'>{sel_month_name} {sel_year} Performance</div>", unsafe_allow_html=True)

    # --- 5. CALCULATION ENGINE ---
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

    # --- 6. RANKING RENDERER ---
    def render_snapshot_rankings(df, score_col, title, is_pending=False):
        st.subheader(title)
        if is_pending:
            st.info("⚠️ Ratings Pending / Approval Awaited")
            st.markdown("<div style='text-align: center; color: #888;'><i>Rankings will appear here once ratings are approved.</i></div>", unsafe_allow_html=True)
            return

        top_5 = df.sort_values(score_col, ascending=False).head(5)
        
        if len(top_5) >= 3:
            p1, p2, p3 = st.columns([1, 1.2, 1])
            with p2: st.markdown(f"<div style='text-align: center;'><div style='font-size: 30px;'>🥇</div><div style='background: #FFD700; border-radius: 50%; width: 100px; height: 100px; margin: auto; display: flex; align-items: center; justify-content: center; color: black; font-weight: bold; font-size: 12px;'>{top_5.iloc[0]['OWNER ID']}</div><p>Winner<br><b>{top_5.iloc[0][score_col]} Pts</b></p></div>", unsafe_allow_html=True)
            with p1: st.markdown(f"<div style='text-align: center; margin-top: 20px;'><div style='font-size: 25px;'>🥈</div><div style='background: #C0C0C0; border-radius: 50%; width: 80px; height: 80px; margin: auto; display: flex; align-items: center; justify-content: center; color: black; font-weight: bold; font-size: 10px;'>{top_5.iloc[1]['OWNER ID']}</div><p>Rank 2<br>{top_5.iloc[1][score_col]} Pts</p></div>", unsafe_allow_html=True)
            with p3: st.markdown(f"<div style='text-align: center; margin-top: 20px;'><div style='font-size: 25px;'>🥉</div><div style='background: #CD7F32; border-radius: 50%; width: 80px; height: 80px; margin: auto; display: flex; align-items: center; justify-content: center; color: black; font-weight: bold; font-size: 10px;'>{top_5.iloc[2]['OWNER ID']}</div><p>Rank 3<br>{top_5.iloc[2][score_col]} Pts</p></div>", unsafe_allow_html=True)

        r4, r5 = st.columns(2)
        if len(top_5) >= 4:
            with r4: st.markdown(f"<div class='rank-card'><div class='rank-star'>★</div><div class='rank-name'>Rank 4<br>{top_5.iloc[3]['OWNER ID']}</div><div class='rank-pts'>{top_5.iloc[3][score_col]} Pts</div></div>", unsafe_allow_html=True)
        if len(top_5) >= 5:
            with r5: st.markdown(f"<div class='rank-card'><div class='rank-star'>★</div><div class='rank-name'>Rank 5<br>{top_5.iloc[4]['OWNER ID']}</div><div class='rank-pts'>{top_5.iloc[4][score_col]} Pts</div></div>", unsafe_allow_html=True)

    # --- 7. TABS & LOGIC ---
    tab_list = ["🏆 Analyst Excellence", "🎖️ TL Excellence", "📊 Scoreboard Explorer"]
    if st.session_state.role in ["Team Lead", "Head AML"]: tab_list.append("⭐ Rating Panel")
    if st.session_state.role in ["Admin", "Head AML", "Head AML/CFT"]: tab_list.append("⚙️ Management & Approvals")
    tabs = st.tabs(tab_list)

    # --- ADMIN / MANAGEMENT TAB ---
    if "⚙️ Management & Approvals" in tab_list:
        with tabs[-1]: 
            if st.session_state.role == "Admin":
                st.subheader("Upload Monthly Data")
                f1, f2 = st.file_uploader("FCCM MTD (.xls)", type=['xls']), st.file_uploader("STR MTD (.xlsx)", type=['xlsx'])
                if st.button("Process Reports"):
                    if f1 and f2: 
                        st.session_state.mtd_data = calculate_performance(pd.read_excel(f1, skiprows=2, engine='xlrd'), pd.read_excel(f2), sel_month)
                        st.session_state.submitted_ratings = set()
                        st.session_state.pending_tl_ratings = []
                        st.session_state.pending_head_aml_ratings = []
                        st.session_state.approved_ratings = {}
                        st.success("Data Updated!")
                        st.rerun()
            
            # HEAD AML Approves Analyst Ratings from Team Leads
            if st.session_state.role == "Head AML":
                st.subheader("Pending Analyst Approvals (from Team Leads)")
                if not st.session_state.pending_tl_ratings:
                    st.info("No pending analyst approvals.")
                for i, entry in enumerate(st.session_state.pending_tl_ratings):
                    st.write(f"**From TL: {entry.get('TL')}**")
                    st.table(pd.DataFrame(entry['Grades'].items(), columns=['Analyst', 'Rating']))
                    c1, c2 = st.columns(2)
                    if c1.button("Approve Analyst Ratings", key=f"aa_{i}"):
                        st.session_state.approved_ratings.update(entry['Grades'])
                        st.session_state.pending_tl_ratings.pop(i)
                        refresh_scores_inplace()
                        st.rerun()
                    if c2.button("Reject Analyst Ratings", key=f"ra_{i}"):
                        if entry.get('TL') in st.session_state.submitted_ratings: st.session_state.submitted_ratings.remove(entry.get('TL'))
                        st.session_state.pending_tl_ratings.pop(i)
                        st.rerun()

            # HEAD AML/CFT Approves TL Ratings from Head AML
            if st.session_state.role == "Head AML/CFT":
                st.subheader("Pending Team Lead Approvals (from Head AML)")
                if not st.session_state.pending_head_aml_ratings:
                    st.info("No pending TL approvals.")
                for i, entry in enumerate(st.session_state.pending_head_aml_ratings):
                    st.table(pd.DataFrame(entry['Grades'].items(), columns=['Team Lead', 'Rating']))
                    c1, c2 = st.columns(2)
                    if c1.button("Approve TL Ratings", key=f"at_{i}"):
                        st.session_state.approved_ratings.update(entry['Grades'])
                        st.session_state.pending_head_aml_ratings.pop(i)
                        refresh_scores_inplace()
                        st.rerun()
                    if c2.button("Reject TL Ratings", key=f"rt_{i}"):
                        st.session_state.pending_head_aml_ratings.pop(i)
                        st.rerun()

    # --- RATING PANEL TAB ---
    if "⭐ Rating Panel" in tab_list:
        with tabs[3]: 
            # Team Lead rates Analysts
            if st.session_state.role == "Team Lead":
                if st.session_state.user_name in st.session_state.submitted_ratings:
                    st.success("✅ Ratings submitted for Head AML approval.")
                else:
                    st.subheader("Rate Your Team (Analysts)")
                    if st.session_state.mtd_data is not None:
                        my_team = TEAM_STRUCTURE.get(st.session_state.user_name, [])
                        with st.form("tl_form"):
                            grades = {oid: st.slider(f"Rating for {oid}", 1, 5, 3) for oid in my_team}
                            if st.form_submit_button("Submit Analyst Ratings"):
                                st.session_state.pending_tl_ratings.append({"TL": st.session_state.user_name, "Grades": grades})
                                st.session_state.submitted_ratings.add(st.session_state.user_name)
                                st.rerun()

            # Head AML rates Team Leads
            if st.session_state.role == "Head AML":
                st.subheader("Rate Team Leads")
                if st.session_state.mtd_data is not None:
                    tl_list = list(TEAM_STRUCTURE.keys())
                    with st.form("head_form"):
                        grades = {tl: st.slider(f"Rating for {tl}", 1, 5, 3) for tl in tl_list}
                        if st.form_submit_button("Submit TL Ratings to Head AML/CFT"):
                            st.session_state.pending_head_aml_ratings.append({"Grades": grades})
                            st.success("TL Ratings sent for final approval!")
                            st.rerun()

    # --- EXCELLENCE VIEWS ---
    if st.session_state.mtd_data is not None:
        ratings_pending = len(st.session_state.approved_ratings) == 0
        right_col_title = "⏳ Ratings & Approval Awaited" if ratings_pending else "Revised Score"

        with tabs[0]: 
            df_a = st.session_state.mtd_data[st.session_state.mtd_data['Role'] == "Analyst"]
            cl, cm, cr = st.columns([10, 1, 10]) 
            with cl: render_snapshot_rankings(df_a, 'System_Score', "System Productivity Only")
            with cm: st.markdown("<div class='vertical-line'></div>", unsafe_allow_html=True)
            with cr: render_snapshot_rankings(df_a, 'Final_Score', right_col_title, is_pending=ratings_pending)
        
        with tabs[1]: 
            df_t = st.session_state.mtd_data[st.session_state.mtd_data['Role'] == "Team Lead"]
            cl, cm, cr = st.columns([10, 1, 10])
            with cl: render_snapshot_rankings(df_t, 'System_Score', "System Productivity Only")
            with cm: st.markdown("<div class='vertical-line'></div>", unsafe_allow_html=True)
            with cr: render_snapshot_rankings(df_t, 'Final_Score', right_col_title, is_pending=ratings_pending)
        
        with tabs[2]: st.dataframe(st.session_state.mtd_data, use_container_width=True)