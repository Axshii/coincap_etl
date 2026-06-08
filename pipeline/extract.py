import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from pipeline.logger import get_logger

load_dotenv()
log = get_logger("extract")
BASE_URL = "https://rest.coincap.io/v3"


def _get_headers() -> dict:
    """Build auth headers from the API key in .env"""
    api_key = os.getenv("COINCAP_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "COINCAP_API_KEY is not set. Check your .env file."
        )
    return {"Authorization": f"Bearer {api_key}"}


def extract_assets(limit: int = 50) -> list[dict]:
    log.info(f"Fetching top {limit} assets from CoinCap...")
    try:
        resp = requests.get(
            f"{BASE_URL}/assets",
            headers=_get_headers(),
            params={"limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        log.info(f"Fetched {len(data)} assets successfully")
        log.debug(f"First asset id: {data[0]['id'] if data else 'none'}")
        return data

    except requests.exceptions.HTTPError as e:
        log.error(f"extract_assets failed: {e}")
        raise

    except requests.exceptions.Timeout:
        log.error("extract_assets timed out after 10s")
        raise

    except requests.exceptions.ConnectionError:
        log.error("extract_assets: no network connection")
        raise


def extract_price_history(
    slug: str,
    interval: str = "h1",
    since: datetime = None,       # ← new parameter
) -> list[dict]:
    """
    Fetch price history for a coin.
    If 'since' is provided, only fetch rows after that timestamp.
    If not, fetch the last 7 days (first-run backfill).
    """
    now_ms = int(time.time() * 1000)

    if since:
        start_ms = int(since.timestamp() * 1000)
        log.info(f"[{slug}] fetching history since {since.isoformat()}")
    else:
        start_ms = now_ms - (7 * 24 * 60 * 60 * 1000)
        log.info(f"[{slug}] no watermark — fetching 7 day backfill")

    resp = requests.get(
        f"{BASE_URL}/assets/{slug}/history",
        headers=_get_headers(),
        params={
            "interval": interval,
            "start":    start_ms,
            "end":      now_ms,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()["data"]

    for row in data:
        row["slug"] = slug

    log.info(f"[{slug}] fetched {len(data)} rows")
    return data


def extract_exchanges(limit: int = 20) -> list[dict]:
    log.info(f"Fetching top {limit} exchanges from CoinCap...")
    try:
        resp = requests.get(
            f"{BASE_URL}/exchanges",
            headers=_get_headers(),
            params={"limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        log.info(f"Fetched {len(data)} exchanges successfully")
        log.debug(f"First exchange: {data[0].get('exchangeId', 'unknown') if data else 'none'}")
        return data

    except requests.exceptions.HTTPError as e:
        log.error(f"extract_exchanges failed: {e}")
        raise

    except requests.exceptions.Timeout:
        log.error("extract_exchanges timed out after 10s")
        raise

    except requests.exceptions.ConnectionError:
        log.error("extract_exchanges: no network connection")
        raise