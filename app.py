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
    parse_email_alert
)
from src.sample_data import seed_sample_data

# Page setup
st.set_page_config(
    page_title="Excel Hunter AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()
pm.seed_default_platforms()
fm.seed_default_fiverr_gigs()
up.get_user_profile()

# Auto-seed sample data if empty
all_jobs = jm.get_jobs()
if len(all_jobs) == 0:
    seed_sample_data()
    all_jobs = jm.get_jobs()

# Simple, friendly, clean CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Friendly Page Header */
    .friendly-header {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .friendly-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0;
    }
    .friendly-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Card styling */
    .app-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }

    /* Recommendation banners */
    .rec-box-apply {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        padding: 16px;
        color: #065F46;
        margin-bottom: 16px;
    }
    .rec-box-learn {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 10px;
        padding: 16px;
        color: #92400E;
        margin-bottom: 16px;
    }
    .rec-box-avoid {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 10px;
        padding: 16px;
        color: #991B1B;
        margin-bottom: 16px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-green { background: #DCFCE7; color: #166534; }
    .badge-blue { background: #DBEAFE; color: #1E40AF; }
    .badge-amber { background: #FEF3C7; color: #92400E; }
    .badge-gray { background: #F1F5F9; color: #475569; }

    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state helpers for seamless navigation
if "active_job_id" not in st.session_state:
    st.session_state["active_job_id"] = None
if "selected_page" not in st.session_state:
    st.session_state["selected_page"] = "🏠 Home & Progress"

# =============================================================
# SIMPLE SIDEBAR
# =============================================================
with st.sidebar:
    st.markdown("### 💼 EXCEL HUNTER AI")
    st.caption("Your Personal Excel Freelance Assistant")
    st.markdown("---")

    menu_options = [
        "🏠 Home & Progress",
        "🔍 Find Excel Jobs",
        "🎯 Job Assistant (Advice & Proposal)",
        "📬 My Applications & Follow-ups",
        "💰 Money Earned",
        "⚙️ My Profile & Skills"
    ]

    current_selection = st.radio(
        "Where would you like to go?",
        menu_options,
        index=menu_options.index(st.session_state["selected_page"]) if st.session_state["selected_page"] in menu_options else 0,
        key="main_nav_radio"
    )
    st.session_state["selected_page"] = current_selection

    st.markdown("---")
    include_samples = st.toggle("Include demo/sample jobs", value=True, help="Turn off to see only live real jobs.")
    if include_samples:
        st.caption("ℹ️ Demo mode is on. You will see both sample and real jobs.")
    else:
        st.caption("🛡️ Viewing real opportunities only.")

    st.markdown("---")
    st.caption("🔒 100% Free & Local • No subscriptions • Private SQLite database")

# Helper to format INR
def fmt_inr(val: float) -> str:
    return f"₹{val:,.0f}"

# =============================================================
# 1. HOME & PROGRESS
# =============================================================
if st.session_state["selected_page"] == "🏠 Home & Progress":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">👋 Welcome back! Let's reach your income goal.</div>
        <div class="friendly-sub">Here is your current progress toward earning ₹10,000–₹20,000 per month with Excel.</div>
    </div>
    """, unsafe_allow_html=True)

    cur_month = datetime.now().strftime("%B %Y")
    summary = et.get_monthly_summary(include_samples=include_samples)
    pipeline_kpis = at.get_pipeline_kpis()

    # Friendly Progress Bars
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### 🎯 Minimum Goal: ₹{TARGET_MIN_INR:,.0f} / month")
        pct1 = min(summary["progress_min_pct"], 100.0)
        st.progress(pct1 / 100.0)
        st.write(f"Earned so far in {cur_month}: **{fmt_inr(summary['total_net'])}** ({pct1:.0f}%)")
        if summary["gap_to_min"] > 0:
            st.caption(f"👉 You need **{fmt_inr(summary['gap_to_min'])}** more to reach your minimum goal!")
        else:
            st.success("🎉 You reached your minimum target for this month!")

    with c2:
        st.markdown(f"#### 🚀 Stretch Goal: ₹{TARGET_MAX_INR:,.0f} / month")
        pct2 = min(summary["progress_max_pct"], 100.0)
        st.progress(pct2 / 100.0)
        st.write(f"Earned so far: **{fmt_inr(summary['total_net'])}** ({pct2:.0f}%)")
        if summary["gap_to_max"] > 0:
            st.caption(f"👉 You need **{fmt_inr(summary['gap_to_max'])}** more to reach your top target.")
        else:
            st.success("🌟 Congratulations! You reached your stretch goal!")

    st.markdown("---")

    # What to do next (Quick Actions)
    st.markdown("### ⚡ What would you like to do next?")
    qa1, qa2, qa3 = st.columns(3)

    with qa1:
        st.markdown("""
        <div class="app-card">
            <h4>🔍 1. Find Jobs</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Scan Freelancer & remote feeds for new Excel opportunities.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Search for Jobs Now 👉", key="btn_go_jobs", use_container_width=True):
            st.session_state["selected_page"] = "🔍 Find Excel Jobs"
            st.rerun()

    with qa2:
        st.markdown("""
        <div class="app-card">
            <h4>🎯 2. Get Job Advice</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Check if a job is right for you and get an instant proposal.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Job Assistant 👉", key="btn_go_assistant", use_container_width=True):
            st.session_state["selected_page"] = "🎯 Job Assistant (Advice & Proposal)"
            st.rerun()

    with qa3:
        st.markdown("""
        <div class="app-card">
            <h4>💰 3. Record Money</h4>
            <p style="color: #64748B; font-size: 0.9rem;">Record money received from clients to update your goal progress.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Log Earnings 👉", key="btn_go_earnings", use_container_width=True):
            st.session_state["selected_page"] = "💰 Money Earned"
            st.rerun()

    st.markdown("---")

    # Simple activity counters
    st.markdown("### 📊 Your Freelance Numbers at a Glance")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Available Jobs", len(jm.get_jobs(include_samples=include_samples)))
    sc2.metric("Proposals Sent", pipeline_kpis["apps_submitted"])
    sc3.metric("Client Replies", pipeline_kpis["replies_count"] + pipeline_kpis["interviews_count"])
    sc4.metric("Jobs Won", pipeline_kpis["won_count"])

# =============================================================
# 2. FIND EXCEL JOBS
# =============================================================
elif st.session_state["selected_page"] == "🔍 Find Excel Jobs":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">🔍 Find Excel Jobs</div>
        <div class="friendly-sub">Search legitimate Excel freelance jobs or paste a link from any website.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_find, tab_paste = st.tabs(["⚡ Search Public Sources", "🔗 Paste a Job Link / Description"])

    with tab_find:
        st.write("Click this button to check Freelancer.com and remote feeds for new Excel work:")
        if st.button("🚀 Find New Excel Jobs Now", type="primary"):
            with st.spinner("Searching for Excel jobs..."):
                engine = DiscoveryEngine()
                res = engine.run_discovery_scan()
                st.success(f"Done! {res['summary']}")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Jobs Ready for Review")
        jobs_df = jm.get_jobs(include_samples=include_samples)

        if not jobs_df.empty:
            for _, job in jobs_df.iterrows():
                is_demo = job["is_sample"] == 1
                demo_tag = "<span class='badge badge-amber'>DEMO</span>" if is_demo else "<span class='badge badge-green'>REAL JOB</span>"
                budget_str = f"₹{job['budget']:,.0f} {job['currency']}" if job['budget'] > 0 else "Budget not specified"

                with st.container():
                    st.markdown(f"""
                    <div class="app-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <span style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">{job['title']}</span>
                                <div style="margin-top: 4px;">{demo_tag} <span class="badge badge-blue">{job['platform']}</span> <span class="badge badge-gray">Posted: {job.get('date_posted', 'Recent')}</span></div>
                            </div>
                            <div style="font-size: 1.2rem; font-weight: 800; color: #059669;">
                                {budget_str}
                            </div>
                        </div>
                        <p style="color: #475569; font-size: 0.9rem; margin-top: 10px; line-height: 1.5;">
                            {job.get('description', '')[:220]}...
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_col1, btn_col2 = st.columns([1, 4])
                    if btn_col1.button("Check This Job 👉", key=f"eval_btn_{job['id']}", type="primary"):
                        st.session_state["active_job_id"] = job["id"]
                        st.session_state["selected_page"] = "🎯 Job Assistant (Advice & Proposal)"
                        st.rerun()
                    if job.get("url"):
                        btn_col2.markdown(f"[Open Original Posting Online ↗]({job['url']})")
                    st.write("")
        else:
            st.info("No jobs found yet. Click 'Find New Excel Jobs Now' above.")

    with tab_paste:
        st.markdown("#### Found a job on Upwork, WhatsApp, or email? Paste it here:")
        with st.form("simple_paste_form"):
            p_title = st.text_input("Job Title*", placeholder="e.g. Sales MIS Dashboard in Excel")
            p_plat = st.selectbox("Where did you find it?", PLATFORMS)
            p_budget = st.number_input("Budget (in INR, or 0 if not known)", min_value=0.0, step=500.0, value=2500.0)
            p_desc = st.text_area("Job Description / Requirements*", height=120, placeholder="Paste what the client asked for...")
            p_url = st.text_input("Link (optional)", placeholder="https://...")

            if st.form_submit_button("Save Job & Evaluate", type="primary"):
                if p_title and p_desc:
                    s, new_id, msg = jm.add_job({
                        "title": p_title, "description": p_desc, "platform": p_plat,
                        "budget": p_budget, "currency": "INR", "url": p_url, "is_sample": 0
                    })
                    if s:
                        st.success("✅ Job saved!")
                        st.session_state["active_job_id"] = new_id
                        st.session_state["selected_page"] = "🎯 Job Assistant (Advice & Proposal)"
                        st.rerun()
                    else:
                        st.warning(msg)
                else:
                    st.warning("Please fill in both Title and Description.")

# =============================================================
# 3. JOB ASSISTANT (ADVICE + PROPOSAL IN ONE EASY PLACE)
# =============================================================
elif st.session_state["selected_page"] == "🎯 Job Assistant (Advice & Proposal)":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">🎯 Job Assistant</div>
        <div class="friendly-sub">Pick any job to see if it's right for you, what to charge, and get a ready-to-copy proposal.</div>
    </div>
    """, unsafe_allow_html=True)

    jobs_df = jm.get_jobs(include_samples=include_samples)
    if not jobs_df.empty:
        job_map = {f"#{r['id']} - {r['title']} ({r['platform']})": r['id'] for _, r in jobs_df.iterrows()}
        all_labels = list(job_map.keys())

        default_idx = 0
        if st.session_state["active_job_id"]:
            for i, (lbl, jid) in enumerate(job_map.items()):
                if jid == st.session_state["active_job_id"]:
                    default_idx = i
                    break

        selected_label = st.selectbox("Choose a project to evaluate:", all_labels, index=default_idx)
        selected_job_id = job_map[selected_label]
        st.session_state["active_job_id"] = selected_job_id
        job_row = jobs_df[jobs_df["id"] == selected_job_id].iloc[0].to_dict()

        profile = up.get_user_profile()
        analysis = sa.analyse_suitability(job_row, profile)
        pricing = pa.calculate_pricing_recommendation(job_row, profile)

        st.markdown("---")

        # 1. Plain English Recommendation Banner
        rec = analysis["recommendation"]
        score = analysis["suitability_score"]

        if rec == "Apply":
            st.markdown(f"""
            <div class="rec-box-apply">
                <h3 style="margin: 0; color: #065F46;">✅ Yes! You should apply for this job. (Match Score: {score}/100)</h3>
                <p style="margin: 8px 0 0 0; font-size: 0.95rem;">{analysis['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif rec == "Apply after learning something":
            st.markdown(f"""
            <div class="rec-box-learn">
                <h3 style="margin: 0; color: #92400E;">💡 You can do this with a little preparation. (Match Score: {score}/100)</h3>
                <p style="margin: 8px 0 0 0; font-size: 0.95rem;">{analysis['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="rec-box-avoid">
                <h3 style="margin: 0; color: #991B1B;">⚠️ Not recommended right now. (Match Score: {score}/100)</h3>
                <p style="margin: 8px 0 0 0; font-size: 0.95rem;">{analysis['reasoning']}</p>
            </div>
            """, unsafe_allow_html=True)

        # 2. Simple Checklist
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.markdown("#### 🛠️ Skills Needed for this Job")
            if analysis["skills_possessed"]:
                for s in analysis["skills_possessed"]:
                    st.write(f"✅ **You know this**: {s}")
            if analysis["missing_skills"]:
                for s in analysis["missing_skills"]:
                    st.write(f"❌ **You haven't checked this yet**: {s}")

        with c_info2:
            st.markdown("#### 💰 What Should You Charge?")
            st.write(f"• **Client's stated budget**: **{pricing['budget_display']}**")
            st.write(f"• **Recommended quote**: **{pricing['final_quotation_job_currency']:,.2f} {pricing['currency']}**")
            st.write(f"• **Estimated time to complete**: **{pricing['estimated_hours']} hours**")
            st.write(f"• **Take-home earning**: **₹{pricing['net_earnings_inr']:,.2f}** (after platform fees)")

        st.markdown("---")

        # 3. Ready-Made Proposal
        st.markdown("### ✍️ Ready-to-Send Proposal")
        st.caption("This proposal was written using ONLY the skills you confirmed in your profile.")

        my_name = st.text_input("Your Name / Sign-off", value="Excel Freelancer", key="assistant_my_name")
        c_name = st.text_input("Client's Name (if mentioned in post)", placeholder="e.g. John or Sarah", key="assistant_c_name")

        proposals = pi.generate_three_proposal_versions(job_row, profile, client_name=c_name, freelancer_name=my_name)

        p_style = st.radio("Choose proposal style:", [
            "⚡ Short & Direct (Best for quick messages)",
            "👔 Detailed & Professional (Best for big projects)",
            "🤝 Honest & Beginner-Friendly (Best if you are starting out)"
        ])

        if "Short" in p_style:
            prop_text = proposals["version_a"]
        elif "Detailed" in p_style:
            prop_text = proposals["version_b"]
        else:
            prop_text = proposals["version_c"]

        final_proposal = st.text_area("Your Proposal (You can edit anything here before copying):", value=prop_text, height=260)

        # One click to record submission
        col_act1, col_act2 = st.columns([2, 3])
        with col_act1:
            if st.button("✅ I Sent This Proposal to the Client!", type="primary", use_container_width=True):
                succ, a_id, msg = at.record_application(
                    job_id=selected_job_id,
                    platform=job_row.get("platform", "Freelancer"),
                    proposal_text=final_proposal,
                    bid_amount=float(pricing["final_quotation_job_currency"] * (85.0 if pricing["currency"] in ["USD", "EUR"] else 1.0)),
                    status="Submitted",
                    project_title=job_row.get("title", "")
                )
                if succ:
                    st.success("🎉 Awesome! Application recorded in your tracker. You can follow up in a few days.")
                else:
                    st.info(msg)

        with col_act2:
            st.caption("💡 When you copy and submit this proposal on Upwork/Freelancer, click the green button on the left so EXCEL HUNTER AI tracks it for you!")
    else:
        st.info("No jobs available. Go to 'Find Excel Jobs' to search.")

# =============================================================
# 4. MY APPLICATIONS & FOLLOW-UPS
# =============================================================
elif st.session_state["selected_page"] == "📬 My Applications & Follow-ups":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">📬 My Applications & Client Follow-ups</div>
        <div class="friendly-sub">Track every proposal you sent and get gentle reminders when it's time to check in with clients.</div>
    </div>
    """, unsafe_allow_html=True)

    apps_df = at.get_applications()
    groups = at.get_follow_up_groups()

    # Friendly follow-up notice
    overdue_count = len(groups["overdue"]) + len(groups["due_today"])
    if overdue_count > 0:
        st.warning(f"⏰ You have **{overdue_count} client(s)** who haven't replied. Check the 'Follow-up Helper' below to copy a polite check-in message!")

    tab_apps, tab_fu = st.tabs(["📋 Applications List", "✉️ Follow-up Helper"])

    with tab_apps:
        if not apps_df.empty:
            for _, app in apps_df.iterrows():
                stat = app["status"]
                badge_class = "badge-green" if stat in ["Awarded", "Completed"] else ("badge-blue" if stat == "Submitted" else "badge-amber")

                with st.container():
                    st.markdown(f"""
                    <div class="app-card">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <span style="font-weight: 700; font-size: 1.05rem;">{app['job_title']}</span>
                                <div><span class="badge {badge_class}">{stat}</span> <span class="badge badge-gray">{app['platform']}</span> <span style="font-size: 0.8rem; color: #64748B;">Applied on: {app['applied_date']}</span></div>
                            </div>
                            <div style="font-weight: 800; font-size: 1.1rem; color: #059669;">
                                ₹{app['bid_amount']:,.0f}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 🔄 Update Status of an Application")
            sel_app_id = st.selectbox("Select Application:", apps_df["app_id"].tolist())
            cur = apps_df[apps_df["app_id"] == sel_app_id].iloc[0]

            with st.form("up_stat_friendly"):
                new_s = st.selectbox("What happened?", [
                    "Submitted", "Client Replied", "Interview", "Awarded (I got the job! 🎉)", "Completed", "Rejected", "No Response"
                ])
                notes = st.text_input("Notes / Client reply", value=cur.get("client_response") or "")
                if st.form_submit_button("Update Status", type="primary"):
                    # Map friendly label to standard status
                    clean_s = "Awarded" if "Awarded" in new_s else new_s
                    at.update_application_status(sel_app_id, clean_s, client_response=notes)
                    st.success("Updated!"); st.rerun()
        else:
            st.info("You haven't logged any applications yet. When you send a proposal in Job Assistant, click 'I Sent This Proposal' to track it here.")

    with tab_fu:
        st.markdown("#### Need to follow up with a quiet client? Here is a polite template:")
        if not apps_df.empty:
            open_apps = apps_df[~apps_df["status"].isin(["Awarded", "Completed", "Rejected"])]
            if not open_apps.empty:
                app_dict = {f"#{r['app_id']} - {r['job_title']}": r for _, r in open_apps.iterrows()}
                chosen_app = st.selectbox("Select project to follow up on:", list(app_dict.keys()))
                r_data = app_dict[chosen_app]

                fu_msg = at.generate_follow_up_message(r_data["job_title"], client_name=r_data.get("client_name"), stage=1)
                st.text_area("Copy this polite message to your clipboard:", value=fu_msg, height=180)
                st.caption("Paste this message directly into your chat with the client.")
            else:
                st.info("No pending applications need a follow-up right now.")
        else:
            st.info("No applications logged yet.")

# =============================================================
# 5. MONEY EARNED
# =============================================================
elif st.session_state["selected_page"] == "💰 Money Earned":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">💰 Money Earned</div>
        <div class="friendly-sub">Every rupee you earn from Excel projects. Add your client payments here.</div>
    </div>
    """, unsafe_allow_html=True)

    summary = et.get_monthly_summary(include_samples=include_samples)
    earn_df = et.get_earnings(include_samples=include_samples)

    st.markdown(f"""
    <div class="app-card" style="text-align: center; background: #F0FDF4; border-color: #BBF7D0;">
        <div style="font-size: 0.9rem; font-weight: 700; color: #166534;">TOTAL REALIZED EARNINGS THIS MONTH</div>
        <div style="font-size: 2.8rem; font-weight: 800; color: #15803D; margin: 4px 0;">{fmt_inr(summary['total_net'])}</div>
        <div style="color: #475569; font-size: 0.85rem;">Goal: ₹10,000 – ₹20,000 / month</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ I Got Paid! (Record New Payment)", expanded=True):
        with st.form("simple_earn_form"):
            p_name = st.text_input("Project Name*", placeholder="e.g. Sales Dashboard for Client")
            amount = st.number_input("Amount Received (in INR)*", min_value=100.0, step=500.0, value=3000.0)
            fee = st.number_input("Platform Fee (deducted by Freelancer/Fiverr, if any)", min_value=0.0, step=50.0, value=300.0)
            plat = st.selectbox("Platform", PLATFORMS)
            p_date = st.text_input("Date Received", value=datetime.now().strftime("%Y-%m-%d"))

            if st.form_submit_button("Save Payment", type="primary"):
                et.add_earning(p_name, amount, fee, plat, p_date, is_sample=0)
                st.success("🎉 Payment recorded! Your monthly progress has been updated.")
                st.rerun()

    st.markdown("### 📜 Payment History")
    if not earn_df.empty:
        st.dataframe(
            earn_df[["project_name", "platform", "date_received", "gross_amount", "platform_fee", "net_amount"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No earnings recorded yet.")

# =============================================================
# 6. MY PROFILE & SKILLS
# =============================================================
elif st.session_state["selected_page"] == "⚙️ My Profile & Skills":
    st.markdown("""
    <div class="friendly-header">
        <div class="friendly-title">⚙️ My Profile & Confirmed Skills</div>
        <div class="friendly-sub">Tell the assistant what you know. It will only recommend jobs and write proposals based on what you select here.</div>
    </div>
    """, unsafe_allow_html=True)

    profile = up.get_user_profile()

    with st.form("friendly_profile_form"):
        st.markdown("#### 1. What Excel skills do you currently know?")
        st.caption("Check the boxes for things you feel comfortable doing:")

        cur_skills = set(profile.get("excel_skills", []))
        sel_skills = []

        c1, c2 = st.columns(2)
        half = len(up.AVAILABLE_EXCEL_SKILLS) // 2
        with c1:
            for idx, sk in enumerate(up.AVAILABLE_EXCEL_SKILLS[:half]):
                if st.checkbox(sk, value=(sk in cur_skills), key=f"f_sk_{idx}"):
                    sel_skills.append(sk)
        with c2:
            for idx, sk in enumerate(up.AVAILABLE_EXCEL_SKILLS[half:], start=half):
                if st.checkbox(sk, value=(sk in cur_skills), key=f"f_sk_{idx}"):
                    sel_skills.append(sk)

        st.markdown("#### 2. Other software you use")
        cur_tools = set(profile.get("other_tools", []))
        sel_tools = []
        tc1, tc2 = st.columns(2)
        with tc1:
            for idx, t in enumerate(up.AVAILABLE_OTHER_TOOLS[:3]):
                if st.checkbox(t, value=(t in cur_tools), key=f"f_t_{idx}"):
                    sel_tools.append(t)
        with tc2:
            for idx, t in enumerate(up.AVAILABLE_OTHER_TOOLS[3:], start=3):
                if st.checkbox(t, value=(t in cur_tools), key=f"f_t_{idx}"):
                    sel_tools.append(t)

        st.markdown("#### 3. Experience & Minimum Budget")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            exp_l = st.selectbox("Your Experience Level", ["Beginner", "Intermediate", "Advanced"], index=0)
        with e_col2:
            min_pay = st.number_input("Minimum project budget you accept (INR)", min_value=500.0, step=250.0, value=float(profile.get("min_budget", 1500.0)))

        if st.form_submit_button("Save My Skills", type="primary", use_container_width=True):
            up.save_user_profile({
                "excel_skills": sel_skills,
                "other_tools": sel_tools,
                "experience_level": exp_l,
                "min_budget": min_pay,
                "hours_per_week": 15.0
            })
            st.success("✅ Saved! Your proposals and job evaluations are now tailored to your skills.")
            st.rerun()
