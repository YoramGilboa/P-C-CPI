# P&C CPI Blog

A data pipeline that fetches CPI (Consumer Price Index) data from the Bureau of Labor Statistics API, processes it, and generates visualizations for a blog focused on Property & Casualty insurance-relevant inflation metrics.

## Project Structure

```
├── src/                       # Python scripts (numbered by execution order)
│   ├── 01_fetch_bls.py       # Fetches raw CPI data from BLS API
│   ├── 02_clean.py           # Placeholder for future data cleaning logic
│   ├── 03_build_index.py     # Builds weighted severity index
│   ├── 04_plot.py            # Generates Plotly visualizations + JSON export
│   └── logging_config.py     # Centralized logging configuration
├── data/
│   ├── raw/                  # Raw CSV files from BLS (gitignored)
│   ├── processed/            # Cleaned data (gitignored)
│   └── weights.csv           # Category weights for index calculation
├── blog/
│   ├── index.html            # Main blog page with actuarial methodology
│   └── assets/               # Charts, images, and severity_data.json
├── logs/                     # Pipeline log files (gitignored)
├── .github/workflows/
│   └── update.yml            # Monthly GitHub Actions automation (not currently used)
├── .env                      # BLS_API_KEY (gitignored)
└── requirements.txt          # Python dependencies (pinned versions)
```

## CPI Series Tracked

| Name        | Series ID       | Relevance                    |
|-------------|-----------------|------------------------------|
| All Items   | CUUR0000SA0     | Overall inflation benchmark  |
| Core CPI    | CUUR0000SA0L1E  | Ex food & energy             |
| Auto Repair | CUUR0000SETA    | Auto claims costs            |
| Physicians  | CUUR0000SEMC    | Medical liability            |
| Hospital    | CUUR0000SEMD    | Medical liability            |
| Shelter     | CUUR0000SAH1    | Property claims              |
| Food Away   | CUUR0000SEFV    | Workers' comp                |
| Gasoline    | CUUR0000SETB    | Auto claims                  |

## Commands

```bash
# Activate virtual environment
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Run the pipeline (from project root)
python src/01_fetch_bls.py      # Fetch CPI data from BLS
python src/03_build_index.py    # Build weighted severity index
python src/04_plot.py           # Generate charts and JSON metrics

# Note: 02_clean.py is a placeholder for future data cleaning logic
```

## Logging

All pipeline scripts use centralized logging configured in `src/logging_config.py`:
- Console output shows INFO level and above
- Log files are written to `logs/pipeline.log`
- Logs include timestamps, module names, and severity levels

## Output Files

After running the pipeline:
- `data/processed/severity_cpi.csv` - The weighted severity index
- `blog/assets/severity_vs_cpi.html` - Interactive Plotly chart
- `blog/assets/severity_vs_cpi.png` - Static chart image
- `blog/assets/severity_data.json` - Current metrics for dynamic blog display

## Environment Variables

- `BLS_API_KEY`: Bureau of Labor Statistics API key (required for data fetching)
  - Get a free key at https://www.bls.gov/developers/

## Security Notes

- Path traversal protection in `03_build_index.py` validates filenames
- Dependencies are pinned to specific versions in `requirements.txt`
- API key is stored in `.env` (gitignored)

## GitHub Actions

The `update.yml` workflow is configured but not currently active. For manual updates:
1. Run the pipeline commands above
2. Commit changes to `blog/assets/`
3. Push to deploy via GitHub Pages
