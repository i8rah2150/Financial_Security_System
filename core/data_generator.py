"""Synthetic Indian financial transaction and account data generator for FinGuard AI."""

import random
from datetime import datetime, timedelta
from typing import List

import pandas as pd

from core.models import CITIES, KYC_TIERS, PAYMENT_CHANNELS

# Pool of first and last names typical in India
FIRST_NAMES: List[str] = [
    "Rajesh",
    "Priya",
    "Amit",
    "Sneha",
    "Vikram",
    "Ananya",
    "Rohan",
    "Deepika",
    "Suresh",
    "Pooja",
    "Arjun",
    "Kavita",
    "Manish",
    "Neha",
    "Sanjay",
    "Sunita",
    "Rahul",
    "Divya",
    "Karan",
    "Meera",
    "Gaurav",
    "Ritu",
    "Alok",
    "Shweta",
]

LAST_NAMES: List[str] = [
    "Kumar",
    "Sharma",
    "Patel",
    "Verma",
    "Singh",
    "Reddy",
    "Mehta",
    "Gupta",
    "Iyer",
    "Nair",
    "Joshi",
    "Chopra",
    "Bose",
    "Das",
    "Deshmukh",
    "Rao",
    "Agarwal",
    "Pandey",
    "Bhat",
    "Kulkarni",
]


def generate_holder_name() -> str:
    """Generates a realistic Indian account holder name."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_accounts(n: int = 20) -> pd.DataFrame:
    """Generates a synthetic DataFrame of bank accounts.

    Columns: account_id, holder_name, kyc_tier, city, account_age_days, is_blocked
    """
    random.seed(42)
    accounts = []
    used_names = set()

    for i in range(1, n + 1):
        account_id = f"ACC-{1000 + i}"
        name = generate_holder_name()
        while name in used_names:
            name = generate_holder_name()
        used_names.add(name)

        # Designated specific archetypes for key demo accounts:
        # ACC-1001: Structuring hub (medium age)
        # ACC-1002: Money mule pass-through (young account)
        # ACC-1003: Smurfing accomplice
        # ACC-1004: Ring node A
        # ACC-1005: Ring node B
        # ACC-1006: Ring node C
        if i == 1:
            age = 120
            kyc = "Tier 2 - Partial KYC"
            city = "Mumbai"
        elif i == 2:
            age = 45  # young mule
            kyc = "Tier 3 - Minimal KYC"
            city = "Delhi"
        elif i in (4, 5, 6):
            age = 250
            kyc = "Tier 1 - Full KYC"
            city = "Bangalore"
        else:
            age = random.randint(30, 2000)
            kyc = random.choices(
                KYC_TIERS, weights=[0.60, 0.25, 0.15], k=1
            )[0]
            city = random.choice(CITIES)

        accounts.append(
            {
                "account_id": account_id,
                "holder_name": name,
                "kyc_tier": kyc,
                "city": city,
                "account_age_days": age,
                "is_blocked": False,
            }
        )

    return pd.DataFrame(accounts)


def generate_transactions(accounts_df: pd.DataFrame, n: int = 80) -> pd.DataFrame:
    """Generates synthetic Indian financial transactions with realistic patterns and deliberate AML anomalies.

    Includes:
    - Structuring / Smurfing: Rapid transfers just below the ₹50,000 threshold
    - Circular Fund Transfer: A -> B -> C -> A fund flow cycle
    - Fan-Out Burst: One account distributing funds to 5+ distinct accounts
    - Rapid Pass-Through / Money Mule: Fast inbound followed by immediate outbound
    - Normal retail, bill payment, and peer transfers
    """
    random.seed(42)
    account_ids = accounts_df["account_id"].tolist()
    now = datetime(2026, 11, 13, 11, 30, 0)
    txns = []
    txn_counter = 5001

    # -------------------------------------------------------------------------
    # 1. Deliberate Pattern: Structuring (Smurfing) just below ₹50,000 CTR
    # -------------------------------------------------------------------------
    # Sender ACC-1001 structuring transfers to ACC-1003 within 4 hours
    structuring_times = [
        now - timedelta(hours=4, minutes=45),
        now - timedelta(hours=3, minutes=30),
        now - timedelta(hours=2, minutes=15),
        now - timedelta(hours=1, minutes=10),
    ]
    structuring_amounts = [49500.0, 48900.0, 49200.0, 48500.0]

    for t_time, amt in zip(structuring_times, structuring_amounts):
        txns.append(
            {
                "txn_id": f"TXN-{txn_counter}",
                "timestamp": t_time,
                "sender_id": "ACC-1001",
                "receiver_id": "ACC-1003",
                "amount": amt,
                "channel": "IMPS",
                "city": "Mumbai",
            }
        )
        txn_counter += 1

    # -------------------------------------------------------------------------
    # 2. Deliberate Pattern: Circular Fund Transfer Ring (A -> B -> C -> A)
    # -------------------------------------------------------------------------
    # ACC-1004 -> ACC-1005 -> ACC-1006 -> ACC-1004
    ring_time = now - timedelta(hours=6)
    ring_hops = [
        ("ACC-1004", "ACC-1005", 280000.0, "NEFT", ring_time),
        ("ACC-1005", "ACC-1006", 275000.0, "NEFT", ring_time + timedelta(minutes=45)),
        ("ACC-1006", "ACC-1004", 270000.0, "NEFT", ring_time + timedelta(minutes=90)),
    ]
    for sender, receiver, amt, ch, t_time in ring_hops:
        txns.append(
            {
                "txn_id": f"TXN-{txn_counter}",
                "timestamp": t_time,
                "sender_id": sender,
                "receiver_id": receiver,
                "amount": amt,
                "channel": ch,
                "city": "Bangalore",
            }
        )
        txn_counter += 1

    # -------------------------------------------------------------------------
    # 3. Deliberate Pattern: Fan-Out Burst from ACC-1007 to 5 recipients
    # -------------------------------------------------------------------------
    fan_out_recipients = ["ACC-1011", "ACC-1012", "ACC-1013", "ACC-1014", "ACC-1015"]
    burst_time = now - timedelta(hours=5)
    for idx, r_id in enumerate(fan_out_recipients):
        txns.append(
            {
                "txn_id": f"TXN-{txn_counter}",
                "timestamp": burst_time + timedelta(minutes=idx * 6),
                "sender_id": "ACC-1007",
                "receiver_id": r_id,
                "amount": 35000.0 + (idx * 1500.0),
                "channel": "UPI",
                "city": "Delhi",
            }
        )
        txn_counter += 1

    # -------------------------------------------------------------------------
    # 4. Deliberate Pattern: Money Mule Rapid Pass-Through (ACC-1002, 45d old)
    # -------------------------------------------------------------------------
    mule_in_time = now - timedelta(hours=2, minutes=50)
    # Inbound large credit
    txns.append(
        {
            "txn_id": f"TXN-{txn_counter}",
            "timestamp": mule_in_time,
            "sender_id": "ACC-1008",
            "receiver_id": "ACC-1002",
            "amount": 420000.0,
            "channel": "NEFT",
            "city": "Delhi",
        }
    )
    txn_counter += 1
    # Outbound rapid wash to unvetted recipient 18 minutes later
    txns.append(
        {
            "txn_id": f"TXN-{txn_counter}",
            "timestamp": mule_in_time + timedelta(minutes=18),
            "sender_id": "ACC-1002",
            "receiver_id": "ACC-1016",
            "amount": 415000.0,
            "channel": "IMPS",
            "city": "Delhi",
        }
    )
    txn_counter += 1

    # -------------------------------------------------------------------------
    # 5. Normal Baseline Transactions (everyday amounts, UPI/IMPS/NEFT)
    # -------------------------------------------------------------------------
    num_normal = max(0, n - len(txns))
    for _ in range(num_normal):
        sender = random.choice(account_ids)
        receiver = random.choice([acc for acc in account_ids if acc != sender])

        # Power-law distribution: mostly low-value everyday payments (100 - 15,000 INR)
        # Occasionally higher business payments (25,000 - 80,000 INR)
        if random.random() < 0.75:
            amount = round(random.uniform(100.0, 12000.0), 2)
            channel = random.choices(["UPI", "Wallet", "IMPS"], weights=[0.7, 0.2, 0.1])[0]
        else:
            amount = round(random.uniform(15000.0, 85000.0), 2)
            channel = random.choices(["IMPS", "NEFT", "UPI"], weights=[0.45, 0.45, 0.10])[0]

        delta_minutes = random.randint(30, 7 * 24 * 60)
        txn_time = now - timedelta(minutes=delta_minutes)
        city = random.choice(CITIES)

        txns.append(
            {
                "txn_id": f"TXN-{txn_counter}",
                "timestamp": txn_time,
                "sender_id": sender,
                "receiver_id": receiver,
                "amount": amount,
                "channel": channel,
                "city": city,
            }
        )
        txn_counter += 1

    df = pd.DataFrame(txns)
    # Ensure sorted chronologically
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    return df
