import pandas as pd
from datetime import datetime, timezone
from pipeline.logger import get_logger

log = get_logger("transform")

ASSET_SCHEMA = [
    "id", "rank", "symbol", "name", "price_usd",
    "market_cap_usd", "volume_usd_24h", "change_pct_24h",
    "vwap_24h", "supply", "max_supply", "pct_of_max_supply",
    "is_top_10", "ingested_at",
]

HISTORY_SCHEMA = ["slug", "timestamp", "price_usd", "ingested_at"]


def transform_assets(raw: list[dict]) -> pd.DataFrame:
    log.info(f"Transforming {len(raw)} raw asset rows...")

    if not raw:
        log.warning("transform_assets received empty input — returning empty DataFrame")
        return pd.DataFrame(columns=ASSET_SCHEMA)

    df = pd.DataFrame(raw)

    # ── 1. Cast all numeric columns (API returns strings) ────────────
    numeric_cols = [
        "priceUsd", "marketCapUsd", "volumeUsd24Hr",
        "changePercent24Hr", "supply", "maxSupply", "vwap24Hr",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")

    # ── 2. Drop rows with no price ───────────────────────────────────
    before = len(df)
    df = df.dropna(subset=["priceUsd"])
    dropped = before - len(df)
    if dropped > 0:
        log.warning(f"{dropped} row(s) dropped -- null priceUsd")
    else:
        log.debug("No rows dropped -- all prices present")

    # ── 3. Rename to snake_case ──────────────────────────────────────
    df = df.rename(columns={
        "priceUsd":          "price_usd",
        "marketCapUsd":      "market_cap_usd",
        "volumeUsd24Hr":     "volume_usd_24h",
        "changePercent24Hr": "change_pct_24h",
        "vwap24Hr":          "vwap_24h",
        "maxSupply":         "max_supply",
    })

    # ── 4. Derived columns ───────────────────────────────────────────
    df["is_top_10"] = df["rank"] <= 10
    df["pct_of_max_supply"] = (
        (df["supply"] / df["max_supply"] * 100)
        .round(2)
        .where(df["max_supply"].notna())   # stays NaN when max_supply is None (e.g. ETH)
    )
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()

    # ── 5. Validate schema ───────────────────────────────────────────
    missing = set(ASSET_SCHEMA) - set(df.columns)
    if missing:
        raise ValueError(f"transform_assets: missing columns after transform: {missing}")

    log.info(f"Transform complete -- {len(df)} clean asset rows")
    return df[ASSET_SCHEMA]


def transform_history(raw: list[dict]) -> pd.DataFrame:
    log.info(f"Transforming {len(raw)} raw history rows...")

    if not raw:
        log.warning("transform_history received empty input -- returning empty DataFrame")
        return pd.DataFrame(columns=HISTORY_SCHEMA)

    df = pd.DataFrame(raw)

    # ── 1. Cast numeric and datetime ─────────────────────────────────
    df["price_usd"] = pd.to_numeric(df["priceUsd"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["time"], unit="ms", utc=True)

    # ── 2. Drop rows with no price ───────────────────────────────────
    before = len(df)
    df = df.dropna(subset=["price_usd"])
    dropped = before - len(df)
    if dropped > 0:
        log.warning(f"{dropped} history row(s) dropped -- null price_usd")
    else:
        log.debug("No history rows dropped -- all prices present")

    # ── 3. Add ingestion timestamp ───────────────────────────────────
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()

    # ── 4. Validate schema ───────────────────────────────────────────
    missing = set(HISTORY_SCHEMA) - set(df.columns)
    if missing:
        raise ValueError(f"transform_history: missing columns after transform: {missing}")

    log.info(f"Transform complete -- {len(df)} clean history rows")
    return df[HISTORY_SCHEMA]


def transform_exchanges(raw: list[dict]) -> pd.DataFrame:
    EXCHANGE_SCHEMA = [
        "exchange_id", "name", "rank",
        "volume_usd", "trading_pairs", "pct_total_volume", "ingested_at",
    ]

    log.info(f"Transforming {len(raw)} raw exchange rows...")

    if not raw:
        log.warning("transform_exchanges received empty input -- returning empty DataFrame")
        return pd.DataFrame(columns=EXCHANGE_SCHEMA)

    df = pd.DataFrame(raw)

    # ── 1. Cast numeric columns ──────────────────────────────────────
    df["volumeUsd"]       = pd.to_numeric(df.get("volumeUsd"),       errors="coerce")
    df["tradingPairs"]    = pd.to_numeric(df.get("tradingPairs"),     errors="coerce")
    df["percentTotalVolume"] = pd.to_numeric(df.get("percentTotalVolume"), errors="coerce")
    df["rank"]            = pd.to_numeric(df.get("rank"),             errors="coerce").astype("Int64")

    # ── 2. Rename ────────────────────────────────────────────────────
    df = df.rename(columns={
        "exchangeId":          "exchange_id",
        "volumeUsd":           "volume_usd",
        "tradingPairs":        "trading_pairs",
        "percentTotalVolume":  "pct_total_volume",
    })

    # ── 3. Add ingestion timestamp ───────────────────────────────────
    df["ingested_at"] = datetime.now(timezone.utc).isoformat()

    # ── 4. Validate schema ───────────────────────────────────────────
    missing = set(EXCHANGE_SCHEMA) - set(df.columns)
    if missing:
        raise ValueError(f"transform_exchanges: missing columns after transform: {missing}")

    log.info(f"Transform complete -- {len(df)} clean exchange rows")
    return df[EXCHANGE_SCHEMA]