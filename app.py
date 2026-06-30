"""Olist E-Commerce Analytics: Streamlit dashboard.

Reads pre-computed result CSVs from analytics/exports/ (produced by the analysis
notebook) so the app runs anywhere without the raw dataset, including on
Streamlit Cloud. Charts use Plotly.

Visual system (kept deliberately small and reused everywhere):
  - One neutral slate-blue PRIMARY for most series.
  - Exactly two semantic colors, POSITIVE / NEGATIVE, used only for MoM
    up/down and on-time/late comparisons.
  - A single Plotly template ("plotly_white") with consistent margins/titles.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

EXPORT_DIR = Path(__file__).parent / "analytics" / "exports"

st.set_page_config(page_title="Olist Analytics", layout="wide")

# --- Color system -----------------------------------------------------------
PRIMARY = "#3D5A80"   # calm slate blue, the default for most series
POSITIVE = "#3F7D5A"  # muted green, only for MoM up / on-time
NEGATIVE = "#B4574A"  # muted brick, only for MoM down / late

# Four RFM segments, kept distinguishable within the restrained palette.
SEGMENT_COLORS = {
    "Champions": "#2E4A6B",
    "Loyal": "#6E8CAE",
    "At Risk": "#C2A05B",
    "Lost": "#9AA0A8",
}

# Single consistent Plotly look applied to every chart.
pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"


def style(fig: go.Figure) -> go.Figure:
    """Apply consistent margins, fonts, and a quiet title to a figure."""
    fig.update_layout(
        font=dict(color="#1F2933", size=13),
        title=dict(font=dict(size=16, color="#1F2933"), x=0, xanchor="left"),
        margin=dict(l=10, r=10, t=48, b=10),
        legend=dict(title_text=""),
        colorway=[PRIMARY],
    )
    return fig


@st.cache_data
def load(name: str) -> pd.DataFrame:
    """Load an export CSV, or stop the app with a clear message if it's missing."""
    path = EXPORT_DIR / name
    if not path.exists():
        st.error(
            f"Missing export file: `{name}`. "
            "Run `analytics/raw.ipynb` to regenerate `analytics/exports/`."
        )
        st.stop()
    return pd.read_csv(path)


st.title("Olist E-Commerce Analytics")
st.caption(
    "Brazilian marketplace (2016-2018). Revenue trends, retention, RFM "
    "segmentation, and how late delivery relates to review scores."
)

tab_rev, tab_rfm, tab_retention, tab_funnel, tab_ab = st.tabs(
    ["Revenue", "RFM Segments", "Retention", "Delivery Funnel", "Delivery vs. Reviews"]
)

# ----------------------------------------------------------------- Revenue tab
with tab_rev:
    rev = load("revenue_monthly.csv")
    rev["month"] = pd.to_datetime(rev["month"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total delivered GMV", f"R$ {rev['revenue'].sum():,.0f}")
    c2.metric("Total orders", f"{rev['orders'].sum():,.0f}")
    # Median, not mean: the 2016 ramp-up months (revenue near zero) produce
    # five-digit MoM percentages that make the mean meaningless.
    c3.metric("Median MoM growth", f"{rev['mom_growth_pct'].median():.1f}%")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=rev["month"], y=rev["revenue"], mode="lines+markers",
            name="Revenue", line=dict(color=PRIMARY, width=2.5),
            marker=dict(size=6),
        )
    )
    fig.update_layout(
        title="Monthly delivered revenue / GMV (BRL)",
        xaxis_title="Month", yaxis_title="Revenue (R$)", hovermode="x unified",
    )
    st.plotly_chart(style(fig), use_container_width=True)

    rev_mom = rev.dropna(subset=["mom_growth_pct"])
    mom_colors = [POSITIVE if v >= 0 else NEGATIVE for v in rev_mom["mom_growth_pct"]]
    fig_mom = px.bar(
        rev_mom, x="month", y="mom_growth_pct",
        title="Month-over-month revenue growth (%)",
        labels={"mom_growth_pct": "MoM growth (%)", "month": "Month"},
    )
    fig_mom.update_traces(marker_color=mom_colors)
    st.plotly_chart(style(fig_mom), use_container_width=True)

    with st.expander("Monthly data"):
        st.dataframe(rev, use_container_width=True)

# --------------------------------------------------------------------- RFM tab
with tab_rfm:
    seg = load("rfm_segments.csv")
    rr = load("repeat_rate.csv")
    repeat_rate = float(rr["repeat_rate_pct"].iloc[0])

    left, right = st.columns([1, 1])
    with left:
        fig_pie = px.pie(
            seg, names="segment", values="customers", hole=0.45,
            title="Customers by RFM segment",
            color="segment", color_discrete_map=SEGMENT_COLORS,
        )
        st.plotly_chart(style(fig_pie), use_container_width=True)
    with right:
        fig_rev = px.bar(
            seg.sort_values("pct_revenue"), x="pct_revenue", y="segment",
            orientation="h", title="Share of revenue by segment (%)",
            color="segment", color_discrete_map=SEGMENT_COLORS,
            labels={"pct_revenue": "Revenue share (%)", "segment": ""},
        )
        fig_rev.update_layout(showlegend=False)
        st.plotly_chart(style(fig_rev), use_container_width=True)

    st.caption(
        f"Repeat-purchase rate (by customer_unique_id): {repeat_rate:.1f}%. "
        "Olist is a single-purchase marketplace, so the segments rest on Recency "
        "and Monetary value (Frequency is about 1)."
    )
    st.dataframe(seg, use_container_width=True)

# --------------------------------------------------------------- Retention tab
with tab_retention:
    ret = load("cohort_retention.csv")
    pivot = ret.pivot(index="cohort_month", columns="month_offset",
                      values="retention_pct")
    fig_heat = px.imshow(
        pivot,
        labels=dict(x="Months since first order", y="Cohort (first-order month)",
                    color="Retention %"),
        color_continuous_scale="Blues", aspect="auto",
        title="Cohort retention (% of each cohort ordering again, by month offset)",
    )
    st.plotly_chart(style(fig_heat), use_container_width=True)
    st.caption(
        "Month 0 is 100% by definition. From month 1 onward retention sits well "
        "under 1% across every cohort, matching the ~3% overall repeat rate. "
        "Growth here comes from acquisition rather than retention."
    )
    with st.expander("Cohort data"):
        st.dataframe(ret, use_container_width=True)

# ------------------------------------------------------------------ Funnel tab
with tab_funnel:
    funnel = load("delivery_funnel.csv")
    fig_f = go.Figure(
        go.Funnel(
            y=funnel["stage"], x=funnel["orders"],
            textinfo="value+percent initial",
            marker=dict(color=PRIMARY),
        )
    )
    fig_f.update_layout(title="Order delivery funnel")
    st.plotly_chart(style(fig_f), use_container_width=True)

    late = load("delivery_late_vs_score.csv")
    c1, c2 = st.columns([1, 1])
    with c1:
        fig_late = px.bar(
            late, x="delivery_status", y="avg_review_score", color="delivery_status",
            title="Average review score: on-time vs late",
            color_discrete_map={"On time": POSITIVE, "Late": NEGATIVE},
            labels={"avg_review_score": "Avg review score", "delivery_status": ""},
            text="avg_review_score",
        )
        fig_late.update_yaxes(range=[1, 5])
        fig_late.update_layout(showlegend=False)
        st.plotly_chart(style(fig_late), use_container_width=True)
    with c2:
        st.dataframe(funnel, use_container_width=True)
        st.dataframe(late, use_container_width=True)

# ----------------------------------------------------- Delivery vs. reviews tab
with tab_ab:
    res = load("ab_test_result.csv").set_index("metric")["value"]
    dist = load("ab_test_scores.csv")

    p_value = float(res["p_value"])
    delta = float(res["cliffs_delta"])
    effect = str(res["effect_size"])
    ci_low = float(res["cliffs_delta_ci_low"])
    ci_high = float(res["cliffs_delta_ci_high"])
    median_on = float(res["median_on_time"])
    median_late = float(res["median_late"])
    # Honest p-value string (scipy underflows the true value to 0.0).
    p_display = str(res["p_value_display"]) if "p_value_display" in res.index else (
        "< 1e-300" if p_value == 0 else f"{p_value:.2e}"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Median (on time)", f"{median_on:.0f}")
    c2.metric("Median (late)", f"{median_late:.0f}")
    c3.metric("Cliff's delta", f"{delta:.3f}", help=f"Effect size: {effect}")
    c4.metric("p-value", p_display)

    verdict = "statistically significant" if (p_value < 0.05) else "not significant"
    st.markdown(
        f"On-time orders receive higher review scores. The difference is "
        f"**{verdict}** (Mann-Whitney U, p {p_display}) with a **{effect}** "
        f"effect size (Cliff's delta = {delta:.3f}, 95% CI [{ci_low:.3f}, {ci_high:.3f}])."
    )
    st.caption(
        "This is an observational comparison, not a randomized A/B test. "
        "On-time vs. late is not randomly assigned, so it measures association "
        "rather than proven causation. Lateness ties in with distance, freight, "
        "product category, and seasonality. On-time is also relative to Olist's "
        "generous estimated delivery date, and only reviewed orders are compared."
    )

    fig_dist = px.bar(
        dist, x="review_score", y="pct_within_group", color="delivery_status",
        barmode="group", title="Review score distribution by delivery status (%)",
        color_discrete_map={"On time": POSITIVE, "Late": NEGATIVE},
        labels={"pct_within_group": "% within group", "review_score": "Review score"},
    )
    st.plotly_chart(style(fig_dist), use_container_width=True)

    with st.expander("Full test results"):
        st.dataframe(res.reset_index(), use_container_width=True)
