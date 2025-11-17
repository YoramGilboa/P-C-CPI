# src/04_plot.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load
cpi_u = pd.read_csv("../data/raw/All_Items.csv", parse_dates=['date'], index_col='date')['value']
severity = pd.read_csv("../data/processed/severity_cpi.csv", parse_dates=['date'], index_col='date')['P&C_Severity_CPI']

# Normalize both to 2010=100
base_cpi = cpi_u['2010-01-01']
cpi_u_idx = cpi_u / base_cpi * 100

# Plot
fig = make_subplots()
fig.add_trace(go.Scatter(x=cpi_u_idx.index, y=cpi_u_idx, name="CPI-U", line=dict(color="blue")))
fig.add_trace(go.Scatter(x=severity.index, y=severity, name="P&C Severity CPI", line=dict(color="red", dash="dot")))
fig.update_layout(
    title="P&C Severity CPI vs CPI-U (2010 = 100)",
    xaxis_title="Date",
    yaxis_title="Index (2010 = 100)",
    template="plotly_white",
    height=600
)
fig.write_image("../blog/assets/severity_vs_cpi.png")
fig.write_html("../blog/assets/severity_vs_cpi.html")
print("Charts saved!")
