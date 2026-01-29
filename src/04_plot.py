# src/04_plot.py
"""Generate visualizations and export data for the P&C CPI blog."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from logging_config import setup_logging

logger = setup_logging(__name__)


def load_data(raw_dir: Path, processed_dir: Path) -> tuple:
    """
    Load CPI-U and severity index data.

    Args:
        raw_dir: Directory containing raw CPI data
        processed_dir: Directory containing processed severity index

    Returns:
        Tuple of (cpi_u Series, severity Series)

    Raises:
        FileNotFoundError: If required files are missing
        KeyError: If expected columns are missing
    """
    cpi_path = raw_dir / "All_Items.csv"
    severity_path = processed_dir / "severity_cpi.csv"

    logger.info(f"Loading CPI-U from {cpi_path}")
    cpi_u = pd.read_csv(cpi_path, parse_dates=["date"], index_col="date")["value"]

    logger.info(f"Loading severity index from {severity_path}")
    severity = pd.read_csv(severity_path, parse_dates=["date"], index_col="date")[
        "P&C_Severity_CPI"
    ]

    return cpi_u, severity


def create_comparison_chart(cpi_u_idx: pd.Series, severity: pd.Series) -> go.Figure:
    """
    Create interactive comparison chart of CPI-U vs P&C Severity CPI.

    Args:
        cpi_u_idx: Normalized CPI-U series (2010=100)
        severity: P&C Severity CPI series

    Returns:
        Plotly Figure object
    """
    fig = make_subplots()

    fig.add_trace(
        go.Scatter(
            x=cpi_u_idx.index,
            y=cpi_u_idx,
            name="CPI-U (All Items)",
            line=dict(color="#2563eb", width=2),
            hovertemplate="CPI-U: %{y:.1f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=severity.index,
            y=severity,
            name="P&C Severity CPI",
            line=dict(color="#dc2626", width=2, dash="dot"),
            hovertemplate="P&C Severity: %{y:.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="P&C Severity CPI vs CPI-U (2010 = 100)",
            font=dict(size=20),
        ),
        xaxis_title="Date",
        yaxis_title="Index (Jan 2010 = 100)",
        template="plotly_white",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        margin=dict(l=60, r=40, t=80, b=60),
    )

    return fig


def export_metrics_json(severity: pd.Series, cpi_u_idx: pd.Series, output_path: Path):
    """
    Export current metrics as JSON for dynamic blog display.

    Args:
        severity: P&C Severity CPI series
        cpi_u_idx: Normalized CPI-U series
        output_path: Path to save JSON file
    """
    latest_date = severity.index[-1]
    latest_severity = severity.iloc[-1]
    latest_cpi = cpi_u_idx.iloc[-1]

    # Calculate YoY change (12 months back)
    if len(severity) > 12:
        yoy_severity = ((severity.iloc[-1] / severity.iloc[-13]) - 1) * 100
        yoy_cpi = ((cpi_u_idx.iloc[-1] / cpi_u_idx.iloc[-13]) - 1) * 100
    else:
        yoy_severity = 0.0
        yoy_cpi = 0.0

    # Gap between P&C and CPI-U
    gap = latest_severity - latest_cpi

    metrics = {
        "current_severity": round(latest_severity, 1),
        "current_cpi": round(latest_cpi, 1),
        "yoy_severity_change": round(yoy_severity, 1),
        "yoy_cpi_change": round(yoy_cpi, 1),
        "gap": round(gap, 1),
        "last_date": latest_date.strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics exported to {output_path}")
    logger.info(
        f"Current: Severity={latest_severity:.1f}, CPI-U={latest_cpi:.1f}, Gap={gap:.1f}"
    )


# === MAIN ===
if __name__ == "__main__":
    logger.info("Generating P&C CPI visualizations")

    script_dir = Path(__file__).parent
    raw_dir = script_dir.parent / "data" / "raw"
    processed_dir = script_dir.parent / "data" / "processed"
    assets_dir = script_dir.parent / "blog" / "assets"

    # Ensure assets directory exists
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        cpi_u, severity = load_data(raw_dir, processed_dir)
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Missing expected column in data: {e}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse CSV file: {e}")
        sys.exit(1)

    logger.info(f"Loaded data: {len(cpi_u)} CPI-U records, {len(severity)} severity records")

    # Normalize CPI-U to 2010=100
    base_date = "2010-01-01"
    try:
        base_cpi = cpi_u[base_date]
        cpi_u_idx = cpi_u / base_cpi * 100
    except KeyError:
        logger.error(f"Base date {base_date} not found in CPI-U data")
        sys.exit(1)

    # Create chart
    fig = create_comparison_chart(cpi_u_idx, severity)

    # Save outputs
    try:
        png_path = assets_dir / "severity_vs_cpi.png"
        fig.write_image(str(png_path))
        logger.info(f"Saved PNG chart -> {png_path}")
    except Exception as e:
        logger.error(f"Failed to save PNG (is kaleido installed?): {e}")

    try:
        html_path = assets_dir / "severity_vs_cpi.html"
        fig.write_html(str(html_path), include_plotlyjs="cdn")
        logger.info(f"Saved HTML chart -> {html_path}")
    except Exception as e:
        logger.error(f"Failed to save HTML: {e}")
        sys.exit(1)

    # Export metrics JSON
    try:
        json_path = assets_dir / "severity_data.json"
        export_metrics_json(severity, cpi_u_idx, json_path)
    except Exception as e:
        logger.error(f"Failed to export metrics JSON: {e}")
        sys.exit(1)

    logger.info("Chart generation complete")
