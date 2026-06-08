# add to test_extract.py or a new test_transform.py
from pipeline.transform import transform_assets, transform_history

print("\n--- Testing transform_assets ---")
df = transform_assets(assets)
print(df.dtypes)       # check all types are correct (float64, not object)
print(df.head())       # eyeball the data
print(f"Nulls:\n{df.isnull().sum()}")  # should be 0 in key columns