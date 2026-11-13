"""Module 6: Detection Lab & Scenario Simulator for FinGuard AI."""

from datetime import datetime, timedelta
import random
import pandas as pd
import streamlit as st

from core.models import CITIES, PAYMENT_CHANNELS, get_severity_color
from core.state_manager import log_audit_event


def render() -> None:
    """Renders the real-time scenario simulation lab and custom transaction injector."""
    st.markdown("## 🧪 Detection Lab & Scenario Simulator")
    st.caption(
        "Inject live financial crime patterns or custom synthetic transactions to stress-test the multi-stage hybrid detection pipeline."
    )

    transactions_df: pd.DataFrame = st.session_state.get("transactions_df", pd.DataFrame())
    accounts_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())
    detection_engine = st.session_state.get("detection_engine")

    if detection_engine is None or accounts_df.empty:
        st.warning("Detection engine or accounts not initialized.")
        return

    # -------------------------------------------------------------------------
    # 1. Six One-Click Realistic Scenario Injections
    # -------------------------------------------------------------------------
    st.markdown("### ⚡ One-Click Financial Crime Scenarios")
    st.caption("Trigger realistic synthetic transaction payloads that execute through the live detection engine.")

    sc_col1, sc_col2, sc_col3 = st.columns(3)

    account_ids = accounts_df["account_id"].tolist()
    now = datetime.now()

    def run_scenario(scenario_name: str, new_txns: list):
        with st.spinner(f"Injecting and analyzing {scenario_name}..."):
            df_new = pd.DataFrame(new_txns)
            df_combined = pd.concat([transactions_df, df_new], ignore_index=True)
            df_combined["timestamp"] = pd.to_datetime(df_combined["timestamp"])
            df_combined = df_combined.sort_values(by="timestamp").reset_index(drop=True)

            # Re-run the full pipeline so graph cycles, velocity windows, and Z-scores reflect new state
            scored_df = detection_engine.run_pipeline(df_combined, accounts_df)
            new_alerts = detection_engine.generate_alerts(scored_df, accounts_df)

            st.session_state.transactions_df = scored_df
            st.session_state.alerts = new_alerts

            # Find the scored new rows to display immediate results
            injected_ids = [t["txn_id"] for t in new_txns]
            scored_injected = scored_df[scored_df["txn_id"].isin(injected_ids)]

            log_audit_event(
                target_ref=scenario_name,
                action="Scenario Injected",
                previous_status="BASELINE",
                new_status="UPDATED",
                notes=f"Injected {len(new_txns)} transactions into ledger.",
            )

            st.toast(f"Executed: {scenario_name} ({len(new_txns)} txns processed)", icon="⚡")

            # Store in session state for result display
            st.session_state.last_scenario_result = {
                "name": scenario_name,
                "injected_txns": scored_injected.to_dict(orient="records"),
            }
            st.rerun()

    # Scenario 1: Normal Transaction
    with sc_col1:
        with st.container(border=True):
            st.markdown("🟢 **Normal Everyday P2P**")
            st.caption("Standard ₹2,450 UPI peer transfer between long-standing retail accounts.")
            if st.button("Launch Scenario 1", key="sc_1", use_container_width=True):
                txn_payload = [
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now,
                        "sender_id": account_ids[3],
                        "receiver_id": account_ids[7],
                        "amount": 2450.0,
                        "channel": "UPI",
                        "city": "Mumbai",
                    }
                ]
                run_scenario("Normal Everyday P2P", txn_payload)

    # Scenario 2: High-Value Anomaly
    with sc_col2:
        with st.container(border=True):
            st.markdown("🟠 **High-Value Outflow on Young Account**")
            st.caption("₹450,000 NEFT transfer initiated from a young (<60d) account.")
            if st.button("Launch Scenario 2", key="sc_2", use_container_width=True):
                txn_payload = [
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now,
                        "sender_id": "ACC-1002",  # Young 45d account
                        "receiver_id": account_ids[8],
                        "amount": 450000.0,
                        "channel": "NEFT",
                        "city": "Delhi",
                    }
                ]
                run_scenario("High-Value Young Account Outflow", txn_payload)

    # Scenario 3: Velocity Burst
    with sc_col3:
        with st.container(border=True):
            st.markdown("🔴 **High-Frequency Velocity Burst**")
            st.caption("6 rapid successive UPI disbursements in 10 minutes from ACC-1007.")
            if st.button("Launch Scenario 3", key="sc_3", use_container_width=True):
                burst = []
                for i in range(6):
                    burst.append(
                        {
                            "txn_id": f"TXN-{random.randint(6000, 9999)}",
                            "timestamp": now - timedelta(minutes=(6 - i) * 2),
                            "sender_id": "ACC-1007",
                            "receiver_id": account_ids[(10 + i) % len(account_ids)],
                            "amount": 14500.0 + (i * 800),
                            "channel": "UPI",
                            "city": "Pune",
                        }
                    )
                run_scenario("Velocity Burst Pattern", burst)

    sc_col4, sc_col5, sc_col6 = st.columns(3)

    # Scenario 4: Structuring
    with sc_col4:
        with st.container(border=True):
            st.markdown("🔴 **Structuring (BSA Smurfing)**")
            st.caption("4 transactions between ₹48,000–₹49,900 to evade ₹50,000 reporting threshold.")
            if st.button("Launch Scenario 4", key="sc_4", use_container_width=True):
                structuring_txns = []
                amounts = [49200.0, 48900.0, 49500.0, 48750.0]
                for i, amt in enumerate(amounts):
                    structuring_txns.append(
                        {
                            "txn_id": f"TXN-{random.randint(6000, 9999)}",
                            "timestamp": now - timedelta(minutes=(4 - i) * 15),
                            "sender_id": "ACC-1001",
                            "receiver_id": "ACC-1003",
                            "amount": amt,
                            "channel": "IMPS",
                            "city": "Mumbai",
                        }
                    )
                run_scenario("Structuring / Smurfing", structuring_txns)

    # Scenario 5: Money Mule Pass-Through
    with sc_col5:
        with st.container(border=True):
            st.markdown("🚨 **Money Mule Rapid Pass-Through**")
            st.caption("Inbound ₹380,000 credit followed by immediate ₹375,000 wash 8 mins later.")
            if st.button("Launch Scenario 5", key="sc_5", use_container_width=True):
                mule_txns = [
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now - timedelta(minutes=12),
                        "sender_id": account_ids[9],
                        "receiver_id": "ACC-1002",
                        "amount": 380000.0,
                        "channel": "NEFT",
                        "city": "Delhi",
                    },
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now - timedelta(minutes=4),
                        "sender_id": "ACC-1002",
                        "receiver_id": account_ids[14],
                        "amount": 375000.0,
                        "channel": "IMPS",
                        "city": "Delhi",
                    },
                ]
                run_scenario("Money Mule Pass-Through", mule_txns)

    # Scenario 6: Circular Ring
    with sc_col6:
        with st.container(border=True):
            st.markdown("🔄 **Circular Fund Transfer Ring**")
            st.caption("Triangular wash: ACC-1004 ➔ ACC-1005 ➔ ACC-1006 ➔ ACC-1004.")
            if st.button("Launch Scenario 6", key="sc_6", use_container_width=True):
                ring = [
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now - timedelta(minutes=30),
                        "sender_id": "ACC-1004",
                        "receiver_id": "ACC-1005",
                        "amount": 320000.0,
                        "channel": "NEFT",
                        "city": "Bangalore",
                    },
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now - timedelta(minutes=20),
                        "sender_id": "ACC-1005",
                        "receiver_id": "ACC-1006",
                        "amount": 315000.0,
                        "channel": "NEFT",
                        "city": "Bangalore",
                    },
                    {
                        "txn_id": f"TXN-{random.randint(6000, 9999)}",
                        "timestamp": now - timedelta(minutes=10),
                        "sender_id": "ACC-1006",
                        "receiver_id": "ACC-1004",
                        "amount": 310000.0,
                        "channel": "NEFT",
                        "city": "Bangalore",
                    },
                ]
                run_scenario("Circular Fund Transfer Ring", ring)

    # -------------------------------------------------------------------------
    # 2. Display Result of Last Scenario Run
    # -------------------------------------------------------------------------
    last_res = st.session_state.get("last_scenario_result")
    if last_res:
        st.markdown("---")
        st.markdown(f"#### 🔎 Injected Scenario Evaluation: *{last_res['name']}*")
        df_res = pd.DataFrame(last_res["injected_txns"])
        st.dataframe(
            df_res[
                [
                    "txn_id",
                    "timestamp",
                    "sender_id",
                    "receiver_id",
                    "amount",
                    "channel",
                    "ml_probability",
                    "zscore",
                    "aml_patterns",
                    "risk_score",
                    "risk_severity",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "amount": st.column_config.NumberColumn("Amount (₹)", format="₹%,.2f"),
                "ml_probability": st.column_config.NumberColumn("ML Prob", format="%.3f"),
                "zscore": st.column_config.NumberColumn("Z-Score", format="%+.2f"),
                "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d"),
            },
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. Custom Transaction Simulator Form
    # -------------------------------------------------------------------------
    st.markdown("### ✍️ Custom Transaction Injector")
    st.caption("Configure custom parameters to test specific anomaly thresholds.")

    with st.form("custom_txn_form"):
        c_col1, c_col2, c_col3 = st.columns(3)

        with c_col1:
            custom_sender = st.selectbox("Sender Account", options=account_ids, index=0)
            custom_receiver = st.selectbox(
                "Receiver Account",
                options=[acc for acc in account_ids if acc != custom_sender],
                index=1,
            )

        with c_col2:
            custom_amount = st.number_input(
                "Amount in INR (₹)",
                min_value=100.0,
                max_value=10_000_000.0,
                value=49500.0,
                step=500.0,
            )
            custom_channel = st.selectbox("Payment Channel", options=PAYMENT_CHANNELS)

        with c_col3:
            custom_city = st.selectbox("City / Jurisdiction", options=CITIES)
            custom_submit = st.form_submit_button("⚡ Process Custom Transaction", type="primary", use_container_width=True)

    if custom_submit:
        if custom_sender == custom_receiver:
            st.error("Sender and receiver accounts must be distinct entities.")
        else:
            custom_payload = [
                {
                    "txn_id": f"TXN-{random.randint(6000, 9999)}",
                    "timestamp": datetime.now(),
                    "sender_id": custom_sender,
                    "receiver_id": custom_receiver,
                    "amount": float(custom_amount),
                    "channel": custom_channel,
                    "city": custom_city,
                }
            ]
            run_scenario("Custom Transaction", custom_payload)
