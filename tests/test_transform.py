import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from pipeline.transform import transform_assets, transform_history


# ── transform_assets ─────────────────────────────────────────

class TestTransformAssets:

    def test_returns_dataframe(self, sample_assets_raw):
        df = transform_assets(sample_assets_raw)
        assert isinstance(df, pd.DataFrame)

    def test_numeric_columns_are_float(self, sample_assets_raw):
        df = transform_assets(sample_assets_raw)
        for col in ["price_usd", "market_cap_usd", "volume_usd_24h"]:
            # assert is_numeric_dtype rather than the exact float64 string, which accepts both int64 and float64
            assert pd.api.types.is_numeric_dtype(df["market_cap_usd"]), \
                f"market_cap_usd should be numeric, instead got {df['market_cap_usd'].dtype}"

    def test_rank_is_integer(self, sample_assets_raw):
        df = transform_assets(sample_assets_raw)
        assert pd.api.types.is_integer_dtype(df["rank"])
    
    def test_null_price_row_dropped(self, sample_assets_raw):
        sample_assets_raw[0]["priceUsd"] = None
        df = transform_assets(sample_assets_raw)
        assert "bitcoin" not in df["id"].values

    def test_is_top_10_correct(self, sample_assets_raw):
        df = transform_assets(sample_assets_raw)
        assert df.loc[df["id"] == "bitcoin", "is_top_10"].values[0]

    def test_pct_max_supply_calculation(self, sample_assets_raw):
        df = transform_assets(sample_assets_raw)
        btc_pct = df.loc[df["id"] == "bitcoin", "pct_of_max_supply"].values[0]
        assert abs(btc_pct - 90.48) < 0.01

    def test_output_has_correct_columns(self, sample_assets_raw):
        expected = {"id", "rank", "symbol", "name", "price_usd",
                    "market_cap_usd", "volume_usd_24h", "change_pct_24h",
                    "vwap_24h", "supply", "max_supply",
                    "pct_of_max_supply", "is_top_10", "ingested_at"}
        df = transform_assets(sample_assets_raw)
        assert set(df.columns) == expected

    def test_empty_input(self):
        df = transform_assets([])
        assert len(df) == 0

# ── transform_history ─────────────────────────────────────────

class TestTransformHistory:

    def test_price_usd_is_float(self, sample_history_raw):
        df = transform_history(sample_history_raw)
        assert df["price_usd"].dtype == "float64"

    def test_timestamp_is_datetime(self, sample_history_raw):
        df = transform_history(sample_history_raw)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_row_count_preserved(self, sample_history_raw):
        df = transform_history(sample_history_raw)
        assert len(df) == len(sample_history_raw)

    def test_slug_column_present(self, sample_history_raw):
        df = transform_history(sample_history_raw)
        assert "slug" in df.columns