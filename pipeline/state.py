import sqlite3
from datetime import datetime, timezone, timedelta
from pipeline.logger import get_logger

log = get_logger("state")
DB_PATH = "data/crypto.db"

CREATE_STATE = """
CREATE TABLE IF NOT EXISTS pipeline_state (
    pipeline_name  TEXT PRIMARY KEY,
    last_loaded_at TEXT NOT NULL,
    updated_at     TEXT NOT NULL
)"""

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_STATE)
    conn.commit()
    return conn

def get_watermark(pipeline_name: str, default_days_back: int = 7) -> datetime:
    """
    Return the last loaded timestamp for this pipeline.
    If no watermark exists (first run), default to N days ago.
    """
    conn = _conn()
    row = conn.execute(
        "SELECT last_loaded_at FROM pipeline_state WHERE pipeline_name = ?",
        (pipeline_name,)
    ).fetchone()
    conn.close()

    if row:
        wm = datetime.fromisoformat(row[0])
        log.info(f"[{pipeline_name}] watermark: {wm.isoformat()}")
        return wm
    else:
        # First run — backfill from N days ago
        default = datetime.now(timezone.utc) - timedelta(days=default_days_back)
        log.info(f"[{pipeline_name}] no watermark — backfilling {default_days_back} days")
        return default

def set_watermark(pipeline_name: str, timestamp: datetime):
    """
    Update the watermark after a successful load.
    Only call this AFTER data has been committed — never before.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    conn.execute("""
        INSERT INTO pipeline_state (pipeline_name, last_loaded_at, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(pipeline_name) DO UPDATE SET
            last_loaded_at = excluded.last_loaded_at,
            updated_at     = excluded.updated_at
    """, (pipeline_name, timestamp.isoformat(), now))
    conn.commit()
    conn.close()
    log.info(f"[{pipeline_name}] watermark updated to {timestamp.isoformat()}")