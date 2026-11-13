"""Financial Security System - Streamlit Boilerplate.

Built with Python, Streamlit, and the official google-genai SDK.
"""

import time
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. Page Configuration (Wide Layout)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Financial Security System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = pd.DataFrame()

if "security_analysis" not in st.session_state:
    st.session_state.security_analysis = None


# -----------------------------------------------------------------------------
# 3. Helper Functions: Sample Data & Gemini API
# -----------------------------------------------------------------------------
def get_sample_transactions() -> pd.DataFrame:
    """Returns sample financial transaction records for live demonstration."""
    return pd.DataFrame(
        [
            {
                "Transaction_ID": "TXN-8091",
                "Timestamp": "2026-11-13 02:14:22",
                "Account_ID": "ACC-5412",
                "Amount_USD": 45000.00,
                "Merchant": "Offshore Wire Exchange",
                "Location": "Unknown / TOR Exit",
                "Risk_Flag": "High",
            },
            {
                "Transaction_ID": "TXN-8092",
                "Timestamp": "2026-11-13 08:30:10",
                "Account_ID": "ACC-9921",
                "Amount_USD": 14.50,
                "Merchant": "Downtown Coffee",
                "Location": "Seattle, WA",
                "Risk_Flag": "Low",
            },
            {
                "Transaction_ID": "TXN-8093",
                "Timestamp": "2026-11-13 09:12:44",
                "Account_ID": "ACC-3141",
                "Amount_USD": 9800.00,
                "Merchant": "Luxury Electronics Retail",
                "Location": "Miami, FL",
                "Risk_Flag": "Medium",
            },
            {
                "Transaction_ID": "TXN-8094",
                "Timestamp": "2026-11-13 10:05:03",
                "Account_ID": "ACC-5412",
                "Amount_USD": 49999.00,
                "Merchant": "P2P Crypto Gateway",
                "Location": "Bucharest, RO",
                "Risk_Flag": "High",
            },
        ]
    )


def call_gemini_with_retry(
    api_key: str, prompt: str, model_name: str = "gemini-2.5-flash", max_retries: int = 3
) -> str:
    """Calls Gemini API using the official google-genai SDK with exponential backoff on 429 errors."""
    client = genai.Client(api_key=api_key)
    delay_seconds = 2.0

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as error:
            error_str = str(error)
            # Retry on rate limits (HTTP 429 / RESOURCE_EXHAUSTED)
            is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str.upper()
            if is_rate_limit and attempt < max_retries - 1:
                time.sleep(delay_seconds)
                delay_seconds *= 2
                continue
            raise error


# -----------------------------------------------------------------------------
# 4. Sidebar: API Key Resolution & System Settings
# -----------------------------------------------------------------------------
st.sidebar.title("🔐 Configuration")

# Priority 1: Read from st.secrets if configured
configured_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        configured_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    configured_key = ""

# Priority 2: Sidebar password input fallback
if configured_key:
    st.sidebar.success("Gemini API key detected in st.secrets")
    gemini_api_key = configured_key
else:
    gemini_api_key = st.sidebar.text_input(
        label="Gemini API Key",
        type="password",
        placeholder="Paste your AI Studio API key...",
        help="Reads from st.secrets['GEMINI_API_KEY'] when deployed, or paste your key here.",
    )

st.sidebar.markdown("---")
st.sidebar.subheader("System Info")
st.sidebar.caption("Model: `gemini-2.5-flash`")
st.sidebar.caption("SDK: `google-genai`")


# -----------------------------------------------------------------------------
# 5. Main Application Header & Two-Tab Navigation
# -----------------------------------------------------------------------------
st.title("🛡️ Financial Security & Fraud Intelligence System")
st.caption("Real-time transaction risk scoring and anomaly detection powered by Gemini 2.5 Flash.")

tab_main, tab_notes = st.tabs(["📊 Main Application", "📝 Project Notes"])

# -----------------------------------------------------------------------------
# TAB 1: Main Application
# -----------------------------------------------------------------------------
with tab_main:
    # Top Control Bar: Sample Data Loader
    top_col1, top_col2 = st.columns([1, 4])
    with top_col1:
        if st.button("📥 Load Sample Data", type="primary", use_container_width=True):
            st.session_state.transactions_df = get_sample_transactions()
            st.session_state.data_loaded = True
            st.session_state.security_analysis = None
            st.rerun()

    with top_col2:
        if st.session_state.data_loaded:
            st.success("Sample transaction ledger loaded successfully.")
        else:
            st.info("Click 'Load Sample Data' to populate the demo ledger.")

    # High-level Metrics Section
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    if not st.session_state.transactions_df.empty:
        df = st.session_state.transactions_df
        total_volume = df["Amount_USD"].sum()
        total_txns = len(df)
        high_risk_txns = len(df[df["Risk_Flag"] == "High"])

        m_col1.metric("Total Transactions", total_txns)
        m_col2.metric("Total Volume", f"${total_volume:,.2f}")
        m_col3.metric("Flagged High Risk", high_risk_txns, delta=f"{high_risk_txns} alert(s)", delta_color="inverse")
        m_col4.metric("Engine Status", "Active", delta="OK")
    else:
        m_col1.metric("Total Transactions", "0")
        m_col2.metric("Total Volume", "$0.00")
        m_col3.metric("Flagged High Risk", "0")
        m_col4.metric("Engine Status", "Standby")

    st.markdown("### 📋 Transaction Ledger")
    if not st.session_state.transactions_df.empty:
        st.dataframe(
            st.session_state.transactions_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No records available. Please load sample data above.")

    st.markdown("---")
    st.subheader("🤖 AI Security & Anomaly Assessment")

    # Interactive Inspection Form
    with st.form("security_assessment_form"):
        focus_area = st.selectbox(
            "Select Security Inspection Focus",
            [
                "Comprehensive Fraud & Structuring Detection",
                "High-Risk Geo-Location & TOR Hop Analysis",
                "Immediate Account Freeze & Escalation Plan",
            ],
        )
        submit_analysis = st.form_submit_button("Run Risk Assessment", use_container_width=True)

    if submit_analysis:
        if not gemini_api_key:
            st.error("Please enter a valid Gemini API key in the sidebar (or configure st.secrets) to proceed.")
        elif st.session_state.transactions_df.empty:
            st.warning("Please load sample data before running the risk assessment.")
        else:
            with st.spinner("Analyzing transaction ledger with Gemini 2.5 Flash..."):
                prompt = (
                    f"You are a financial fraud and security intelligence specialist. "
                    f"Analyze the following transactions ledger and perform: '{focus_area}'.\n\n"
                    f"Ledger Data:\n{st.session_state.transactions_df.to_string(index=False)}\n\n"
                    f"Provide structured findings including:\n"
                    f"1. Executive Summary\n"
                    f"2. High-Risk Anomalies Detected\n"
                    f"3. Recommended Security Actions (e.g. freeze, monitor, KYC request)"
                )
                try:
                    analysis_text = call_gemini_with_retry(
                        api_key=gemini_api_key,
                        prompt=prompt,
                    )
                    st.session_state.security_analysis = analysis_text
                except Exception as exc:
                    st.error(f"Failed to generate assessment: {exc}")

    # Display Persistent AI Results
    if st.session_state.security_analysis:
        st.markdown("### 🔎 Assessment Findings")
        st.markdown(st.session_state.security_analysis)


# -----------------------------------------------------------------------------
# TAB 2: Project Notes
# -----------------------------------------------------------------------------
with tab_notes:
    st.subheader("📌 Project Overview & Hackathon Blueprint")
    st.markdown(
        """
        ### Architecture & Stack
        - **Frontend & Dashboard**: [Streamlit](https://streamlit.io/) with wide responsive layout.
        - **Intelligence Layer**: Official [`google-genai`](https://github.com/googleapis/python-genai) SDK targeting `gemini-2.5-flash`.
        - **Security & Key Management**: Keys resolved seamlessly via `st.secrets` with sidebar manual fallback.
        - **Resilience**: Exponential backoff retry handler for HTTP 429 rate-limiting.

        ### Hackathon Checklist
        - [x] Initial boilerplate configured with `GEMINI.md`, `requirements.txt`, and `app.py`.
        - [x] Streamlit multi-tab structured layout.
        - [x] Working "Load Sample Data" button for reliable live demo presentation.
        - [ ] Connect custom fraud detection logic and rules.
        - [ ] Add export feature for compliance incident reports.
        """
    )
