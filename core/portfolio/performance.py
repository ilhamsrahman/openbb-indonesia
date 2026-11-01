"""Valuation and the daily NAV index (unit method)."""

from collections import defaultdict
from datetime import date

from .holdings import holdings_on
from .prices import _benchmark_prices, _last_on_or_before, _price_cache, _stock_prices, price_on
from .tracker import EXTERNAL_FLOW, _f, _tracker_cache, load_tracker


# ---------------------------------------------------------------- valuation & NAV
TRADABLE_AT_COST = {"PBS", "FR"}   # tradable SBN: valued at purchase price (no price feed yet)

def _bond_value(code: str, b: dict) -> float:
    """Retail SR/ST/ORI/SBR at face value; PBS/FR at purchase cost."""
    ty = str(load_tracker()["bonds"].get(code, {}).get("Type") or "").upper()
    return b["cost"] if ty in TRADABLE_AT_COST and b["cost"] > 0 else b["face"]

def value_on(d: date) -> dict:
    h = holdings_on(d)
    t = load_tracker()
    stock_mv = {"Core": 0.0, "Dibuang": 0.0}
    for code, s in h["stocks"].items():
        if s["qty"] <= 0:
            continue
        p, _, _ = price_on(code, d)
        tag = str(t["stocks"].get(code, {}).get("Tag") or "Core").strip().title()
        stock_mv["Dibuang" if tag == "Dibuang" else "Core"] += (p or 0) * s["qty"]
    bond_face = sum(_bond_value(code, b) for (code, _), b in h["bonds"].items() if b["face"] > 0)
    return {"stocks_core": stock_mv["Core"], "stocks_dibuang": stock_mv["Dibuang"],
            "stocks": stock_mv["Core"] + stock_mv["Dibuang"], "bonds": bond_face, "cash": h["cash"],
            "total": stock_mv["Core"] + stock_mv["Dibuang"] + bond_face + h["cash"]}

def _calendar_days(start: date, end: date) -> list[date]:
    t = load_tracker()
    bench = _benchmark_prices(str(t["settings"].get("Benchmark") or "^JKSE"))
    days = {d for d in bench if start <= d <= end}
    if len(days) < 2:  # no benchmark data: use stock price dates
        for code in {r["Code"] for r in t["transactions"] if r["Asset"] == "Stock"}:
            days |= {d for d in _stock_prices(code) if start <= d <= end}
    days |= {start}
    return sorted(days)

def nav_series() -> list[dict]:
    t = load_tracker()
    cache = _tracker_cache.setdefault("computed", {})
    stamp = (date.today(), len(_price_cache))
    if cache.get("nav_stamp") == stamp:
        return cache["nav"]
    start, today = t["start"], date.today()
    days = _calendar_days(start, today)
    flows = defaultdict(float)
    for r in t["transactions"]:
        if r["Type"] in EXTERNAL_FLOW:
            flows[r["Date"]] += EXTERNAL_FLOW[r["Type"]] * _f(r.get("Amount (IDR)"))
    bench_sym = str(t["settings"].get("Benchmark") or "^JKSE")
    bench = _benchmark_prices(bench_sym)
    b0 = bench.get(max((x for x in bench if x <= start), default=start))

    out, units, prev_day = [], None, None
    for d in days:
        v = value_on(d)
        f = sum(amt for fd, amt in flows.items() if (prev_day is None or fd > prev_day) and fd <= d) if prev_day else 0
        if units is None:
            units = v["total"] / 100.0
            nav = 100.0
        else:
            nav_pre = (v["total"] - f) / units if units else 100.0
            if f and nav_pre:
                units += f / nav_pre
            nav = v["total"] / units if units else 100.0
        bd = _last_on_or_before("__bench__", bench, d) if bench else None
        bp = bench.get(bd) if bd else None
        out.append({"date": d.isoformat(), "nav": round(nav, 4),
                    "benchmark": round(bp / b0 * 100, 4) if (bp and b0) else None,
                    "total_value": round(v["total"]), "stocks": round(v["stocks"]), "bonds": round(v["bonds"]),
                    "cash": round(v["cash"]), "external_flow": round(f)})
        prev_day = d
    cache.update(nav=out, nav_stamp=stamp)
    return out
