"""Data models, constants, and schema definitions for FinGuard AI."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Supported Indian metropolitan and financial hubs
CITIES: List[str] = [
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
]

# Expanded payment rails & settlement channels
PAYMENT_CHANNELS: List[str] = [
    "UPI",
    "Money Transfer",
    "Crypto",
    "Card Swipe",
    "IMPS",
    "NEFT",
    "Wallet",
]

# Regulatory KYC tiers
KYC_TIERS: List[str] = [
    "Tier 1 - Full KYC",
    "Tier 2 - Partial KYC",
    "Tier 3 - Minimal KYC",
]

# Risk severity thresholds
RISK_SEVERITY_THRESHOLDS = {
    "Critical": 80.0,
    "High": 60.0,
    "Medium": 40.0,
    "Low": 0.0,
}

# Investigation lifecycle statuses
ALERT_STATUSES: List[str] = [
    "New",
    "Investigating",
    "Investigated",
    "Escalated",
    "Closed",
]

# Known AML crime typologies
AML_TYPOLOGIES: List[str] = [
    "Circular Fund Transfer",
    "Structuring / Smurfing",
    "Money Mule Network",
    "Fan-In Pattern",
    "Fan-Out Pattern",
    "Rapid Pass-Through",
]


def get_risk_severity(score: float) -> str:
    """Maps a 0-100 numerical risk score to its corresponding risk severity band."""
    if score >= RISK_SEVERITY_THRESHOLDS["Critical"]:
        return "Critical"
    elif score >= RISK_SEVERITY_THRESHOLDS["High"]:
        return "High"
    elif score >= RISK_SEVERITY_THRESHOLDS["Medium"]:
        return "Medium"
    else:
        return "Low"


def get_severity_color(severity: str) -> str:
    """Returns the standardized hex color code for a given risk severity level."""
    color_map = {
        "Critical": "#FF4444",
        "High": "#FF8C00",
        "Medium": "#FFD700",
        "Low": "#00C851",
    }
    return color_map.get(severity, "#888888")


@dataclass
class Account:
    """Representation of an account entity in the system."""

    account_id: str
    holder_name: str
    kyc_tier: str
    city: str
    account_age_days: int
    is_blocked: bool = False
    created_at: Optional[datetime] = None


@dataclass
class Transaction:
    """Representation of a financial transaction record."""

    txn_id: str
    timestamp: datetime
    sender_id: str
    receiver_id: str
    amount: float
    channel: str
    city: str
    ml_probability: float = 0.0
    zscore: float = 0.0
    aml_patterns: str = ""
    risk_score: float = 0.0
    risk_severity: str = "Low"
    explanation: str = ""


@dataclass
class Alert:
    """Representation of a compliance security alert."""

    alert_id: str
    timestamp: str
    account_id: str
    txn_id: str
    severity: str
    typology: str
    status: str = "New"
    evidence: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""


@dataclass
class AuditLogEntry:
    """Audit trail record for investigator actions."""

    event_id: str
    timestamp: str
    target_ref: str
    action: str
    previous_status: str
    new_status: str
    notes: str = ""
