import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pipeline.extract import extract_assets, extract_price_history, extract_exchanges

# Test 1: assets
print("--- Testing extract_assets ---")
assets = extract_assets(limit=5)
print(f"Got {len(assets)} assets")
print("First asset:", assets[0])

# Test 2: price history
print("\n--- Testing extract_price_history ---")
history = extract_price_history("bitcoin", interval="h1")
print(f"Got {len(history)} history rows")
print("First row:", history[0])

# Test 3: exchanges
print("\n--- Testing extract_exchanges ---")
exchanges = extract_exchanges(limit=5)
print(f"Got {len(exchanges)} exchanges")
print("First exchange:", exchanges[0])

# add to test_extract.py or a new test_transform.py
from pipeline.transform import transform_assets

print("\n--- Testing transform_assets ---")
df = transform_assets(assets)
print(df.dtypes)       # check all types are correct (float64, not object)
print(df.head())       # eyeball the data
print(f"Nulls:\n{df.isnull().sum()}")  # should be 0 in key columns

# test the full round-trip
from pipeline.load import load_assets
import sqlite3, pandas as pd

load_assets(df)

# Read it back to confirm it landed correctly
conn = sqlite3.connect("data/crypto.db")
result = pd.read_sql("SELECT * FROM asset_snapshots", conn)
conn.close()

print(f"\n--- DB check ---")
print(f"Rows in DB: {len(result)}")
print(result[["name", "symbol", "price_usd", "change_pct_24h"]].head(10))