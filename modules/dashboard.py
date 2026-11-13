"""Module 1: Overview Dashboard for FinGuard AI."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from core.models import get_severity_color


def render() -> None:
    """Renders the comprehensive executive monitoring dashboard."""
    st.markdown("## 📊 Executive Overview Dashboard")
    st.caption(
        "Real-time financial crime posture, automated risk velocity trends, and prioritized compliance intelligence."
    )

    transactions_df: pd.DataFrame = st.session_state.get("transactions_df", pd.DataFrame())
    alerts = st.session_state.get("alerts", [])
    accounts_df: pd.DataFrame = st.session_state.get("accounts_df", pd.DataFrame())

    if transactions_df.empty:
        st.warning("No transaction data loaded. Please initialize or reload sample data.")
        return

    # -------------------------------------------------------------------------
    # 1. KPI Cards (6 Key Metrics Computed Directly from State)
    # -------------------------------------------------------------------------
    total_txns = len(transactions_df)
    ml_flagged = len(transactions_df[transactions_df.get("ml_probability", 0) >= 0.70])
    critical_alerts = len([a for a in alerts if a.get("severity") == "Critical"])
    high_alerts = len([a for a in alerts if a.get("severity") == "High"])
    active_flagged_accounts = len(
        set(a["account_id"] for a in alerts if a.get("status") != "Closed")
    )
    unique_typologies = len(set(a["typology"] for a in alerts))

    kpi_cols = st.columns(6)

    def render_kpi(col, label: str, val: str, subtext: str, accent_color: str = "#00D4FF"):
        col.markdown(
            f"""
            <div style="background:#131722; border:1px solid #232733; border-radius:8px; padding:12px; text-align:center; min-height:105px;">
                <div style="color:#8B8D93; font-size:11px; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">{label}</div>
                <div style="color:{accent_color}; font-size:24px; font-weight:700; margin:4px 0;">{val}</div>
                <div style="color:#6C707C; font-size:11px;">{subtext}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_kpi(kpi_cols[0], "Total Txns", f"{total_txns:,}", "Scanned volume")
    render_kpi(kpi_cols[1], "ML Flagged", f"{ml_flagged}", "Probability ≥ 70%", "#FF8C00")
    render_kpi(kpi_cols[2], "Critical Alerts", f"{critical_alerts}", "Immediate triage", "#FF4444")
    render_kpi(kpi_cols[3], "High-Risk Alerts", f"{high_alerts}", "Elevated priority", "#FF8C00")
    render_kpi(kpi_cols[4], "Flagged Accounts", f"{active_flagged_accounts}", "Active entity watch", "#FFD700")
    render_kpi(kpi_cols[5], "AML Typologies", f"{unique_typologies}", "Active ring patterns", "#00D4FF")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Main Visualizations: Dual-Axis Trend & Risk Score Donut
    # -------------------------------------------------------------------------
    chart_col1, chart_col2 = st.columns([1.6, 1.0])

    with chart_col1:
        st.markdown("##### 📈 Transaction Velocity & Mean Risk Trend")

        df_time = transactions_df.copy()
        df_time["timestamp"] = pd.to_datetime(df_time["timestamp"])
        df_time = df_time.sort_values(by="timestamp")

        # Group by 6-hour windows or date for smooth trend
        df_time["time_bin"] = df_time["timestamp"].dt.floor("6h")
        trend = (
            df_time.groupby("time_bin")
            .agg(volume=("txn_id", "count"), mean_risk=("risk_score", "mean"))
            .reset_index()
        )

        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

        # Bar: Volume
        fig_trend.add_trace(
            go.Bar(
                x=trend["time_bin"],
                y=trend["volume"],
                name="Txn Volume",
                marker_color="#00D4FF",
                opacity=0.45,
            ),
            secondary_y=False,
        )

        # Line: Mean Risk Score
        fig_trend.add_trace(
            go.Scatter(
                x=trend["time_bin"],
                y=trend["mean_risk"],
                name="Mean Risk Score",
                line=dict(color="#FF4444", width=3),
                mode="lines+markers",
            ),
            secondary_y=True,
        )

        fig_trend.update_layout(
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            margin=dict(l=10, r=10, t=25, b=10),
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#C0C4CC")),
            xaxis=dict(
                showgrid=True,
                gridcolor="#1E222D",
                tickfont=dict(color="#8B8D93", size=10),
            ),
            yaxis=dict(
                title=dict(text="Volume", font=dict(color="#00D4FF", size=11)),
                tickfont=dict(color="#8B8D93", size=10),
                showgrid=True,
                gridcolor="#1E222D",
            ),
            yaxis2=dict(
                title=dict(text="Risk (0-100)", font=dict(color="#FF4444", size=11)),
                tickfont=dict(color="#8B8D93", size=10),
                showgrid=False,
                range=[0, 100],
            ),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with chart_col2:
        st.markdown("##### 🎯 Risk Score Distribution")
        sev_counts = transactions_df["risk_severity"].value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]

        color_map = {
            "Critical": "#FF4444",
            "High": "#FF8C00",
            "Medium": "#FFD700",
            "Low": "#00C851",
        }
        fig_pie = px.pie(
            sev_counts,
            values="Count",
            names="Severity",
            hole=0.55,
            color="Severity",
            color_discrete_map=color_map,
        )
        fig_pie.update_layout(
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            margin=dict(l=10, r=10, t=25, b=10),
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="#C0C4CC")),
        )
        fig_pie.update_traces(
            textinfo="percent+label",
            textfont=dict(color="#FFFFFF", size=11),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. Intelligence Panels (Recent Critical Alerts & Highest Risk Accounts)
    # -------------------------------------------------------------------------
    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(255, 68, 68, 0.14) 0%, rgba(255, 140, 0, 0.08) 100%);
                        border: 1px solid rgba(255, 68, 68, 0.55);
                        border-left: 5px solid #FF4444;
                        border-radius: 8px;
                        padding: 14px 16px;
                        margin-bottom: 12px;
                        box-shadow: 0 0 18px rgba(255, 68, 68, 0.15);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#FF5555; font-weight:800; font-size:13px; letter-spacing:0.8px;">
                        🚨 CRITICAL & HIGH-PRIORITY ALERT WATCHLIST
                    </span>
                    <span style="background:#FF4444; color:#FFFFFF; font-size:10px; font-weight:700; padding:3px 9px; border-radius:4px; letter-spacing:0.5px;">
                        TRIAGE REQUIRED
                    </span>
                </div>
                <div style="color:#C4C8D4; font-size:11px; margin-top:4px;">
                    Entities flagged by multi-stage ML velocity anomalies and graph structuring heuristics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        filtered_alerts = [a for a in alerts if a.get("severity") in ("Critical", "High")]
        if filtered_alerts:
            alert_records = []
            for a in filtered_alerts[:5]:
                alert_records.append(
                    {
                        "Alert ID": a["alert_id"],
                        "Account": a["account_id"],
                        "Typology": a["typology"],
                        "Severity": a["severity"],
                        "Status": a["status"],
                        "Timestamp": a["timestamp"],
                    }
                )
            df_alert_view = pd.DataFrame(alert_records)
            st.dataframe(
                df_alert_view,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No critical alerts pending triage.")

    with p_col2:
        st.markdown("##### 👤 Most Suspicious Accounts (Threat Ranking)")
        # Group by sender to aggregate risk
        acc_risk = (
            transactions_df.groupby("sender_id")
            .agg(
                max_risk=("risk_score", "max"),
                total_volume=("amount", "sum"),
                txn_count=("txn_id", "count"),
            )
            .reset_index()
            .sort_values(by="max_risk", ascending=False)
            .head(5)
        )
        acc_risk.columns = ["Account ID", "Max Risk", "Total Volume (₹)", "Txn Count"]

        st.dataframe(
            acc_risk,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Volume (₹)": st.column_config.NumberColumn(format="₹%,.2f"),
                "Max Risk": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            },
        )
