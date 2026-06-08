import sys
import os

# Add project root to Python path so 'pipeline' is findable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from airflow.sdk import dag, task
from datetime import datetime
import json, pandas as pd

from pipeline.extract import extract_assets, extract_price_history
from pipeline.transform import transform_assets, transform_history
from pipeline.load import load_assets, load_history

COINS = ["bitcoin", "ethereum", "solana"]

@dag(
    schedule="*/10 * * * *",       # every 10 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay_seconds": 30},
    tags=["crypto", "coincap"],
)

def coincap_pipeline():

    # ── Pipeline 1: Asset snapshot ────────────────
    @task()
    def extract_assets_task():
        return json.dumps(extract_assets(limit=50))

    @task()
    def transform_assets_task(raw):
        df = transform_assets(json.loads(raw))
        return df.to_json()

    @task()
    def load_assets_task(clean):
        load_assets(pd.read_json(clean))

    # ── Pipeline 2: Price history (3 coins) ───────
    @task()
    def extract_history_task():
        # runs every 10 min but only on the first run of each hour
        rows = []
        for coin in COINS:
            rows.extend(extract_price_history(coin, interval="h1"))
        return json.dumps(rows)
    
    @task()
    def transform_history_task(raw):
        return transform_history(json.loads(raw)).to_json()

    @task()
    def load_history_task(clean):
        load_history(pd.read_json(clean))

    # ── Wire tasks together ───────────────────────
    load_assets_task(transform_assets_task(extract_assets_task()))
    load_history_task(transform_history_task(extract_history_task()))

coincap_pipeline()