"""IDX daily prices from Yahoo Finance (yfinance), cached to local CSV files.

Cache: Data_raw/Prices/<SYMBOL>.csv  (e.g. BBCA.csv)
- First request for a symbol downloads its full history.
- Each time run.py starts, the first request for a symbol downloads only the
  missing recent days and appends them; later requests in the same session
  read the CSV only (no Yahoo calls).
- If Yahoo fails, the cached data is served instead.
"""

import asyncio
import csv
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)

PRICE_DIR = Path(__file__).resolve().parents[1] / "Data_raw" / "Prices"
_updated_this_run: set[str] = set()  # symbols already refreshed since run.py started
OVERLAP_DAYS = 7         # re-download the last N days to pick up late corrections
DEFAULT_LOOKBACK = 365   # days returned when no start_date is given
FIELDS = ["date", "open", "high", "low", "close", "volume"]
NOT_ON_YAHOO_FILE = PRICE_DIR / "_failed.txt"   # written by bulk_download_prices.py
logging.getLogger("yfinance").setLevel(logging.CRITICAL)   # keep the server window clean


def not_on_yahoo() -> set[str]:
    """Codes Yahoo has no data for (first column of _failed.txt). Skipped to avoid noisy errors."""
    if not NOT_ON_YAHOO_FILE.exists():
        return set()
    return {line.split("\t")[0].strip().upper() for line in NOT_ON_YAHOO_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()}


def _base_symbol(symbol: str) -> str:
    """'bbca' / 'BBCA.JK' -> 'BBCA'."""
    return symbol.strip().upper().removesuffix(".JK")


def _read_cache(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["date"]: row for row in csv.DictReader(f)}


def _write_cache(path: Path, rows: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for d in sorted(rows):
            writer.writerow({k: rows[d][k] for k in FIELDS})
    tmp.replace(path)


def _download(base: str, start: date | None) -> dict[str, dict]:
    import yfinance as yf

    ticker = yf.Ticker(f"{base}.JK")
    if start is None:
        df = ticker.history(period="max", interval="1d", auto_adjust=False)
    else:
        df = ticker.history(start=start.isoformat(), interval="1d", auto_adjust=False)

    rows = {}
    for idx, r in df.iterrows():
        if any(r[c] != r[c] for c in ("Open", "High", "Low", "Close")):  # skip NaN rows
            continue
        d = idx.date().isoformat()
        rows[d] = {
            "date": d,
            "open": float(r["Open"]),
            "high": float(r["High"]),
            "low": float(r["Low"]),
            "close": float(r["Close"]),
            "volume": int(r["Volume"]),
        }
    return rows


def get_prices(symbol: str) -> list[dict]:
    """Return the full cached daily history for an IDX symbol, refreshing if stale."""
    base = _base_symbol(symbol)
    path = PRICE_DIR / f"{base}.csv"
    cached = _read_cache(path)
    if not cached and base in not_on_yahoo():
        raise ValueError(f"{base}.JK is not available on Yahoo Finance (listed in {NOT_ON_YAHOO_FILE.name})")

    if base not in _updated_this_run:
        start = None
        if cached:
            start = date.fromisoformat(max(cached)) - timedelta(days=OVERLAP_DAYS)
        try:
            new_rows = _download(base, start)
            if new_rows or cached:
                cached.update(new_rows)
                _write_cache(path, cached)
        except Exception as e:  # Yahoo down / rate-limited: fall back to cache
            if not cached:
                raise ValueError(f"Could not download prices for {base}.JK: {e}") from e
        _updated_this_run.add(base)

    if not cached:
        raise ValueError(f"No price data found for {base}.JK")
    return [cached[d] for d in sorted(cached)]


class IndoEquityHistoricalFetcher(
    Fetcher[EquityHistoricalQueryParams, list[EquityHistoricalData]]
):
    @classmethod
    def transform_query(cls, params: dict) -> EquityHistoricalQueryParams:
        return EquityHistoricalQueryParams(**params)

    @classmethod
    async def aextract_data(
        cls,
        query: EquityHistoricalQueryParams,
        credentials: dict | None,
        **kwargs,
    ) -> list[dict]:
        rows = await asyncio.to_thread(get_prices, query.symbol)

        start = query.start_date or (datetime.now().date() - timedelta(days=DEFAULT_LOOKBACK))
        end = query.end_date or datetime.now().date()
        return [r for r in rows if start.isoformat() <= r["date"] <= end.isoformat()]

    @classmethod
    def transform_data(
        cls,
        query: EquityHistoricalQueryParams,
        data: list[dict],
        **kwargs,
    ) -> list[EquityHistoricalData]:
        return [EquityHistoricalData(**row) for row in data]
