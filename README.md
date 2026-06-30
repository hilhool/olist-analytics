# Olist E-Commerce Analytics

Analytics on the [Brazilian Olist e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(~100k orders, 2016-2018). The notebook covers exploratory analysis, data-quality
checks, and four SQL analysis blocks (revenue growth, cohort retention, RFM
segmentation, delivery funnel), plus a statistical test on delivery timeliness
versus review scores. A Streamlit dashboard renders the results.

## Goals

- Track revenue growth and its month-over-month trend.
- Measure customer retention using the stable customer identifier.
- Segment customers with RFM to find where revenue comes from.
- Test whether on-time delivery is associated with higher review scores, and
  report the effect size, not only the p-value.

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

The CSVs in `analytics/exports/` are committed, so the dashboard runs on
Streamlit Cloud without the raw dataset. The `data/` CSVs stay gitignored.
DuckDB runs in-memory over those CSVs (each table is a view), so it writes no
database file.

## How to run

```bash
# 1. Environment
python -m venv .venv
.venv\Scripts\activate          # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. Launch the dashboard (uses the committed exports; no raw data needed)
streamlit run app.py

# 3. (Optional) Reproduce the full analysis
#    Download the Olist dataset from Kaggle, place the CSVs in ./data/,
#    then run the notebook (it rebuilds analytics/exports/):
jupyter lab analytics/raw.ipynb     # or: jupyter notebook analytics/raw.ipynb
```

The dashboard has five tabs: Revenue, RFM Segments, Retention (cohort heatmap),
Delivery Funnel, and Delivery vs. Reviews.

## Key findings

`analytics/raw.ipynb` produces every number below and writes it to
`analytics/exports/`.

### Revenue
- Total delivered GMV ≈ **R$ 15.42M** (gross merchandise value, price + freight)
  across **96.5k delivered orders**.
- Median month-over-month growth ≈ **7.8%**. The mean is distorted: the 2016
  ramp-up months start near zero and produce five-digit MoM percentages.
- Peak month: **November 2017** (≈ R$ 1.15M), Black Friday.

### Retention
- Of **93,358 unique customers** (`customer_unique_id`), **2,801** place a second
  order, a **repeat-purchase rate of 3.0%**.
- Olist works as a single-purchase marketplace. Cohort retention falls below 1%
  from month 1 onward.
- ⚠️ You see this only when you key on `customer_unique_id`. The dataset
  regenerates `customer_id` for each order, so keying on it forces retention to
  ~0% by construction.

### RFM segments

| Segment   | Customers | Avg. monetary | Share of revenue |
|-----------|----------:|--------------:|-----------------:|
| Champions |    24,019 |     R$ 264.63 |          **41.2%** |
| At Risk   |    21,735 |     R$ 264.36 |          **37.3%** |
| Loyal     |    23,917 |      R$ 75.51 |            11.7% |
| Lost      |    23,687 |      R$ 63.82 |             9.8% |

Champions and At Risk together (~46k customers) account for **78.5% of revenue**.
Retain Champions and reactivate the At-Risk cohort before they churn. Frequency
sits at ≈ 1 for most customers, so the segments reduce to a Recency×Monetary
grid; that is why Champions and At Risk show near-identical average spend.

### Delivery funnel & review scores
- Funnel: 99,441 purchased → 99,281 approved → 97,658 shipped → 96,476 delivered
  → **88,649 delivered on time** (≈ **91.9% on-time rate** among delivered
  orders). On-time uses Olist's own estimated delivery date, which runs generous.
- Late orders average **2.57 stars** versus **4.29 stars** for on-time orders.

### Delivery timeliness vs. review scores (statistical test)
Do on-time orders receive higher review scores? Review scores are ordinal (1-5)
and non-normal, so the test is **Mann-Whitney U**, reported with an effect size.

| Metric | On time | Late |
|--------|--------:|-----:|
| n | 88,653 | 7,700 |
| Median review score | 5 | 2 |
| Mean review score | 4.294 | 2.566 |

- Mann-Whitney U (one-sided, on-time > late): **p < 1e-300** (scipy underflows
  the exact value to 0).
- Cliff's delta = **0.553**, a large effect. 95% bootstrap CI **[0.542, 0.565]**
  over 1,000 resamples; the narrow CI reflects the large sample size.

On-time delivery is associated with higher review scores, with a large and
well-estimated effect. Delivery timeliness is the most actionable lever for
review quality.

> ⚠️ This comparison is observational, not a randomized experiment. On-time
> versus late is not randomly assigned, so the result shows association rather
> than proven causation: lateness correlates with shipping distance and region,
> freight, product category, and seasonality, and only reviewed orders enter the
> test (possible non-response bias). A causal estimate would need a
> confounder-adjusted model such as regression or difference-in-differences.

## Tech stack

- **Python**: pandas, NumPy, SciPy
- **DuckDB**: in-process SQL engine (CTEs, window functions, `NTILE`, `LAG`)
- **Streamlit** + **Plotly**: dashboard
- **Jupyter**: analysis notebook

## Live dashboard

🔗 **Streamlit Cloud:** _TODO: add deployment link here_

## License

For educational and portfolio use. Dataset © Olist, distributed via Kaggle.
