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
    page_title="EXCEL HUNTER AI — Freelance Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database, platform records, gigs, and user profile
init_db()
pm.seed_default_platforms()
fm.seed_default_fiverr_gigs()
up.get_user_profile()

# Auto-seed sample data if database is brand new and empty
all_jobs = jm.get_jobs()
if len(all_jobs) == 0:
    seed_sample_data()
    all_jobs = jm.get_jobs()

# =============================================================
# SENIOR PRODUCT DESIGN SYSTEM (CSS INJECTION)
# =============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Top App Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-radius: 16px;
        padding: 24px 28px;
        color: #FFFFFF;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Executive Stat Card */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02), 0 1px 2px rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
    }
    .stat-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 8px;
    }
    .stat-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .stat-subtext {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Professional Job Card */
    .job-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: border-color 0.2s ease;
    }
    .job-card:hover {
        border-color: #3B82F6;
    }
    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 10px;
    }
    .job-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.3;
    }
    .job-meta {
        font-size: 0.82rem;
        color: #64748B;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
    }

    /* Status Pills & Tags */
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .pill-blue { background: #EFF6FF; color: #1D4ED8; border: 1px solid #DBEAFE; }
    .pill-emerald { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
    .pill-amber { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
    .pill-rose { background: #FFF1F2; color: #BE123C; border: 1px solid #FECDD3; }
    .pill-purple { background: #FAF5FF; color: #6D28D9; border: 1px solid #E9D5FF; }
    .pill-slate { background: #F1F5F9; color: #334155; border: 1px solid #E2E8F0; }

    /* Platform Grid Cards */
    .platform-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        transition: transform 0.15s ease;
    }
    .platform-card:hover {
        transform: translateY(-2px);
        border-color: #3B82F6;
    }
    .platform-title {
        font-weight: 700;
        font-size: 0.92rem;
        color: #1E293B;
        margin-bottom: 4px;
    }

    /* Section Header */
    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-top: 10px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Suitability Score Gauge */
    .gauge-container {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 1px solid #DBEAFE;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 20px;
    }
    .gauge-score {
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1;
        margin: 10px 0;
    }

    /* Proposal Box */
    .proposal-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Clean Streamlit Element Polish */
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        letter-spacing: -0.03em !important;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px) !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================
# SIDEBAR DESIGN
# =============================================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 15px 0;">
        <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">
            <span>⚡</span> EXCEL HUNTER AI
        </div>
        <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px;">
            Enterprise Freelance Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    navigation = st.radio(
        "Navigation",
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
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    include_samples = st.toggle("Show Demo Data", value=True, help="Toggle sample demonstration opportunities.")
    if include_samples:
        st.markdown("<span class='pill pill-amber'>⚠️ Demo Mode Active</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='pill pill-emerald'>🛡️ Production Mode (Live Only)</span>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top: 25px; padding: 12px; background: #F8FAFC; border-radius: 10px; border: 1px solid #E2E8F0; font-size: 0.75rem; color: #64748B;">
        <div style="font-weight: 700; color: #334155; margin-bottom: 4px;">SYSTEM STATUS</div>
        <div>🟢 Local SQLite Engine</div>
        <div>🟢 Read-Only Public APIs</div>
        <div>🔒 ₹0 Total Operating Cost</div>
        <div>⚡ v3.0 Production Ready</div>
    </div>
    """, unsafe_allow_html=True)

# Helper for formatted currency display
def fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}"

# =============================================================
# MODULE 1: OVERVIEW
# =============================================================
if navigation == "1. 📊 Overview":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>📊</span> Freelance Operations Command Center</div>
        <div class="hero-subtitle">Real-time intelligence for Excel freelance discovery, pipeline health, and monthly revenue targets.</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Income Target Progress
    cur_month = datetime.now().strftime("%Y-%m")
    summary = et.get_monthly_summary(target_month=cur_month, include_samples=include_samples)
    pipeline_kpis = at.get_pipeline_kpis()
    perf_analytics = et.get_performance_analytics(include_samples=include_samples)

    st.markdown('<div class="section-title">🎯 Monthly Income Milestones</div>', unsafe_allow_html=True)
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)

    with col_t1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Month Net Realized</div>
            <div class="stat-value" style="color: #059669;">{fmt_inr(summary['total_net'])}</div>
            <div class="stat-subtext">📅 {cur_month} Verified Receipts</div>
        </div>
        """, unsafe_allow_html=True)

    with col_t2:
        pct_min = min(summary["progress_min_pct"], 100.0)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Target 1: ₹10,000 / mo</div>
            <div class="stat-value" style="color: #2563EB;">{pct_min:.1f}%</div>
            <div class="stat-subtext">Remaining Gap: <b>{fmt_inr(summary['gap_to_min'])}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_t3:
        pct_max = min(summary["progress_max_pct"], 100.0)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Target 2: ₹20,000 / mo</div>
            <div class="stat-value" style="color: #7C3AED;">{pct_max:.1f}%</div>
            <div class="stat-subtext">Remaining Gap: <b>{fmt_inr(summary['gap_to_max'])}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_t4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Active Contract Value</div>
            <div class="stat-value" style="color: #0F172A;">{fmt_inr(perf_analytics['total_project_value'])}</div>
            <div class="stat-subtext">Outstanding: <b>{fmt_inr(perf_analytics['outstanding_payments'])}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 2. Pipeline Funnel
    st.markdown('<div class="section-title">🚦 Opportunity & Application Pipeline</div>', unsafe_allow_html=True)
    pk1, pk2, pk3, pk4, pk5 = st.columns(5)
    pk1.metric("Shortlisted / Awaiting", pipeline_kpis["awaiting_apps"])
    pk2.metric("Proposals Drafted", pipeline_kpis["proposals_drafted"])
    pk3.metric("Applications Submitted", pipeline_kpis["apps_submitted"])
    pk4.metric("Client Inquiries / Replies", pipeline_kpis["replies_count"] + pipeline_kpis["interviews_count"])
    pk5.metric("Contracts Awarded", pipeline_kpis["won_count"])

    if pipeline_kpis["follow_ups_due"] > 0:
        st.markdown(f"""
        <div style="background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 10px; padding: 12px 16px; margin: 16px 0; display: flex; align-items: center; justify-content: space-between;">
            <div style="font-size: 0.88rem; color: #92400E; font-weight: 600;">
                ⏰ <b>Action Required:</b> You have {pipeline_kpis['follow_ups_due']} client follow-up(s) due today or overdue.
            </div>
            <span class="pill pill-amber">Open Follow-up Manager</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 3. Platform Integrations Overview
    st.markdown('<div class="section-title">🌐 Platform Health & Integration Matrix</div>', unsafe_allow_html=True)
    plat_df = pm.get_platform_accounts()
    p_cols = st.columns(min(len(plat_df), 6))
    for idx, (_, p_row) in enumerate(plat_df.head(6).iterrows()):
        with p_cols[idx % 6]:
            is_conn = "Connect" in p_row.get("connection_status", "") or p_row.get("connection_status", "") == "Active"
            st_color = "#10B981" if is_conn else "#F59E0B"
            st_text = p_row.get("connection_status", "Manual")
            st.markdown(f"""
            <div class="platform-card">
                <div class="platform-title">{p_row['platform_name']}</div>
                <div style="font-size: 0.72rem; color: {st_color}; font-weight: 700; margin-bottom: 2px;">● {st_text}</div>
                <div style="font-size: 0.7rem; color: #64748B;">{p_row.get('integration_mode', 'Manual')}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 4. Top Opportunities Spotlight
    jobs_df = jm.get_jobs(include_samples=include_samples)
    st.markdown('<div class="section-title">🔥 Top High-Priority Opportunities</div>', unsafe_allow_html=True)

    if not jobs_df.empty:
        high_df = jobs_df[jobs_df["priority"] == "High"].head(4)
        if not high_df.empty:
            for _, job in high_df.iterrows():
                sample_badge = "<span class='pill pill-amber'>SAMPLE DEMO</span>" if job["is_sample"] == 1 else "<span class='pill pill-emerald'>VERIFIED LIVE</span>"
                score_badge = f"<span class='pill pill-blue'>Score {job['score']}/100</span>"
                budget_str = f"₹{job['budget']:,.0f} {job['currency']}" if job['budget'] > 0 else "Budget Unspecified"
                
                st.markdown(f"""
                <div class="job-card">
                    <div class="job-header">
                        <div>
                            <span class="job-title">{job['title']}</span>
                            <div style="margin-top: 4px;">{sample_badge} {score_badge} <span class="pill pill-slate">{job['platform']}</span></div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A;">{budget_str}</div>
                            <div style="font-size: 0.75rem; color: #64748B;">Posted: {job.get('date_posted', 'Recent')}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin: 8px 0; line-height: 1.5;">
                        {job.get('description', '')[:220]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No high-priority jobs at this time. Run discovery scan in Module 2.")
    else:
        st.info("Repository empty. Run discovery scan or toggle demo data.")

# =============================================================
# MODULE 2: JOB DISCOVERY
# =============================================================
elif navigation == "2. 🔍 Job Discovery":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>🔍</span> Job Discovery Command Center</div>
        <div class="hero-subtitle">Multi-source discovery engine pulling legitimate Excel projects from permitted public feeds and official APIs.</div>
    </div>
    """, unsafe_allow_html=True)

    disc_tab1, disc_tab2, disc_tab3 = st.tabs([
        "🚀 Automated Live Scanner",
        "📥 Universal Opportunity Importer",
        "📋 Job Repository & Pipeline"
    ])

    with disc_tab1:
        d_col1, d_col2 = st.columns([2, 1])
        with d_col1:
            st.markdown('<div class="section-title">🚀 Run Multi-Source Scanner</div>', unsafe_allow_html=True)
            st.caption("Scans Freelancer.com Official API and Remotive Public Feeds. Deduplicates against existing database.")

            selected_terms = st.multiselect(
                "Target Search Keywords for Scan:",
                options=SEARCH_TERMS,
                default=SEARCH_TERMS[:4]
            )

            if st.button("🚀 Execute Discovery Scan", type="primary", use_container_width=True):
                with st.spinner("Executing discovery scan..."):
                    engine = DiscoveryEngine()
                    res = engine.run_discovery_scan(search_terms=selected_terms)
                    st.success(f"✅ {res['summary']}")
                    st.rerun()

        with d_col2:
            st.markdown('<div class="section-title">🩺 Adapter Health</div>', unsafe_allow_html=True)
            engine = DiscoveryEngine()
            for ad in engine.adapters:
                health = ad.test_connection()
                icon = "🟢" if health.get("healthy") else "🟡"
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 8px;">
                    <div style="font-weight: 700; font-size: 0.88rem;">{icon} {ad.source_name}</div>
                    <div style="font-size: 0.75rem; color: #64748B;">{health.get('message', '')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-title">📜 Scan Audit History</div>', unsafe_allow_html=True)
        history_df = get_discovery_history(limit=5)
        if not history_df.empty:
            st.dataframe(history_df[["run_timestamp", "jobs_found", "duplicates_skipped", "errors_logged", "status", "summary_notes"]], use_container_width=True, hide_index=True)

    with disc_tab2:
        st.markdown('<div class="section-title">📥 Ingest from Any Source</div>', unsafe_allow_html=True)
        it1, it2, it3, it4 = st.tabs(["🔗 Paste URL", "📄 Paste Text / Chat", "📬 Parse Email Alert", "📊 Upload CSV"])

        with it1:
            with st.form("imp_url"):
                url_in = st.text_input("Opportunity URL*", placeholder="https://www.upwork.com/jobs/~01example...")
                title_in = st.text_input("Job Title (optional)")
                budget_in = st.number_input("Budget (INR)", min_value=0.0, step=500.0, value=3500.0)
                desc_in = st.text_area("Description Excerpt (optional)", height=90)
                client_in = st.text_input("Client Info (optional)")
                if st.form_submit_button("Import Link", type="primary"):
                    succ, j_id, msg = import_job_from_url(url_in, title_in, budget_in, desc_in, client_in)
                    if succ: st.success(f"✅ Job #{j_id} imported!"); st.rerun()
                    else: st.warning(msg)

        with it2:
            with st.form("imp_txt"):
                p_in = st.selectbox("Platform / Source", PLATFORMS)
                link_in = st.text_input("Link (optional)")
                b_in = st.number_input("Budget (0 to auto-extract)", min_value=0.0, step=500.0, value=0.0)
                text_in = st.text_area("Job Brief / Client Message*", height=140)
                if st.form_submit_button("Import Text", type="primary"):
                    succ, j_id, msg = import_job_from_pasted_text(text_in, p_in, link_in, b_in)
                    if succ: st.success(f"✅ Job #{j_id} imported!"); st.rerun()
                    else: st.warning(msg)

        with it3:
            with st.form("imp_em"):
                sub_in = st.text_input("Subject Line*")
                pl_in = st.selectbox("Alert Source", ["Upwork", "Freelancer.com", "Fiverr", "Other"])
                em_body = st.text_area("Email Body*", height=140)
                if st.form_submit_button("Parse Alert", type="primary"):
                    succ, j_id, msg = parse_email_alert(sub_in, em_body, pl_in)
                    if succ: st.success(f"✅ Job #{j_id} imported!"); st.rerun()
                    else: st.warning(msg)

        with it4:
            csv_f = st.file_uploader("Upload CSV", type=["csv"])
            if csv_f and st.button("Process CSV File", type="primary"):
                df = pd.read_csv(csv_f)
                c_imp = 0
                for _, r in df.iterrows():
                    s, _, _ = jm.add_job({
                        "title": str(r.get("title", "")), "description": str(r.get("description", "")),
                        "platform": str(r.get("platform", "Direct Client")), "budget": float(r.get("budget", 0) or 0),
                        "currency": str(r.get("currency", "INR")), "url": str(r.get("url", "")), "is_sample": 0
                    })
                    if s: c_imp += 1
                st.success(f"Successfully imported {c_imp} jobs!"); st.rerun()

    with disc_tab3:
        jobs_df = jm.get_jobs(include_samples=include_samples)
        if not jobs_df.empty:
            st.dataframe(
                jobs_df[["id", "title", "platform", "budget", "currency", "priority", "score", "status", "date_posted"]],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No jobs recorded.")

# =============================================================
# MODULE 3: USER SKILLS PROFILE
# =============================================================
elif navigation == "3. 👤 My Skills Profile":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>👤</span> My Confirmed Skills & Portfolio</div>
        <div class="hero-subtitle">Your verified foundation. The assistant will NEVER fabricate client claims or tools you have not selected.</div>
    </div>
    """, unsafe_allow_html=True)

    profile = up.get_user_profile()
    prof_t1, prof_t2 = st.tabs(["📝 Skills & Experience Profile", "📁 Verified Portfolio Projects"])

    with prof_t1:
        with st.form("prof_form"):
            st.markdown('<div class="section-title">1. Confirmed Excel Skills</div>', unsafe_allow_html=True)
            st.caption("Check only the skills you can confidently execute today:")
            sel_excel = []
            cur_excel = set(profile.get("excel_skills", []))
            ec1, ec2, ec3 = st.columns(3)
            for idx, sk in enumerate(up.AVAILABLE_EXCEL_SKILLS):
                with [ec1, ec2, ec3][idx % 3]:
                    if st.checkbox(sk, value=(sk in cur_excel), key=f"ex_{idx}"):
                        sel_excel.append(sk)

            st.markdown('<div class="section-title">2. Other Software & Tools</div>', unsafe_allow_html=True)
            sel_tools = []
            cur_tools = set(profile.get("other_tools", []))
            tc1, tc2, tc3 = st.columns(3)
            for idx, tl in enumerate(up.AVAILABLE_OTHER_TOOLS):
                with [tc1, tc2, tc3][idx % 3]:
                    if st.checkbox(tl, value=(tl in cur_tools), key=f"tl_{idx}"):
                        sel_tools.append(tl)

            st.markdown("---")
            st.markdown('<div class="section-title">3. Experience Level & Narrative</div>', unsafe_allow_html=True)
            c_lvl, c_hrs = st.columns(2)
            with c_lvl:
                cur_exp = profile.get("experience_level", "Beginner")
                exp_idx = up.EXPERIENCE_LEVELS.index(cur_exp) if cur_exp in up.EXPERIENCE_LEVELS else 0
                sel_exp = st.selectbox("Experience Level", up.EXPERIENCE_LEVELS, index=exp_idx)
            with c_hrs:
                hrs_val = st.number_input("Weekly Available Hours", min_value=1.0, max_value=80.0, value=float(profile.get("hours_per_week", 15.0)))

            w_desc = st.text_area("Actual Practical Work Experience", value=profile.get("work_experience_desc", ""), height=70, placeholder="e.g. 2 years building MIS sheets and cleaning retail databases...")
            c_proj = st.text_area("Completed Projects Summary", value=profile.get("completed_projects_desc", ""), height=70, placeholder="e.g. Cash flow model, sales tracking dashboard with slicers...")
            i_know = st.text_area("Industry & Business Knowledge", value=profile.get("industry_knowledge", ""), height=70, placeholder="e.g. Retail inventory, e-commerce sales reporting, general bookkeeping...")

            st.markdown("---")
            st.markdown('<div class="section-title">4. Minimum Financial Threshold</div>', unsafe_allow_html=True)
            min_b = st.number_input("Minimum Acceptable Project Budget (INR)", min_value=500.0, max_value=100000.0, value=float(profile.get("min_budget", 1500.0)), step=250.0)

            if st.form_submit_button("💾 Save Verified Profile", type="primary", use_container_width=True):
                up.save_user_profile({
                    "excel_skills": sel_excel, "other_tools": sel_tools, "experience_level": sel_exp,
                    "work_experience_desc": w_desc, "completed_projects_desc": c_proj, "industry_knowledge": i_know,
                    "hours_per_week": hrs_val, "preferred_duration": "1-2 weeks", "min_budget": min_b
                })
                st.success("✅ Profile successfully saved! All proposals and suitability models will reflect these verified attributes."); st.rerun()

    with prof_t2:
        st.markdown('<div class="section-title">📁 Confirmed Portfolio Projects</div>', unsafe_allow_html=True)
        items = up.get_portfolio_projects()
        if items:
            for p in items:
                with st.expander(f"📊 {p['project_title']} ({p.get('completion_status', 'Completed')})"):
                    st.write(p.get("project_description", ""))
                    st.caption(f"**Skills:** {p.get('skills_used', '')} | **Link:** {p.get('portfolio_link', 'None')}")
                    if st.button("Delete Project", key=f"del_p_{p['id']}"):
                        up.delete_portfolio_project(p['id']); st.rerun()
        else:
            st.info("No portfolio projects recorded.")

        st.markdown('<div class="section-title">➕ Add New Project</div>', unsafe_allow_html=True)
        with st.form("new_port"):
            ntitle = st.text_input("Project Name*")
            ndesc = st.text_area("Project Summary*")
            nskills = st.text_input("Skills Used (e.g. Dashboards, Pivot Tables)*")
            nlink = st.text_input("File Link / Repository (optional)")
            if st.form_submit_button("Add to Portfolio", type="primary"):
                if ntitle and ndesc:
                    up.add_portfolio_project(ntitle, ndesc, nskills, nlink)
                    st.success("✅ Added to portfolio!"); st.rerun()

# =============================================================
# MODULE 4: PROJECT SUITABILITY ANALYSER
# =============================================================
elif navigation == "4. 🧠 Project Analysis":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>🧠</span> 100-Point Project Suitability Analyser</div>
        <div class="hero-subtitle">Mathematical evaluation of skill fit, scope feasibility, and budget suitability against your verified profile.</div>
    </div>
    """, unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if not jobs_df.empty:
        job_map = {f"#{r['id']} - {r['title']} ({r['platform']})": r['id'] for _, r in jobs_df.iterrows()}
        sel_lbl = st.selectbox("Select Project for Deep Analysis:", list(job_map.keys()))
        job_row = jobs_df[jobs_df["id"] == job_map[sel_lbl]].iloc[0].to_dict()

        profile = up.get_user_profile()
        analysis = sa.analyse_suitability(job_row, profile)

        # Recommendation Card
        rec = analysis["recommendation"]
        score_color = "#10B981" if analysis["suitability_score"] >= 70 else ("#F59E0B" if analysis["suitability_score"] >= 50 else "#EF4444")

        st.markdown(f"""
        <div class="gauge-container">
            <div style="font-size: 0.85rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">OVERALL SUITABILITY INDEX</div>
            <div class="gauge-score" style="color: {score_color};">{analysis['suitability_score']}<span style="font-size: 1.5rem; color: #94A3B8;">/100</span></div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">RECOMMENDATION: {rec.upper()}</div>
            <div style="font-size: 0.92rem; color: #475569; max-width: 650px; margin: 0 auto;">{analysis['reasoning']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Breakdown Metrics
        st.markdown('<div class="section-title">📊 6-Factor Suitability Breakdown</div>', unsafe_allow_html=True)
        sb = analysis["score_breakdown"]
        sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
        sc1.metric("Skill Match", f"{sb['skill_match']}/30")
        sc2.metric("Budget Fit", f"{sb['budget_suitability']}/15")
        sc3.metric("Scope Clarity", f"{sb['project_clarity']}/15")
        sc4.metric("Credibility", f"{sb['client_credibility']}/15")
        sc5.metric("Feasibility", f"{sb['delivery_feasibility']}/15")
        sc6.metric("Deadline", f"{sb['deadline_feasibility']}/10")

        st.markdown("---")
        sk_col1, sk_col2 = st.columns(2)
        with sk_col1:
            st.markdown('<div class="section-title">✅ Verified Skills Possessed</div>', unsafe_allow_html=True)
            if analysis["skills_possessed"]:
                for s in analysis["skills_possessed"]:
                    st.markdown(f"<span class='pill pill-emerald' style='margin: 4px 4px 4px 0;'>✓ {s}</span>", unsafe_allow_html=True)
            else:
                st.caption("No specific advanced formulas extracted.")

        with sk_col2:
            st.markdown('<div class="section-title">⚠️ Unconfirmed / Missing Skills</div>', unsafe_allow_html=True)
            if analysis["missing_skills"]:
                for s in analysis["missing_skills"]:
                    st.markdown(f"<span class='pill pill-rose' style='margin: 4px 4px 4px 0;'>✗ {s}</span>", unsafe_allow_html=True)
            else:
                st.success("Zero missing skills! You possess 100% of required tools.")

        if analysis["potential_risks"]:
            st.markdown('<div class="section-title">🚩 Identified Scope & Platform Risks</div>', unsafe_allow_html=True)
            for rk in analysis["potential_risks"]:
                st.caption(f"• {rk}")
    else:
        st.info("No jobs to analyze.")

# =============================================================
# MODULE 5: BID & PRICING ASSISTANT
# =============================================================
elif navigation == "5. 🏷️ Bid & Pricing Assistant":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>🏷️</span> Data-Backed Pricing Assistant</div>
        <div class="hero-subtitle">Calibrates quotes against project complexity, platform commissions, and realistic hourly rates.</div>
    </div>
    """, unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if not jobs_df.empty:
        job_map = {f"#{r['id']} - {r['title']} ({r['platform']})": r['id'] for _, r in jobs_df.iterrows()}
        sel_lbl = st.selectbox("Select Project to Price:", list(job_map.keys()))
        job_row = jobs_df[jobs_df["id"] == job_map[sel_lbl]].iloc[0].to_dict()

        profile = up.get_user_profile()

        st.markdown('<div class="section-title">🎛️ Interactive Bid Simulator</div>', unsafe_allow_html=True)
        c_sim1, c_sim2 = st.columns([1, 2])
        with c_sim1:
            override_val = st.number_input("Custom Quote Override (Job Currency, 0 for default):", min_value=0.0, step=100.0, value=0.0)
            use_override = override_val if override_val > 0 else None

        pricing = pa.calculate_pricing_recommendation(job_row, profile, manual_quote_override=use_override)

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Client Stated Budget</div>
                <div class="stat-value" style="font-size: 1.4rem;">{pricing['budget_display']}</div>
                <div class="stat-subtext">Currency: {pricing['currency']}</div>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Suggested Quotation</div>
                <div class="stat-value" style="color: #2563EB; font-size: 1.4rem;">{pricing['final_quotation_job_currency']:,.2f} {pricing['currency']}</div>
                <div class="stat-subtext">Est. Hours: {pricing['estimated_hours']} hrs</div>
            </div>
            """, unsafe_allow_html=True)

        with p3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Platform Commission</div>
                <div class="stat-value" style="color: #D97706; font-size: 1.4rem;">{pricing['platform_fee_rate_percent']}%</div>
                <div class="stat-subtext">Fee: {fmt_inr(pricing['platform_fee_amount_inr'])}</div>
            </div>
            """, unsafe_allow_html=True)

        with p4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Net Take-Home / hr</div>
                <div class="stat-value" style="color: #059669; font-size: 1.4rem;">₹{pricing['estimated_hourly_earning_inr']:,.0f} / hr</div>
                <div class="stat-subtext">Total Net: <b>{fmt_inr(pricing['net_earnings_inr'])}</b></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.write(f"• **Recommended Turnaround Time**: **{pricing['delivery_time_recommendation']}**")
        st.write(f"• **Minimum Acceptable Floor**: **{pricing['minimum_acceptable_quotation']:,.2f} {pricing['currency']}**")
    else:
        st.info("No jobs to price.")

# =============================================================
# MODULE 6: PROPOSAL GENERATOR
# =============================================================
elif navigation == "6. ✍️ Proposal Generator":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>✍️</span> AI Proposal Intelligence Suite</div>
        <div class="hero-subtitle">Customized, human-sounding proposals crafted exclusively around your verified capabilities.</div>
    </div>
    """, unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if not jobs_df.empty:
        job_map = {f"#{r['id']} - {r['title']} ({r['platform']})": r['id'] for _, r in jobs_df.iterrows()}
        sel_lbl = st.selectbox("Select Project to Draft Proposals For:", list(job_map.keys()))
        job_row = jobs_df[jobs_df["id"] == job_map[sel_lbl]].iloc[0].to_dict()

        profile = up.get_user_profile()
        c_name_in = st.text_input("Client Name (optional, if stated in post)", placeholder="e.g. Sarah")
        my_name = st.text_input("Your Sign-Off Name", value="Excel Specialist")

        proposals = pi.generate_three_proposal_versions(job_row, profile, client_name=c_name_in, freelancer_name=my_name)

        pt1, pt2, pt3 = st.tabs([
            "⚡ Version A: Short & Direct",
            "👔 Version B: Professional Roadmap",
            "🤝 Version C: Transparent & Honest"
        ])

        for tab, ver_key, desc in [
            (pt1, "version_a", "Brief, crisp, and to the point. Perfect for mobile-reading clients."),
            (pt2, "version_b", "Structured phases and quality assurance guarantees for larger models."),
            (pt3, "version_c", "Friendly, genuine, and focused on meticulous accuracy and communication.")
        ]:
            with tab:
                st.caption(desc)
                text_draft = st.text_area("Custom Proposal Text (Editable)", value=proposals[ver_key], height=300, key=f"draft_{ver_key}")
                if st.button("💾 Save as Application Draft", key=f"save_{ver_key}", type="primary"):
                    succ, a_id, msg = at.record_application(
                        job_id=job_row["id"], platform=job_row.get("platform", "Freelancer"),
                        proposal_text=text_draft, bid_amount=float(job_row.get("budget", 2000.0) or 2000.0),
                        status="Proposal Drafted", project_title=job_row.get("title", "")
                    )
                    if succ: st.success(f"✅ Application #{a_id} saved in Application Tracker!"); st.rerun()
                    else: st.warning(msg)
    else:
        st.info("No jobs to generate proposals for.")

# =============================================================
# MODULE 7: APPLICATION TRACKER
# =============================================================
elif navigation == "7. 📬 Application Tracker":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>📬</span> Application Pipeline & History</div>
        <div class="hero-subtitle">Comprehensive tracking across all 13 pipeline stages. Strictly requires human confirmation.</div>
    </div>
    """, unsafe_allow_html=True)

    at_tab1, at_tab2 = st.tabs(["📋 Active Pipeline Board", "➕ Record Application Manually"])

    with at_tab1:
        apps_df = at.get_applications()
        if not apps_df.empty:
            f_plat = st.selectbox("Filter Platform", ["All"] + list(apps_df["platform"].unique()))
            f_stat = st.selectbox("Filter Status", ["All"] + at.APPLICATION_STATUSES)

            view_df = apps_df.copy()
            if f_plat != "All": view_df = view_df[view_df["platform"] == f_plat]
            if f_stat != "All": view_df = view_df[view_df["status"] == f_stat]

            st.dataframe(
                view_df[["app_id", "job_title", "platform", "bid_amount", "currency", "status", "applied_date", "follow_up_date"]],
                use_container_width=True, hide_index=True
            )

            st.markdown('<div class="section-title">🔄 Update Application Progress</div>', unsafe_allow_html=True)
            sel_app = st.selectbox("Select Application ID to Update:", view_df["app_id"].tolist())
            app_curr = view_df[view_df["app_id"] == sel_app].iloc[0]

            with st.form("up_app"):
                idx_st = at.APPLICATION_STATUSES.index(app_curr["status"]) if app_curr["status"] in at.APPLICATION_STATUSES else 0
                new_st = st.selectbox("Pipeline Status", at.APPLICATION_STATUSES, index=idx_st)
                new_fu = st.text_input("Next Follow-up Date (YYYY-MM-DD)", value=app_curr.get("follow_up_date") or "")
                new_rsp = st.text_area("Client Response / Notes", value=app_curr.get("client_response") or "")

                if st.form_submit_button("Save Application Update", type="primary"):
                    at.update_application_status(sel_app, new_st, follow_up_date=new_fu, client_response=new_rsp)
                    st.success("✅ Application updated!"); st.rerun()
        else:
            st.info("No applications logged yet.")

    with at_tab2:
        jobs_df = jm.get_jobs(include_samples=include_samples)
        if not jobs_df.empty:
            with st.form("rec_app_man"):
                j_map = {f"#{r['id']} - {r['title']}": r['id'] for _, r in jobs_df.iterrows()}
                cj = st.selectbox("Project", list(j_map.keys()))
                cplat = st.selectbox("Platform", PLATFORMS)
                c_bid = st.number_input("Proposed Bid (INR)", min_value=0.0, step=500.0, value=3000.0)
                c_stat = st.selectbox("Status", at.APPLICATION_STATUSES, index=at.APPLICATION_STATUSES.index("Submitted"))
                c_prop = st.text_area("Proposal Copy", height=120)
                c_fdate = st.text_input("Follow-up Date", value=(date.today() + timedelta(days=3)).strftime("%Y-%m-%d"))

                if st.form_submit_button("Confirm & Record Application", type="primary"):
                    s, a_id, msg = at.record_application(
                        job_id=j_map[cj], platform=cplat, proposal_text=c_prop,
                        bid_amount=c_bid, status=c_stat, follow_up_date=c_fdate
                    )
                    if s: st.success(f"✅ Application #{a_id} recorded!"); st.rerun()
                    else: st.warning(msg)

# =============================================================
# MODULE 8: FOLLOW-UP MANAGER
# =============================================================
elif navigation == "8. ⏰ Follow-up Manager":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>⏰</span> Client Follow-up Command Center</div>
        <div class="hero-subtitle">Systematic client check-ins ensuring zero dropped opportunities. Prepares polite templates ready to copy.</div>
    </div>
    """, unsafe_allow_html=True)

    groups = at.get_follow_up_groups()

    t_od, t_dt, t_up, t_nr = st.tabs([
        f"🚨 Overdue ({len(groups['overdue'])})",
        f"📌 Due Today ({len(groups['due_today'])})",
        f"📅 Upcoming ({len(groups['upcoming'])})",
        f"⏳ No Response ({len(groups['no_response'])})"
    ])

    for tab, k in [(t_od, "overdue"), (t_dt, "due_today"), (t_up, "upcoming"), (t_nr, "no_response")]:
        with tab:
            df_curr = groups[k]
            if not df_curr.empty:
                st.dataframe(
                    df_curr[["app_id", "job_title", "platform", "bid_amount", "applied_date", "follow_up_date", "status"]],
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("No items in this category.")

    st.markdown("---")
    st.markdown('<div class="section-title">✉️ Generate Professional Follow-up Message</div>', unsafe_allow_html=True)
    all_apps = at.get_applications()
    if not all_apps.empty:
        open_apps = all_apps[~all_apps["status"].isin(["Awarded", "Completed", "Rejected", "Withdrawn"])]
        if not open_apps.empty:
            choices = {f"#{r['app_id']} - {r['job_title']} ({r['platform']})": r for _, r in open_apps.iterrows()}
            chosen = st.selectbox("Select Target Application:", list(choices.keys()))
            row = choices[chosen]

            stage = st.radio("Follow-up Cadence:", [1, 2], format_func=lambda x: "Stage 1 (3-4 Days Polite Check-in)" if x == 1 else "Stage 2 (6-8 Days Final Friendly Touchpoint)")
            msg_text = at.generate_follow_up_message(row["job_title"], client_name=row.get("client_name"), stage=stage)

            st.text_area("Message Copy (Ready to Paste to Client)", value=msg_text, height=180)
            st.caption("💡 Copy and send directly inside your client's official portal messaging interface.")
        else:
            st.info("No active pending applications.")

# =============================================================
# MODULE 9: EARNINGS & ANALYTICS
# =============================================================
elif navigation == "9. 📈 Earnings & Analytics":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>📈</span> Executive Financial & Pipeline Analytics</div>
        <div class="hero-subtitle">Comprehensive freelance business analytics. Strictly keeps contract value, completed revenue, and money received separate.</div>
    </div>
    """, unsafe_allow_html=True)

    analytics = et.get_performance_analytics(include_samples=include_samples)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Total Contract Value</div>
            <div class="stat-value" style="color: #2563EB;">{fmt_inr(analytics['total_project_value'])}</div>
            <div class="stat-subtext">Won & Completed Projects</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Money Actually Received</div>
            <div class="stat-value" style="color: #059669;">{fmt_inr(analytics['amount_received'])}</div>
            <div class="stat-subtext">Verified Bank Receipts</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Outstanding Balances</div>
            <div class="stat-value" style="color: #D97706;">{fmt_inr(analytics['outstanding_payments'])}</div>
            <div class="stat-subtext">Contract Value - Received</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">Proposal Win Rate</div>
            <div class="stat-value" style="color: #7C3AED;">{analytics['success_rate_pct']}%</div>
            <div class="stat-subtext">Awarded / Submitted</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">🚦 Conversion Funnel Velocity</div>', unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("Proposals Submitted", analytics["proposals_submitted"])
    f2.metric("Client Replies", analytics["client_replies"])
    f3.metric("Interviews", analytics["interviews_count"])
    f4.metric("Awarded", analytics["projects_awarded"])
    f5.metric("Completed", analytics["projects_completed"])

    st.markdown("---")
    st.markdown('<div class="section-title">💰 Realized Cash Inflow Ledger</div>', unsafe_allow_html=True)
    earn_df = et.get_earnings(include_samples=include_samples)
    if not earn_df.empty:
        st.dataframe(
            earn_df[["id", "project_name", "platform", "date_received", "gross_amount", "platform_fee", "net_amount", "status"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No earnings records logged.")

    with st.expander("➕ Record New Verified Payment"):
        with st.form("add_earn"):
            ep = st.text_input("Project Name*")
            eg = st.number_input("Gross Amount (INR)*", min_value=0.0, step=500.0, value=6000.0)
            ef = st.number_input("Platform Fee (INR)", min_value=0.0, step=100.0, value=600.0)
            eplat = st.selectbox("Platform", PLATFORMS)
            ed = st.text_input("Date Received", value=datetime.now().strftime("%Y-%m-%d"))
            estat = st.selectbox("Status", ["received", "expected"])

            if st.form_submit_button("Record Cash Entry", type="primary"):
                et.add_earning(ep, eg, ef, eplat, ed, status=estat, is_sample=0)
                st.success("✅ Payment logged!"); st.rerun()

# =============================================================
# MODULE 10: SETTINGS
# =============================================================
elif navigation == "10. ⚙️ Settings":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title"><span>⚙️</span> System Settings & Data Integrity</div>
        <div class="hero-subtitle">Platform account controls, Fiverr gig optimization, and local SQLite data backups.</div>
    </div>
    """, unsafe_allow_html=True)

    st1, st2, st3 = st.tabs(["🌐 Platform Accounts", "💼 Fiverr Gigs", "💾 Data Backups"])

    with st1:
        st.markdown('<div class="section-title">🌐 Configured Platforms</div>', unsafe_allow_html=True)
        plat_df = pm.get_platform_accounts()
        st.dataframe(plat_df[["platform_name", "account_status", "integration_mode", "connection_status", "last_checked_date", "profile_url"]], use_container_width=True, hide_index=True)

    with st2:
        st.markdown('<div class="section-title">💼 Fiverr Gigs Portfolio</div>', unsafe_allow_html=True)
        g_df = fm.get_fiverr_gigs()
        st.dataframe(g_df[["id", "gig_title", "status", "target_keywords", "gig_url"]], use_container_width=True, hide_index=True)

    with st3:
        st.markdown('<div class="section-title">💾 Local SQLite Database Operations</div>', unsafe_allow_html=True)
        st.write(f"- Database Path: `{DB_PATH}`")
        if st.button("Download CSV Backup of Jobs"):
            jobs_df = jm.get_jobs(include_samples=False)
            st.download_button("Click to Download CSV", jobs_df.to_csv(index=False), "excel_hunter_jobs_backup.csv", "text/csv")
