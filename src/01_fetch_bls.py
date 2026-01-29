# src/01_fetch_bls.py
"""Fetch CPI data from Bureau of Labor Statistics API."""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from logging_config import setup_logging

load_dotenv()
logger = setup_logging(__name__)

API_KEY = os.getenv("BLS_API_KEY")
HEADERS = {"Content-type": "application/json"}
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Maximum retries for transient failures
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# === P&C RELEVANT SERIES ===
SERIES = {
    "All Items": "CUUR0000SA0",
    "Core CPI": "CUUR0000SA0L1E",
    "Auto Repair": "CUUR0000SETA",
    "Physicians": "CUUR0000SEMC",
    "Hospital": "CUUR0000SEMD",
    "Shelter": "CUUR0000SAH1",
    "Food Away": "CUUR0000SEFV",
    "Gasoline": "CUUR0000SETB",
}


def validate_api_key() -> bool:
    """Check that BLS_API_KEY is set."""
    if not API_KEY:
        logger.error("BLS_API_KEY not found in environment. Set it in .env file.")
        return False
    return True


def validate_bls_response(json_data: dict) -> bool:
    """
    Validate BLS API response structure.

    Args:
        json_data: Parsed JSON response from BLS API

    Returns:
        True if response is valid, False otherwise
    """
    if not isinstance(json_data, dict):
        logger.error("Invalid response: not a JSON object")
        return False

    if "status" not in json_data:
        logger.error("Invalid response: missing 'status' field")
        return False

    if json_data["status"] != "REQUEST_SUCCEEDED":
        msg = json_data.get("message", ["Unknown error"])
        logger.error(f"BLS API error: {msg}")
        return False

    if "Results" not in json_data:
        logger.error("Invalid response: missing 'Results' field")
        return False

    if "series" not in json_data["Results"]:
        logger.error("Invalid response: missing 'series' in Results")
        return False

    if len(json_data["Results"]["series"]) == 0:
        logger.error("Invalid response: empty series array")
        return False

    if "data" not in json_data["Results"]["series"][0]:
        logger.error("Invalid response: missing 'data' in series")
        return False

    return True


def fetch_series(series_id: str, start: str = "2010", end: str = "2026") -> pd.Series:
    """
    Fetch a single CPI series from BLS API with retry logic.

    Args:
        series_id: BLS series identifier
        start: Start year (inclusive)
        end: End year (inclusive)

    Returns:
        pandas Series with date index and CPI values, or empty Series on failure
    """
    data = {
        "seriesid": [series_id],
        "startyear": start,
        "endyear": end,
        "registrationkey": API_KEY,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"Attempt {attempt}/{MAX_RETRIES} for series {series_id}")
            resp = requests.post(BLS_API_URL, json=data, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            json_data = resp.json()

            if not validate_bls_response(json_data):
                return pd.Series(dtype=float)

            records = []
            for item in json_data["Results"]["series"][0]["data"]:
                value_str = item["value"]
                if value_str == "-" or value_str == "":
                    logger.debug(f"Skipping missing value for {item['year']}-{item['period']}")
                    continue
                records.append(
                    {
                        "date": f"{item['year']}-{item['period'][1:]}-01",
                        "value": float(value_str),
                    }
                )

            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").set_index("date")
            logger.debug(f"Successfully fetched {len(df)} records for {series_id}")
            return df["value"]

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt}/{MAX_RETRIES} for {series_id}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt}/{MAX_RETRIES} for {series_id}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {series_id}: {e}")
            return pd.Series(dtype=float)
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Data parsing error for {series_id}: {e}")
            return pd.Series(dtype=float)

        if attempt < MAX_RETRIES:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)

    logger.error(f"Failed to fetch {series_id} after {MAX_RETRIES} attempts")
    return pd.Series(dtype=float)


# === MAIN ===
if __name__ == "__main__":
    logger.info("Starting BLS data fetch")

    if not validate_api_key():
        sys.exit(1)

    # Use pathlib for cross-platform paths
    script_dir = Path(__file__).parent
    raw_dir = script_dir.parent / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for name, sid in SERIES.items():
        logger.info(f"Fetching {name} ({sid})...")
        df = fetch_series(sid)
        if not df.empty:
            output_path = raw_dir / f"{name.replace(' ', '_')}.csv"
            df.to_csv(output_path)
            logger.info(f"Saved {name} -> {output_path.name}")
            success_count += 1
        else:
            logger.error(f"Failed to fetch {name}")

    logger.info(f"Completed: {success_count}/{len(SERIES)} series fetched successfully")
    if success_count < len(SERIES):
        sys.exit(1)
