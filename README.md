# Olist E-Commerce Analytics

End-to-end analytics on the [Brazilian Olist e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(~100k orders, 2016–2018): exploratory analysis and data-quality checks in
DuckDB SQL, four analysis blocks (revenue growth, cohort retention, RFM
segmentation, delivery funnel), a statistical A/B test on delivery timeliness,
and an interactive Streamlit dashboard.

## Goals

- Quantify revenue growth and its month-over-month trend.
- Measure customer retention correctly using the stable customer identifier.
- Segment customers (RFM) to find where revenue actually comes from.
- Test whether **on-time delivery drives higher review scores** — with a proper
  effect size, not just a p-value.

## Project structure

```
Olist/
├── analytics/
│   ├── raw.ipynb              # EDA, data cleaning, SQL analysis blocks, A/B test
│   ├── exports/              # pre-computed result CSVs consumed by the dashboard
│   └── olist.duckdb          # local DuckDB file (gitignored)
├── data/                     # raw Olist CSVs from Kaggle (gitignored)
├── app.py                    # Streamlit dashboard (reads analytics/exports/)
├── requirements.txt
└── README.md
```

The CSVs in `analytics/exports/` **are committed**, so the dashboard runs
anywhere (including Streamlit Cloud) without the raw dataset. The raw `data/`
CSVs and the `.duckdb` file are gitignored.

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
#    then run analytics/raw.ipynb top to bottom. It rebuilds analytics/exports/.
```

## Key findings

All numbers below are produced by `analytics/raw.ipynb` and written to
`analytics/exports/`.

### Revenue
- **Total delivered revenue: ≈ R$ 15.42M** across **96.5k delivered orders**.
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
The clear priority is retaining Champions and reactivating the equally valuable
At-Risk cohort before they churn.

### Delivery funnel & review scores
- Funnel: 99,441 purchased → 99,281 approved → 97,658 shipped → 96,476 delivered
  → **88,649 delivered on time** (≈ **91.9% on-time rate** among delivered orders).
- Late orders average **2.57 stars** vs. **4.29 stars** for on-time orders.

### A/B test — on-time vs. late delivery
Hypothesis: on-time orders receive higher review scores. Scores are ordinal
(1–5) and non-normal, so we use the **Mann-Whitney U** test and report an
effect size alongside the p-value.

| Metric | On time | Late |
|--------|--------:|-----:|
| n | 88,653 | 7,700 |
| Median review score | 5 | 2 |
| Mean review score | 4.294 | 2.566 |

- **Mann-Whitney U** (one-sided, on-time > late): **p ≈ 0** (below floating-point
  precision, < 1e-300).
- **Cliff's delta = 0.553 — a *large* effect**, 95% bootstrap CI **[0.542, 0.565]**
  (1,000 resamples).

**Conclusion:** late delivery is the single biggest *controllable* driver of low
review scores. The effect is not just statistically significant — it is large
and tightly estimated. Improving on-time delivery is the highest-leverage lever
for review quality.

## Tech stack

- **Python** — pandas, NumPy, SciPy
- **DuckDB** — in-process SQL engine (CTEs, window functions, `NTILE`, `LAG`)
- **Streamlit** + **Plotly** — interactive dashboard
- **Jupyter** — analysis notebook

## Live dashboard

🔗 **Streamlit Cloud:** _TODO — add deployment link here_

## License

For educational/portfolio use. Dataset © Olist, distributed via Kaggle.
