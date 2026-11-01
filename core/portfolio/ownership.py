"""KSEI Balancepos ownership signals for held stocks (foreign %, mutual funds)."""

import csv
from typing import Optional

from core.paths import KSEI_MONTHLY
from .tracker import _f


_bp_cache: dict[str, dict] = {}

CATS = ["IS", "CP", "PF", "IB", "ID", "MF", "SC", "FD", "OT"]

def _balancepos_months() -> list[str]:
    return sorted({p.stem.replace("Balancepos", "")[:6] for p in KSEI_MONTHLY.glob("Balancepos*.txt")})

def _balancepos(ym: str) -> dict:
    if ym in _bp_cache:
        return _bp_cache[ym]
    out = {}
    files = sorted(KSEI_MONTHLY.glob(f"Balancepos{ym}*.txt"))
    if files:
        with open(files[-1], encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter="|")
            next(reader, None)
            for r in reader:
                if len(r) < 25 or r[2].strip() != "EQUITY":
                    continue
                local = {c: _f(r[5 + i]) for i, c in enumerate(CATS)}
                foreign = {c: _f(r[15 + i]) for i, c in enumerate(CATS)}
                tot = _f(r[14]) + _f(r[24])
                out[r[1].strip()] = {"local": local, "foreign": foreign, "local_total": _f(r[14]),
                                     "foreign_total": _f(r[24]), "total": tot}
    _bp_cache[ym] = out
    return out

def _foreign_pct(rec: Optional[dict]) -> Optional[float]:
    return rec["foreign_total"] / rec["total"] * 100 if rec and rec["total"] else None

def _share_pct(rec: Optional[dict], side: str, cat: str) -> Optional[float]:
    return rec[side][cat] / rec["total"] * 100 if rec and rec["total"] else None

def ownership_for(ticker: str) -> dict:
    months = _balancepos_months()
    if not months:
        return {}
    latest = months[-1]
    pick = lambda back: months[-1 - back] if len(months) > back else None
    cur = _balancepos(latest).get(ticker)
    res = {"ksei_month": latest, "foreign_pct": None, "foreign_chg_1m": None, "foreign_chg_3m": None,
           "foreign_chg_12m": None, "mutual_fund_pct": None, "mutual_fund_chg_1m": None,
           "pension_insurance_pct": None, "individual_pct": None}
    if not cur:
        return res
    fp = _foreign_pct(cur)
    res["foreign_pct"] = round(fp, 2) if fp is not None else None
    for back, key in ((1, "foreign_chg_1m"), (3, "foreign_chg_3m"), (12, "foreign_chg_12m")):
        m = pick(back)
        old = _foreign_pct(_balancepos(m).get(ticker)) if m else None
        res[key] = round(fp - old, 2) if (fp is not None and old is not None) else None
    mf = (_share_pct(cur, "local", "MF") or 0) + (_share_pct(cur, "foreign", "MF") or 0)
    res["mutual_fund_pct"] = round(mf, 2)
    m1 = pick(1)
    prev = _balancepos(m1).get(ticker) if m1 else None
    if prev:
        mf_prev = (_share_pct(prev, "local", "MF") or 0) + (_share_pct(prev, "foreign", "MF") or 0)
        res["mutual_fund_chg_1m"] = round(mf - mf_prev, 2)
    res["pension_insurance_pct"] = round(sum((_share_pct(cur, s, c) or 0) for s in ("local", "foreign")
                                             for c in ("PF", "IS")), 2)
    res["individual_pct"] = round((_share_pct(cur, "local", "ID") or 0) + (_share_pct(cur, "foreign", "ID") or 0), 2)
    return res

def _signal(o: dict) -> str:
    c1, c3 = o.get("foreign_chg_1m"), o.get("foreign_chg_3m")
    if c1 is None:
        return "No KSEI data"
    parts = []
    if c1 >= 0.5:
        parts.append("Foreign buying (1M)")
    elif c1 <= -0.5:
        parts.append("Foreign selling (1M)")
    if c3 is not None and abs(c3) >= 1.5:
        parts.append(("Foreign accumulation" if c3 > 0 else "Foreign exit") + " (3M)")
    mf = o.get("mutual_fund_chg_1m")
    if mf is not None and abs(mf) >= 0.5:
        parts.append("Mutual funds " + ("adding" if mf > 0 else "reducing"))
    return ", ".join(parts) or "Stable"
