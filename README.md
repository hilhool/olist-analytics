# Olist E-Commerce Analytics

End-to-end analytics on the [Brazilian Olist e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(~100k orders, 2016–2018): exploratory analysis and data-quality checks in
DuckDB SQL, four analysis blocks (revenue growth, cohort retention, RFM
segmentation, delivery funnel), a statistical test on delivery timeliness vs.
review scores, and an interactive Streamlit dashboard.

## Goals

- Quantify revenue growth and its month-over-month trend.
- Measure customer retention correctly using the stable customer identifier.
- Segment customers (RFM) to find where revenue actually comes from.
- Test whether **on-time delivery is associated with higher review scores** —
  reporting a proper effect size, not just a p-value.

## Project structure

```
Olist/
├── analytics/
│   ├── raw.ipynb             # EDA, data cleaning, SQL analysis blocks, statistical test
│   └── exports/              # pre-computed result CSVs consumed by the dashboard
├── data/                     # raw Olist CSVs from Kaggle (gitignored)
├── app.py                    # Streamlit dashboard (reads analytics/exports/)
├── requirements.txt
└── README.md
```

The CSVs in `analytics/exports/` **are committed**, so the dashboard runs
anywhere (including Streamlit Cloud) without the raw dataset. The raw `data/`
CSVs are gitignored. DuckDB runs **in-memory** over those CSVs (every table is a
view), so no database file is created.

## How to run

```bash
# 1. Environment
python -m venv .venv
.venv\Scripts\activate          # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. Launch the dashboard (works from the committed exports — no raw data needed)
streamlit run app.py

# 3. (Optional) Reproduce the full analysis
#    Download the Olist dataset from Kaggle and place the CSVs in ./data/,
#    then run the notebook (rebuilds analytics/exports/):
jupyter lab analytics/raw.ipynb     # or: jupyter notebook analytics/raw.ipynb
```

The dashboard has five tabs: Revenue, RFM Segments, Retention (cohort heatmap),
Delivery Funnel, and Delivery vs. Reviews.

## Key findings

All numbers below are produced by `analytics/raw.ipynb` and written to
`analytics/exports/`.

### Revenue
- **Total delivered GMV: ≈ R$ 15.42M** (gross merchandise value = price +
  freight, not net/margin) across **96.5k delivered orders**.
- **Median month-over-month growth: ~7.8%** (the mean is meaningless — the 2016
  ramp-up months start from near-zero revenue and produce five-digit MoM %).
- Peak month: **November 2017 (≈ R$ 1.15M)**, driven by Black Friday.

### Retention
- Of **93,358 unique customers** (`customer_unique_id`), only **2,801** ever
  place a second order — a **repeat-purchase rate of just 3.0%**.
- Olist is effectively a **single-purchase marketplace**; cohort retention drops
  to near zero after month 0.
- ⚠️ This is only visible when keying on `customer_unique_id`. The dataset's
  `customer_id` is regenerated per order, so using it would report ~0% retention
  by construction.

### RFM segments

| Segment   | Customers | Avg. monetary | Share of revenue |
|-----------|----------:|--------------:|-----------------:|
| Champions |    24,019 |     R$ 264.63 |          **41.2%** |
| At Risk   |    21,735 |     R$ 264.36 |          **37.3%** |
| Loyal     |    23,917 |      R$ 75.51 |            11.7% |
| Lost      |    23,687 |      R$ 63.82 |             9.8% |

**Champions + At Risk (~46k high-value customers) drive ~78.5% of revenue.**
The clear priority is retaining Champions and reactivating the At-Risk cohort
before they churn. (Note: with Frequency ≈ 1 for almost everyone, segments are
effectively a Recency×Monetary grid — Champions and At-Risk have near-identical
average spend *by construction* of the cut, not as a finding.)

### Delivery funnel & review scores
- Funnel: 99,441 purchased → 99,281 approved → 97,658 shipped → 96,476 delivered
  → **88,649 delivered on time** (≈ **91.9% on-time rate** among delivered orders,
  measured against Olist's own — fairly generous — estimated delivery date).
- Late orders average **2.57 stars** vs. **4.29 stars** for on-time orders.

### Delivery timeliness vs. review scores (statistical test)
Question: do on-time orders receive higher review scores? Scores are ordinal
(1–5) and non-normal, so we use the **Mann-Whitney U** test and report an
effect size alongside the p-value.

| Metric | On time | Late |
|--------|--------:|-----:|
| n | 88,653 | 7,700 |
| Median review score | 5 | 2 |
| Mean review score | 4.294 | 2.566 |

- **Mann-Whitney U** (one-sided, on-time > late): **p < 1e-300** (scipy underflows
  the exact value to 0).
- **Cliff's delta = 0.553 — a *large* effect**, 95% bootstrap CI **[0.542, 0.565]**
  (1,000 resamples; the narrow CI reflects the large sample, not extra robustness).

**Conclusion:** on-time delivery is strongly associated with higher review
scores, with a large and precisely estimated effect — the most actionable lever
for review quality.

> ⚠️ **This is an observational comparison, not a randomized A/B test.** On-time
> vs. late is not randomly assigned, so the result is an *association*, not proven
> causation: lateness is confounded with shipping distance/region, freight,
> product category and seasonality, and only reviewed orders are compared
> (possible non-response bias). A causal estimate would require a
> confounder-adjusted model (e.g. regression / difference-in-differences).

## Tech stack

- **Python** — pandas, NumPy, SciPy
- **DuckDB** — in-process SQL engine (CTEs, window functions, `NTILE`, `LAG`)
- **Streamlit** + **Plotly** — interactive dashboard
- **Jupyter** — analysis notebook

## Live dashboard

🔗 **Streamlit Cloud:** _TODO — add deployment link here_

## License

For educational/portfolio use. Dataset © Olist, distributed via Kaggle.
