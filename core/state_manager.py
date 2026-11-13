"""Session state manager, audit logger, and centralized state transitions for FinGuard AI."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from core.data_generator import generate_accounts, generate_transactions
from core.detection_engine import DetectionEngine


def init_session_state() -> None:
    """Initializes all shared application state keys in st.session_state if not already present."""
    if "detection_engine" not in st.session_state:
        st.session_state.detection_engine = DetectionEngine()

    if "accounts_df" not in st.session_state:
        st.session_state.accounts_df = generate_accounts(20)

    if "transactions_df" not in st.session_state:
        # Generate initial transaction ledger and score through pipeline
        raw_txns = generate_transactions(st.session_state.accounts_df, 80)
        scored_txns = st.session_state.detection_engine.run_pipeline(
            raw_txns, st.session_state.accounts_df
        )
        st.session_state.transactions_df = scored_txns

    if "alerts" not in st.session_state:
        st.session_state.alerts = st.session_state.detection_engine.generate_alerts(
            st.session_state.transactions_df, st.session_state.accounts_df
        )

    if "audit_log" not in st.session_state:
        st.session_state.audit_log = [
            {
                "event_id": "EVT-1001",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_ref": "SYSTEM",
                "action": "System Initialized",
                "previous_status": "OFFLINE",
                "new_status": "ONLINE",
                "notes": "Detection engine baseline calibrated with 20 accounts and 80 transactions.",
            }
        ]

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Overview Dashboard"

    if "selected_account_id" not in st.session_state:
        st.session_state.selected_account_id = "ACC-1001"

    if "selected_txn_id" not in st.session_state:
        st.session_state.selected_txn_id = None

    if "selected_alert_id" not in st.session_state:
        st.session_state.selected_alert_id = None


def log_audit_event(
    target_ref: str,
    action: str,
    previous_status: str,
    new_status: str,
    notes: str = "",
) -> None:
    """Records an immutable audit event in the investigator audit trail."""
    log_list = st.session_state.get("audit_log", [])
    event_id = f"EVT-{1001 + len(log_list)}"
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "event_id": event_id,
        "timestamp": timestamp_str,
        "target_ref": target_ref,
        "action": action,
        "previous_status": previous_status,
        "new_status": new_status,
        "notes": notes,
    }
    log_list.append(entry)
    st.session_state.audit_log = log_list


def update_alert_status(alert_id: str, new_status: str, notes: str = "") -> bool:
    """Updates the investigation lifecycle status of a specific security alert."""
    alerts: List[Dict[str, Any]] = st.session_state.get("alerts", [])
    for alert in alerts:
        if alert["alert_id"] == alert_id:
            old_status = alert.get("status", "New")
            alert["status"] = new_status
            log_audit_event(
                target_ref=alert_id,
                action="Alert Status Update",
                previous_status=old_status,
                new_status=new_status,
                notes=notes or f"Updated status to {new_status}",
            )
            st.session_state.alerts = alerts
            return True
    return False


def block_account(account_id: str, reason: str = "Suspected AML/Fraud Activity") -> bool:
    """Sets the simulated block status on an account and logs the enforcement action."""
    acc_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())
    if acc_df.empty or "account_id" not in acc_df.columns:
        return False

    idx = acc_df[acc_df["account_id"] == account_id].index
    if not idx.empty:
        acc_df.loc[idx, "is_blocked"] = True
        st.session_state.accounts_df = acc_df
        log_audit_event(
            target_ref=account_id,
            action="Account Enforcement: Blocked",
            previous_status="Active",
            new_status="Blocked",
            notes=reason,
        )
        return True
    return False


def unblock_account(account_id: str, reason: str = "Compliance Review Cleared") -> bool:
    """Restores an account to active status after investigator clearance."""
    acc_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())
    if acc_df.empty or "account_id" not in acc_df.columns:
        return False

    idx = acc_df[acc_df["account_id"] == account_id].index
    if not idx.empty:
        acc_df.loc[idx, "is_blocked"] = False
        st.session_state.accounts_df = acc_df
        log_audit_event(
            target_ref=account_id,
            action="Account Enforcement: Unblocked",
            previous_status="Blocked",
            new_status="Active",
            notes=reason,
        )
        return True
    return False


def reload_sample_data() -> None:
    """Reloads baseline demonstration data and re-calibrates the detection engine."""
    engine = DetectionEngine()
    accounts = generate_accounts(20)
    raw_txns = generate_transactions(accounts, 80)
    scored = engine.run_pipeline(raw_txns, accounts)
    alerts = engine.generate_alerts(scored, accounts)

    st.session_state.detection_engine = engine
    st.session_state.accounts_df = accounts
    st.session_state.transactions_df = scored
    st.session_state.alerts = alerts

    log_audit_event(
        target_ref="SYSTEM",
        action="Sample Data Reload",
        previous_status="ACTIVE",
        new_status="RESET",
        notes="Reset all transaction records, account profiles, and alert queues to demo baseline.",
    )
