import sys, os, time
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from pipeline.logger    import get_logger
from pipeline.state     import get_watermark, set_watermark
from pipeline.extract   import extract_assets, extract_price_history, extract_exchanges
from pipeline.transform import transform_assets, transform_history, transform_exchanges
from pipeline.load      import load_assets, load_history, load_exchanges

log = get_logger("run")
COINS = ["bitcoin", "ethereum", "solana"]

def run_assets_pipeline():
    # Snapshot pipeline — always fetches latest (no watermark needed)
    log.info("=== Asset snapshot pipeline ===")
    raw = extract_assets(limit=50)
    df  = transform_assets(raw)
    load_assets(df)

def run_exchanges_pipeline():
    log.info("=== Exchanges snapshot pipeline ===")
    raw = extract_exchanges()
    df  = transform_exchanges(raw)
    load_exchanges(df)

def run_history_pipeline():
    # Incremental pipeline — only fetch what's new since last run
    log.info("=== Price history pipeline (incremental) ===")
    for coin in COINS:
        pipeline_name = f"history_{coin}"

        # 1. Read watermark — when did we last load this coin?
        since = get_watermark(pipeline_name, default_days_back=7)

        # 2. Extract only rows after the watermark
        raw = extract_price_history(coin, interval="h1", since=since)

        if not raw:
            log.info(f"[{coin}] no new data since {since.isoformat()}")
            continue

        # 3. Transform
        df = transform_history(raw)

        # 4. Load and get back the max timestamp
        new_watermark = load_history(df)

        # 5. Save new watermark — only if load succeeded
        if new_watermark:
            set_watermark(pipeline_name, new_watermark)

if __name__ == "__main__":
    start = time.time()
    log.info("=== CoinCap ETL pipeline starting ===")
    try:
        run_assets_pipeline()
        run_history_pipeline()
        run_exchanges_pipeline()
        log.info(f"Done in {round(time.time()-start, 2)}s")
    except Exception:
        log.exception("Pipeline failed")
        sys.exit(1)