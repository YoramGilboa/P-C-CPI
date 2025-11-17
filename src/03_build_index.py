# src/03_build_index.py
import pandas as pd
import os

# Load weights
weights = pd.read_csv("../data/weights.csv")
data_dir = "../data/raw"

# Load all series
dfs = {}
for _, row in weights.iterrows():
    name = row['series_file']
    if name not in dfs:
        try:
            df = pd.read_csv(f"{data_dir}/{name}", parse_dates=['date'], index_col='date')
            dfs[name] = df['value']
        except:
            print(f"Missing: {name}")

# Combine
panel = pd.DataFrame(dfs)

# Normalize to Jan 2010 = 100
base = panel.loc['2010-01-01']
panel_indexed = panel.div(base) * 100

# Apply weights per category
severity_idx = pd.Series(0.0, index=panel_indexed.index)
for _, row in weights.iterrows():
    series_file = row['series_file']
    w = row['weight']
    if series_file in panel_indexed.columns:
        severity_idx += w * panel_indexed[series_file]

# Save
severity_idx.name = "P&C_Severity_CPI"
severity_idx.to_csv("../data/processed/severity_cpi.csv")
print("P&C Severity CPI built → data/processed/severity_cpi.csv")
