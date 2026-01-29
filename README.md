# P&C Severity CPI

[![Monthly CPI Update](https://github.com/YoramGilboa/p-c-cpi-blog/actions/workflows/update.yml/badge.svg)](https://github.com/YoramGilboa/p-c-cpi-blog/actions/workflows/update.yml)
[![Data: BLS](https://img.shields.io/badge/Data-Bureau%20of%20Labor%20Statistics-blue)](https://www.bls.gov/developers/)

A claims-weighted CPI index for Property & Casualty insurance actuaries. This project reweights Bureau of Labor Statistics CPI components to better approximate the inflation experienced in P&C claims payments.

## Current Metrics

| Metric | Value |
|--------|-------|
| P&C Severity CPI | **155.3** |
| YoY Change | +3.2% |
| CPI-U Index | 149.5 |
| Gap vs CPI-U | +5.7 points |

*Last updated: 2025-12-01*

## Why a Custom Index?

The standard CPI-U basket significantly underweights cost components that drive P&C claims severity:

- CPI-U assigns only ~6% to medical care, while bodily injury claims can be 30-50% of auto liability losses
- Shelter receives ~33% in CPI-U but may not reflect specific materials and labor in property claims
- Auto repair, hospital costs, and physician fees are underrepresented relative to claims exposure

This index provides a more accurate inflation benchmark for loss trending and rate adequacy analysis.

## Index Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Auto Repair | 20% | Parts, labor, glass, paint for auto PD and collision claims |
| Physicians | 15% | Medical evaluations, IMEs, treatment costs in BI claims |
| Hospital | 15% | Inpatient costs for severe bodily injury claims |
| Shelter | 20% | Proxy for construction/rebuild costs (lumber, labor, materials) |
| Core CPI (Wages) | 15% | Legal fees, adjusters, administrative costs |
| Core CPI (General) | 15% | Residual services, general inflation exposure |

Weights can be customized in `data/weights.csv` for specific portfolios.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YoramGilboa/p-c-cpi-blog
cd p-c-cpi-blog

# Create virtual environment
python -m venv .venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Set up BLS API key (get one free at https://www.bls.gov/developers/)
echo "BLS_API_KEY=your_key_here" > .env

# Run the pipeline
python src/01_fetch_bls.py      # Fetch CPI data from BLS
python src/03_build_index.py    # Build weighted severity index
python src/04_plot.py           # Generate charts and JSON metrics
```

## Project Structure

```
p-c-cpi-blog/
├── src/                       # Python scripts (numbered by execution order)
│   ├── 01_fetch_bls.py       # Fetches raw CPI data from BLS API
│   ├── 02_clean.py           # Placeholder for future data cleaning
│   ├── 03_build_index.py     # Builds weighted severity index
│   ├── 04_plot.py            # Generates Plotly visualizations
│   └── logging_config.py     # Centralized logging configuration
├── data/
│   ├── raw/                  # Raw CSV files from BLS (gitignored)
│   ├── processed/            # Cleaned data (gitignored)
│   └── weights.csv           # Category weights for index calculation
├── blog/
│   ├── index.html            # Main blog page with methodology
│   └── assets/               # Charts and severity_data.json
├── .github/workflows/
│   └── update.yml            # Monthly GitHub Actions automation
└── requirements.txt          # Python dependencies
```

## Automation

The workflow runs automatically on the 15th of each month (aligned with BLS data releases):

1. Fetches latest CPI data from BLS API
2. Rebuilds the weighted severity index
3. Generates updated charts and metrics
4. Commits changes and deploys to GitHub Pages

You can also trigger updates manually from the Actions tab.

## Methodology

Full methodology documentation is available on the [blog page](https://yoramgilboa.github.io/p-c-cpi-blog/), including:

- Index formula and calculation details
- Base period selection rationale
- Line of business applications
- Interpretation guidelines

## Data Source

All CPI data comes from the [Bureau of Labor Statistics API v2](https://www.bls.gov/developers/). Data is seasonally unadjusted to avoid BLS seasonal adjustment methodology potentially masking P&C-relevant patterns.

## Important Caveats

This index does not capture:
- Social inflation and litigation trends
- Regulatory or fee schedule changes
- Claim frequency shifts
- Regional variation

Always supplement with loss development analysis and market-specific data. Consult qualified actuaries for rate filing decisions.
