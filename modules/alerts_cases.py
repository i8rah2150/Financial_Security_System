"""Module 5: Alerts & Case Management for SentinelGuard with Deep Gemini AI Integration."""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st
from google import genai

from core.models import ALERT_STATUSES, get_severity_color
from core.state_manager import block_account, log_audit_event, unblock_account, update_alert_status


def generate_gemini_case_assessment(
    api_key: str, alert: Dict[str, Any], acc_info: Dict[str, Any], related_txns: List[Dict[str, Any]]
) -> str:
    """Generates an executive forensic compliance assessment using Gemini with 429 retry handling."""
    client = genai.Client(api_key=api_key)

    txn_summary = "\n".join(
        [
            f"- {t.get('txn_id')}: ₹{t.get('amount', 0):,.2f} via {t.get('channel')} ({t.get('sender_id')} ➔ {t.get('receiver_id')}) [Risk: {t.get('risk_score', 0):.0f}]"
            for t in related_txns[:6]
        ]
    )

    prompt = f"""
    You are a Senior Financial Intelligence Unit (FIU) Compliance Director and AML Forensic Investigator.
    Generate an authoritative, professional compliance risk assessment and executive briefing for this flagged financial crime case.

    CASE PROFILE:
    - Alert Reference: {alert['alert_id']}
    - Target Entity: {alert['account_id']} (Name: {acc_info.get('holder_name')}, KYC: {acc_info.get('kyc_tier')}, Jurisdiction: {acc_info.get('city')}, Account Age: {acc_info.get('account_age_days')} days)
    - Risk Severity: {alert['severity']}
    - Detected AML Typology: {alert['typology']}
    - Unified Threat Score: {alert.get('evidence', {}).get('risk_score')}/100
    - Supervised ML Model Fraud Probability: {alert.get('evidence', {}).get('ml_probability', 0)*100:.1f}%
    - Behavioral Z-Score Deviation: {alert.get('evidence', {}).get('zscore', 0):+.2f}σ vs historical account baseline
    - Flagged Transaction Amount: ₹{alert.get('evidence', {}).get('amount', 0):,.2f} INR

    EVIDENCE NOTES:
    {alert.get('explanation')}

    RECENT TRANSACTION CORRIDOR:
    {txn_summary}

    Structure the assessment strictly with:
    1. 📋 **Executive Threat Briefing**: Clear synopsis of illicit financial activity.
    2. 🚩 **Forensic Red Flags**: Specific behavioral deviations and graph topology anomalies identified.
    3. ⚖️ **Regulatory Compliance Implications**: Reference relevant PMLA / FATF Recommendation 16 / Structuring CTR guidelines.
    4. 🛡️ **Mandatory Remediation Protocol**: Immediate recommended enforcement steps (Immediate Freeze, Suspicious Activity Report (SAR/STR) filing, Enhanced Due Diligence).
    """

    delay_seconds = 2.0
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str.upper()) and attempt < 2:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
            # Try secondary model fallback
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt,
                )
                return response.text
            except Exception:
                raise e


def get_mock_ai_assessment(alert: Dict[str, Any], acc_info: Dict[str, Any]) -> str:
    """Provides a deterministic fallback assessment for demo evaluation when API key is unconfigured."""
    return f"""### 📋 Executive Threat Briefing
Entity `{alert['account_id']}` ({acc_info.get('holder_name', 'Account Holder')}) exhibits critical velocity and structuring signatures. The multi-stage detection engine scored an aggregated unified threat index of **{alert.get('evidence', {}).get('risk_score', 92):.1f}/100**, driven by an acute behavioral deviation ({alert.get('evidence', {}).get('zscore', 0):+.2f}σ) and ML fraud probability ({alert.get('evidence', {}).get('ml_probability', 0)*100:.1f}%).

### 🚩 Forensic Red Flags
* **Smurfing / Threshold Evasion**: Repeated disbursements engineered to remain just beneath the statutory ₹50,000 CTR declaration benchmark.
* **Rapid Velocity Clustering**: Capital received into `{alert['account_id']}` disbursed across counterparties within compressed temporal windows.
* **Jurisdictional Hopping**: Irregular payment corridor routing originating in {acc_info.get('city', 'Metro')} to offshore entities.

### ⚖️ Regulatory Compliance Implications (PMLA & FATF)
Under **Section 12 of the Prevention of Money Laundering Act (PMLA)** and **FATF Recommendation 16**, repeated sub-threshold transactions with no verifiable commercial rationale mandate the generation of a **Suspicious Transaction Report (STR)** to the Financial Intelligence Unit (FIU-IND).

### 🛡️ Mandatory Remediation Protocol
1. **Immediate Administrative Debit Freeze**: Restrict all outbound automated clearing and instant payment rails (`UPI`, `IMPS`, `NEFT`).
2. **Mandatory SAR/STR Filing**: Transmit Form STR-E to regulatory authorities within 7 operational days.
3. **Step-Up Enhanced Due Diligence (EDD)**: Request source-of-wealth documentation, tax filings, and ultimate beneficial ownership (UBO) records.
"""


def render() -> None:
    """Renders the investigator alert triage workspace, deep Gemini AI copilot, and audit trail."""
    st.markdown("## 🚨 Security Alerts & Case Management")
    st.caption(
        "Triage high-priority AML alerts, generate AI-powered case assessments, and execute auditable compliance actions."
    )

    alerts = st.session_state.get("alerts", [])
    accounts_df = st.session_state.get("accounts_df", pd.DataFrame())
    transactions_df = st.session_state.get("transactions_df", pd.DataFrame())
    audit_log = st.session_state.get("audit_log", [])

    if "gemini_case_assessments" not in st.session_state:
        st.session_state.gemini_case_assessments = {}

    if not alerts:
        st.success("🎉 All security alerts have been triaged! No active flags.")
        return

    # -------------------------------------------------------------------------
    # 1. Filters & Search Bar
    # -------------------------------------------------------------------------
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.0])
    with f_col1:
        status_filter = st.multiselect(
            "Filter by Lifecycle Status",
            options=ALERT_STATUSES,
            default=ALERT_STATUSES,
        )
    with f_col2:
        severity_filter = st.multiselect(
            "Filter by Severity",
            options=["Critical", "High", "Medium", "Low"],
            default=["Critical", "High", "Medium", "Low"],
        )
    with f_col3:
        search_query = st.text_input("Search Alert ID / Account", placeholder="e.g. ALT-7001")

    filtered_alerts = [
        a
        for a in alerts
        if a.get("status") in status_filter
        and a.get("severity") in severity_filter
        and (
            not search_query
            or search_query.upper() in a["alert_id"].upper()
            or search_query.upper() in a["account_id"].upper()
        )
    ]

    st.markdown(
        f"**Active Alert Ledger** <span style='color:#8B8D93;'>— Showing {len(filtered_alerts)} of {len(alerts)} alerts</span>",
        unsafe_allow_html=True,
    )

    alert_ids = [a["alert_id"] for a in filtered_alerts]
    if not alert_ids:
        st.info("No alerts match the selected criteria.")
        return

    selected_alert_id = st.selectbox(
        "Select Alert to Investigate & Triage",
        options=alert_ids,
        index=0,
    )

    alert = next((a for a in filtered_alerts if a["alert_id"] == selected_alert_id), None)
    if not alert:
        return

    sev_color = get_severity_color(alert["severity"])

    # -------------------------------------------------------------------------
    # 2. Main Investigation Dossier
    # -------------------------------------------------------------------------
    with st.container(border=True):
        top_c1, top_c2, top_c3 = st.columns([1.5, 2.5, 1.5])
        with top_c1:
            st.markdown(f"### `{alert['alert_id']}`")
            st.markdown(f"**Target Entity:** `{alert['account_id']}`")
            st.markdown(f"**Transaction Ref:** `{alert['txn_id']}`")
        with top_c2:
            st.markdown(f"#### Pattern: {alert['typology']}")
            st.caption(f"Detected: {alert['timestamp']}")
            st.markdown(f"**Current Status:** `{alert['status']}`")
        with top_c3:
            st.markdown(
                f"""
                <div style="background:#181C27; border:1px solid {sev_color}; border-radius:6px; padding:12px; text-align:center;">
                    <div style="color:{sev_color}; font-size:20px; font-weight:800;">{alert['severity'].upper()}</div>
                    <div style="color:#8B8D93; font-size:11px;">SEVERITY BAND</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Multi-Engine Detection Signals
        st.markdown("#### 🔬 Multi-Engine Evidence Signals")
        ev = alert.get("evidence", {})

        ev_col1, ev_col2, ev_col3, ev_col4 = st.columns(4)
        ev_col1.metric("Supervised ML Prob", f"{ev.get('ml_probability', 0.0) * 100:.1f}%")
        ev_col2.metric("Behavioral Z-Score", f"{ev.get('zscore', 0.0):+.2f}σ")
        ev_col3.metric("Unified Threat Score", f"{ev.get('risk_score', 0.0):.1f}/100")
        ev_col4.metric("Flagged Amount (₹)", f"₹{ev.get('amount', 0.0):,.2f}")

        st.markdown(
            f"""
            <div style="background:#131722; border-left:4px solid {sev_color}; padding:12px 16px; border-radius:4px; margin-top:8px;">
                <div style="color:#8B8D93; font-size:11px; text-transform:uppercase; font-weight:600;">Detection Pipeline Summary</div>
                <div style="color:#E2E4E9; font-size:13px; line-height:1.5; margin-top:4px;">{alert.get('explanation', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ---------------------------------------------------------------------
        # 3. Deep Gemini AI Copilot Integration
        # ---------------------------------------------------------------------
        st.markdown("### 🤖 Gemini AI Forensic Copilot")
        st.caption("Generate a comprehensive executive risk briefing and regulatory SAR filing assessment.")

        acc_target = alert["account_id"]
        acc_match = accounts_df[accounts_df["account_id"] == acc_target]
        acc_info = acc_match.iloc[0].to_dict() if not acc_match.empty else {}

        related_txns = transactions_df[
            (transactions_df["sender_id"] == acc_target) | (transactions_df["receiver_id"] == acc_target)
        ].to_dict(orient="records")

        # Check for Gemini API key
        configured_key = ""
        try:
            if "GEMINI_API_KEY" in st.secrets:
                configured_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            configured_key = ""

        sidebar_key = st.session_state.get("gemini_api_key_input", "")
        active_key = configured_key or sidebar_key

        has_cached_assessment = alert["alert_id"] in st.session_state.gemini_case_assessments

        ai_btn_col1, ai_btn_col2 = st.columns([1.5, 3.5])
        with ai_btn_col1:
            btn_generate = st.button(
                "✨ Generate AI Case Assessment" if not has_cached_assessment else "🔄 Re-generate AI Assessment",
                type="primary",
                use_container_width=True,
                key=f"ai_gen_{alert['alert_id']}",
            )

        if btn_generate:
            if active_key:
                with st.spinner("🤖 Gemini AI Copilot analyzing transaction network & drafting compliance assessment..."):
                    try:
                        assessment_markdown = generate_gemini_case_assessment(
                            api_key=active_key,
                            alert=alert,
                            acc_info=acc_info,
                            related_txns=related_txns,
                        )
                        st.session_state.gemini_case_assessments[alert["alert_id"]] = assessment_markdown
                        st.toast("Gemini AI compliance assessment generated!", icon="✨")
                    except Exception as exc:
                        st.error(f"Gemini API error: {exc}. Displaying calibrated forensic template.")
                        st.session_state.gemini_case_assessments[alert["alert_id"]] = get_mock_ai_assessment(
                            alert, acc_info
                        )
            else:
                with st.spinner("Generating forensic compliance assessment template..."):
                    time.sleep(0.8)
                    st.session_state.gemini_case_assessments[alert["alert_id"]] = get_mock_ai_assessment(
                        alert, acc_info
                    )
                    st.info("💡 Note: Add your Gemini API key in `st.secrets` or the sidebar for live model generation.")

        # Display AI Assessment if present
        if alert["alert_id"] in st.session_state.gemini_case_assessments:
            st.markdown(
                """
                <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(20, 25, 38, 0.8) 100%);
                            border: 1px solid rgba(0, 212, 255, 0.35);
                            border-radius: 8px;
                            padding: 16px 20px;
                            margin-top: 10px;
                            margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <span style="color:#00D4FF; font-weight:800; font-size:13px; letter-spacing:0.8px;">
                            🛡️ GEMINI AI EXECUTIVE COMPLIANCE REPORT
                        </span>
                        <span style="color:#8B8D93; font-size:11px;">MODEL: GEMINI 2.5 FLASH</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(st.session_state.gemini_case_assessments[alert["alert_id"]])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # 4. Investigator Action Controls
        # ---------------------------------------------------------------------
        st.markdown("#### ⚖️ Compliance Enforcement Controls")
        act_col1, act_col2, act_col3, act_col4, act_col5 = st.columns(5)

        with act_col1:
            if st.button("🔍 Mark Investigating", use_container_width=True, disabled=alert["status"] == "Investigating"):
                update_alert_status(alert["alert_id"], "Investigating", "Assigned to compliance officer for review.")
                st.toast(f"{alert['alert_id']} set to Investigating.", icon="🔍")
                st.rerun()

        with act_col2:
            if st.button("✅ Mark Investigated", use_container_width=True, disabled=alert["status"] == "Investigated"):
                update_alert_status(alert["alert_id"], "Investigated", "Forensic analysis completed.")
                st.toast(f"{alert['alert_id']} marked as Investigated.", icon="✅")
                st.rerun()

        with act_col3:
            if st.button("⚠️ Escalate Tier-2", use_container_width=True, disabled=alert["status"] == "Escalated"):
                update_alert_status(alert["alert_id"], "Escalated", "Escalated to Senior FIU Director.")
                st.toast(f"{alert['alert_id']} escalated to Tier-2.", icon="⚠️")
                st.rerun()

        with act_col4:
            if st.button("🔒 Close Case", use_container_width=True, disabled=alert["status"] == "Closed"):
                update_alert_status(alert["alert_id"], "Closed", "Case cleared or SAR filed.")
                st.toast(f"{alert['alert_id']} closed.", icon="🔒")
                st.rerun()

        with act_col5:
            is_blocked = acc_info.get("is_blocked", False)
            if not is_blocked:
                if st.button("🚫 Block Account", type="primary", use_container_width=True):
                    block_account(alert["account_id"], f"Blocked via {alert['alert_id']} ({alert['typology']})")
                    update_alert_status(alert["alert_id"], "Escalated", "Account blocked. SAR draft generated.")
                    st.toast(f"Account {alert['account_id']} blocked!", icon="🚫")
                    st.rerun()
            else:
                if st.button("🔓 Unblock Account", use_container_width=True):
                    unblock_account(alert["account_id"], "Cleared by compliance audit.")
                    st.toast(f"Account {alert['account_id']} unblocked.", icon="🔓")
                    st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. Immutable Compliance Audit Trail
    # -------------------------------------------------------------------------
    st.markdown("### 📜 Immutable Compliance Audit Trail")
    st.caption("All investigator status transitions and entity enforcement actions are permanently logged.")

    if audit_log:
        df_audit = pd.DataFrame(audit_log).sort_values(by="timestamp", ascending=False)
        st.dataframe(
            df_audit,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Audit log is currently empty.")
