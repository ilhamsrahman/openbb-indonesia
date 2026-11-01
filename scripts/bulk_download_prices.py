"""One-time bulk download of daily IDX prices (full history) from Yahoo Finance.

Fills Data_raw/Prices/<SYMBOL>.csv for every EQUITY code in the latest KSEI
Balancepos file - the same cache the Indonesian Stock Chart widget reads.

Usage (in the conda env, from the openbb-indonesia folder):
    python scripts/bulk_download_prices.py                  # all stocks, skip ones already downloaded
    python scripts/bulk_download_prices.py --update         # also top up existing files with new days
    python scripts/bulk_download_prices.py BBCA TLKM ASII   # only these symbols
    python scripts/bulk_download_prices.py --sleep 3        # slower, if Yahoo rate-limits you

Safe to stop with Ctrl+C and re-run: finished stocks are skipped.
"""

import argparse
import csv
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # project root

from openbb_indonesia.fetchers import (
    OVERLAP_DAYS,
    PRICE_DIR,
    _download,
    _read_cache,
    _write_cache,
)

from core.paths import KSEI_MONTHLY as KSEI_DIR  # noqa: E402
FAILED_LOG = PRICE_DIR / "_failed.txt"
MAX_RETRIES = 3
RATE_LIMIT_WAIT = 60  # seconds to wait after a "Too Many Requests" error


def ksei_equity_codes() -> list[str]:
    latest = sorted(KSEI_DIR.glob("Balancepos*.txt"))[-1]
    with open(latest, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="|"))[1:]
    codes = {r[1].strip() for r in rows if len(r) > 2 and r[2].strip() == "EQUITY"}
    codes = sorted(c for c in codes if len(c) == 4)  # skip odd 5-letter codes (EDJSA, MAMIP...)
    print(f"{len(codes)} equity codes from {latest.name}")
    return codes


def is_rate_limit(e: Exception) -> bool:
    msg = f"{type(e).__name__} {e}".lower()
    return "ratelimit" in msg or "too many requests" in msg or "429" in msg


def fetch_one(symbol: str, update: bool) -> str:
    path = PRICE_DIR / f"{symbol}.csv"
    cached = _read_cache(path)
    if cached and not update:
        return "skipped (already downloaded)"

    start = date.fromisoformat(max(cached)) - timedelta(days=OVERLAP_DAYS) if cached else None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            new_rows = _download(symbol, start)
            break
        except Exception as e:
            if is_rate_limit(e) and attempt < MAX_RETRIES:
                print(f"   rate-limited, waiting {RATE_LIMIT_WAIT}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            raise
    if not new_rows and not cached:
        raise ValueError("no data on Yahoo (delisted, new listing, or different ticker)")
    cached.update(new_rows)
    _write_cache(path, cached)
    first, last = min(cached), max(cached)
    return f"{len(cached)} rows  {first} -> {last}  (+{len(new_rows)} fetched)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbols", nargs="*", help="symbols to download (default: all KSEI equities)")
    ap.add_argument("--update", action="store_true", help="top up files that already exist")
    ap.add_argument("--sleep", type=float, default=1.5, help="seconds between requests (default 1.5)")
    args = ap.parse_args()

    symbols = [s.upper().removesuffix(".JK") for s in args.symbols] or ksei_equity_codes()
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    started = datetime.now()

    try:
        for i, sym in enumerate(symbols, 1):
            try:
                result = fetch_one(sym, args.update)
                print(f"[{i}/{len(symbols)}] {sym}: {result}")
                if result.startswith("skipped"):
                    continue
            except Exception as e:
                print(f"[{i}/{len(symbols)}] {sym}: FAILED - {e}")
                failed.append(f"{sym}\t{e}")
            time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("\nStopped. Re-run the same command to continue where you left off.")

    if failed:
        FAILED_LOG.write_text("\n".join(failed) + "\n", encoding="utf-8")
    mins = (datetime.now() - started).total_seconds() / 60
    print(f"\nDone in {mins:.1f} min. Failed: {len(failed)}"
          + (f" (see {FAILED_LOG})" if failed else ""))


if __name__ == "__main__":
    sys.exit(main())
