"""Module 4: Account Risk Profiles for FinGuard AI."""

import pandas as pd
import streamlit as st

from core.models import get_risk_severity, get_severity_color


def render() -> None:
    """Renders the comprehensive account ranking ledger and granular profile investigator."""
    st.markdown("## 👤 Account Risk Profiles & Entity Intelligence")
    st.caption(
        "Holistic customer risk profiles, transaction flow concentration, and entity-level AML investigation."
    )

    transactions_df: pd.DataFrame = st.session_state.get("transactions_df", pd.DataFrame())
    accounts_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())
    alerts = st.session_state.get("alerts", [])

    if accounts_df.empty:
        st.warning("No accounts available.")
        return

    # -------------------------------------------------------------------------
    # 1. Compute Comprehensive Account-Level Metrics
    # -------------------------------------------------------------------------
    records = []
    for _, acc in accounts_df.iterrows():
        acc_id = acc["account_id"]

        inbound = transactions_df[transactions_df["receiver_id"] == acc_id]
        outbound = transactions_df[transactions_df["sender_id"] == acc_id]

        in_count = len(inbound)
        out_count = len(outbound)
        in_vol = inbound["amount"].sum()
        out_vol = outbound["amount"].sum()

        combined = pd.concat([inbound, outbound])
        max_risk = combined["risk_score"].max() if not combined.empty else 0.0

        # Unique counterparties
        counterparties = set(inbound["sender_id"].tolist() + outbound["receiver_id"].tolist())

        # Active non-closed alerts
        active_alerts = len([a for a in alerts if a["account_id"] == acc_id and a.get("status") != "Closed"])

        records.append(
            {
                "Account ID": acc_id,
                "Holder Name": acc["holder_name"],
                "KYC Tier": acc["kyc_tier"],
                "City": acc["city"],
                "Age (Days)": acc["account_age_days"],
                "Max Risk Score": round(max_risk, 1),
                "Severity": get_risk_severity(max_risk),
                "Inbound Count": in_count,
                "Outbound Count": out_count,
                "Inbound (₹)": in_vol,
                "Outbound (₹)": out_vol,
                "Net Flow (₹)": in_vol - out_vol,
                "Counterparties": len(counterparties),
                "Active Alerts": active_alerts,
                "Status": "BLOCKED" if acc["is_blocked"] else "ACTIVE",
            }
        )

    df_acc_metrics = pd.DataFrame(records).sort_values(by="Max Risk Score", ascending=False)

    # -------------------------------------------------------------------------
    # 2. Hard-Filtered High & Critical Risk Ranking Ledger (Color-Coded)
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="background:rgba(255, 68, 68, 0.10); border:1px solid rgba(255, 68, 68, 0.40); border-left:4px solid #FF4444; padding:8px 14px; border-radius:6px; margin-bottom:12px;">
            <span style="color:#FF6666; font-weight:700; font-size:12px;">🔥 HIGH & CRITICAL RISK WATCHLIST (HARD FILTERED: RISK SCORE ≥ 60.0)</span>
            <div style="color:#A0A4B0; font-size:11px;">Showing only entities subject to enhanced due diligence (EDD) and AML escalation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Hard-filter strictly to High and Critical risk accounts
    df_table = df_acc_metrics[df_acc_metrics["Max Risk Score"] >= 60.0].copy()

    # Color-code account risk rows
    def style_account_row(row):
        sev = str(row.get("Severity", "Low"))
        if sev == "Critical":
            return ["background-color: rgba(255, 68, 68, 0.22); color: #FF8888; font-weight: 600;"] * len(row)
        elif sev == "High":
            return ["background-color: rgba(255, 140, 0, 0.18); color: #FFAA33; font-weight: 500;"] * len(row)
        return [""] * len(row)

    styled_table = df_table.style.apply(style_account_row, axis=1)

    st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Max Risk Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            "Inbound (₹)": st.column_config.NumberColumn(format="₹%,.2f"),
            "Outbound (₹)": st.column_config.NumberColumn(format="₹%,.2f"),
            "Net Flow (₹)": st.column_config.NumberColumn(format="₹%,.2f"),
        },
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. Individual Account Deep Forensic Profile
    # -------------------------------------------------------------------------
    st.markdown("### 📋 Individual Account Dossier")
    acc_options = df_acc_metrics["Account ID"].tolist()
    selected_id = st.selectbox("Select Account Dossier to Inspect", options=acc_options)

    if not selected_id:
        return

    profile_row = df_acc_metrics[df_acc_metrics["Account ID"] == selected_id].iloc[0]
    acc_raw = accounts_df[accounts_df["account_id"] == selected_id].iloc[0]

    # KPI Top Bar
    k1, k2, k3, k4, k5 = st.columns(5)
    sev_color = get_severity_color(profile_row["Severity"])

    k1.metric("Risk Score", f"{profile_row['Max Risk Score']:.1f}/100", delta=profile_row["Severity"])
    k2.metric("Total Inflow", f"₹{profile_row['Inbound (₹)']:,.2f}")
    k3.metric("Total Outflow", f"₹{profile_row['Outbound (₹)']:,.2f}")
    k4.metric("Active Counterparties", profile_row["Counterparties"])
    k5.metric("Open Alerts", profile_row["Active Alerts"])

    # Account Profile Tabs
    tab_summary, tab_txns, tab_alerts, tab_risk = st.tabs(
        ["📑 Entity Summary", "💳 Transaction History", "🚨 Associated Alerts", "🔬 Risk Analysis"]
    )

    with tab_summary:
        st.markdown(
            f"""
            <div style="background:#131722; border:1px solid #232733; border-radius:8px; padding:16px; margin-top:8px;">
                <div style="font-size:14px; color:#00D4FF; font-weight:700; margin-bottom:12px;">ACCOUNT REGISTRATION & COMPLIANCE METADATA</div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:13px;">
                    <div><strong>Account Number:</strong> <code>{selected_id}</code></div>
                    <div><strong>Account Holder:</strong> {profile_row['Holder Name']}</div>
                    <div><strong>KYC Status:</strong> {profile_row['KYC Tier']}</div>
                    <div><strong>City / Branch:</strong> {profile_row['City']}</div>
                    <div><strong>Account Age:</strong> {profile_row['Age (Days)']} days</div>
                    <div><strong>Enforcement Status:</strong> <span style="color:{'#FF4444' if acc_raw['is_blocked'] else '#00C851'}; font-weight:700;">{profile_row['Status']}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_txns:
        user_txns = transactions_df[
            (transactions_df["sender_id"] == selected_id) | (transactions_df["receiver_id"] == selected_id)
        ].sort_values(by="timestamp", ascending=False)

        if not user_txns.empty:
            st.dataframe(
                user_txns[
                    ["txn_id", "timestamp", "sender_id", "receiver_id", "amount", "channel", "risk_score", "risk_severity"]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%,.2f"),
                    "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d"),
                },
            )
        else:
            st.info("No transaction history recorded for this entity.")

    with tab_alerts:
        user_alerts = [a for a in alerts if a["account_id"] == selected_id]
        if user_alerts:
            for al in user_alerts:
                with st.container(border=True):
                    st.markdown(f"**Alert ID:** `{al['alert_id']}` | **Severity:** `{al['severity']}` | **Status:** `{al['status']}`")
                    st.write(f"**Typology:** {al['typology']}")
                    st.caption(f"Detected: {al['timestamp']} on Txn: {al['txn_id']}")
                    st.info(al["explanation"])
        else:
            st.success("No active compliance alerts for this account.")

    with tab_risk:
        st.markdown("#### Detection Signal Distribution for Entity")
        if not user_txns.empty:
            avg_ml = user_txns["ml_probability"].mean()
            max_z = user_txns["zscore"].abs().max()
            triggered = set()
            for p in user_txns["aml_patterns"]:
                if p != "None":
                    for sub_p in p.split(","):
                        triggered.add(sub_p.strip())

            r_col1, r_col2 = st.columns(2)
            r_col1.metric("Average ML Anomaly Probability", f"{avg_ml * 100:.1f}%")
            r_col2.metric("Peak Behavioral Z-Score", f"{max_z:.2f}σ")

            st.write(f"**Historical Typologies Encountered:** {', '.join(triggered) if triggered else 'None'}")
