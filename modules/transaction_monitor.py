"""Module 2: Transaction Monitor for FinGuard AI."""

from datetime import datetime
import pandas as pd
import streamlit as st

from core.models import CITIES, PAYMENT_CHANNELS, get_severity_color


def render() -> None:
    """Renders the comprehensive transaction investigation ledger and inspection workspace."""
    st.markdown("## ⚡ Transaction Monitor & Ledger")
    st.caption(
        "Multi-parameter transaction screening, behavioral anomaly breakdown, and forensic inspection in INR (₹)."
    )

    transactions_df: pd.DataFrame = st.session_state.get("transactions_df", pd.DataFrame())
    accounts_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())

    if transactions_df.empty:
        st.warning("No transactions loaded.")
        return

    # -------------------------------------------------------------------------
    # 1. Multi-Dimensional Filter Workspace
    # -------------------------------------------------------------------------
    with st.expander("🔍 Filter & Search Parameters", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            search_txn = st.text_input("Transaction ID", placeholder="e.g. TXN-5001")
            search_acc = st.text_input("Account ID (Sender/Receiver)", placeholder="e.g. ACC-1001")

        with f_col2:
            city_filter = st.selectbox("City / Jurisdiction", options=["All"] + CITIES)
            channel_filter = st.multiselect(
                "Payment Rail",
                options=PAYMENT_CHANNELS,
                default=PAYMENT_CHANNELS,
            )

        with f_col3:
            severity_filter = st.multiselect(
                "Risk Severity",
                options=["Critical", "High", "Medium", "Low"],
                default=["Critical", "High", "Medium", "Low"],
            )
            sort_order = st.selectbox(
                "Sort Records",
                options=[
                    "Newest First",
                    "Oldest First",
                    "Risk Score (High to Low)",
                    "Amount (High to Low)",
                ],
            )

        with f_col4:
            st.write("")
            st.write("")
            reset_filters = st.button("🔄 Reset All Filters", use_container_width=True)

    # -------------------------------------------------------------------------
    # 2. Filter Application (AND Logic)
    # -------------------------------------------------------------------------
    df_filtered = transactions_df.copy()

    if not reset_filters:
        if search_txn:
            df_filtered = df_filtered[
                df_filtered["txn_id"].astype(str).str.contains(search_txn.strip(), case=False)
            ]
        if search_acc:
            acc_str = search_acc.strip().upper()
            df_filtered = df_filtered[
                df_filtered["sender_id"].astype(str).str.upper().str.contains(acc_str)
                | df_filtered["receiver_id"].astype(str).str.upper().str.contains(acc_str)
            ]
        if city_filter != "All":
            df_filtered = df_filtered[df_filtered["city"] == city_filter]
        if channel_filter:
            df_filtered = df_filtered[df_filtered["channel"].isin(channel_filter)]
        if severity_filter:
            df_filtered = df_filtered[df_filtered["risk_severity"].isin(severity_filter)]

        # Sorting logic
        if sort_order == "Newest First":
            df_filtered = df_filtered.sort_values(by="timestamp", ascending=False)
        elif sort_order == "Oldest First":
            df_filtered = df_filtered.sort_values(by="timestamp", ascending=True)
        elif sort_order == "Risk Score (High to Low)":
            df_filtered = df_filtered.sort_values(by="risk_score", ascending=False)
        elif sort_order == "Amount (High to Low)":
            df_filtered = df_filtered.sort_values(by="amount", ascending=False)
    else:
        st.rerun()

    # -------------------------------------------------------------------------
    # 3. Transaction Ledger Table
    # -------------------------------------------------------------------------
    st.markdown(
        f"**Transaction Records** <span style='color:#8B8D93;'>— Showing {len(df_filtered)} of {len(transactions_df)} transactions</span>",
        unsafe_allow_html=True,
    )

    display_cols = [
        "txn_id",
        "timestamp",
        "sender_id",
        "receiver_id",
        "amount",
        "channel",
        "city",
        "ml_probability",
        "zscore",
        "aml_patterns",
        "risk_score",
        "risk_severity",
    ]

    # Color-coding transaction records by risk severity
    def style_severity_row(row):
        sev = str(row.get("risk_severity", "Low"))
        if sev == "Critical":
            return ["background-color: rgba(255, 68, 68, 0.22); color: #FF8888; font-weight: 600;"] * len(row)
        elif sev == "High":
            return ["background-color: rgba(255, 140, 0, 0.18); color: #FFBB55;"] * len(row)
        elif sev == "Medium":
            return ["background-color: rgba(255, 215, 0, 0.10); color: #FFE066;"] * len(row)
        elif sev == "Low":
            return ["background-color: rgba(0, 200, 81, 0.06); color: #77E899;"] * len(row)
        return [""] * len(row)

    styled_ledger = df_filtered[display_cols].style.apply(style_severity_row, axis=1)

    st.dataframe(
        styled_ledger,
        use_container_width=True,
        hide_index=True,
        column_config={
            "txn_id": st.column_config.TextColumn("Txn ID", width="small"),
            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm"),
            "sender_id": st.column_config.TextColumn("Sender", width="small"),
            "receiver_id": st.column_config.TextColumn("Receiver", width="small"),
            "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%,.2f"),
            "channel": st.column_config.TextColumn("Rail"),
            "city": st.column_config.TextColumn("City"),
            "ml_probability": st.column_config.NumberColumn("ML Prob", format="%.3f"),
            "zscore": st.column_config.NumberColumn("Z-Score", format="%+.2f"),
            "aml_patterns": st.column_config.TextColumn("AML Typology", width="medium"),
            "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d"),
            "risk_severity": st.column_config.TextColumn("Severity"),
        },
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. Deep Forensic Transaction Inspector
    # -------------------------------------------------------------------------
    st.markdown("### 🔎 Forensic Transaction Inspector")
    st.caption("Select a transaction ID below to inspect model evidence, counterparty profiles, and AML rule triggers.")

    txn_list = df_filtered["txn_id"].tolist()
    if not txn_list:
        st.info("No transactions match current filters.")
        return

    selected_txn_id = st.selectbox(
        "Select Transaction to Inspect",
        options=txn_list,
        index=0,
    )

    txn_match = df_filtered[df_filtered["txn_id"] == selected_txn_id]
    if txn_match.empty:
        return

    txn = txn_match.iloc[0]

    # Look up Sender and Receiver Account records
    sender_info = accounts_df[accounts_df["account_id"] == txn["sender_id"]]
    receiver_info = accounts_df[accounts_df["account_id"] == txn["receiver_id"]]

    s_name = sender_info.iloc[0]["holder_name"] if not sender_info.empty else "Unknown Entity"
    s_kyc = sender_info.iloc[0]["kyc_tier"] if not sender_info.empty else "N/A"
    s_age = sender_info.iloc[0]["account_age_days"] if not sender_info.empty else "N/A"
    s_city = sender_info.iloc[0]["city"] if not sender_info.empty else txn["city"]
    s_blocked = sender_info.iloc[0]["is_blocked"] if not sender_info.empty else False

    r_name = receiver_info.iloc[0]["holder_name"] if not receiver_info.empty else "Unknown Entity"
    r_kyc = receiver_info.iloc[0]["kyc_tier"] if not receiver_info.empty else "N/A"
    r_age = receiver_info.iloc[0]["account_age_days"] if not receiver_info.empty else "N/A"

    # Inspector Layout: 3 Columns (Metadata, Counterparties, Detection Engine Breakdown)
    insp_col1, insp_col2, insp_col3 = st.columns([1.1, 1.2, 1.3])

    with insp_col1:
        st.markdown(
            f"""
            <div style="background:#131722; border:1px solid #232733; border-radius:8px; padding:16px;">
                <div style="color:#00D4FF; font-weight:700; font-size:14px; margin-bottom:12px;">TRANSACTION METADATA</div>
                <div style="font-size:12px; margin-bottom:6px;"><strong>ID:</strong> <code>{txn['txn_id']}</code></div>
                <div style="font-size:12px; margin-bottom:6px;"><strong>Timestamp:</strong> {txn['timestamp']}</div>
                <div style="font-size:12px; margin-bottom:6px;"><strong>Amount:</strong> <span style="font-size:16px; color:#00D4FF; font-weight:700;">₹{txn['amount']:,.2f}</span></div>
                <div style="font-size:12px; margin-bottom:6px;"><strong>Payment Rail:</strong> <code>{txn['channel']}</code></div>
                <div style="font-size:12px;"><strong>Jurisdiction:</strong> {txn['city']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insp_col2:
        block_badge = "<span style='color:#FF4444; font-weight:bold;'>[BLOCKED]</span>" if s_blocked else "<span style='color:#00C851;'>[ACTIVE]</span>"
        st.markdown(
            f"""
            <div style="background:#131722; border:1px solid #232733; border-radius:8px; padding:16px;">
                <div style="color:#00D4FF; font-weight:700; font-size:14px; margin-bottom:12px;">COUNTERPARTY INTELLIGENCE</div>
                <div style="font-size:12px; margin-bottom:8px;">
                    <strong>Sender:</strong> <code>{txn['sender_id']}</code> {block_badge}<br/>
                    <span style="color:#8B8D93;">Name: {s_name} | KYC: {s_kyc} | Age: {s_age}d</span>
                </div>
                <hr style="border:0; border-top:1px solid #232733; margin:8px 0;"/>
                <div style="font-size:12px;">
                    <strong>Receiver:</strong> <code>{txn['receiver_id']}</code><br/>
                    <span style="color:#8B8D93;">Name: {r_name} | KYC: {r_kyc} | Age: {r_age}d</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insp_col3:
        sev_color = get_severity_color(txn["risk_severity"])
        st.markdown(
            f"""
            <div style="background:#131722; border:1px solid #232733; border-radius:8px; padding:16px;">
                <div style="color:#00D4FF; font-weight:700; font-size:14px; margin-bottom:12px;">DETECTION BREAKDOWN</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:12px;">Unified Risk Score:</span>
                    <span style="font-size:18px; font-weight:700; color:{sev_color};">{txn['risk_score']:.1f}/100 ({txn['risk_severity']})</span>
                </div>
                <div style="font-size:12px; margin-bottom:4px;"><strong>ML Model Probability:</strong> {txn['ml_probability'] * 100:.1f}%</div>
                <div style="font-size:12px; margin-bottom:4px;"><strong>Behavioral Z-Score:</strong> {txn['zscore']:+.2f}σ deviation</div>
                <div style="font-size:12px;"><strong>AML Rule Triggers:</strong> <code>{txn['aml_patterns']}</code></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Full Explainable AI Narrative
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:#181C27; border-left:4px solid {sev_color}; padding:14px 18px; border-radius:4px;">
            <div style="color:#8B8D93; font-size:11px; text-transform:uppercase; font-weight:600; letter-spacing:0.8px;">Explainable AI Detection Narrative</div>
            <div style="color:#E2E4E9; font-size:13px; line-height:1.5; margin-top:4px;">{txn['explanation']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
