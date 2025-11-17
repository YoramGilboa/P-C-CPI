# src/01_fetch_bls.py
import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("BLS_API_KEY")
HEADERS = {"Content-type": "application/json"}

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

def fetch_series(series_id, start="2010", end="2025"):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    data = {
        "seriesid": [series_id],
        "startyear": start,
        "endyear": end,
        "registrationkey": API_KEY
    }
    resp = requests.post(url, json=data, headers=HEADERS)
    json_data = resp.json()
    if json_data['status'] != 'REQUEST_SUCCEEDED':
        print(f"Error: {json_data['message']}")
        return pd.DataFrame()
    
    records = []
    for item in json_data['Results']['series'][0]['data']:
        records.append({
            'date': f"{item['year']}-{item['period'][1:]}-01",
            'value': float(item['value'])
        })
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    return df['value']

# === SAVE ALL ===
if __name__ == "__main__":
    os.makedirs("../data/raw", exist_ok=True)
    for name, sid in SERIES.items():
        print(f"Fetching {name}...")
        df = fetch_series(sid)
        df.to_csv(f"../data/raw/{name.replace(' ', '_')}.csv")
    print("Done! Raw data saved.")
    