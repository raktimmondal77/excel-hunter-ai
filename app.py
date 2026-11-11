import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from src.db import init_db
from src.config import (
    JOB_STATUSES, PRIORITIES, PLATFORMS, JOB_CATEGORIES, SEARCH_TERMS,
    TARGET_MIN_INR, TARGET_MAX_INR, DB_PATH, SAMPLE_CSV_PATH, INTEGRATION_STATES
)
import src.job_manager as jm
import src.earnings_tracker as et
import src.platform_manager as pm
import src.application_tracker as at
import src.fiverr_manager as fm
import src.user_profile as up
import src.suitability_analyser as sa
import src.pricing_assistant as pa
import src.proposal_intelligence as pi
from src.discovery.engine import DiscoveryEngine, get_last_discovery_run, get_discovery_history
from src.discovery.universal_importer import (
    import_job_from_url,
    import_job_from_pasted_text,
    parse_email_alert,
    detect_platform_from_url
)
from src.sample_data import seed_sample_data

# Set Streamlit page config
st.set_page_config(
    page_title="Excel Hunter AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database, platform records, gigs, and user profile
init_db()
pm.seed_default_platforms()
fm.seed_default_fiverr_gigs()
up.get_user_profile() # Ensures default profile exists

# Auto-seed sample data if database is brand new and empty
all_jobs = jm.get_jobs()
if len(all_jobs) == 0:
    seed_sample_data()
    all_jobs = jm.get_jobs()

# Custom CSS for polished styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .badge-sample {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid #FCD34D;
    }
    .badge-high {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-risk {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .status-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation (10 Requested Modules)
st.sidebar.markdown("# 🎯 EXCEL HUNTER AI")
st.sidebar.caption("Zero-Cost Excel Freelance Intelligence Assistant")
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Go to Module:",
    [
        "1. 📊 Overview",
        "2. 🔍 Job Discovery",
        "3. 👤 My Skills Profile",
        "4. 🧠 Project Analysis",
        "5. 🏷️ Bid & Pricing Assistant",
        "6. ✍️ Proposal Generator",
        "7. 📬 Application Tracker",
        "8. ⏰ Follow-up Manager",
        "9. 📈 Earnings & Analytics",
        "10. ⚙️ Settings"
    ]
)

include_samples = st.sidebar.checkbox("Include Sample Data", value=True, help="Toggle visibility of demonstration records.")

if include_samples:
    st.sidebar.warning("⚠️ Demo Mode: Sample records are visible. Uncheck to view only real data.")
else:
    st.sidebar.success("🛡️ Production Mode: Viewing real records only.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Safety & Policy Rules")
st.sidebar.caption("• ₹0 Budget: No paid APIs or subscriptions\n• Offline-first: Data stored locally in SQLite\n• Strict Verification: Zero invented skills or claims\n• Human confirmation required for all submissions")

# =============================================================
# MODULE 1: OVERVIEW
# =============================================================
if navigation == "1. 📊 Overview":
    st.markdown('<div class="main-header">📊 Freelance Operations Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live command center for Excel freelance discovery, pipeline health, and monthly income targets.</div>', unsafe_allow_html=True)

    # 1. Connected Platforms Quick Overview
    st.markdown("### 🌐 Connected Platforms")
    plat_df = pm.get_platform_accounts()
    p_cols = st.columns(min(len(plat_df), 6))
    for idx, (_, p_row) in enumerate(plat_df.head(6).iterrows()):
        with p_cols[idx % 6]:
            status_color = "#059669" if "Connect" in p_row.get("connection_status", "") or p_row.get("connection_status", "") == "Active" else "#D97706"
            st.markdown(f"""
            <div class="status-card">
                <b>{p_row['platform_name']}</b><br/>
                <span style="color: {status_color}; font-size: 0.85rem; font-weight: 600;">{p_row.get('connection_status', 'Manual')}</span><br/>
                <span style="color: #64748B; font-size: 0.75rem;">{p_row.get('integration_mode', 'Manual')}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. Monthly Target Progress
    cur_month = datetime.now().strftime("%Y-%m")
    summary = et.get_monthly_summary(target_month=cur_month, include_samples=include_samples)

    target_col1, target_col2 = st.columns(2)
    with target_col1:
        st.markdown(f"#### 🎯 Target 1: ₹{TARGET_MIN_INR:,.0f} / month")
        pct1 = min(summary["progress_min_pct"], 100.0)
        st.progress(pct1 / 100.0)
        st.caption(f"Achieved: **₹{summary['total_net']:,.2f}** ({pct1}%) | Remaining Gap: **₹{summary['gap_to_min']:,.2f}**")

    with target_col2:
        st.markdown(f"#### 🚀 Target 2: ₹{TARGET_MAX_INR:,.0f} / month")
        pct2 = min(summary["progress_max_pct"], 100.0)
        st.progress(pct2 / 100.0)
        st.caption(f"Achieved: **₹{summary['total_net']:,.2f}** ({pct2}%) | Remaining Gap: **₹{summary['gap_to_max']:,.2f}**")

    st.markdown("---")

    # 3. Application & Opportunity Pipeline
    pipeline_kpis = at.get_pipeline_kpis()
    st.markdown("### 🚦 Application Pipeline Health")
    pkpi1, pkpi2, pkpi3, pkpi4, pkpi5 = st.columns(5)
    pkpi1.metric("Awaiting Applications", pipeline_kpis["awaiting_apps"])
    pkpi2.metric("Proposals Drafted", pipeline_kpis["proposals_drafted"])
    pkpi3.metric("Applications Submitted", pipeline_kpis["apps_submitted"])
    pkpi4.metric("Client Replies / Active", pipeline_kpis["replies_count"] + pipeline_kpis["interviews_count"])
    pkpi5.metric("Projects Awarded", pipeline_kpis["won_count"])

    if pipeline_kpis["follow_ups_due"] > 0:
        st.warning(f"⏰ **{pipeline_kpis['follow_ups_due']} Follow-up(s) Due!** Open the Follow-up Manager tab to review clients waiting for communication.")

    st.markdown("---")

    # 4. High Priority Job Spotlight & Risk Flags
    jobs_df = jm.get_jobs(include_samples=include_samples)
    total_jobs = len(jobs_df)

    if total_jobs > 0:
        flagged_jobs = jobs_df[jobs_df["risk_flags"].str.len() > 2]
        if len(flagged_jobs) > 0:
            with st.expander(f"⚠️ Fraud & Risk Detection: {len(flagged_jobs)} Job(s) Flagged as Suspicious", expanded=False):
                st.warning("Excel Hunter AI identified suspicious patterns (e.g. registration fees, security deposits, or off-platform contact). Review carefully before interacting:")
                for _, f_row in flagged_jobs.iterrows():
                    reasons = f_row["risk_flags"]
                    try:
                        reasons_list = json.loads(reasons)
                        reasons_str = " • ".join(reasons_list)
                    except Exception:
                        reasons_str = str(reasons)
                    sample_tag = " [SAMPLE DATA]" if f_row["is_sample"] == 1 else ""
                    st.markdown(f"- **{f_row['title']}** ({f_row['platform']}){sample_tag}: <span class='badge-risk'>{reasons_str}</span>", unsafe_allow_html=True)

        st.markdown("### 🔥 Top High-Priority Opportunities")
        high_df = jobs_df[jobs_df["priority"] == "High"].head(5)
        if len(high_df) > 0:
            for _, job in high_df.iterrows():
                with st.container():
                    c_title, c_budget, c_score, c_status = st.columns([3, 1, 1, 1])
                    sample_lbl = " [SAMPLE]" if job["is_sample"] == 1 else ""
                    c_title.markdown(f"**{job['title']}**{sample_lbl}\n\n*Platform:* {job['platform']} | *Category:* {job.get('category') or 'Excel'} | *Posted:* {job['date_posted'] or 'Recent'}")
                    c_budget.markdown(f"**₹{job['budget']:,.0f}** {job['currency']}")
                    c_score.markdown(f"Score: **{job['score']}/100**")
                    c_status.markdown(f"`{job['status']}`")
                    st.divider()
        else:
            st.info("No high-priority jobs at this time. Run a discovery scan in Module 2.")
    else:
        st.info("No jobs recorded. Run a discovery scan or enable sample data.")

# =============================================================
# MODULE 2: JOB DISCOVERY
# =============================================================
elif navigation == "2. 🔍 Job Discovery":
    st.markdown('<div class="main-header">🔍 Job Discovery Command Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-source scanner and universal importer pulling legitimate Excel freelance opportunities.</div>', unsafe_allow_html=True)

    disc_tab1, disc_tab2, disc_tab3 = st.tabs([
        "🚀 Automated Live Scanner",
        "📥 Universal Opportunity Importer",
        "📋 Job Repository & Pipeline"
    ])

    with disc_tab1:
        d_col1, d_col2 = st.columns([2, 1])
        with d_col1:
            st.markdown("#### 🚀 On-Demand Discovery Scan")
            st.write("Scans active adapters (Freelancer.com Official API, Remotive Public API). Automatically scores opportunities and rejects duplicates.")

            selected_terms = st.multiselect(
                "Target Search Keywords for this Scan:",
                options=SEARCH_TERMS,
                default=SEARCH_TERMS[:4]
            )

            if st.button("🚀 Run Discovery Scan Now", type="primary"):
                with st.spinner("Scanning permitted sources and evaluating Excel opportunities..."):
                    engine = DiscoveryEngine()
                    res = engine.run_discovery_scan(search_terms=selected_terms)
                    st.success(f"✅ Scan completed! {res['summary']}")
                    if res["error_logs"]:
                        with st.expander("Review Adapter Notices / Warnings"):
                            for err in res["error_logs"]:
                                st.write(f"- {err}")
                    st.rerun()

        with d_col2:
            st.markdown("#### 🩺 Source Health & Readiness")
            engine = DiscoveryEngine()
            for ad in engine.adapters:
                health = ad.test_connection()
                h_icon = "🟢" if health.get("healthy") else ("🟡" if "pending" in health.get("status", "").lower() or "manual" in health.get("status", "").lower() else "🔴")
                st.write(f"{h_icon} **{ad.source_name}**")
                st.caption(f"Status: *{health['status']}* — {health['message']}")

        st.markdown("---")
        st.markdown("### 📜 Discovery Scan Audit History")
        history_df = get_discovery_history(limit=6)
        if len(history_df) > 0:
            h_view = history_df[["id", "run_timestamp", "jobs_found", "duplicates_skipped", "errors_logged", "status", "summary_notes"]].copy()
            h_view = h_view.rename(columns={
                "id": "Run ID", "run_timestamp": "Timestamp", "jobs_found": "New Jobs",
                "duplicates_skipped": "Duplicates Skipped", "errors_logged": "Warnings",
                "status": "Status", "summary_notes": "Summary"
            })
            st.dataframe(h_view, use_container_width=True, hide_index=True)
        else:
            st.info("No discovery runs recorded yet.")

    with disc_tab2:
        st.markdown("#### 📥 Ingest Opportunities from Any Source")
        imp_sub1, imp_sub2, imp_sub3, imp_sub4 = st.tabs([
            "🔗 Paste URL", "📄 Paste Text / Chat", "📬 Parse Email Alert", "📊 Upload CSV"
        ])
        with imp_sub1:
            with st.form("imp_url_form"):
                in_url = st.text_input("Job URL*", placeholder="https://www.upwork.com/jobs/~01example...")
                in_utitle = st.text_input("Job Title (optional)")
                in_ubudget = st.number_input("Budget (INR)", min_value=0.0, step=500.0, value=3000.0)
                in_udesc = st.text_area("Description Excerpt (optional)", height=80)
                in_uclient = st.text_input("Client Info (optional)")
                if st.form_submit_button("Import URL", type="primary"):
                    succ, j_id, msg = import_job_from_url(in_url, in_utitle, in_ubudget, in_udesc, in_uclient)
                    if succ:
                        st.success(f"✅ Job #{j_id} imported successfully!")
                    else:
                        st.warning(msg)

        with imp_sub2:
            with st.form("imp_text_form"):
                in_tplatform = st.selectbox("Platform / Source", PLATFORMS, index=PLATFORMS.index("Direct Client") if "Direct Client" in PLATFORMS else 0)
                in_turl = st.text_input("URL / Link (optional)")
                in_tbudget = st.number_input("Known Budget (INR, 0 to auto-extract)", min_value=0.0, step=500.0, value=0.0)
                in_ttext = st.text_area("Raw Text Body*", height=150, placeholder="Paste job description or client WhatsApp/email text here...")
                if st.form_submit_button("Import Text", type="primary"):
                    succ, j_id, msg = import_job_from_pasted_text(in_ttext, in_tplatform, in_turl, in_tbudget)
                    if succ:
                        st.success(f"✅ Job #{j_id} imported successfully!")
                    else:
                        st.warning(msg)

        with imp_sub3:
            with st.form("imp_email_form"):
                in_esubject = st.text_input("Email Subject*", placeholder="e.g. Upwork Job Alert: Senior Excel Dashboard Developer")
                in_eplatform = st.selectbox("Platform Alert Source", ["Upwork", "Freelancer.com", "Fiverr", "Other"])
                in_ebody = st.text_area("Email Content*", height=140)
                if st.form_submit_button("Parse Alert", type="primary"):
                    succ, j_id, msg = parse_email_alert(in_esubject, in_ebody, in_eplatform)
                    if succ:
                        st.success(f"✅ Job #{j_id} parsed and imported!")
                    else:
                        st.warning(msg)

        with imp_sub4:
            st.caption("Upload CSV containing columns: title, description, platform, budget, currency, url, date_posted")
            csv_file = st.file_uploader("Choose CSV File", type=["csv"])
            if csv_file:
                df = pd.read_csv(csv_file)
                st.write(f"Detected {len(df)} rows.")
                if st.button("Import CSV Rows", type="primary"):
                    success_count = 0
                    for _, r in df.iterrows():
                        j_data = {
                            "title": str(r.get("title", "")),
                            "description": str(r.get("description", "")),
                            "platform": str(r.get("platform", "Direct Client")),
                            "budget": float(r.get("budget", 0) or 0),
                            "currency": str(r.get("currency", "INR")),
                            "url": str(r.get("url", "")),
                            "date_posted": str(r.get("date_posted", datetime.now().strftime("%Y-%m-%d"))),
                            "is_sample": 0
                        }
                        s, _, _ = jm.add_job(j_data)
                        if s:
                            success_count += 1
                    st.success(f"Successfully imported {success_count} jobs from CSV!")
                    st.rerun()

    with disc_tab3:
        st.markdown("#### 📋 Filterable Opportunities Repository")
        jobs_df = jm.get_jobs(include_samples=include_samples)
        if not jobs_df.empty:
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                plat_filter = st.selectbox("Filter Platform", ["All"] + list(jobs_df["platform"].unique()))
            with f_col2:
                prio_filter = st.selectbox("Filter Priority", ["All", "High", "Medium", "Low"])
            with f_col3:
                status_filter = st.selectbox("Filter Status", ["All"] + list(jobs_df["status"].unique()))

            filtered = jobs_df.copy()
            if plat_filter != "All":
                filtered = filtered[filtered["platform"] == plat_filter]
            if prio_filter != "All":
                filtered = filtered[filtered["priority"] == prio_filter]
            if status_filter != "All":
                filtered = filtered[filtered["status"] == status_filter]

            st.dataframe(
                filtered[["id", "title", "platform", "budget", "currency", "priority", "score", "status", "date_posted"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No jobs found in repository.")

# =============================================================
# MODULE 3: USER SKILLS PROFILE
# =============================================================
elif navigation == "3. 👤 My Skills Profile":
    st.markdown('<div class="main-header">👤 My Skills Profile & Portfolio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your confirmed skills baseline. EXCEL HUNTER AI will NEVER invent skills or claim tools you have not selected.</div>', unsafe_allow_html=True)

    profile = up.get_user_profile()

    prof_tab1, prof_tab2 = st.tabs(["📝 Skills & Experience Profile", "📁 Verified Portfolio Projects"])

    with prof_tab1:
        with st.form("user_profile_form"):
            st.markdown("### 1. Excel Skills")
            st.caption("Check only the skills you currently possess and are comfortable delivering:")
            selected_excel = []
            e_cols = st.columns(3)
            current_excel = set(profile.get("excel_skills", []))
            for idx, skill in enumerate(up.AVAILABLE_EXCEL_SKILLS):
                with e_cols[idx % 3]:
                    if st.checkbox(skill, value=(skill in current_excel), key=f"skill_{idx}"):
                        selected_excel.append(skill)

            st.markdown("### 2. Other Tools")
            selected_tools = []
            t_cols = st.columns(3)
            current_tools = set(profile.get("other_tools", []))
            for idx, tool in enumerate(up.AVAILABLE_OTHER_TOOLS):
                with t_cols[idx % 3]:
                    if st.checkbox(tool, value=(tool in current_tools), key=f"tool_{idx}"):
                        selected_tools.append(tool)

            st.markdown("---")
            st.markdown("### 3. Experience & Domain Knowledge")
            c_exp1, c_exp2 = st.columns([1, 2])
            with c_exp1:
                cur_exp = profile.get("experience_level", "Beginner")
                exp_index = up.EXPERIENCE_LEVELS.index(cur_exp) if cur_exp in up.EXPERIENCE_LEVELS else 0
                selected_exp_level = st.selectbox("Current Experience Level", up.EXPERIENCE_LEVELS, index=exp_index)
            with c_exp2:
                work_desc = st.text_area("Actual Work Experience", value=profile.get("work_experience_desc", ""), height=80, placeholder="e.g. Managing inventory and sales sheets in Excel for retail business...")

            c_proj1, c_proj2 = st.columns(2)
            with c_proj1:
                comp_proj = st.text_area("Relevant Projects Completed", value=profile.get("completed_projects_desc", ""), height=80, placeholder="e.g. Sales summary model, budget calculator...")
            with c_proj2:
                ind_know = st.text_area("Industry / Business Knowledge", value=profile.get("industry_knowledge", ""), height=80, placeholder="e.g. Retail sales, logistics, finance basics...")

            st.markdown("---")
            st.markdown("### 4. Availability & Budget Targets")
            a_col1, a_col2, a_col3 = st.columns(3)
            with a_col1:
                hours_pw = st.number_input("Hours Available per Week", min_value=1.0, max_value=80.0, value=float(profile.get("hours_per_week", 15.0)), step=1.0)
            with a_col2:
                pref_dur = st.selectbox("Preferred Project Duration", ["Under 1 week", "1-2 weeks", "2-4 weeks", "Ongoing / Monthly"], index=1)
            with a_col3:
                min_bud = st.number_input("Minimum Acceptable Budget (INR)", min_value=500.0, max_value=100000.0, value=float(profile.get("min_budget", 1500.0)), step=250.0)

            save_btn = st.form_submit_button("💾 Save Profile", type="primary")
            if save_btn:
                up_data = {
                    "excel_skills": selected_excel,
                    "other_tools": selected_tools,
                    "experience_level": selected_exp_level,
                    "work_experience_desc": work_desc,
                    "completed_projects_desc": comp_proj,
                    "industry_knowledge": ind_know,
                    "hours_per_week": hours_pw,
                    "preferred_duration": pref_dur,
                    "min_budget": min_bud
                }
                if up.save_user_profile(up_data):
                    st.success("✅ Profile successfully saved! Proposals and suitability scoring will now reflect your updated skills.")
                    st.rerun()

    with prof_tab2:
        st.markdown("### 📁 Confirmed Portfolio Projects")
        st.caption("Add actual Excel projects you have built. These are verified proof of your work that can be quoted in proposals.")

        portfolio_items = up.get_portfolio_projects()
        if portfolio_items:
            for p in portfolio_items:
                with st.expander(f"📊 {p['project_title']} ({p.get('completion_status', 'Completed')})"):
                    st.write(p.get("project_description", ""))
                    st.caption(f"**Skills:** {p.get('skills_used', '')} | **Link:** {p.get('portfolio_link', 'None')}")
                    if st.button("Delete Project", key=f"del_port_{p['id']}"):
                        up.delete_portfolio_project(p['id'])
                        st.success("Project deleted.")
                        st.rerun()
        else:
            st.info("No portfolio projects added yet. Use the form below to add your first project.")

        st.markdown("#### ➕ Add New Portfolio Project")
        with st.form("new_portfolio_form"):
            p_title = st.text_input("Project Title*", placeholder="e.g. Retail Sales KPI Dashboard")
            p_desc = st.text_area("Description*", placeholder="Explain what the spreadsheet did and what problem it solved...")
            p_skills = st.text_input("Skills Used*", placeholder="e.g. Pivot Tables, Slicers, XLOOKUP, Charts")
            p_link = st.text_input("Portfolio File / GitHub Link (optional)", placeholder="https://...")
            p_stat = st.selectbox("Status", ["Completed", "In Progress"])

            if st.form_submit_button("Add Portfolio Item", type="primary"):
                if p_title and p_desc:
                    up.add_portfolio_project(p_title, p_desc, p_skills, p_link, p_stat)
                    st.success("✅ Portfolio project added!")
                    st.rerun()
                else:
                    st.warning("Please provide both title and description.")

# =============================================================
# MODULE 4: PROJECT SUITABILITY ANALYSER
# =============================================================
elif navigation == "4. 🧠 Project Analysis":
    st.markdown('<div class="main-header">🧠 Project Suitability Analyser</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluates 100-point suitability against your verified profile. Separates capability fit from fraud-risk detection.</div>', unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if jobs_df.empty:
        st.info("No jobs available to evaluate. Run discovery scan in Module 2.")
    else:
        # Job selector
        job_options = {f"#{row['id']} - {row['title']} ({row['platform']})": row['id'] for _, row in jobs_df.iterrows()}
        selected_job_label = st.selectbox("Select Project to Analyze:", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        job_data = jobs_df[jobs_df["id"] == selected_job_id].iloc[0].to_dict()

        profile = up.get_user_profile()
        analysis = sa.analyse_suitability(job_data, profile)

        # Recommendation Banner
        rec = analysis["recommendation"]
        if rec == "Apply":
            st.success(f"### 🎯 Recommendation: A. Apply\n**{analysis['reasoning']}**")
        elif rec == "Apply after learning something":
            st.warning(f"### 💡 Recommendation: B. Apply after learning something\n**{analysis['reasoning']}**")
        else:
            st.error(f"### ⛔ Recommendation: C. Avoid\n**{analysis['reasoning']}**")

        st.markdown("---")

        # Score Breakdown & Key Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Suitability", f"{analysis['suitability_score']}/100")
        m2.metric("Difficulty Level", analysis["estimated_difficulty"])
        m3.metric("Estimated Hours", f"{analysis['estimated_hours']} hrs")
        m4.metric("Beginner Friendly", "Yes ✅" if analysis["is_beginner_friendly"] else "No / Caution ⚠️")

        st.markdown("### 📊 100-Point Suitability Breakdown")
        sb = analysis["score_breakdown"]
        sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
        sc1.metric("Skill Match", f"{sb['skill_match']}/30")
        sc2.metric("Budget Fit", f"{sb['budget_suitability']}/15")
        sc3.metric("Clarity", f"{sb['project_clarity']}/15")
        sc4.metric("Credibility", f"{sb['client_credibility']}/15")
        sc5.metric("Feasibility", f"{sb['delivery_feasibility']}/15")
        sc6.metric("Deadline", f"{sb['deadline_feasibility']}/10")

        st.markdown("---")
        c_skills1, c_skills2 = st.columns(2)
        with c_skills1:
            st.markdown("#### ✅ Skills Matched")
            if analysis["skills_possessed"]:
                for s in analysis["skills_possessed"]:
                    st.write(f"- {s}")
            else:
                st.caption("No specific advanced skills required for this job.")

        with c_skills2:
            st.markdown("#### ⚠️ Missing / Unconfirmed Skills")
            if analysis["missing_skills"]:
                for s in analysis["missing_skills"]:
                    st.write(f"- <span style='color: #DC2626; font-weight: 600;'>{s}</span>", unsafe_allow_html=True)
            else:
                st.success("None! You possess all extracted skills for this project.")

        if analysis["potential_risks"]:
            st.markdown("#### 🚩 Potential Flags & Risks to Keep in Mind")
            for r in analysis["potential_risks"]:
                st.caption(f"• {r}")

# =============================================================
# MODULE 5: BID & PRICING ASSISTANT
# =============================================================
elif navigation == "5. 🏷️ Bid & Pricing Assistant":
    st.markdown('<div class="main-header">🏷️ Bid & Pricing Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Data-backed pricing recommendations calibrated for your skill level, estimated hours, and platform fees.</div>', unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if jobs_df.empty:
        st.info("No jobs available. Run discovery scan in Module 2.")
    else:
        job_options = {f"#{row['id']} - {row['title']} ({row['platform']})": row['id'] for _, row in jobs_df.iterrows()}
        selected_job_label = st.selectbox("Select Project for Pricing Guidance:", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        job_data = jobs_df[jobs_df["id"] == selected_job_id].iloc[0].to_dict()

        profile = up.get_user_profile()

        # Manual Override Input
        manual_override = st.number_input(
            "Test Manual Quotation Override (Job Currency, 0 for default suggested quote):",
            min_value=0.0, step=100.0, value=0.0
        )
        override_val = manual_override if manual_override > 0 else None

        pricing = pa.calculate_pricing_recommendation(job_data, profile, manual_quote_override=override_val)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Client's Stated Budget", pricing["budget_display"])
        p2.metric("Suggested Quotation", f"{pricing['final_quotation_job_currency']:,.2f} {pricing['currency']}")
        p3.metric("Platform Fee", f"{pricing['platform_fee_rate_percent']}% (₹{pricing['platform_fee_amount_inr']:,.0f})")
        p4.metric("Est. Net Hourly Earning", f"₹{pricing['estimated_hourly_earning_inr']:,.0f} / hr")

        st.markdown("---")
        st.markdown("### 📐 Pricing Factors & Economics")
        st.write(f"- **Complexity**: {pricing['complexity']} | **Estimated Time**: {pricing['estimated_hours']} hours | **Recommended Turnaround**: {pricing['delivery_time_recommendation']}")
        st.write(f"- **Minimum Acceptable Quote**: {pricing['minimum_acceptable_quotation']:,.2f} {pricing['currency']} (based on your profile threshold)")
        st.write(f"- **Net Take-Home**: **₹{pricing['net_earnings_inr']:,.2f}** after platform commission")

        if not pricing["budget_stated"]:
            st.info("ℹ️ The client has not stated a budget for this job. Quote reasonably based on the estimated delivery time.")

# =============================================================
# MODULE 6: PROPOSAL GENERATOR
# =============================================================
elif navigation == "6. ✍️ Proposal Generator":
    st.markdown('<div class="main-header">✍️ AI Proposal Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Customized, natural proposals referencing ONLY your confirmed skills. Generates 3 distinct human-sounding versions.</div>', unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if jobs_df.empty:
        st.info("No jobs available. Run discovery scan in Module 2.")
    else:
        job_options = {f"#{row['id']} - {row['title']} ({row['platform']})": row['id'] for _, row in jobs_df.iterrows()}
        selected_job_label = st.selectbox("Select Project for Proposal Generation:", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        job_data = jobs_df[jobs_df["id"] == selected_job_id].iloc[0].to_dict()

        profile = up.get_user_profile()

        c_name = st.text_input("Client Name (optional, if known from posting)", placeholder="e.g. John or Sarah")
        freelancer_name = st.text_input("Your Name / Sign-off", value="Excel Freelancer")

        proposals = pi.generate_three_proposal_versions(job_data, profile, client_name=c_name, freelancer_name=freelancer_name)

        prop_tab1, prop_tab2, prop_tab3 = st.tabs([
            "⚡ Version A: Short & Direct",
            "👔 Version B: Professional & Detailed",
            "🤝 Version C: Beginner-Friendly & Honest"
        ])

        with prop_tab1:
            st.caption("Ideal for quick-decision clients, Upwork short bids, or busy employers who value brevity.")
            p_text_a = st.text_area("Draft Text (Editable)", value=proposals["version_a"], height=280, key="txt_prop_a")
            c_save_a, c_copy_a = st.columns([1, 4])
            if c_save_a.button("💾 Save Draft to Tracker", key="btn_save_a"):
                succ, a_id, msg = at.record_application(
                    job_id=selected_job_id,
                    platform=job_data.get("platform", "Freelancer"),
                    proposal_text=p_text_a,
                    bid_amount=float(job_data.get("budget", 2000.0) or 2000.0),
                    status="Proposal Drafted",
                    project_title=job_data.get("title", "")
                )
                if succ:
                    st.success(f"✅ Application #{a_id} saved as 'Proposal Drafted' in Application Tracker!")
                else:
                    st.warning(msg)

        with prop_tab2:
            st.caption("Comprehensive roadmap for larger dashboard or MIS consolidation projects.")
            p_text_b = st.text_area("Draft Text (Editable)", value=proposals["version_b"], height=320, key="txt_prop_b")
            c_save_b, _ = st.columns([1, 4])
            if c_save_b.button("💾 Save Draft to Tracker", key="btn_save_b"):
                succ, a_id, msg = at.record_application(
                    job_id=selected_job_id,
                    platform=job_data.get("platform", "Freelancer"),
                    proposal_text=p_text_b,
                    bid_amount=float(job_data.get("budget", 2000.0) or 2000.0),
                    status="Proposal Drafted",
                    project_title=job_data.get("title", "")
                )
                if succ:
                    st.success(f"✅ Application #{a_id} saved as 'Proposal Drafted' in Application Tracker!")
                else:
                    st.warning(msg)

        with prop_tab3:
            st.caption("Transparent, polite, and enthusiastic. Focuses on meticulous accuracy and prompt revisions.")
            p_text_c = st.text_area("Draft Text (Editable)", value=proposals["version_c"], height=300, key="txt_prop_c")
            c_save_c, _ = st.columns([1, 4])
            if c_save_c.button("💾 Save Draft to Tracker", key="btn_save_c"):
                succ, a_id, msg = at.record_application(
                    job_id=selected_job_id,
                    platform=job_data.get("platform", "Freelancer"),
                    proposal_text=p_text_c,
                    bid_amount=float(job_data.get("budget", 2000.0) or 2000.0),
                    status="Proposal Drafted",
                    project_title=job_data.get("title", "")
                )
                if succ:
                    st.success(f"✅ Application #{a_id} saved as 'Proposal Drafted' in Application Tracker!")
                else:
                    st.warning(msg)

# =============================================================
# MODULE 7: APPLICATION TRACKER
# =============================================================
elif navigation == "7. 📬 Application Tracker":
    st.markdown('<div class="main-header">📬 Application Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage bids across all 13 pipeline stages. Strictly requires human confirmation for submission.</div>', unsafe_allow_html=True)

    app_tab1, app_tab2 = st.tabs(["📋 Application Pipeline", "➕ Record New Application"])

    with app_tab1:
        apps_df = at.get_applications()
        if not apps_df.empty:
            f_plat = st.selectbox("Filter by Platform", ["All"] + list(apps_df["platform"].unique()), key="app_f_plat")
            f_stat = st.selectbox("Filter by Status", ["All"] + at.APPLICATION_STATUSES, key="app_f_stat")

            f_view = apps_df.copy()
            if f_plat != "All":
                f_view = f_view[f_view["platform"] == f_plat]
            if f_stat != "All":
                f_view = f_view[f_view["status"] == f_stat]

            st.dataframe(
                f_view[["app_id", "job_title", "platform", "bid_amount", "currency", "status", "applied_date", "follow_up_date"]],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.markdown("#### 🔄 Update Application Status")
            sel_app_id = st.selectbox("Select Application ID to Update:", f_view["app_id"].tolist())
            cur_app = f_view[f_view["app_id"] == sel_app_id].iloc[0]

            with st.form("update_app_form"):
                u_stat_idx = at.APPLICATION_STATUSES.index(cur_app["status"]) if cur_app["status"] in at.APPLICATION_STATUSES else 0
                new_stat = st.selectbox("New Status", at.APPLICATION_STATUSES, index=u_stat_idx)
                new_fdate = st.text_input("Next Follow-up Date (YYYY-MM-DD)", value=cur_app.get("follow_up_date") or "")
                new_resp = st.text_area("Client Response / Notes", value=cur_app.get("client_response") or "")

                if st.form_submit_button("Update Status", type="primary"):
                    at.update_application_status(sel_app_id, new_stat, follow_up_date=new_fdate, client_response=new_resp)
                    st.success("✅ Application updated!")
                    st.rerun()
        else:
            st.info("No applications logged yet. Prepare an application in Module 6 or log one below.")

    with app_tab2:
        st.markdown("#### Log / Record an Application")
        jobs_df = jm.get_jobs(include_samples=include_samples)
        if not jobs_df.empty:
            with st.form("manual_app_form"):
                job_map = {f"#{r['id']} - {r['title']}": r['id'] for _, r in jobs_df.iterrows()}
                chosen_j = st.selectbox("Associated Job", list(job_map.keys()))
                rec_plat = st.selectbox("Platform", PLATFORMS)
                rec_amount = st.number_input("Proposed Amount (INR)", min_value=0.0, step=500.0, value=2500.0)
                rec_stat = st.selectbox("Initial Status", at.APPLICATION_STATUSES, index=at.APPLICATION_STATUSES.index("Submitted"))
                rec_prop = st.text_area("Proposal Text", height=120)
                rec_fdate = st.text_input("Follow-up Date (YYYY-MM-DD)", value=(date.today() + timedelta(days=3)).strftime("%Y-%m-%d"))

                submit_app = st.form_submit_button("Record Application", type="primary")
                if submit_app:
                    succ, a_id, msg = at.record_application(
                        job_id=job_map[chosen_j],
                        platform=rec_plat,
                        proposal_text=rec_prop,
                        bid_amount=rec_amount,
                        status=rec_stat,
                        follow_up_date=rec_fdate
                    )
                    if succ:
                        st.success(f"✅ Application #{a_id} recorded!")
                        st.rerun()
                    else:
                        st.warning(msg)

# =============================================================
# MODULE 8: FOLLOW-UP MANAGER
# =============================================================
elif navigation == "8. ⏰ Follow-up Manager":
    st.markdown('<div class="main-header">⏰ Follow-up Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ensure no client falls through the cracks. Prepares polite follow-up messages without automatic sending.</div>', unsafe_allow_html=True)

    groups = at.get_follow_up_groups()

    fu_tab1, fu_tab2, fu_tab3, fu_tab4 = st.tabs([
        f"🚨 Overdue ({len(groups['overdue'])})",
        f"📌 Due Today ({len(groups['due_today'])})",
        f"📅 Upcoming ({len(groups['upcoming'])})",
        f"⏳ No Response ({len(groups['no_response'])})"
    ])

    for tab, key, title in zip([fu_tab1, fu_tab2, fu_tab3, fu_tab4], ["overdue", "due_today", "upcoming", "no_response"], ["Overdue", "Due Today", "Upcoming", "No Response"]):
        with tab:
            df_g = groups[key]
            if not df_g.empty:
                st.dataframe(
                    df_g[["app_id", "job_title", "platform", "bid_amount", "applied_date", "follow_up_date", "status"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No {title.lower()} follow-ups.")

    st.markdown("---")
    st.markdown("### ✉️ Generate Polite Follow-up Message")
    all_apps = at.get_applications()
    if not all_apps.empty:
        active_apps = all_apps[~all_apps["status"].isin(["Awarded", "Completed", "Rejected", "Withdrawn"])]
        if not active_apps.empty:
            app_choices = {f"#{r['app_id']} - {r['job_title']} ({r['platform']})": r for _, r in active_apps.iterrows()}
            sel_choice = st.selectbox("Select Application for Follow-up:", list(app_choices.keys()))
            chosen_row = app_choices[sel_choice]

            stage = st.radio("Follow-up Stage:", [1, 2], format_func=lambda x: "Stage 1 (3-4 Days After Bidding)" if x == 1 else "Stage 2 (6-8 Days Gentle Check-in)")
            fu_msg = at.generate_follow_up_message(chosen_row["job_title"], client_name=chosen_row.get("client_name"), stage=stage)

            st.text_area("Customizable Message Template", value=fu_msg, height=180)
            st.caption("💡 Copy this text and send it directly through the client's official platform messaging interface.")
        else:
            st.info("No active open applications requiring follow-ups.")

# =============================================================
# MODULE 9: EARNINGS & ANALYTICS
# =============================================================
elif navigation == "9. 📈 Earnings & Analytics":
    st.markdown('<div class="main-header">📈 Earnings & Pipeline Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive freelance analytics. Strictly separates contract value, completed revenue, and money actually received.</div>', unsafe_allow_html=True)

    analytics = et.get_performance_analytics(include_samples=include_samples)

    # Top KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Project Value (Awarded)", f"₹{analytics['total_project_value']:,.0f}")
    k2.metric("Money Actually Received", f"₹{analytics['amount_received']:,.0f}")
    k3.metric("Outstanding Payments", f"₹{analytics['outstanding_payments']:,.0f}")
    k4.metric("Award Success Rate", f"{analytics['success_rate_pct']}%")

    st.markdown("---")

    # Pipeline Funnel Metrics
    st.markdown("### 🚦 Pipeline Conversion Funnel")
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("Proposals Submitted", analytics["proposals_submitted"])
    f2.metric("Client Replies", analytics["client_replies"])
    f3.metric("Interviews", analytics["interviews_count"])
    f4.metric("Awarded", analytics["projects_awarded"])
    f5.metric("Completed", analytics["projects_completed"])

    st.markdown("---")

    # Realized Earnings Logger
    st.markdown("### 💰 Realized Earnings Ledger")
    earn_df = et.get_earnings(include_samples=include_samples)
    if not earn_df.empty:
        st.dataframe(
            earn_df[["id", "project_name", "platform", "date_received", "gross_amount", "platform_fee", "net_amount", "status"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No earnings records logged yet.")

    with st.expander("➕ Log New Realized Payment"):
        with st.form("add_earn_form"):
            e_proj = st.text_input("Project Name*", placeholder="e.g. Sales MIS Dashboard Handover")
            e_gross = st.number_input("Gross Amount (INR)*", min_value=0.0, step=500.0, value=5000.0)
            e_fee = st.number_input("Platform Fee (INR)", min_value=0.0, step=100.0, value=500.0)
            e_plat = st.selectbox("Platform", PLATFORMS)
            e_date = st.text_input("Date Received (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
            e_stat = st.selectbox("Payment Status", ["received", "expected"])

            if st.form_submit_button("Record Payment", type="primary"):
                et.add_earning(e_proj, e_gross, e_fee, e_plat, e_date, status=e_stat, is_sample=0)
                st.success("✅ Payment successfully recorded!")
                st.rerun()

# =============================================================
# MODULE 10: SETTINGS
# =============================================================
elif navigation == "10. ⚙️ Settings":
    st.markdown('<div class="main-header">⚙️ System Settings & Platforms</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Configure platform credentials, manage Fiverr gigs, and audit local database integrity.</div>', unsafe_allow_html=True)

    set_tab1, set_tab2, set_tab3 = st.tabs(["🌐 Platform Accounts", "💼 Fiverr Gigs", "💾 Database Integrity & Backups"])

    with set_tab1:
        st.markdown("### 🌐 Platform Account Manager")
        plat_df = pm.get_platform_accounts()
        st.dataframe(plat_df[["platform_name", "account_status", "integration_mode", "connection_status", "last_checked_date", "profile_url"]], use_container_width=True, hide_index=True)

    with set_tab2:
        st.markdown("### 💼 Fiverr Gigs & Buyer Requests")
        gigs_df = fm.get_fiverr_gigs()
        st.dataframe(gigs_df[["id", "gig_title", "status", "target_keywords", "gig_url"]], use_container_width=True, hide_index=True)

    with set_tab3:
        st.markdown("### 💾 Database Safety & Backup")
        st.write(f"- Database Path: `{DB_PATH}`")
        st.write("- SQLite Local-first architecture: ₹0 cost, no external hosting, full data privacy.")
        if st.button("Export Jobs Backup (CSV)"):
            jobs_df = jm.get_jobs(include_samples=False)
            csv_data = jobs_df.to_csv(index=False)
            st.download_button("Download CSV Backup", csv_data, file_name="excel_hunter_jobs_backup.csv", mime="text/csv")
