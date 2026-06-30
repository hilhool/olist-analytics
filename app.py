"""Olist E-Commerce Analytics — Streamlit dashboard.

Reads pre-computed result CSVs from analytics/exports/ (produced by the analysis
notebook) so the app runs anywhere without the raw dataset, including on
Streamlit Cloud. Charts use Plotly.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

EXPORT_DIR = Path(__file__).parent / "analytics" / "exports"

st.set_page_config(page_title="Olist Analytics", page_icon="📦", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(EXPORT_DIR / name)


# Brand-ish palette for the 4 RFM segments
SEGMENT_COLORS = {
    "Champions": "#2ca02c",
    "Loyal": "#1f77b4",
    "At Risk": "#ff7f0e",
    "Lost": "#d62728",
}

st.title("📦 Olist E-Commerce Analytics")
st.caption(
    "Brazilian marketplace (2016–2018). Revenue trends, retention, RFM "
    "segmentation, and an A/B test on how late delivery affects review scores."
)

tab_rev, tab_rfm, tab_funnel, tab_ab = st.tabs(
    ["💰 Revenue", "🎯 RFM Segments", "🚚 Delivery Funnel", "🧪 A/B Test"]
)

# ----------------------------------------------------------------- Revenue tab
with tab_rev:
    rev = load("revenue_monthly.csv")
    rev["month"] = pd.to_datetime(rev["month"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total delivered revenue", f"R$ {rev['revenue'].sum():,.0f}")
    c2.metric("Total orders", f"{rev['orders'].sum():,.0f}")
    # Median, not mean: the 2016 ramp-up months (revenue near zero) produce
    # five-digit MoM percentages that make the mean meaningless.
    c3.metric("Median MoM growth", f"{rev['mom_growth_pct'].median():.1f}%")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rev["month"], y=rev["revenue"], mode="lines+markers",
            name="Revenue", line=dict(color="#1f77b4", width=3),
        )
    )
    fig.update_layout(
        title="Monthly delivered revenue (BRL)",
        xaxis_title="Month", yaxis_title="Revenue (R$)", hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    fig_mom = px.bar(
        rev.dropna(subset=["mom_growth_pct"]), x="month", y="mom_growth_pct",
        title="Month-over-month revenue growth (%)",
        labels={"mom_growth_pct": "MoM growth (%)", "month": "Month"},
    )
    fig_mom.update_traces(
        marker_color=rev.dropna(subset=["mom_growth_pct"])["mom_growth_pct"]
        .apply(lambda v: "#2ca02c" if v >= 0 else "#d62728")
    )
    st.plotly_chart(fig_mom, use_container_width=True)

    with st.expander("Monthly data"):
        st.dataframe(rev, use_container_width=True)

# --------------------------------------------------------------------- RFM tab
with tab_rfm:
    seg = load("rfm_segments.csv")
    try:
        rr = load("repeat_rate.csv")
        repeat_rate = rr["repeat_rate_pct"].iloc[0]
    except Exception:
        repeat_rate = None

    left, right = st.columns([1, 1])
    with left:
        fig_pie = px.pie(
            seg, names="segment", values="customers", hole=0.45,
            title="Customers by RFM segment",
            color="segment", color_discrete_map=SEGMENT_COLORS,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with right:
        fig_rev = px.bar(
            seg.sort_values("pct_revenue"), x="pct_revenue", y="segment",
            orientation="h", title="Share of revenue by segment (%)",
            color="segment", color_discrete_map=SEGMENT_COLORS,
            labels={"pct_revenue": "Revenue share (%)", "segment": ""},
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    if repeat_rate is not None:
        st.info(
            f"Repeat-purchase rate (by `customer_unique_id`): **{repeat_rate}%** "
            "— Olist is an overwhelmingly single-purchase marketplace, so "
            "segments are driven mainly by Recency and Monetary value."
        )
    st.dataframe(seg, use_container_width=True)

# ------------------------------------------------------------------ Funnel tab
with tab_funnel:
    funnel = load("delivery_funnel.csv")
    fig_f = go.Figure(
        go.Funnel(
            y=funnel["stage"], x=funnel["orders"],
            textinfo="value+percent initial",
            marker=dict(color="#1f77b4"),
        )
    )
    fig_f.update_layout(title="Order delivery funnel")
    st.plotly_chart(fig_f, use_container_width=True)

    late = load("delivery_late_vs_score.csv")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig_late = px.bar(
            late, x="delivery_status", y="avg_review_score", color="delivery_status",
            title="Average review score: on-time vs late",
            color_discrete_map={"On time": "#2ca02c", "Late": "#d62728"},
            labels={"avg_review_score": "Avg review score", "delivery_status": ""},
            text="avg_review_score",
        )
        fig_late.update_yaxes(range=[1, 5])
        st.plotly_chart(fig_late, use_container_width=True)
    with c2:
        st.dataframe(funnel, use_container_width=True)
        st.dataframe(late, use_container_width=True)

# -------------------------------------------------------------------- A/B test
with tab_ab:
    res = load("ab_test_result.csv").set_index("metric")["value"]
    dist = load("ab_test_scores.csv")

    p_value = float(res["p_value"])
    delta = float(res["cliffs_delta"])
    effect = str(res["effect_size"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Median (on time)", res["median_on_time"])
    c2.metric("Median (late)", res["median_late"])
    c3.metric("Cliff's delta", f"{delta:.3f}", help=f"Effect size: {effect}")
    c4.metric("p-value", f"{p_value:.2e}")

    verdict = "statistically significant" if p_value < 0.05 else "not significant"
    st.success(
        f"On-time orders receive higher review scores — the difference is "
        f"**{verdict}** (Mann-Whitney U, p = {p_value:.2e}) with a **{effect}** "
        f"effect size (Cliff's δ = {delta:.3f}, 95% CI "
        f"[{res['cliffs_delta_ci_low']}, {res['cliffs_delta_ci_high']}])."
    )

    fig_dist = px.bar(
        dist, x="review_score", y="pct_within_group", color="delivery_status",
        barmode="group", title="Review score distribution by delivery status (%)",
        color_discrete_map={"On time": "#2ca02c", "Late": "#d62728"},
        labels={"pct_within_group": "% within group", "review_score": "Review score"},
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    with st.expander("Full test results"):
        st.dataframe(res.reset_index(), use_container_width=True)
