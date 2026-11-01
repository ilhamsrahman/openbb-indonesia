"""Price lookups: Yahoo daily closes (via the provider cache), benchmark, KSEI fallback, dividends."""

import bisect
import csv
import threading
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Optional

from core.paths import PRICE_DIR
from .tracker import _f


# ---------------------------------------------------------------- prices
_price_cache: dict[str, dict[date, float]] = {}

_price_lock = threading.Lock()

def _read_csv_prices(path: Path) -> dict[date, float]:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {date.fromisoformat(r["date"]): float(r["close"]) for r in csv.DictReader(f) if r.get("close")}

def _stock_prices(ticker: str) -> dict[date, float]:
    with _price_lock:
        if ticker in _price_cache:
            return _price_cache[ticker]
    series: dict[date, float] = {}
    try:  # refreshes from Yahoo once per run.py session
        from openbb_indonesia.fetchers import get_prices
        series = {date.fromisoformat(r["date"]): float(r["close"]) for r in get_prices(ticker)}
    except Exception:
        series = _read_csv_prices(PRICE_DIR / f"{ticker}.csv")
    with _price_lock:
        _price_cache[ticker] = series
    return series

def _benchmark_prices(symbol: str) -> dict[date, float]:
    key = f"__bench__{symbol}"
    with _price_lock:
        if key in _price_cache:
            return _price_cache[key]
    path = PRICE_DIR / f"_{symbol.replace('^', '')}.csv"
    series = _read_csv_prices(path)
    try:
        import yfinance as yf
        start = (max(series) - timedelta(days=7)) if series else date(2025, 1, 1)
        df = yf.Ticker(symbol).history(start=start.isoformat(), interval="1d", auto_adjust=False)
        for idx, r in df.iterrows():
            if r["Close"] == r["Close"]:
                series[idx.date()] = float(r["Close"])
        PRICE_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "close"])
            for d in sorted(series):
                w.writerow([d.isoformat(), series[d]])
    except Exception:
        pass
    with _price_lock:
        _price_cache[key] = series
    return series

_ksei_close: dict[str, tuple[date, float]] = {}

def _ksei_fallback(ticker: str) -> Optional[tuple[date, float]]:
    if not _ksei_close:
        try:
            from core.ksei.master import list_months, load_master
            for m in load_master(list_months()[0]):
                if m.get("Type") == "EQUITY" and _f(m.get("Closing Price")) > 0:
                    d = datetime.strptime(m["Date"], "%d-%b-%Y").date()
                    _ksei_close[m["Code"]] = (d, _f(m["Closing Price"]))
        except Exception:
            _ksei_close["__none__"] = (date.min, 0)
    return _ksei_close.get(ticker)

_sorted_keys: dict[str, list] = {}

def _last_on_or_before(key: str, series: dict, d: date) -> Optional[date]:
    keys = _sorted_keys.get(key)
    if keys is None or len(keys) != len(series):
        keys = _sorted_keys[key] = sorted(series)
    i = bisect.bisect_right(keys, d)
    return keys[i - 1] if i else None

def price_on(ticker: str, d: date) -> tuple[Optional[float], Optional[date], str]:
    series = _stock_prices(ticker)
    best = _last_on_or_before(ticker, series, d)
    if best:
        return series[best], best, "Yahoo"
    fb = _ksei_fallback(ticker)
    if fb and fb[0] <= d + timedelta(days=31):
        return fb[1], fb[0], "KSEI month-end"
    return None, None, "missing"

# ---------------- 2. Dividends (Yahoo Finance, cached per session)
DIV_DIR = PRICE_DIR / "_dividends"

_div_cache: dict[str, dict[date, float]] = {}

def _dividends(ticker: str) -> dict[date, float]:
    with _price_lock:
        if ticker in _div_cache:
            return _div_cache[ticker]
    path = DIV_DIR / f"{ticker}.csv"
    series = _read_csv_prices(path) if path.exists() else {}
    try:
        from openbb_indonesia.fetchers import not_on_yahoo
        skip = ticker in not_on_yahoo()
    except Exception:
        skip = False
    try:
        if skip:
            raise LookupError("not on Yahoo")
        import yfinance as yf
        divs = yf.Ticker(f"{ticker}.JK").dividends
        fresh = {idx.date(): float(v) for idx, v in divs.items() if v == v and v > 0}
        if fresh or not series:
            series = fresh
            DIV_DIR.mkdir(parents=True, exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "close"])           # same 2-column format as price files
                for d in sorted(series):
                    w.writerow([d.isoformat(), series[d]])
    except Exception:
        pass
    with _price_lock:
        _div_cache[ticker] = series
    return series
