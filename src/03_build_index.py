# src/03_build_index.py
"""Build weighted P&C Severity CPI index from raw CPI data."""

import re
import sys
from pathlib import Path

import pandas as pd

from logging_config import setup_logging

logger = setup_logging(__name__)

# Allowed filename pattern: alphanumeric, underscores, hyphens, ending in .csv
VALID_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+\.csv$")


def validate_filename(filename: str) -> bool:
    """
    Validate filename to prevent path traversal attacks.

    Args:
        filename: The filename to validate

    Returns:
        True if filename is safe, False otherwise
    """
    if not VALID_FILENAME_PATTERN.match(filename):
        logger.error(f"Invalid filename rejected: {filename}")
        return False
    return True


def validate_path_within_directory(filepath: Path, allowed_dir: Path) -> bool:
    """
    Ensure resolved path stays within the allowed directory.

    Args:
        filepath: Path to validate
        allowed_dir: Directory that must contain the file

    Returns:
        True if path is safe, False otherwise
    """
    try:
        resolved = filepath.resolve()
        allowed_resolved = allowed_dir.resolve()
        if not str(resolved).startswith(str(allowed_resolved)):
            logger.error(f"Path traversal attempt blocked: {filepath}")
            return False
        return True
    except (OSError, ValueError) as e:
        logger.error(f"Path validation error: {e}")
        return False


def load_series_data(data_dir: Path, weights_df: pd.DataFrame) -> dict:
    """
    Load all CPI series data from CSV files.

    Args:
        data_dir: Directory containing raw CSV files
        weights_df: DataFrame with series_file column

    Returns:
        Dictionary mapping filename to pandas Series
    """
    dfs = {}
    for _, row in weights_df.iterrows():
        name = row["series_file"]

        # Security: validate filename
        if not validate_filename(name):
            continue

        if name in dfs:
            continue  # Already loaded

        filepath = data_dir / name

        # Security: validate path stays within data_dir
        if not validate_path_within_directory(filepath, data_dir):
            continue

        try:
            df = pd.read_csv(filepath, parse_dates=["date"], index_col="date")
            dfs[name] = df["value"]
            logger.debug(f"Loaded {name}: {len(df)} records")
        except FileNotFoundError:
            logger.warning(f"File not found: {name}")
        except pd.errors.EmptyDataError:
            logger.warning(f"Empty file: {name}")
        except KeyError as e:
            logger.error(f"Missing column in {name}: {e}")
        except pd.errors.ParserError as e:
            logger.error(f"CSV parse error in {name}: {e}")

    return dfs


def build_severity_index(panel: pd.DataFrame, weights_df: pd.DataFrame) -> pd.Series:
    """
    Build weighted severity index from normalized CPI panel.

    Args:
        panel: DataFrame with CPI series as columns (indexed to 100)
        weights_df: DataFrame with series_file and weight columns

    Returns:
        Weighted severity index as pandas Series
    """
    severity_idx = pd.Series(0.0, index=panel.index)
    total_weight = 0.0

    for _, row in weights_df.iterrows():
        series_file = row["series_file"]
        weight = row["weight"]

        if series_file in panel.columns:
            severity_idx += weight * panel[series_file]
            total_weight += weight
            logger.debug(f"Applied weight {weight} to {series_file}")
        else:
            logger.warning(f"Series not found in panel: {series_file}")

    if abs(total_weight - 1.0) > 0.01:
        logger.warning(f"Weights sum to {total_weight:.3f}, expected ~1.0")

    return severity_idx


# === MAIN ===
if __name__ == "__main__":
    logger.info("Building P&C Severity CPI index")

    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "raw"
    processed_dir = script_dir.parent / "data" / "processed"
    weights_path = script_dir.parent / "data" / "weights.csv"

    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load weights
    try:
        weights = pd.read_csv(weights_path)
        logger.info(f"Loaded {len(weights)} weight entries")
    except FileNotFoundError:
        logger.error(f"Weights file not found: {weights_path}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse weights file: {e}")
        sys.exit(1)

    # Load all series data
    dfs = load_series_data(data_dir, weights)
    if not dfs:
        logger.error("No data files loaded successfully")
        sys.exit(1)

    logger.info(f"Loaded {len(dfs)} series files")

    # Combine into panel
    panel = pd.DataFrame(dfs)

    # Normalize to Jan 2010 = 100
    base_date = "2010-01-01"
    try:
        base = panel.loc[base_date]
        panel_indexed = panel.div(base) * 100
        logger.info(f"Normalized to base period: {base_date}")
    except KeyError:
        logger.error(f"Base date {base_date} not found in data")
        sys.exit(1)

    # Build weighted index
    severity_idx = build_severity_index(panel_indexed, weights)
    severity_idx.name = "P&C_Severity_CPI"

    # Save output
    output_path = processed_dir / "severity_cpi.csv"
    severity_idx.to_csv(output_path)
    logger.info(f"P&C Severity CPI saved -> {output_path}")

    # Log summary statistics
    latest = severity_idx.iloc[-1]
    yoy_change = ((severity_idx.iloc[-1] / severity_idx.iloc[-13]) - 1) * 100 if len(severity_idx) > 13 else 0
    logger.info(f"Latest value: {latest:.2f}, YoY change: {yoy_change:.1f}%")
