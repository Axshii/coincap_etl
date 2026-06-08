# analysis/visualise.py — run everything
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3, pandas as pd
import plotly.express as px
from pipeline.logger import get_logger

log = get_logger("visualise")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crypto.db")
os.makedirs("analysis", exist_ok=True)

def query(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

def latest_snapshot_condition():
    return "ingested_at = (SELECT MAX(ingested_at) FROM asset_snapshots)"

# 1. Price history line chart
def chart_price_history():
    df = query("SELECT slug, timestamp, price_usd FROM price_history ORDER BY slug, timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    fig = px.line(df, x="timestamp", y="price_usd", color="slug",
                  title="Price history (7 days)", template="plotly_white")
    fig.update_layout(hovermode="x unified")
    fig.write_html("analysis/price_history.html")
    log.info("Saved analysis/price_history.html")

# 2. Market cap bar chart
def chart_market_cap():
    df = query(f"""
        SELECT name, symbol, market_cap_usd / 1e9 AS market_cap_b
        FROM   asset_snapshots
        WHERE  {latest_snapshot_condition()}
        ORDER  BY market_cap_usd DESC LIMIT 10
    """)
    fig = px.bar(df, x="market_cap_b", y="symbol", orientation="h",
                  title="Top 10 by market cap ($B)", template="plotly_white",
                  color="market_cap_b", color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    fig.write_html("analysis/market_cap.html")
    log.info("Saved analysis/market_cap.html")

# 3. 24h movers bar chart
def chart_movers():
    df = query(f"""
        SELECT symbol, change_pct_24h
        FROM   asset_snapshots
        WHERE  {latest_snapshot_condition()} AND change_pct_24h IS NOT NULL
        ORDER  BY change_pct_24h DESC LIMIT 20
    """)
    df["colour"] = df["change_pct_24h"].apply(lambda x: "gain" if x >= 0 else "loss")
    fig = px.bar(df, x="symbol", y="change_pct_24h", color="colour",
                  color_discrete_map={"gain": "#22c55e", "loss": "#ef4444"},
                  title="24h price change (%)", template="plotly_white")
    fig.write_html("analysis/movers_24h.html")
    log.info("Saved analysis/movers_24h.html")

# 4. Bubble scatter chart
def chart_bubble():
    df = query(f"""
        SELECT name, symbol, volume_usd_24h, change_pct_24h, market_cap_usd
        FROM   asset_snapshots
        WHERE  {latest_snapshot_condition()}
          AND  volume_usd_24h IS NOT NULL AND change_pct_24h IS NOT NULL
    """)
    fig = px.scatter(df, x="volume_usd_24h", y="change_pct_24h",
                      size="market_cap_usd", hover_name="name", text="symbol",
                      log_x=True, color="change_pct_24h",
                      color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                      title="Volume vs price change — bubble = market cap",
                      template="plotly_white")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.write_html("analysis/bubble.html")
    log.info("Saved analysis/bubble.html")

if __name__ == "__main__":
    log.info("Generating all charts...")
    chart_price_history()
    chart_market_cap()
    chart_movers()
    chart_bubble()
    log.info("Done — open the HTML files in analysis/")

