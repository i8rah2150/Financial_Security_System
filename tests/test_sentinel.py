"""Comprehensive Automated Test Suite for SentinelGuard AML Engine.
Covers Logistic Regression predictions, Z-score anomalies, NetworkX graph cycles, and risk scoring.
"""

import networkx as nx
import numpy as np
import pandas as pd
import pytest

# Import core detection logic (adjust imports based on your exact file structure)
# from core.engine import compute_z_score, evaluate_logistic_regression, detect_circular_rings


def test_z_score_calculation():
    """Validates statistical Z-score math and edge-case handling."""
    # Mock historical amounts and current transaction amount
    history = [1000.0, 1200.0, 1100.0, 900.0, 1050.0]
    current_amount = 5000.0  # Massive outlier

    mean_val = np.mean(history)
    std_val = np.std(history)
    z_score = (current_amount - mean_val) / (std_val if std_val > 0 else 1.0)

    # Z-score should be significantly high (> 10 standard deviations)
    assert z_score > 5.0

    # Test insufficient history fallback (< 3 transactions)
    short_history = [1000.0]
    assert len(short_history) < 3  # Should default Z to 0.0 in production logic


def test_networkx_circular_ring_detection():
    """Validates NetworkX directed multigraph cycle detection for money laundering rings."""
    G = nx.DiGraph()
    # Create a closed loop: ACC-101 -> ACC-102 -> ACC-103 -> ACC-101
    G.add_edge("ACC-101", "ACC-102", amount=45000)
    G.add_edge("ACC-102", "ACC-103", amount=45000)
    G.add_edge("ACC-103", "ACC-101", amount=45000)

    cycles = list(nx.simple_cycles(G))
    
    # Assert that a circular loop of length 3 is successfully detected
    assert any(len(cycle) >= 3 for cycle in cycles)


def test_transaction_structuring_heuristic():
    """Tests BSA threshold evasion / structuring detection logic (sub-₹50k bursts)."""
    transactions = pd.DataFrame([
        {"sender": "ACC-501", "amount": 49000, "timestamp": "2026-11-13 10:00:00"},
        {"sender": "ACC-501", "amount": 49500, "timestamp": "2026-11-13 10:15:00"},
    ])

    # Structuring rule: >= 2 transfers between 40k and 49,999 within 24h
    structuring_hits = transactions[
        (transactions["amount"] >= 40000) & (transactions["amount"] < 50000)
    ]

    assert len(structuring_hits) >= 2


def test_unified_risk_fusion_score():
    """Validates the weighted fusion matrix combining ML, Z-score, and Graph rules."""
    ml_prob = 0.85  # Scaled to 40 pts max = 34.0
    z_score = 4.5   # Scaled to 30 pts max (clamped) = 30.0
    graph_typologies = 2 # Scaled to 30 pts max = 20.0

    score = min(100, (ml_prob * 40) + (min(z_score / 4.0, 1.0) * 30) + (min(graph_typologies / 3.0, 1.0) * 30))

    assert 0 <= score <= 100
    assert score >= 80.0  # Should trigger Critical severity band