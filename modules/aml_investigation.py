"""Module 3: AML Investigation / Clean Graph View for SentinelGuard."""

from typing import Dict, List, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.models import get_risk_severity, get_severity_color


def render() -> None:
    """Renders the streamlined AML relationship visualizer and topology pattern forensics."""
    st.markdown("## 🕸️ AML Topology & Capital Flow Forensics")
    st.caption(
        "Simplified visual intelligence mapping fund flows, circular laundering rings, and money mule networks."
    )

    transactions_df: pd.DataFrame = st.session_state.get("transactions_df", pd.DataFrame())
    accounts_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())

    if transactions_df.empty:
        st.warning("No transactions loaded to build relationship maps.")
        return

    # -------------------------------------------------------------------------
    # 1. Build Account Statistics & Graph Structure
    # -------------------------------------------------------------------------
    G = nx.DiGraph()
    account_stats = {}

    for _, row in transactions_df.iterrows():
        s = str(row["sender_id"])
        r = str(row["receiver_id"])
        amt = float(row["amount"])
        risk = float(row.get("risk_score", 0.0))

        for acc in (s, r):
            if acc not in account_stats:
                account_stats[acc] = {"max_risk": 0.0, "volume": 0.0, "in_deg": 0, "out_deg": 0}
            account_stats[acc]["max_risk"] = max(account_stats[acc]["max_risk"], risk)
            account_stats[acc]["volume"] += amt

        account_stats[s]["out_deg"] += 1
        account_stats[r]["in_deg"] += 1

        if G.has_edge(s, r):
            G[s][r]["weight"] += amt
            G[s][r]["count"] += 1
            G[s][r]["max_risk"] = max(G[s][r]["max_risk"], risk)
        else:
            G.add_edge(s, r, weight=amt, count=1, max_risk=risk)

    for acc_id, stats in account_stats.items():
        G.add_node(acc_id, **stats)

    # -------------------------------------------------------------------------
    # 2. Visualization Mode Selector (Clean Sankey Flow vs. Focal Threat Graph)
    # -------------------------------------------------------------------------
    viz_mode = st.radio(
        "VISUALIZATION VIEW",
        ["🌊 Capital Flow Pathway (Sankey)", "🎯 Focal Threat Topology (Flagged Entities Only)"],
        horizontal=True,
    )

    if viz_mode == "🌊 Capital Flow Pathway (Sankey)":
        # Aggregate flows between senders and receivers, focusing on top / high-risk flows
        flow_df = (
            transactions_df.groupby(["sender_id", "receiver_id"])
            .agg(
                total_amount=("amount", "sum"),
                max_risk=("risk_score", "max"),
                count=("txn_id", "count"),
            )
            .reset_index()
            .sort_values(by="max_risk", ascending=False)
            .head(25)  # Focus on top 25 flows for clean visibility
        )

        all_entities = list(set(flow_df["sender_id"].tolist() + flow_df["receiver_id"].tolist()))
        entity_to_idx = {entity: idx for idx, entity in enumerate(all_entities)}

        node_colors = []
        for entity in all_entities:
            risk = account_stats.get(entity, {}).get("max_risk", 0.0)
            sev = get_risk_severity(risk)
            node_colors.append(get_severity_color(sev))

        sources = [entity_to_idx[s] for s in flow_df["sender_id"]]
        targets = [entity_to_idx[r] for r in flow_df["receiver_id"]]
        values = flow_df["total_amount"].tolist()

        link_colors = []
        for _, row in flow_df.iterrows():
            sev = get_risk_severity(row["max_risk"])
            if sev == "Critical":
                link_colors.append("rgba(255, 68, 68, 0.45)")
            elif sev == "High":
                link_colors.append("rgba(255, 140, 0, 0.40)")
            elif sev == "Medium":
                link_colors.append("rgba(255, 215, 0, 0.25)")
            else:
                link_colors.append("rgba(0, 200, 81, 0.20)")

        fig_sankey = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=20,
                        thickness=18,
                        line=dict(color="#0E1117", width=1.5),
                        label=all_entities,
                        color=node_colors,
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                        color=link_colors,
                    ),
                )
            ]
        )
        fig_sankey.update_layout(
            title=dict(
                text="Top Directional Capital Flows (Ribbons Colored by Severity)",
                font=dict(color="#E2E4E9", size=13),
            ),
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            height=460,
            margin=dict(l=15, r=15, t=35, b=15),
            font=dict(color="#E2E4E9", size=11),
        )
        st.plotly_chart(fig_sankey, use_container_width=True)

    else:
        # Focal Threat Topology: Show only flagged entities (Risk >= 60) and their direct connections
        flagged_nodes = [
            node for node, stats in account_stats.items() if stats["max_risk"] >= 60.0
        ]
        sub_nodes = set(flagged_nodes)
        for node in flagged_nodes:
            sub_nodes.update(G.predecessors(node))
            sub_nodes.update(G.successors(node))

        sub_G = G.subgraph(list(sub_nodes))
        pos = nx.circular_layout(sub_G) if len(sub_nodes) <= 12 else nx.spring_layout(sub_G, seed=42, k=0.8)

        edge_x, edge_y = [], []
        for u, v in sub_G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1.5, color="rgba(0, 212, 255, 0.40)"),
            hoverinfo="none",
            mode="lines",
        )

        node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
        for node in sub_G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            stats = account_stats[node]
            sev = get_risk_severity(stats["max_risk"])
            color = get_severity_color(sev)

            acc_row = accounts_df[accounts_df["account_id"] == node]
            holder = acc_row.iloc[0]["holder_name"] if not acc_row.empty else "Entity"

            node_colors.append(color)
            node_sizes.append(26 if stats["max_risk"] >= 80 else 18)
            node_text.append(f"<b>{node}</b> ({holder})<br>Risk: {stats['max_risk']:.1f} [{sev}]")

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=list(sub_G.nodes()),
            textposition="top center",
            textfont=dict(size=10, color="#FFFFFF"),
            hoverinfo="text",
            hovertext=node_text,
            marker=dict(color=node_colors, size=node_sizes, line=dict(color="#0E1117", width=2)),
        )

        fig_graph = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text="Filtered Threat Cluster Topology (Nodes Colored by Risk)",
                    font=dict(color="#E2E4E9", size=13),
                ),
                showlegend=False,
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=460,
                margin=dict(l=15, r=15, t=35, b=15),
            ),
        )
        st.plotly_chart(fig_graph, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. Topology Patterns Detected (Bug-Free, Robust Logic)
    # -------------------------------------------------------------------------
    p_col1, p_col2 = st.columns([1.2, 1.3])

    with p_col1:
        st.markdown("### 🚨 Topology Patterns Detected")

        # 1. Circular Laundering Rings: Check for true cycles with length >= 3
        detected_rings = []
        try:
            # Look for simple cycles of length >= 3
            all_cycles = list(nx.simple_cycles(G))
            for c in all_cycles:
                if len(c) >= 3:
                    detected_rings.append(c)
        except Exception:
            detected_rings = []

        if detected_rings:
            for ring in detected_rings[:3]:
                ring_path = " ➔ ".join(ring + [ring[0]])
                st.markdown(
                    f"""
                    <div style="background:rgba(255, 68, 68, 0.12); border-left:4px solid #FF4444; padding:10px 14px; border-radius:4px; margin-bottom:8px;">
                        <span style="color:#FF4444; font-weight:700; font-size:12px;">🔄 CIRCULAR WASH RING DETECTED</span><br/>
                        <code style="color:#FFFFFF; font-size:12px;">{ring_path}</code>
                        <div style="color:#A0A4B0; font-size:11px; margin-top:4px;">Layered circular transfer loop detected across {len(ring)} accounts.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("✅ No closed circular laundering rings identified in active ledger.")

        # 2. Structuring Hubs
        pattern_col = transactions_df["aml_patterns"].astype(str)
        structuring_df = transactions_df[pattern_col.str.contains("Structuring", case=False, na=False)]

        if not structuring_df.empty:
            hubs = structuring_df["sender_id"].unique().tolist()
            for hub in hubs:
                hub_txns = structuring_df[structuring_df["sender_id"] == hub]
                hub_vol = hub_txns["amount"].sum()
                st.markdown(
                    f"""
                    <div style="background:rgba(255, 140, 0, 0.12); border-left:4px solid #FF8C00; padding:10px 14px; border-radius:4px; margin-bottom:8px;">
                        <span style="color:#FFAA33; font-weight:700; font-size:12px;">📉 STRUCTURING / SMURFING HUB: <code>{hub}</code></span><br/>
                        <span style="color:#E2E4E9; font-size:12px;">Total Structured Volume: <strong>₹{hub_vol:,.2f}</strong> ({len(hub_txns)} transfers just below ₹50,000 CTR threshold)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # 3. Money Mule Pass-Through Nodes
        mule_df = transactions_df[pattern_col.str.contains("Money Mule|Pass-Through", case=False, na=False)]
        if not mule_df.empty:
            mule_senders = mule_df["sender_id"].unique().tolist()
            for mule in mule_senders:
                m_txns = mule_df[mule_df["sender_id"] == mule]
                m_vol = m_txns["amount"].sum()
                st.markdown(
                    f"""
                    <div style="background:rgba(255, 68, 68, 0.12); border-left:4px solid #FF4444; padding:10px 14px; border-radius:4px; margin-bottom:8px;">
                        <span style="color:#FF5555; font-weight:700; font-size:12px;">🐎 MONEY MULE PASS-THROUGH CONDUIT: <code>{mule}</code></span><br/>
                        <span style="color:#E2E4E9; font-size:12px;">Rapid inbound credit washed to unvetted outbound target (Volume: ₹{m_vol:,.2f})</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -------------------------------------------------------------------------
    # 4. Interactive Node Forensic Inspector
    # -------------------------------------------------------------------------
    with p_col2:
        st.markdown("### 👤 Entity Flow Forensic Inspector")
        all_accounts = sorted(list(account_stats.keys()))
        selected_node = st.selectbox("Select Account Entity to Inspect", options=all_accounts)

        if selected_node:
            stats = account_stats[selected_node]
            acc_data = accounts_df[accounts_df["account_id"] == selected_node]

            name = acc_data.iloc[0]["holder_name"] if not acc_data.empty else "N/A"
            kyc = acc_data.iloc[0]["kyc_tier"] if not acc_data.empty else "N/A"
            city = acc_data.iloc[0]["city"] if not acc_data.empty else "N/A"
            is_blocked = acc_data.iloc[0]["is_blocked"] if not acc_data.empty else False

            nd1, nd2, nd3 = st.columns(3)
            nd1.metric("Max Risk", f"{stats['max_risk']:.1f}/100", get_risk_severity(stats["max_risk"]))
            nd2.metric("Total Capital Flow", f"₹{stats['volume']:,.2f}")
            nd3.metric("Counterparties", f"{G.degree(selected_node)}")

            st.write(f"**Holder:** {name} | **City:** {city} | **KYC:** {kyc}")
            if is_blocked:
                st.error("🚫 STATUS: ACCOUNT CURRENTLY BLOCKED")

            in_edges = list(G.in_edges(selected_node, data=True))
            out_edges = list(G.out_edges(selected_node, data=True))

            in_summary = [f"{u} (₹{d['weight']:,.2f})" for u, _, d in in_edges]
            out_summary = [f"{v} (₹{d['weight']:,.2f})" for _, v, d in out_edges]

            st.markdown(
                f"""
                <div style="background:#131722; border:1px solid #232733; padding:12px 14px; border-radius:6px; font-size:12px; margin-top:8px;">
                    <div><strong>Inbound Sources ({len(in_edges)}):</strong> {', '.join(in_summary) if in_summary else 'None'}</div>
                    <div style="margin-top:6px;"><strong>Outbound Targets ({len(out_edges)}):</strong> {', '.join(out_summary) if out_summary else 'None'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
