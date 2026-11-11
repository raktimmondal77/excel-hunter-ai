import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from src.db import init_db
from src.config import JOB_STATUSES, PRIORITIES, PLATFORMS, TARGET_MIN_INR, TARGET_MAX_INR, DB_PATH, SAMPLE_CSV_PATH
import src.job_manager as jm
import src.earnings_tracker as et
import src.platform_manager as pm
import src.proposal_generator as pg
import src.application_tracker as at
from src.sample_data import seed_sample_data

# Set Streamlit page config
st.set_page_config(
    page_title="Excel Hunter AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and platform accounts
init_db()
pm.seed_default_platforms()

# Auto-seed sample data if database is brand new and empty
all_jobs = jm.get_jobs()
if len(all_jobs) == 0:
    seed_sample_data()
    all_jobs = jm.get_jobs()

# Custom CSS for polished styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
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
    .card-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("# 🎯 EXCEL HUNTER AI")
st.sidebar.markdown("Zero-Cost Freelance Job Hunting Assistant")
st.sidebar.markdown("---")

navigation = st.sidebar.radio(
    "Go to Module:",
    [
        "📊 Dashboard & Overview",
        "🚀 Application Assistant",
        "📬 Application History & Follow-ups",
        "📋 Job Repository & Pipeline",
        "💰 Earnings & Monthly Targets",
        "📥 CSV Job Import",
        "🌐 Platform Accounts & Policies",
        "⚙️ Database & Settings"
    ]
)

include_samples = st.sidebar.checkbox("Include Sample Data", value=True, help="Toggle visibility of demonstration records.")

if include_samples:
    st.sidebar.warning("⚠️ Demo Mode: Sample demonstration records are visible. Uncheck above to view only real data.")
else:
    st.sidebar.success("🛡️ Production Mode: Viewing real records only.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Safety & Rules")
st.sidebar.caption("• ₹0 Budget: No paid APIs or subscriptions\n• Offline-first: Data stored locally in SQLite\n• No automatic proposal sending\n• No passwords or cookies stored\n• Approval required for all client actions")

# -------------------------------------------------------------
# Module 1: Dashboard & Overview
# -------------------------------------------------------------
if navigation == "📊 Dashboard & Overview":
    st.markdown('<div class="main-header">📊 Freelance Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live view of discovered Excel opportunities, application pipeline, and monthly income targets.</div>', unsafe_allow_html=True)

    # Monthly Summary
    cur_month = datetime.now().strftime("%Y-%m")
    summary = et.get_monthly_summary(target_month=cur_month, include_samples=include_samples)

    # Monthly Target Progress Bars
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

    # Application Pipeline Counters
    pipeline_kpis = at.get_pipeline_kpis()
    st.markdown("### 🚦 Application & Opportunity Pipeline")
    pkpi1, pkpi2, pkpi3, pkpi4 = st.columns(4)
    pkpi1.metric("Jobs Awaiting Applications", pipeline_kpis["awaiting_apps"], help="Shortlisted jobs ready for proposal generation.")
    pkpi2.metric("Proposals Ready for Review", pipeline_kpis["proposals_drafted"], help="Jobs with drafted proposals.")
    pkpi3.metric("Applications Submitted", pipeline_kpis["apps_submitted"], help="Proposals sent to clients.")
    pkpi4.metric(
        "Replies & Follow-ups Due",
        pipeline_kpis["follow_ups_due"],
        delta=f"{pipeline_kpis['replies_count']} Client Replies" if pipeline_kpis['replies_count'] > 0 else None,
        help="Applications due for check-in or client responses received."
    )

    # Follow-ups Due Alert
    follow_ups_df = at.get_follow_ups_due()
    if len(follow_ups_df) > 0:
        with st.expander(f"⏰ Follow-Up Reminder: {len(follow_ups_df)} Application(s) Due for Check-In", expanded=True):
            st.info("Clients often take 2-4 days to review bids. A courteous follow-up increases response rates:")
            for _, f_app in follow_ups_df.iterrows():
                st.markdown(f"- **{f_app['job_title']}** on {f_app['platform']} (Applied: {f_app['applied_date']}, Due: {f_app['follow_up_date']}) — *Note: {f_app['follow_up_notes'] or 'Standard follow-up'}*")

    st.markdown("---")

    # High-level KPIs
    jobs_df = jm.get_jobs(include_samples=include_samples)
    total_jobs = len(jobs_df)
    high_priority_count = len(jobs_df[jobs_df["priority"] == "High"]) if total_jobs > 0 else 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Jobs Found", total_jobs)
    kpi2.metric("High Priority Matches", high_priority_count, help="Jobs scored 70+ matching Excel, Dashboard, or VBA skills.")
    kpi3.metric("Interviews Active", pipeline_kpis["interviews_count"])
    kpi4.metric("Net Earned (This Month)", f"₹{summary['total_net']:,.0f}", delta=f"Expected: ₹{summary['expected_net']:,.0f}")

    # Risk & Flagged Alert Section
    if total_jobs > 0:
        flagged_jobs = jobs_df[jobs_df["risk_flags"].str.len() > 2]
        if len(flagged_jobs) > 0:
            with st.expander(f"⚠️ Fraud & Risk Detection: {len(flagged_jobs)} Job(s) Flagged as Suspicious", expanded=True):
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

    # High Priority Job Spotlight
    st.markdown("### 🔥 Top High-Priority Opportunities")
    if total_jobs > 0:
        high_df = jobs_df[jobs_df["priority"] == "High"].head(5)
        if len(high_df) > 0:
            for _, job in high_df.iterrows():
                with st.container():
                    c_title, c_budget, c_score, c_status = st.columns([3, 1, 1, 1])
                    sample_lbl = " [SAMPLE]" if job["is_sample"] == 1 else ""
                    c_title.markdown(f"**{job['title']}**{sample_lbl}\n\n*Platform:* {job['platform']} | *Posted:* {job['date_posted'] or 'Recent'}")
                    c_budget.markdown(f"**₹{job['budget']:,.0f}** {job['currency']}")
                    c_score.markdown(f"Match Score: **{job['score']}/100**")
                    c_status.markdown(f"`{job['status']}`")
                    st.divider()
        else:
            st.info("No high-priority jobs at this time. Import new jobs via CSV to evaluate more opportunities.")
    else:
        st.info("No jobs recorded. Import CSV jobs or enable sample data.")

# -------------------------------------------------------------
# Module 2: Job Application Assistant & Honest Proposal Generator
# -------------------------------------------------------------
elif navigation == "🚀 Application Assistant":
    st.markdown('<div class="main-header">🚀 Job Application Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect opportunities, open original postings, generate honest tailored proposals, and confirm submissions.</div>', unsafe_allow_html=True)

    # Policy notice
    st.info("🛡️ **Policy Protection**: Excel Hunter AI assists your workflow by generating tailored drafts and opening links. All logins, submissions, and client communications remain 100% human-controlled in accordance with platform rules.")

    jobs_pool = jm.get_jobs(include_samples=include_samples)
    if len(jobs_pool) == 0:
        st.warning("No jobs available. Please import jobs or enable sample data.")
    else:
        # Preferred filter
        st.markdown("##### 1. Select a Freelance Opportunity")
        filter_status = st.radio("Show jobs with status:", ["Shortlisted & Discovered", "All Jobs"], horizontal=True)

        if filter_status == "Shortlisted & Discovered":
            selectable_jobs = jobs_pool[jobs_pool["status"].isin(["shortlisted", "discovered", "proposal_drafted"])]
            if len(selectable_jobs) == 0:
                selectable_jobs = jobs_pool
        else:
            selectable_jobs = jobs_pool

        job_options = selectable_jobs["id"].tolist()
        selected_job_id = st.selectbox(
            "Choose Job to Apply For:",
            options=job_options,
            format_func=lambda jid: f"#{jid} [{selectable_jobs[selectable_jobs['id']==jid]['platform'].values[0]}] {selectable_jobs[selectable_jobs['id']==jid]['title'].values[0]} (₹{selectable_jobs[selectable_jobs['id']==jid]['budget'].values[0]:,.0f})"
        )

        selected_job = selectable_jobs[selectable_jobs["id"] == selected_job_id].iloc[0]

        # Job Overview Card
        st.markdown("---")
        st.markdown(f"### 📋 Job Brief: #{selected_job['id']} — {selected_job['title']}")

        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        bcol1.metric("Platform", selected_job["platform"])
        bcol2.metric("Budget", f"₹{selected_job['budget']:,.0f} {selected_job['currency']}")
        bcol3.metric("Skill Match Score", f"{selected_job['score']}/100")
        bcol4.metric("Current Status", selected_job["status"].upper())

        if selected_job["risk_flags"] and selected_job["risk_flags"] != "[]":
            st.error(f"⚠️ Flagged Risk Signals: {selected_job['risk_flags']}")
        else:
            st.success("✅ Clean Opportunity: No suspicious payment or fee patterns detected.")

        st.markdown("**Client Information:** " + (selected_job["client_info"] or "Not provided"))
        st.markdown("**Full Description:**")
        st.info(selected_job["description"] or "No detailed description provided.")

        # External Link Action
        st.markdown("##### 2. Open Posting in Your Browser")
        if selected_job["url"]:
            st.link_button(f"🌐 Open Original Job on {selected_job['platform']}", url=selected_job["url"], type="secondary")
            st.caption("Opens the original job posting in your default web browser for manual review and submission.")
        else:
            st.caption("No direct URL attached to this job record.")

        st.markdown("---")

        # Proposal Generator Section
        st.markdown("##### 3. Generate Tailored Proposal (Verified Skills Only)")
        st.caption("Proposals emphasize your real Excel capabilities (dashboards, formula repair, XLOOKUP, VBA automation, data cleaning). Zero fabrication.")

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            prop_client = st.text_input("Client Name / Salutation", value="there")
        with p_col2:
            prop_freelancer = st.text_input("Your Name / Sign-off", value="Excel Freelancer")
        with p_col3:
            prop_time = st.selectbox("Turnaround Estimate", ["1-2 days", "2-3 days", "Within 24 hours", "3-5 days"])

        # State session key for proposal text
        prop_key = f"draft_proposal_{selected_job_id}"
        if prop_key not in st.session_state:
            initial_draft = pg.generate_honest_proposal(
                job_title=selected_job["title"],
                job_description=selected_job["description"],
                platform=selected_job["platform"],
                client_name=prop_client,
                freelancer_name=prop_freelancer,
                turnaround_estimate=prop_time
            )
            st.session_state[prop_key] = initial_draft

        if st.button("⚡ Regenerate Proposal Draft"):
            st.session_state[prop_key] = pg.generate_honest_proposal(
                job_title=selected_job["title"],
                job_description=selected_job["description"],
                platform=selected_job["platform"],
                client_name=prop_client,
                freelancer_name=prop_freelancer,
                turnaround_estimate=prop_time
            )
            jm.update_job_status(selected_job_id, "proposal_drafted")
            st.rerun()

        # Editable Proposal Draft
        proposal_content = st.text_area(
            "Proposal Draft (Edit as needed before copying):",
            value=st.session_state[prop_key],
            height=280
        )

        st.markdown("---")

        # Step 4: Submission Confirmation & History Logging
        st.markdown("##### 4. Record Application & Set Follow-Up")

        with st.form("confirm_application_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                bid_val = st.number_input("Your Bid / Quote (INR)*", min_value=100.0, step=200.0, value=float(selected_job["budget"]) if selected_job["budget"] > 0 else 3000.0)
            with c2:
                applied_on = st.date_input("Date Applied", value=datetime.now())
            with c3:
                follow_up_on = st.date_input("Schedule Follow-Up Date", value=datetime.now() + timedelta(days=3))

            f_notes = st.text_input("Follow-Up / Submission Notes", placeholder="e.g. Attached sample dashboard screenshot via platform messenger")

            # Human confirmation gate
            st.markdown("###### 🛡️ Confirmation Gate:")
            confirmed_submission = st.checkbox(
                "I confirm that I have reviewed this proposal and manually submitted it through the official platform website."
            )

            submit_app_btn = st.form_submit_button("📝 Record Application as Submitted", type="primary")

            if submit_app_btn:
                if not confirmed_submission:
                    st.error("Please confirm manual submission above before logging this application.")
                else:
                    success, app_id, msg = at.record_application(
                        job_id=selected_job_id,
                        platform=selected_job["platform"],
                        proposal_text=proposal_content,
                        bid_amount=bid_val,
                        currency=selected_job["currency"],
                        job_url=selected_job["url"],
                        applied_date=applied_on.strftime("%Y-%m-%d"),
                        follow_up_date=follow_up_on.strftime("%Y-%m-%d"),
                        follow_up_notes=f_notes
                    )
                    if success:
                        st.success(f"🎉 Application #{app_id} successfully logged! Job #{selected_job_id} status updated to 'APPLIED'.")
                        st.rerun()
                    else:
                        st.error(msg)

# -------------------------------------------------------------
# Module 3: Application History & Follow-ups
# -------------------------------------------------------------
elif navigation == "📬 Application History & Follow-ups":
    st.markdown('<div class="main-header">📬 Application History & Follow-Up Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Monitor submitted proposals, track client replies, log interview progress, and view scheduled follow-ups.</div>', unsafe_allow_html=True)

    # Filter controls
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        f_plat = st.selectbox("Filter Platform", ["All"] + PLATFORMS)
    with fcol2:
        f_st = st.selectbox("Filter Status", ["All"] + at.APPLICATION_STATUSES)

    apps_df = at.get_applications(platform=f_plat, status=f_st)
    st.markdown(f"**Found {len(apps_df)} submitted application(s)**.")

    if len(apps_df) > 0:
        display_apps = apps_df[["app_id", "job_title", "platform", "bid_amount", "currency", "applied_date", "status", "follow_up_date"]].copy()
        display_apps = display_apps.rename(columns={
            "app_id": "App ID", "job_title": "Project Title", "platform": "Platform",
            "bid_amount": "Bid (INR)", "currency": "Currency", "applied_date": "Date Applied",
            "status": "Status", "follow_up_date": "Next Follow-Up"
        })
        st.dataframe(display_apps, use_container_width=True, hide_index=True)

        st.markdown("### ✏️ Inspect & Update Application Status")
        selected_app_id = st.selectbox(
            "Select Application to Update:",
            options=apps_df["app_id"].tolist(),
            format_func=lambda aid: f"App #{aid} - {apps_df[apps_df['app_id']==aid]['job_title'].values[0]} ({apps_df[apps_df['app_id']==aid]['platform'].values[0]})"
        )

        if selected_app_id:
            app_row = apps_df[apps_df["app_id"] == selected_app_id].iloc[0]
            with st.form(f"update_app_form_{selected_app_id}"):
                c_st1, c_st2, c_st3 = st.columns(3)
                with c_st1:
                    st.write(f"**Bid Amount:** ₹{app_row['bid_amount']:,.2f} {app_row['currency']}")
                    st.write(f"**Date Applied:** {app_row['applied_date']}")
                with c_st2:
                    current_idx = at.APPLICATION_STATUSES.index(app_row["status"]) if app_row["status"] in at.APPLICATION_STATUSES else 0
                    new_app_status = st.selectbox("Update Status:", at.APPLICATION_STATUSES, index=current_idx)
                with c_st3:
                    new_followup = st.date_input(
                        "Next Follow-Up Date",
                        value=datetime.strptime(app_row["follow_up_date"], "%Y-%m-%d").date() if app_row["follow_up_date"] else datetime.now().date() + timedelta(days=3)
                    )

                new_fnotes = st.text_input("Follow-Up Notes / Outcome:", value=app_row["follow_up_notes"] or "")

                with st.expander("📄 View Submitted Proposal Text"):
                    st.text(app_row["proposal_text"])

                up_app_btn = st.form_submit_button("💾 Save Application Update")
                if up_app_btn:
                    ok = at.update_application_status(
                        application_id=selected_app_id,
                        new_status=new_app_status,
                        follow_up_date=new_followup.strftime("%Y-%m-%d"),
                        follow_up_notes=new_fnotes
                    )
                    if ok:
                        st.success(f"Application #{selected_app_id} updated to status '{new_app_status}'!")
                        st.rerun()
    else:
        st.info("No applications logged yet. Use the 'Application Assistant' tab to draft and record your bids.")

# -------------------------------------------------------------
# Module 4: Job Repository & Pipeline
# -------------------------------------------------------------
elif navigation == "📋 Job Repository & Pipeline":
    st.markdown('<div class="main-header">📋 Job Repository & Application Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage, filter, score, and track status for all discovered Excel freelance jobs.</div>', unsafe_allow_html=True)

    # Filter Controls
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        f_platform = st.selectbox("Filter Platform", ["All"] + PLATFORMS)
    with col_f2:
        f_status = st.selectbox("Filter Status", ["All"] + JOB_STATUSES)
    with col_f3:
        f_priority = st.selectbox("Filter Priority", ["All"] + PRIORITIES)
    with col_f4:
        f_search = st.text_input("Search Keyword", placeholder="e.g. dashboard, formula, vba")

    jobs_data = jm.get_jobs(
        platform=f_platform,
        status=f_status,
        priority=f_priority,
        search_keyword=f_search,
        include_samples=include_samples
    )

    st.markdown(f"**Found {len(jobs_data)} job(s)** matching filters.")

    if len(jobs_data) > 0:
        # Display Table Summary
        display_cols = ["id", "title", "platform", "budget", "currency", "score", "priority", "status", "is_sample"]
        preview_df = jobs_data[display_cols].copy()
        preview_df["is_sample"] = preview_df["is_sample"].apply(lambda x: "Yes (Sample)" if x == 1 else "No (Real)")
        preview_df = preview_df.rename(columns={
            "id": "ID", "title": "Title", "platform": "Platform",
            "budget": "Budget", "currency": "Currency", "score": "Score",
            "priority": "Priority", "status": "Status", "is_sample": "Sample Data"
        })
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        # Job Inspector & Status Changer
        st.markdown("### 🔍 Inspect & Update Job")
        selected_id = st.selectbox(
            "Select Job to Inspect or Update Status:",
            options=jobs_data["id"].tolist(),
            format_func=lambda j_id: f"#{j_id} - {jobs_data[jobs_data['id'] == j_id]['title'].values[0]}"
        )

        if selected_id:
            sel_row = jobs_data[jobs_data["id"] == selected_id].iloc[0]
            with st.form(f"update_job_{selected_id}"):
                det1, det2 = st.columns(2)
                with det1:
                    st.write(f"**Title:** {sel_row['title']}")
                    st.write(f"**Platform:** {sel_row['platform']}")
                    st.write(f"**Budget:** ₹{sel_row['budget']:,.2f} {sel_row['currency']}")
                    st.write(f"**Client Info:** {sel_row['client_info'] or 'Not provided'}")
                    if sel_row['url']:
                        st.markdown(f"**Job URL:** [{sel_row['url']}]({sel_row['url']})")
                with det2:
                    st.write(f"**Match Score:** {sel_row['score']}/100")
                    st.write(f"**Priority:** {sel_row['priority']}")
                    if sel_row['risk_flags'] and sel_row['risk_flags'] != "[]":
                        st.markdown(f"**Risk Flags:** <span class='badge-risk'>{sel_row['risk_flags']}</span>", unsafe_allow_html=True)
                    else:
                        st.write("**Risk Assessment:** ✅ Clean, no risk patterns detected")

                st.markdown("**Description:**")
                st.info(sel_row["description"] or "No detailed description.")

                col_st1, col_st2 = st.columns(2)
                with col_st1:
                    new_status = st.selectbox(
                        "Update Pipeline Status:",
                        options=JOB_STATUSES,
                        index=JOB_STATUSES.index(sel_row["status"]) if sel_row["status"] in JOB_STATUSES else 0
                    )
                with col_st2:
                    new_notes = st.text_input("Notes / Next Steps:", value=sel_row["notes"] or "")

                submitted = st.form_submit_button("💾 Save Status Update")
                if submitted:
                    success = jm.update_job_status(selected_id, new_status, new_notes)
                    if success:
                        st.success(f"Job #{selected_id} updated to status '{new_status}'!")
                        st.rerun()

        # Export Button
        st.markdown("### 📤 Export Job Records")
        csv_export = jobs_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Jobs as CSV",
            data=csv_export,
            file_name=f"excel_jobs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No jobs found matching your criteria.")

# -------------------------------------------------------------
# Module 5: Earnings & Monthly Targets
# -------------------------------------------------------------
elif navigation == "💰 Earnings & Monthly Targets":
    st.markdown('<div class="main-header">💰 Earnings & Target Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Track gross income, platform commissions, net earnings in INR, and monitor your monthly ₹10k–₹20k freelance milestones.</div>', unsafe_allow_html=True)

    month_input = st.date_input("Select Month for Target Analysis:", value=datetime.now())
    selected_month_str = month_input.strftime("%Y-%m")

    summary = et.get_monthly_summary(target_month=selected_month_str, include_samples=include_samples)

    # Monthly Progress Cards
    ecol1, ecol2, ecol3, ecol4 = st.columns(4)
    ecol1.metric("Gross Billed", f"₹{summary['total_gross']:,.2f}")
    ecol2.metric("Platform Fees Deducted", f"₹{summary['total_fees']:,.2f}")
    ecol3.metric("Net In-Pocket (INR)", f"₹{summary['total_net']:,.2f}", help="Gross minus platform fees")
    ecol4.metric("Expected Pipeline", f"₹{summary['expected_net']:,.2f}", help="Work in progress or pending release")

    st.markdown(f"### 📈 Progress for {month_input.strftime('%B %Y')}")
    pcol1, pcol2 = st.columns(2)

    with pcol1:
        st.markdown(f"**Goal 1: Baseline Target (₹{TARGET_MIN_INR:,.0f})**")
        p1 = min(summary["progress_min_pct"], 100.0)
        st.progress(p1 / 100.0)
        if summary["target_min_reached"]:
            st.success(f"🎉 Baseline goal reached! Net: ₹{summary['total_net']:,.2f}")
        else:
            st.info(f"**{p1}%** reached. ₹{summary['gap_to_min']:,.2f} more needed to hit ₹{TARGET_MIN_INR:,.0f}.")

    with pcol2:
        st.markdown(f"**Goal 2: Growth Target (₹{TARGET_MAX_INR:,.0f})**")
        p2 = min(summary["progress_max_pct"], 100.0)
        st.progress(p2 / 100.0)
        if summary["target_max_reached"]:
            st.balloons()
            st.success(f"🏆 Growth target achieved! Net: ₹{summary['total_net']:,.2f}")
        else:
            st.info(f"**{p2}%** reached. ₹{summary['gap_to_max']:,.2f} more needed to hit ₹{TARGET_MAX_INR:,.0f}.")

    st.markdown("---")

    # Earnings Form, Ledger & Editor
    e_tab1, e_tab2, e_tab3 = st.tabs(["📜 Earnings Ledger", "➕ Record New Payment", "✏️ Edit / Manage Payment"])

    with e_tab1:
        earnings_df = et.get_earnings(include_samples=include_samples)
        if len(earnings_df) > 0:
            e_display = earnings_df[["id", "date_received", "project_name", "platform", "gross_amount", "platform_fee", "net_amount", "status", "is_sample"]].copy()
            e_display["is_sample"] = e_display["is_sample"].apply(lambda x: "Sample" if x == 1 else "Real")
            st.dataframe(e_display, use_container_width=True, hide_index=True)
        else:
            st.info("No earnings recorded yet. Use the 'Record New Payment' tab to log received income.")

    with e_tab2:
        with st.form("add_earning_form"):
            st.markdown("##### Log an Excel Project Earning")
            f_pname = st.text_input("Project Name / Description*", placeholder="e.g. Retail MIS Dashboard Automation")
            f_plat = st.selectbox("Platform", PLATFORMS)
            f_gross = st.number_input("Gross Amount (INR)*", min_value=0.0, step=500.0, value=5000.0)
            f_fee = st.number_input("Platform Fee / Commission (INR)", min_value=0.0, step=50.0, value=0.0)
            f_date = st.date_input("Date Received / Expected", value=datetime.now())
            f_status = st.selectbox("Payment Status", ["received", "expected"])
            f_notes = st.text_input("Notes (optional)", placeholder="e.g. Paid via UPI / Upwork Escrow")
            f_sample = st.checkbox("Mark as Demonstration / Sample Record", value=False)

            earn_submitted = st.form_submit_button("💾 Save Earnings Record", type="primary")
            if earn_submitted:
                if not f_pname.strip():
                    st.error("Please provide a project name.")
                else:
                    new_e_id = et.add_earning(
                        project_name=f_pname.strip(),
                        gross_amount=f_gross,
                        platform_fee=f_fee,
                        platform=f_plat,
                        date_received=f_date.strftime("%Y-%m-%d"),
                        status=f_status,
                        is_sample=1 if f_sample else 0,
                        notes=f_notes
                    )
                    st.success(f"Payment entry #{new_e_id} recorded successfully!")
                    st.rerun()

    with e_tab3:
        all_earnings = et.get_earnings(include_samples=include_samples)
        if len(all_earnings) > 0:
            edit_id = st.selectbox(
                "Select Payment Entry to Edit:",
                options=all_earnings["id"].tolist(),
                format_func=lambda eid: f"#{eid} - {all_earnings[all_earnings['id'] == eid]['project_name'].values[0]} (₹{all_earnings[all_earnings['id'] == eid]['net_amount'].values[0]:,.0f})"
            )
            if edit_id:
                erow = all_earnings[all_earnings["id"] == edit_id].iloc[0]
                with st.form(f"edit_earning_form_{edit_id}"):
                    st.markdown(f"##### Editing Payment Record #{edit_id}")
                    u_pname = st.text_input("Project Name", value=erow["project_name"])
                    u_plat = st.selectbox(
                        "Platform",
                        PLATFORMS,
                        index=PLATFORMS.index(erow["platform"]) if erow["platform"] in PLATFORMS else 0
                    )
                    u_gross = st.number_input("Gross Amount (INR)", min_value=0.0, step=100.0, value=float(erow["gross_amount"]))
                    u_fee = st.number_input("Platform Fee (INR)", min_value=0.0, step=50.0, value=float(erow["platform_fee"]))
                    u_status = st.selectbox(
                        "Status",
                        ["received", "expected"],
                        index=0 if erow["status"] == "received" else 1
                    )
                    u_notes = st.text_input("Notes", value=erow["notes"] or "")

                    btn_c1, btn_c2 = st.columns([1, 1])
                    with btn_c1:
                        update_sub = st.form_submit_button("💾 Save Changes", type="primary")
                    with btn_c2:
                        delete_sub = st.form_submit_button("🗑️ Delete This Record")

                    if update_sub:
                        ok = et.update_earning(
                            earning_id=edit_id,
                            project_name=u_pname.strip(),
                            gross_amount=u_gross,
                            platform_fee=u_fee,
                            platform=u_plat,
                            status=u_status,
                            notes=u_notes
                        )
                        if ok:
                            st.success(f"Payment entry #{edit_id} updated successfully!")
                            st.rerun()

                    if delete_sub:
                        del_ok = et.delete_earning(edit_id)
                        if del_ok:
                            st.success(f"Payment entry #{edit_id} deleted successfully!")
                            st.rerun()
        else:
            st.info("No records available to edit.")

# -------------------------------------------------------------
# Module 6: CSV Job Import
# -------------------------------------------------------------
elif navigation == "📥 CSV Job Import":
    st.markdown('<div class="main-header">📥 Import Freelance Jobs from CSV</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Zero-cost import: Ingest Excel freelance job listings from manual CSV exports, email alert exports, or saved searches.</div>', unsafe_allow_html=True)

    st.markdown("""
    #### 📋 How CSV Import Works
    - **Safe & Permitted**: We never scrape restricted pages or bypass website logins. You can export or collect job lists from public feeds or alerts.
    - **Intelligent Deduplication**: Duplicates with matching URLs or normalized titles are automatically detected and skipped.
    - **Auto-Evaluation**: Incoming jobs are automatically analyzed for Excel skill match, budget value, clarity, and suspicious fraud signals.
    """)

    import_tab1, import_tab2 = st.tabs(["Upload Your CSV", "Load Included Sample Template CSV"])

    with import_tab1:
        uploaded_file = st.file_uploader("Select a CSV file to import jobs:", type=["csv"])
        mark_as_sample = st.checkbox("Mark imported records as Sample Data", value=False)

        if uploaded_file is not None:
            if st.button("🚀 Process & Import CSV", type="primary"):
                result = jm.import_jobs_from_csv(uploaded_file, is_sample=mark_as_sample)
                if result["success"]:
                    st.success(f"✅ Successfully imported **{result['imported_count']}** new job(s).")
                    if result["duplicate_count"] > 0:
                        st.info(f"ℹ️ Skipped **{result['duplicate_count']}** duplicate job(s) already in the database.")
                    if result["errors"]:
                        with st.expander("Review Warning/Error Rows"):
                            for err in result["errors"]:
                                st.write(f"- {err}")
                else:
                    st.error(f"Import failed: {result['error']}")

    with import_tab2:
        st.markdown("Use this option to test the import pipeline with our pre-packaged `data/sample_jobs.csv` containing realistic test Excel listings.")
        sample_csv_path = SAMPLE_CSV_PATH
        if sample_csv_path.exists():
            sample_df = pd.read_csv(sample_csv_path)
            st.dataframe(sample_df, use_container_width=True)
            if st.button("📥 Import Sample CSV into Database"):
                with open(sample_csv_path, "r", encoding="utf-8") as f:
                    res = jm.import_jobs_from_csv(f, is_sample=True)
                st.success(f"Imported {res['imported_count']} jobs ({res['duplicate_count']} duplicates skipped).")
        else:
            st.warning("Sample CSV not found at `data/sample_jobs.csv`.")

# -------------------------------------------------------------
# Module 7: Platform Accounts & Policies
# -------------------------------------------------------------
elif navigation == "🌐 Platform Accounts & Policies":
    st.markdown('<div class="main-header">🌐 Platform Accounts & Policy Control</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage your freelance platform profiles, enforce human-controlled automation safety, and maintain compliance.</div>', unsafe_allow_html=True)

    # Security callout
    st.success("🔒 **Zero-Credential Security Architecture**: Excel Hunter AI never requests, accepts, or stores passwords, API secrets, or browser session cookies. All client logins and payments occur securely on the platforms' official web portals.")

    plat_tab1, plat_tab2 = st.tabs(["📋 Configured Platforms", "➕ Add Custom Platform"])

    with plat_tab1:
        platforms_df = pm.get_platform_accounts()
        if len(platforms_df) > 0:
            view_cols = platforms_df[["id", "platform_name", "account_status", "integration_mode", "profile_url"]].copy()
            view_cols = view_cols.rename(columns={
                "id": "ID", "platform_name": "Platform", "account_status": "Status",
                "integration_mode": "Integration Policy", "profile_url": "Profile URL"
            })
            st.dataframe(view_cols, use_container_width=True, hide_index=True)

            st.markdown("### ✏️ Edit Platform Profile & Compliance Settings")
            sel_pid = st.selectbox(
                "Select Platform to Manage:",
                options=platforms_df["id"].tolist(),
                format_func=lambda pid: f"#{pid} - {platforms_df[platforms_df['id']==pid]['platform_name'].values[0]} ({platforms_df[platforms_df['id']==pid]['integration_mode'].values[0]})"
            )

            if sel_pid:
                p_row = platforms_df[platforms_df["id"] == sel_pid].iloc[0]
                with st.form(f"edit_platform_{sel_pid}"):
                    st.markdown(f"#### Platform: {p_row['platform_name']}")
                    ep_url = st.text_input("Your Public Profile URL", value=p_row["profile_url"] or "")
                    
                    c_p1, c_p2 = st.columns(2)
                    with c_p1:
                        ep_status = st.selectbox(
                            "Account Status",
                            pm.ACCOUNT_STATUSES,
                            index=pm.ACCOUNT_STATUSES.index(p_row["account_status"]) if p_row["account_status"] in pm.ACCOUNT_STATUSES else 0
                        )
                    with c_p2:
                        ep_mode = st.selectbox(
                            "Integration Capability",
                            pm.INTEGRATION_MODES,
                            index=pm.INTEGRATION_MODES.index(p_row["integration_mode"]) if p_row["integration_mode"] in pm.INTEGRATION_MODES else 0
                        )

                    ep_policy = st.text_area("Platform Policy & Terms Compliance Notes", value=p_row["policy_notes"] or "")
                    ep_notes = st.text_input("Personal Strategy Notes / Gigs", value=p_row["notes"] or "")

                    save_p_btn = st.form_submit_button("💾 Save Platform Settings")
                    if save_p_btn:
                        ok = pm.update_platform_account(
                            platform_id=sel_pid,
                            profile_url=ep_url,
                            account_status=ep_status,
                            integration_mode=ep_mode,
                            policy_notes=ep_policy,
                            notes=ep_notes
                        )
                        if ok:
                            st.success(f"Platform settings for '{p_row['platform_name']}' updated successfully!")
                            st.rerun()

    with plat_tab2:
        with st.form("add_platform_form"):
            st.markdown("##### Connect a New Platform or Direct Channel")
            np_name = st.text_input("Platform / Channel Name*", placeholder="e.g. Guru, Truelancer, WhatsApp Direct")
            np_url = st.text_input("Public Profile / Link", placeholder="https://www.example.com/freelancer")
            np_status = st.selectbox("Initial Status", pm.ACCOUNT_STATUSES)
            np_mode = st.selectbox("Integration Policy", pm.INTEGRATION_MODES)
            np_notes = st.text_input("Notes", placeholder="e.g. Specializing in Excel reporting")

            add_p_btn = st.form_submit_button("➕ Add Platform Record", type="primary")
            if add_p_btn:
                if not np_name.strip():
                    st.error("Platform name is required.")
                else:
                    new_pid = pm.add_custom_platform(
                        platform_name=np_name,
                        profile_url=np_url,
                        account_status=np_status,
                        integration_mode=np_mode,
                        notes=np_notes
                    )
                    if new_pid:
                        st.success(f"Platform '{np_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Platform '{np_name}' already exists or could not be saved.")

# -------------------------------------------------------------
# Module 8: Database & Settings
# -------------------------------------------------------------
elif navigation == "⚙️ Database & Settings":
    st.markdown('<div class="main-header">⚙️ System & Data Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Manage your local SQLite storage, clear sample entries, or re-seed initial data.</div>', unsafe_allow_html=True)

    st.markdown(f"**Database Location:** `{DB_PATH.resolve()}`")
    all_current_jobs = jm.get_jobs(include_samples=True)
    sample_jobs_count = len(all_current_jobs[all_current_jobs["is_sample"] == 1]) if len(all_current_jobs) > 0 else 0
    real_jobs_count = len(all_current_jobs[all_current_jobs["is_sample"] == 0]) if len(all_current_jobs) > 0 else 0

    st.write(f"- Real user jobs: **{real_jobs_count}**")
    st.write(f"- Sample demonstration jobs: **{sample_jobs_count}**")

    st.markdown("---")
    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("#### 🧹 Clear Sample Demonstration Data")
        st.write("Remove all built-in sample jobs and sample earnings while preserving your real records.")
        if st.button("Delete All Sample Records", type="secondary"):
            jd, ed = jm.delete_sample_data()
            st.success(f"Cleared {jd} sample jobs and {ed} sample earnings.")
            st.rerun()

    with col_act2:
        st.markdown("#### 🔄 Reset / Reload Sample Data")
        st.write("Restore standard demonstration records to explore dashboard features.")
        if st.button("Load Demonstration Records"):
            res = seed_sample_data()
            st.success(f"Loaded sample records (Added: {res['jobs_added']} jobs, {res['earnings_added']} earnings).")
            st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Beginner's Quick Reference")
    st.markdown("""
    - **To run the dashboard anytime:** Open Command Prompt or PowerShell in this folder and run:
      ```powershell
      python -m streamlit run app.py
      ```
    - **Your computer stops/starts:** Your data is safely stored in `data/excel_hunter.db` on your hard drive. It will never vanish when you turn off your PC.
    - **Budget:** 100% Free. No API keys needed.
    """)
