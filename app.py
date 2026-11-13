"""Financial Security, Fraud Detection & Anti-Money Laundering (AML) Dashboard.

Built with Python, Streamlit, and the official google-genai SDK (gemini-3.5-flash-lite).
Designed for hackathon live jury demonstrations with persistent state and structured analytics.
"""

import json
import time
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. Page Configuration (Wide Layout & Theming)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SentinelGuard | AI Financial Security & AML System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# 2. Structured Pydantic Schemas for Gemini 3.5 Flash Lite
# -----------------------------------------------------------------------------
class RiskIndicator(BaseModel):
    indicator_name: str = Field(
        description="Concise name of the detected risk factor, e.g., Velocity Anomaly, Structuring / Smurfing, Jurisdiction Risk"
    )
    severity: str = Field(
        description="Severity level: 'Low', 'Medium', or 'High'"
    )
    description: str = Field(
        description="Detailed explanation of why this factor elevates fraud or AML risk"
    )


class TransactionRiskAssessment(BaseModel):
    risk_score: int = Field(
        description="Overall risk score integer from 0 (completely safe) to 100 (critical fraud/AML risk)"
    )
    risk_level: str = Field(
        description="Classification: 'Safe', 'Medium Risk', or 'High Risk'"
    )
    executive_summary: str = Field(
        description="Clear 2-3 sentence overview of the fraud and AML assessment"
    )
    aml_patterns_detected: List[str] = Field(
        description="List of detected financial crime patterns, e.g., 'Structuring (BSA evasion)', 'Rapid Velocity', 'Sanctions Hop'"
    )
    risk_indicators: List[RiskIndicator] = Field(
        description="List of granular risk indicator breakdowns"
    )
    recommended_action: str = Field(
        description="Operational action: 'Approve', 'Step-Up KYC Verification', 'Hold & Escalate', 'Freeze Account & File SAR'"
    )


# -----------------------------------------------------------------------------
# 3. Session State Management (Persistence Across Reruns)
# -----------------------------------------------------------------------------
def init_session_state() -> None:
    """Initializes all session state variables to ensure user data persists across interactions."""
    if "batch_transactions" not in st.session_state:
        st.session_state.batch_transactions = pd.DataFrame()

    if "live_screener_result" not in st.session_state:
        st.session_state.live_screener_result = None

    if "active_alerts" not in st.session_state:
        st.session_state.active_alerts = []

    if "sample_loaded" not in st.session_state:
        st.session_state.sample_loaded = False

    if "screener_prefill" not in st.session_state:
        st.session_state.screener_prefill = {
            "amount": 9950.00,
            "txn_type": "Wire Transfer",
            "sender_loc": "Miami, USA",
            "recipient_loc": "Panama City, Panama",
            "account_age": 7,
            "daily_freq": 14,
        }


init_session_state()


# -----------------------------------------------------------------------------
# 4. Synthetic Sample Data Generators (Demo-Ready)
# -----------------------------------------------------------------------------
def get_sample_batch_transactions() -> pd.DataFrame:
    """Generates 10 pre-built synthetic transactions covering normal, suspicious, and AML patterns."""
    return pd.DataFrame(
        [
            {
                "Transaction_ID": "TXN-9011",
                "Timestamp": "2026-11-13 09:12:04",
                "Amount_USD": 9950.00,
                "Type": "Wire Transfer",
                "Sender": "ACC-4102 (Miami, USA)",
                "Recipient": "ACC-8831 (Panama City, PAN)",
                "Risk_Score": 92,
                "Status": "High Risk",
                "Pattern_Notes": "Structuring anomaly: Just below $10,000 CTR reporting threshold.",
            },
            {
                "Transaction_ID": "TXN-9012",
                "Timestamp": "2026-11-13 09:14:22",
                "Amount_USD": 42.50,
                "Type": "Card Swipe",
                "Sender": "ACC-1092 (Seattle, USA)",
                "Recipient": "Downtown Coffee Roasters",
                "Risk_Score": 8,
                "Status": "Safe",
                "Pattern_Notes": "Standard everyday retail swipe.",
            },
            {
                "Transaction_ID": "TXN-9013",
                "Timestamp": "2026-11-13 09:21:49",
                "Amount_USD": 48500.00,
                "Type": "Crypto",
                "Sender": "ACC-9921 (Tor Exit Node / Unknown)",
                "Recipient": "Unhosted Cold Wallet 0x7a...4e",
                "Risk_Score": 96,
                "Status": "High Risk",
                "Pattern_Notes": "Darknet tumbler signature with anonymous hops.",
            },
            {
                "Transaction_ID": "TXN-9014",
                "Timestamp": "2026-11-13 09:30:11",
                "Amount_USD": 120.00,
                "Type": "UPI",
                "Sender": "ACC-3140 (Mumbai, IND)",
                "Recipient": "ACC-5521 (Bangalore, IND)",
                "Risk_Score": 12,
                "Status": "Safe",
                "Pattern_Notes": "Routine domestic peer-to-peer settlement.",
            },
            {
                "Transaction_ID": "TXN-9015",
                "Timestamp": "2026-11-13 09:34:55",
                "Amount_USD": 9850.00,
                "Type": "Wire Transfer",
                "Sender": "ACC-4102 (Miami, USA)",
                "Recipient": "ACC-8831 (Panama City, PAN)",
                "Risk_Score": 94,
                "Status": "High Risk",
                "Pattern_Notes": "Smurfing leg #2: Repeated sub-$10k transfer within 25 minutes.",
            },
            {
                "Transaction_ID": "TXN-9016",
                "Timestamp": "2026-11-13 09:45:00",
                "Amount_USD": 1450.00,
                "Type": "Card Swipe",
                "Sender": "ACC-7801 (San Francisco, USA)",
                "Recipient": "Luxury Duty Free (Tokyo, JPN)",
                "Risk_Score": 58,
                "Status": "Medium Risk",
                "Pattern_Notes": "Sudden cross-border card use without travel notice.",
            },
            {
                "Transaction_ID": "TXN-9017",
                "Timestamp": "2026-11-13 09:51:18",
                "Amount_USD": 9900.00,
                "Type": "Wire Transfer",
                "Sender": "ACC-4102 (Miami, USA)",
                "Recipient": "ACC-9912 (George Town, CYM)",
                "Risk_Score": 95,
                "Status": "High Risk",
                "Pattern_Notes": "Smurfing leg #3: Offshore entity redirection.",
            },
            {
                "Transaction_ID": "TXN-9018",
                "Timestamp": "2026-11-13 10:02:40",
                "Amount_USD": 310.00,
                "Type": "UPI",
                "Sender": "ACC-6602 (Delhi, IND)",
                "Recipient": "Utility Power Corp",
                "Risk_Score": 6,
                "Status": "Safe",
                "Pattern_Notes": "Verified merchant bill payment.",
            },
            {
                "Transaction_ID": "TXN-9019",
                "Timestamp": "2026-11-13 10:11:05",
                "Amount_USD": 75000.00,
                "Type": "Crypto",
                "Sender": "ACC-2029 (Moscow, RUS)",
                "Recipient": "ACC-6019 (Dubai, UAE)",
                "Risk_Score": 89,
                "Status": "High Risk",
                "Pattern_Notes": "Potential sanctions evasion corridor with high volume.",
            },
            {
                "Transaction_ID": "TXN-9020",
                "Timestamp": "2026-11-13 10:18:33",
                "Amount_USD": 85.00,
                "Type": "Card Swipe",
                "Sender": "ACC-5412 (Chicago, USA)",
                "Recipient": "Metro Grocery Market",
                "Risk_Score": 5,
                "Status": "Safe",
                "Pattern_Notes": "Established neighborhood merchant.",
            },
        ]
    )


def get_sample_alerts() -> List[Dict[str, Any]]:
    """Initializes synthetic security alerts for AML officer triaging."""
    return [
        {
            "id": "ALT-101",
            "account_id": "ACC-4102",
            "pattern": "Multi-Step Smurfing / Structuring ($29,700 total in 3 sub-$10k hops)",
            "risk_score": 95,
            "risk_level": "High",
            "timestamp": "12 mins ago",
            "status": "Active",
            "jurisdiction": "USA -> Panama / Cayman Islands",
        },
        {
            "id": "ALT-102",
            "account_id": "ACC-9921",
            "pattern": "Anonymous Darknet Inflow to Unhosted Wallet ($48,500 Crypto)",
            "risk_score": 96,
            "risk_level": "High",
            "timestamp": "25 mins ago",
            "status": "Active",
            "jurisdiction": "TOR Exit Node -> Unhosted",
        },
        {
            "id": "ALT-103",
            "account_id": "ACC-7801",
            "pattern": "Impossible Velocity / Geo-Hopping (SF card swipe, then Tokyo in 30 mins)",
            "risk_score": 62,
            "risk_level": "Medium",
            "timestamp": "48 mins ago",
            "status": "Active",
            "jurisdiction": "USA / Japan",
        },
        {
            "id": "ALT-104",
            "account_id": "ACC-2029",
            "pattern": "Sanctions Screening Trigger & High-Value Offshore Inflow ($75,000)",
            "risk_score": 89,
            "risk_level": "High",
            "timestamp": "1 hour ago",
            "status": "Active",
            "jurisdiction": "Russia -> UAE",
        },
    ]


def load_all_sample_data() -> None:
    """Populates both the batch dataset and security alert queue."""
    st.session_state.batch_transactions = get_sample_batch_transactions()
    st.session_state.active_alerts = get_sample_alerts()
    st.session_state.sample_loaded = True


# Auto-populate if empty so jury always has immediate visual feedback
if not st.session_state.sample_loaded or st.session_state.batch_transactions.empty:
    load_all_sample_data()


# -----------------------------------------------------------------------------
# 5. Gemini API Wrapper with 429 Exponential Backoff
# -----------------------------------------------------------------------------
def analyze_transaction_with_gemini(
    api_key: str,
    transaction_payload: Dict[str, Any],
    max_retries: int = 3,
) -> TransactionRiskAssessment:
    """Invokes Gemini 3.5 Flash Lite with structured JSON output schema and exponential backoff retry."""
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an elite Anti-Money Laundering (AML) Compliance Officer and Financial Fraud Detection Intelligence Engine.
    Analyze this single transaction record rigorously for:
    1. Structuring / Smurfing (attempts to stay below regulatory thresholds like $10,000 USD CTR).
    2. Velocity Anomalies (abnormally high daily transaction frequency on young accounts).
    3. Geopolitical & Jurisdiction Risk (cross-border flows into tax havens, sanctioned regions, or offshore nodes).
    4. Payment Rail Risk (Crypto tumbler hops, rapid wire transfers, unusual card swipes).

    TRANSACTION METADATA:
    - Amount: ${transaction_payload.get('amount', 0):,.2f} USD
    - Rail / Type: {transaction_payload.get('txn_type')}
    - Sender Location: {transaction_payload.get('sender_loc')}
    - Recipient Location: {transaction_payload.get('recipient_loc')}
    - Account Age: {transaction_payload.get('account_age')} days
    - Daily Transaction Frequency: {transaction_payload.get('daily_freq')} transactions today

    Evaluate and return a structured JSON response adhering strictly to the provided responseSchema.
    """

    delay_seconds = 2.0
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TransactionRiskAssessment,
                    temperature=0.1,
                ),
            )
            # Parse verified JSON into Pydantic model
            parsed_data = json.loads(response.text)
            return TransactionRiskAssessment(**parsed_data)

        except Exception as err:
            err_msg = str(err)
            is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper()
            if is_rate_limit and attempt < max_retries - 1:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
            raise err


# -----------------------------------------------------------------------------
# 6. Sidebar: API Key Resolution & Global Demo Shortcut
# -----------------------------------------------------------------------------
st.sidebar.markdown("# 🛡️ Financial Security")
st.sidebar.title("SentinelGuard AML")
st.sidebar.caption("Autonomous Financial Crime & Fraud Intelligence")

# Check st.secrets first per GEMINI.md rules
configured_api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        configured_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    configured_api_key = ""

if configured_api_key:
    st.sidebar.success("🔒 API Key loaded from st.secrets")
    active_api_key = configured_api_key
else:
    active_api_key = st.sidebar.text_input(
        label="Gemini API Key",
        type="password",
        placeholder="AI Studio API Key...",
        help="Reads automatically from st.secrets['GEMINI_API_KEY'] or enter manually here.",
    )

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Live Demo Controls")
if st.sidebar.button("🔄 Reset / Reload Sample Data", use_container_width=True):
    load_all_sample_data()
    st.sidebar.success("Sample transactions & alerts reloaded!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("**Model**: `gemini-3.5-flash-lite`")
st.sidebar.caption("**SDK**: `google-genai` official")
st.sidebar.caption("**Rule Engine**: Structured `responseSchema`")


# -----------------------------------------------------------------------------
# 7. Main Screen Header with Demo Shortcut
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("🛡️ Financial Security, Fraud & AML System")
    st.markdown(
        "Autonomous real-time transaction screening, structuring detection, and AML alert triage powered by **Gemini 3.5 Flash Lite**."
    )
with header_col2:
    st.write("")
    if st.button("⚡ One-Click Demo Load", type="primary", use_container_width=True):
        load_all_sample_data()
        st.toast("Synthetic financial crime ledger loaded!", icon="✅")
        st.rerun()


# -----------------------------------------------------------------------------
# 8. Four Distinct Tabs Layout
# -----------------------------------------------------------------------------
tab_screener, tab_scanner, tab_alerts, tab_analytics = st.tabs(
    [
        "⚡ Live Transaction Screener",
        "📁 Batch AML & Fraud Scanner",
        "🚨 Active Security Alerts",
        "📊 Analytics & System Metrics",
    ]
)


# =============================================================================
# TAB 1: ⚡ Live Transaction Screener
# =============================================================================
with tab_screener:
    st.subheader("⚡ Real-Time Transaction Screening Engine")
    st.caption(
        "Input transaction details or use instant presets to evaluate fraud and AML risk patterns via Gemini 3.5 Flash Lite structured output."
    )

    # Preset Quick Loaders for Demo Convenience
    preset_col1, preset_col2, preset_col3 = st.columns([1, 1, 2])
    with preset_col1:
        if st.button("🚩 Preset: Structuring / Smurfing", use_container_width=True):
            st.session_state.screener_prefill = {
                "amount": 9950.00,
                "txn_type": "Wire Transfer",
                "sender_loc": "Miami, USA",
                "recipient_loc": "Panama City, Panama",
                "account_age": 8,
                "daily_freq": 16,
            }
            st.rerun()
    with preset_col2:
        if st.button("🟢 Preset: Safe Everyday UPI", use_container_width=True):
            st.session_state.screener_prefill = {
                "amount": 35.50,
                "txn_type": "UPI",
                "sender_loc": "Seattle, USA",
                "recipient_loc": "Seattle, USA",
                "account_age": 730,
                "daily_freq": 2,
            }
            st.rerun()
    with preset_col3:
        if st.button("🏴 Preset: Darknet Crypto Anomaly", use_container_width=True):
            st.session_state.screener_prefill = {
                "amount": 54000.00,
                "txn_type": "Crypto",
                "sender_loc": "Tor Exit Node / Unknown",
                "recipient_loc": "Unhosted Cold Wallet 0x81...cc",
                "account_age": 2,
                "daily_freq": 22,
            }
            st.rerun()

    st.markdown("---")

    # Transaction Input Form
    with st.form("screener_form"):
        col_in1, col_in2, col_in3 = st.columns(3)

        with col_in1:
            input_amount = st.number_input(
                "Transaction Amount ($ USD)",
                min_value=1.0,
                max_value=10_000_000.0,
                value=float(st.session_state.screener_prefill["amount"]),
                step=50.0,
                help="Transactions just below $10,000 trigger Bank Secrecy Act (BSA) structuring checks.",
            )
            type_options = ["Wire Transfer", "UPI", "Crypto", "Card Swipe"]
            input_type = st.selectbox(
                "Transaction Type / Payment Rail",
                options=type_options,
                index=type_options.index(st.session_state.screener_prefill["txn_type"])
                if st.session_state.screener_prefill["txn_type"] in type_options
                else 0,
            )

        with col_in2:
            input_sender = st.text_input(
                "Sender Location / Jurisdiction",
                value=st.session_state.screener_prefill["sender_loc"],
                help="Country or city where origin account or IP resides.",
            )
            input_recipient = st.text_input(
                "Recipient Location / Jurisdiction",
                value=st.session_state.screener_prefill["recipient_loc"],
                help="Destination account or wallet location.",
            )

        with col_in3:
            input_account_age = st.number_input(
                "Account Age (Days)",
                min_value=1,
                max_value=7300,
                value=int(st.session_state.screener_prefill["account_age"]),
                help="New accounts with high initial volume are high-risk indicators.",
            )
            input_daily_freq = st.number_input(
                "Daily Frequency (Transactions Today)",
                min_value=1,
                max_value=500,
                value=int(st.session_state.screener_prefill["daily_freq"]),
                help="Rapid bursts in 24 hours signal structuring or bot automation.",
            )

        btn_analyze = st.form_submit_button(
            "⚡ Analyze Transaction Risk", type="primary", use_container_width=True
        )

    # Execution & Result Presentation
    if btn_analyze:
        if not active_api_key:
            st.error(
                "⚠️ Gemini API Key missing! Please enter your key in the sidebar or configure `st.secrets`."
            )
        else:
            payload = {
                "amount": input_amount,
                "txn_type": input_type,
                "sender_loc": input_sender,
                "recipient_loc": input_recipient,
                "account_age": input_account_age,
                "daily_freq": input_daily_freq,
            }
            with st.spinner("🤖 SentinelGuard Engine: Analyzing risk vectors with Gemini 3.5 Flash Lite..."):
                try:
                    result_model = analyze_transaction_with_gemini(
                        api_key=active_api_key,
                        transaction_payload=payload,
                    )
                    st.session_state.live_screener_result = result_model.model_dump()
                    st.toast("Analysis complete!", icon="🛡️")
                except Exception as ex:
                    st.error(f"Error during AI risk assessment: {str(ex)}")

    # Display Persistent AI Insights
    if st.session_state.live_screener_result:
        res = st.session_state.live_screener_result
        st.markdown("### 🔍 Risk Scoring & Explainable AI Insights")

        score = res["risk_score"]
        level = res["risk_level"]

        # Color-coded metric and status badge
        res_col1, res_col2, res_col3 = st.columns([1, 1, 2])
        with res_col1:
            st.metric(
                label="Risk Score",
                value=f"{score}/100",
                delta=f"{level}",
                delta_color="inverse" if score > 50 else "normal",
            )
        with res_col2:
            if score >= 75 or "High" in level:
                st.error(f"🚨 **STATUS: {level.upper()}**\n\nImmediate intervention recommended.")
            elif score >= 40 or "Medium" in level:
                st.warning(f"⚠️ **STATUS: {level.upper()}**\n\nManual compliance review suggested.")
            else:
                st.success(f"✅ **STATUS: {level.upper()}**\n\nLow anomaly probability. Auto-cleared.")

        with res_col3:
            st.info(
                f"**Recommended Compliance Action:**\n\n`{res.get('recommended_action', 'Escalate to AML Tier 2')}`"
            )

        # Executive Summary & AML Patterns
        st.markdown("#### 📝 Executive Summary")
        st.write(res.get("executive_summary", ""))

        if res.get("aml_patterns_detected"):
            st.markdown("##### 🚩 AML & Fraud Patterns Triggered:")
            for pat in res["aml_patterns_detected"]:
                st.markdown(f"- 🔴 **{pat}**")

        # Granular Explainable Risk Indicators
        st.markdown("#### 🔬 Granular Risk Factor Breakdown")
        indicators = res.get("risk_indicators", [])
        if indicators:
            ind_df = pd.DataFrame(indicators)
            ind_df.columns = ["Indicator Name", "Severity Level", "Analytical Detail"]
            st.dataframe(ind_df, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 2: 📁 Batch AML & Fraud Scanner
# =============================================================================
with tab_scanner:
    st.subheader("📁 Batch AML & Fraud Scanner")
    st.caption(
        "Screen synthetic batch ledgers to identify structuring networks, threshold smurfing, and cross-border anomalies."
    )

    col_btn, col_filter, col_type = st.columns([1.2, 1, 1])
    with col_btn:
        if st.button("📥 Load Sample Dataset", type="primary", use_container_width=True):
            st.session_state.batch_transactions = get_sample_batch_transactions()
            st.toast("Loaded 10 synthetic transactions!", icon="📊")
            st.rerun()

    with col_filter:
        high_risk_only = st.checkbox("🔥 High Risk Only (Score ≥ 75)", value=False)

    with col_type:
        available_types = ["All Types", "Wire Transfer", "Crypto", "Card Swipe", "UPI"]
        selected_type = st.selectbox("Filter Payment Rail", available_types)

    # Filter Application
    df_display = st.session_state.batch_transactions.copy()
    if not df_display.empty:
        if high_risk_only:
            df_display = df_display[df_display["Risk_Score"] >= 75]
        if selected_type != "All Types":
            df_display = df_display[df_display["Type"] == selected_type]

        # Key Batch Summary Metrics
        b_m1, b_m2, b_m3, b_m4 = st.columns(4)
        b_m1.metric("Visible Records", len(df_display))
        b_m2.metric("Batch Volume", f"${df_display['Amount_USD'].sum():,.2f}")
        b_m3.metric("Flagged High Risk", len(df_display[df_display["Risk_Score"] >= 75]))
        b_m4.metric("Avg Risk Score", f"{df_display['Risk_Score'].mean():.1f}/100")

        st.markdown("### 📑 Transaction Records Ledger")
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount_USD": st.column_config.NumberColumn("Amount ($)", format="$%,.2f"),
                "Risk_Score": st.column_config.ProgressColumn(
                    "Risk Score", min_value=0, max_value=100, format="%d"
                ),
            },
        )
    else:
        st.info("No transaction data available. Click 'Load Sample Dataset' to begin.")


# =============================================================================
# TAB 3: 🚨 Active Security Alerts
# =============================================================================
with tab_alerts:
    st.subheader("🚨 Prioritized Active Security Alerts")
    st.caption(
        "Triage high-priority financial crime alerts. Actions persist in session state across user clicks."
    )

    alerts = st.session_state.active_alerts

    if not alerts:
        st.success("🎉 All security alerts have been investigated and triaged!")
    else:
        for idx, alert in enumerate(alerts):
            with st.container(border=True):
                al_col1, al_col2, al_col3, al_col4 = st.columns([1, 2.5, 1.2, 1.3])

                with al_col1:
                    if alert["risk_score"] >= 90:
                        st.error(f"🔥 **{alert['id']}**\n\nScore: **{alert['risk_score']}**")
                    else:
                        st.warning(f"⚠️ **{alert['id']}**\n\nScore: **{alert['risk_score']}**")
                    st.caption(f"Status: **{alert['status']}**")

                with al_col2:
                    st.markdown(f"**Target Account:** `{alert['account_id']}`")
                    st.markdown(f"**Pattern:** {alert['pattern']}")
                    st.caption(f"Jurisdiction: {alert['jurisdiction']} • Detected: {alert['timestamp']}")

                with al_col3:
                    # Mark as Investigated Button
                    investigated_disabled = alert["status"] == "Investigated"
                    if st.button(
                        "✅ Investigated",
                        key=f"inv_{alert['id']}_{idx}",
                        disabled=investigated_disabled,
                        use_container_width=True,
                    ):
                        alert["status"] = "Investigated"
                        st.toast(f"Alert {alert['id']} marked as investigated.", icon="✅")
                        st.rerun()

                with al_col4:
                    # Block Account Button
                    blocked_disabled = alert["status"] == "Account Blocked"
                    if st.button(
                        "🚫 Block Account",
                        key=f"blk_{alert['id']}_{idx}",
                        disabled=blocked_disabled,
                        type="primary" if not blocked_disabled else "secondary",
                        use_container_width=True,
                    ):
                        alert["status"] = "Account Blocked"
                        st.toast(f"Account {alert['account_id']} blocked and SAR initiated!", icon="🚫")
                        st.rerun()


# =============================================================================
# TAB 4: 📊 Analytics & System Metrics
# =============================================================================
with tab_analytics:
    st.subheader("📊 Analytics & Real-Time Threat Intelligence")
    st.caption("Aggregated security posture, financial crime distribution, and operational metrics.")

    df_all = st.session_state.batch_transactions
    alerts_all = st.session_state.active_alerts

    total_scanned = len(df_all) if not df_all.empty else 0
    high_risk_txns = df_all[df_all["Risk_Score"] >= 75] if not df_all.empty else pd.DataFrame()
    total_prevented = high_risk_txns["Amount_USD"].sum() if not high_risk_txns.empty else 0.0
    avg_score = df_all["Risk_Score"].mean() if not df_all.empty else 0.0
    active_aml_flags = len([a for a in alerts_all if a["status"] != "Investigated"])

    # Summary KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(
        label="Total Transactions Scanned",
        value=f"{total_scanned:,}",
        delta="+10 in batch",
    )
    kpi2.metric(
        label="Total Fraud Prevented ($)",
        value=f"${total_prevented:,.2f}",
        delta="Protected Capital",
        delta_color="normal",
    )
    kpi3.metric(
        label="Average Risk Score",
        value=f"{avg_score:.1f}/100",
        delta="Threat Index",
        delta_color="inverse",
    )
    kpi4.metric(
        label="Active AML Flags",
        value=active_aml_flags,
        delta=f"{len(alerts_all) - active_aml_flags} resolved",
    )

    st.markdown("---")

    # Visual Threat Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 💳 Risk Score Distribution by Payment Rail")
        if not df_all.empty:
            type_risk = df_all.groupby("Type")["Risk_Score"].mean().reset_index()
            type_risk.columns = ["Payment Rail", "Average Risk Score"]
            st.bar_chart(
                type_risk.set_index("Payment Rail"),
                use_container_width=True,
                color="#FF4B4B",
            )
        else:
            st.caption("Load batch dataset to view risk charts.")

    with chart_col2:
        st.markdown("#### 💰 Flagged Fraud Volume by Payment Rail ($ USD)")
        if not df_all.empty:
            type_vol = (
                df_all[df_all["Risk_Score"] >= 60].groupby("Type")["Amount_USD"].sum().reset_index()
            )
            type_vol.columns = ["Payment Rail", "Flagged Volume ($)"]
            st.bar_chart(
                type_vol.set_index("Payment Rail"),
                use_container_width=True,
                color="#FFAA00",
            )
        else:
            st.caption("Load batch dataset to view volume distribution.")

    st.markdown("---")
    st.markdown("#### 📈 Hourly Anomaly Detection & Threat Velocity")
    # Synthetic time-series threat progression
    timeline_data = pd.DataFrame(
        {
            "Hour": ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00"],
            "Structuring Anomalies": [1, 0, 2, 4, 3, 5],
            "Sanction/Geo Alerts": [0, 1, 0, 2, 1, 3],
        }
    ).set_index("Hour")
    st.line_chart(timeline_data, use_container_width=True)
