import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pipeline.logger import get_logger

log = get_logger("load")

DB_PATH = "data/crypto.db"

CREATE_ASSETS = """
CREATE TABLE IF NOT EXISTS asset_snapshots (
    id                TEXT,
    rank              INTEGER,
    symbol            TEXT,
    name              TEXT,
    price_usd         REAL,
    market_cap_usd    REAL,
    volume_usd_24h    REAL,
    change_pct_24h    REAL,
    vwap_24h          REAL,
    supply            REAL,
    max_supply        REAL,
    pct_of_max_supply REAL,
    is_top_10         INTEGER,
    ingested_at       TEXT,
    PRIMARY KEY (id, ingested_at)
)"""

CREATE_HISTORY = """
CREATE TABLE IF NOT EXISTS price_history (
    slug        TEXT,
    timestamp   TEXT,
    price_usd   REAL,
    ingested_at TEXT,
    PRIMARY KEY (slug, timestamp)
)"""

CREATE_EXCHANGES = """
CREATE TABLE IF NOT EXISTS exchange_snapshots (
    exchange_id      TEXT,
    name             TEXT,
    rank             INTEGER,
    volume_usd       REAL,
    trading_pairs    INTEGER,
    pct_total_volume REAL,
    ingested_at      TEXT,
    PRIMARY KEY (exchange_id, ingested_at)
)"""


def get_conn() -> sqlite3.Connection:
    """Open DB connection and ensure all tables exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_ASSETS)
    conn.execute(CREATE_HISTORY)
    conn.execute(CREATE_EXCHANGES)
    conn.commit()
    return conn


def load_assets(df: pd.DataFrame) -> None:
    """Append an asset snapshot. Uses get_conn() so tables are always created first."""
    log.info(f"Loading {len(df)} rows into asset_snapshots...")
    try:
        conn = get_conn()                          # was: sqlite3.connect() — bypassed table creation
        df.to_sql("asset_snapshots", conn, if_exists="append", index=False)
        count = conn.execute(
            "SELECT COUNT(*) FROM asset_snapshots"
        ).fetchone()[0]
        log.info(f"Load complete -- {count} total rows now in DB")
        conn.close()
    except Exception as e:
        log.error(f"Failed to load assets into DB: {e}")
        raise


def load_history(df: pd.DataFrame) -> datetime | None:
    """
    Upsert history rows. Returns the max timestamp loaded
    so the caller can update the watermark.
    Returns None if df is empty (nothing to update).
    """
    if df.empty:
        log.info("No new rows to load — already up to date")
        return None

    conn = sqlite3.connect("data/crypto.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            slug        TEXT,
            timestamp   TEXT,
            price_usd   REAL,
            ingested_at TEXT,
            PRIMARY KEY (slug, timestamp)
        )""")
    
    df["timestamp"] = df["timestamp"].astype(str)
    df["ingested_at"] = df["ingested_at"].astype(str)

    conn.executemany("""
        INSERT OR IGNORE INTO price_history
        VALUES (:slug, :timestamp, :price_usd, :ingested_at)
    """, df.to_dict("records"))
    conn.commit()

    # Find the latest timestamp we just wrote
    max_ts = pd.to_datetime(df["timestamp"].max(), utc=True).to_pydatetime()
    
    log.info(f"Loaded {len(df)} rows — latest: {max_ts.isoformat()}")
    conn.close()
    return max_ts                          

def load_exchanges(df: pd.DataFrame) -> None:
    """Append an exchange snapshot."""
    if df.empty:
        log.info("No exchange rows to load")
        return

    log.info(f"Loading {len(df)} rows into exchange_snapshots...")
    try:
        conn = get_conn()
        df.to_sql("exchange_snapshots", conn, if_exists="append", index=False)
        count = conn.execute(
            "SELECT COUNT(*) FROM exchange_snapshots"
        ).fetchone()[0]
        log.info(f"Load complete -- {count} total rows now in DB")
        conn.close()
    except Exception as e:
        log.error(f"Failed to load exchanges into DB: {e}")
        raise