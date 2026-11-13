"""SentinelGuard | AI Financial Security & AML System.

Enterprise-grade Financial Crime Detection, Anti-Money Laundering (AML),
and Network Topology Intelligence Platform.
"""

import streamlit as st

# -----------------------------------------------------------------------------
# 1. Page Configuration & Dark Cybersecurity Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SentinelGuard | AI Financial Security & AML System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Dark Cybersecurity CSS Theme
st.markdown(
    """
    <style>
        /* Global Background & Typography */
        .stApp {
            background-color: #0E1117;
            color: #E2E4E9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Top Header Styling */
        header[data-testid="stHeader"] {
            background: transparent;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #11141C;
            border-right: 1px solid #1D212C;
        }

        /* Navigation Buttons */
        div[data-testid="stSidebar"] .stButton > button {
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            border-radius: 6px !important;
            margin-bottom: 2px !important;
            transition: all 0.15s ease-in-out !important;
        }
        div[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.20) 0%, rgba(0, 212, 255, 0.05) 100%) !important;
            border: 1px solid #00D4FF !important;
            color: #00D4FF !important;
            box-shadow: 0 0 12px rgba(0, 212, 255, 0.25) !important;
        }
        div[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background-color: #161922 !important;
            border: 1px solid #232733 !important;
            color: #B0B4BC !important;
        }
        div[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            border-color: #00D4FF !important;
            color: #FFFFFF !important;
            background-color: #1C202C !important;
        }

        /* Metric Overrides */
        div[data-testid="stMetricValue"] {
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            color: #00D4FF !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px !important;
            color: #8B8D93 !important;
        }

        /* Dataframe Overrides */
        div[data-testid="stDataFrame"] {
            border: 1px solid #232733;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid #232733;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 8px 16px;
            color: #8B8D93;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            color: #00D4FF !important;
            border-bottom: 2px solid #00D4FF !important;
            background-color: #151821;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. Initialize Shared Application State
# -----------------------------------------------------------------------------
from core.state_manager import init_session_state, reload_sample_data

init_session_state()

# -----------------------------------------------------------------------------
# 3. Import UI Modules (Methodology moved to README.md per spec)
# -----------------------------------------------------------------------------
from modules import (
    account_profiles,
    alerts_cases,
    aml_investigation,
    dashboard,
    detection_lab,
    transaction_monitor,
)

# -----------------------------------------------------------------------------
# 4. Sidebar Navigation & Clickable Tabs
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px; padding-top:4px;">
            <div style="background:#00D4FF; width:38px; height:38px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:20px; color:#0E1117; font-weight:bold; box-shadow:0 0 10px rgba(0,212,255,0.4);">
                🛡️
            </div>
            <div>
                <div style="font-size:17px; font-weight:800; color:#FFFFFF; letter-spacing:0.5px; line-height:1.2;">SentinelGuard</div>
                <div style="font-size:10px; color:#00D4FF; font-weight:700; letter-spacing:1px; text-transform:uppercase;">AI Financial Security & AML</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Clickable Sidebar Tabs/Buttons Navigation
    st.markdown("<p style='color:#8B8D93; font-size:11px; font-weight:700; letter-spacing:1px; margin-bottom:6px;'>NAVIGATION MODULES</p>", unsafe_allow_html=True)

    MODULES = [
        ("📊", "Overview Dashboard"),
        ("⚡", "Transaction Monitor"),
        ("🕸️", "AML Investigation"),
        ("👤", "Account Risk Profiles"),
        ("🚨", "Alerts & Case Management"),
        ("🧪", "Detection Lab & Simulator"),
    ]

    current_page = st.session_state.get("current_page", "Overview Dashboard")

    for icon, mod_name in MODULES:
        is_selected = (current_page == mod_name)
        btn_type = "primary" if is_selected else "secondary"
        if st.button(f"{icon}  {mod_name}", key=f"nav_btn_{mod_name}", type=btn_type, use_container_width=True):
            st.session_state.current_page = mod_name
            st.rerun()

    st.markdown("---")

    # Quick Demo Controls
    st.subheader("🎯 Live Demo Controls")
    if st.button("🔄 Reload Baseline Ledger", use_container_width=True):
        reload_sample_data()
        st.toast("Baseline demonstration data reloaded!", icon="✅")
        st.rerun()

    st.markdown("---")

    # API Key & Copilot Integration
    configured_api_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            configured_api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        configured_api_key = ""

    if configured_api_key:
        st.success("🔒 Gemini AI: Key active via st.secrets")
    else:
        api_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AI Studio API Key...",
            help="Enables live Gemini AI forensic case assessments in Alerts & Case Management.",
            key="gemini_api_key_input",
        )

    st.caption("**Engine**: Hybrid ML + Z-Score + NetworkX")
    st.caption("**Payment Rails**: UPI, Crypto, Card, IMPS, NEFT")
    st.caption("**Currency**: INR (₹)")

# -----------------------------------------------------------------------------
# 5. Module Routing Dispatcher
# -----------------------------------------------------------------------------
active_tab = st.session_state.get("current_page", "Overview Dashboard")

if active_tab == "Overview Dashboard":
    dashboard.render()
elif active_tab == "Transaction Monitor":
    transaction_monitor.render()
elif active_tab == "AML Investigation":
    aml_investigation.render()
elif active_tab == "Account Risk Profiles":
    account_profiles.render()
elif active_tab == "Alerts & Case Management":
    alerts_cases.render()
elif active_tab == "Detection Lab & Simulator":
    detection_lab.render()
